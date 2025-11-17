"""
Bank Statement Extractor for XFORIA DAD
Extracts structured information from bank statement images
"""

import re
from typing import Dict, List, Optional
from google.cloud import vision


class BankStatementExtractor:
    """Extract structured information from bank statement images."""

    def __init__(self, credentials_path: str):
        self.client = vision.ImageAnnotatorClient.from_service_account_file(credentials_path)

    def extract_statement_details(self, image_path: str) -> Dict:
        """Extract details from a bank statement image."""
        with open(image_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = self.client.document_text_detection(image=image)

        if response.error.message:
            raise Exception(f"Google Vision API Error: {response.error.message}")

        if response.full_text_annotation and response.full_text_annotation.text:
            full_text = response.full_text_annotation.text
        else:
            texts = response.text_annotations
            full_text = texts[0].description if texts else ""

        lines = [line.strip() for line in full_text.splitlines() if line.strip()]

        statement_details = {
            "filename": image_path.split('/')[-1],
            "bank_name": self._extract_bank_name(lines),
            "account_holder": self._extract_account_holder(lines),
            "account_number": self._extract_account_number(full_text),
            "statement_period": self._extract_statement_period(full_text),
            "balances": self._extract_balances(full_text, lines),
            "transactions": self._extract_transactions(lines),
            "raw_text": full_text[:1000],  # Limit to first 1000 chars
        }

        # Infer balances from transactions if not found in summary
        statement_details["balances"] = self._infer_missing_balances(
            statement_details["balances"],
            statement_details["transactions"]
        )

        statement_details["summary"] = self._build_summary(statement_details)
        return statement_details

    def _extract_bank_name(self, lines: List[str]) -> Optional[str]:
        """Extract bank name from the statement."""
        security_phrases = [
            "THIS MULTI-TONE AREA",
            "ORIGINAL DOCUMENT",
            "SECURITY FEATURE",
        ]

        # Known bank names that might appear without the word "BANK"
        known_banks = [
            "WELLS FARGO", "CHASE", "CITIBANK", "BANK OF AMERICA",
            "CAPITAL ONE", "US BANK", "PNC", "TD BANK", "TRUIST"
        ]

        for line in lines[:12]:
            upper = line.upper()
            if any(phrase in upper for phrase in security_phrases):
                continue

            # Check for known bank names first
            for bank in known_banks:
                if bank in upper:
                    return line.strip()

            # Then check for generic bank keywords
            if any(keyword in upper for keyword in ["BANK", "CREDIT UNION", "FINANCIAL"]):
                return line.strip()
        return None

    def _extract_account_holder(self, lines: List[str]) -> Optional[str]:
        """Extract account holder name."""
        skip_keywords = {
            "BANK", "STATEMENT", "CUSTOMER", "ACCOUNT", "SUMMARY",
            "SERVICE", "INFORMATION", "TRANSACTION", "CHECKING",
            "SAVINGS", "TOTAL", "PAGE", "DATE", "CENTER",
            "JPMORGAN", "THIS", "MULTI-TONE", "ORIGINAL", "DOCUMENT",
            "WELLS", "FARGO", "CHASE", "CITIBANK", "CAPITAL", "ONE",
            "NATIONAL", "FIRST", "FINANCIAL", "CREDIT", "UNION",
            "BOA", "BOX", "COLUMBUS", "P.O.", "AMERICA"
        }
        for line in lines[:40]:
            candidate = line.strip()
            if not candidate:
                continue
            upper = candidate.upper()
            if any(keyword in upper for keyword in skip_keywords):
                continue
            if any(char.isdigit() for char in candidate):
                continue
            words = candidate.split()
            if len(words) >= 2 and all(len(word) > 1 for word in words):
                return candidate
        return None

    def _extract_account_number(self, text: str) -> Optional[str]:
        """Extract account number."""
        patterns = [
            r'Account\s+(?:Number|No\.?)[:\s#]*([A-Z0-9\-\*]+)',
            r'Acct\s+(?:Number|No\.?)[:\s#]*([A-Z0-9\-\*]+)',
            r'Account\s*#[\s:]*([A-Z0-9\-\*]+)',
            r'account\s+ending\s+in\s+(\d{4})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                raw_value = match.group(1).strip()
                digits = re.sub(r"\D", "", raw_value)
                if len(digits) >= 4:
                    return digits[-4:]
                return raw_value
        return None

    def _extract_statement_period(self, text: str) -> Optional[str]:
        """Extract statement period."""
        month_range = (
            r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})'
            r'\s+(?:through|-)\s+'
            r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})'
        )
        patterns = [
            r'Statement\s+Period[:\s]*([A-Za-z0-9,\s/-]+)',
            month_range,
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.lastindex and match.lastindex > 1:
                    start = match.group(1).strip()
                    end = match.group(2).strip()
                    return f"{start} - {end}"
                else:
                    return match.group(match.lastindex or 1).strip()
        return None

    def _extract_balances(self, text: str, lines: List[str]) -> Dict[str, Optional[str]]:
        """Extract balance information."""
        balance_fields = {
            "opening_balance": None,
            "ending_balance": None,
            "available_balance": None,
            "current_balance": None,
        }

        amount_regex = re.compile(r'([+-]?\$?[\d,]+\.\d{2})')

        def extract_amount_from_line(line: str) -> Optional[str]:
            match = amount_regex.search(line)
            return match.group(1) if match else None

        def find_amount_nearby(idx: int, max_lines: int = 5) -> Optional[str]:
            """Look for amount in nearby lines"""
            for offset in range(0, max_lines):
                if idx + offset < len(lines):
                    amount = extract_amount_from_line(lines[idx + offset])
                    if amount:
                        return amount
            return None

        # Strategy 1: Look for CHECKING SUMMARY section (Chase format)
        # This is the most reliable source for Chase statements
        in_checking_summary = False
        checking_summary_balances = {}

        for idx, raw_line in enumerate(lines):
            line = raw_line.strip()
            upper = line.upper()

            # Check if we're in the CHECKING SUMMARY section
            if "CHECKING SUMMARY" in upper or "ACCOUNT SUMMARY" in upper:
                in_checking_summary = True
                continue

            # Exit summary section when we hit transaction details or balance summary
            if in_checking_summary and ("TRANSACTION DETAIL" in upper or "TRANSACTION HISTORY" in upper or "BALANCE SUMMARY" in upper):
                break

            # Extract balances from CHECKING SUMMARY section (highest priority)
            if in_checking_summary:
                # Look for opening/beginning/starting balance WITHOUT a colon
                opening_keywords = ["BEGINNING BALANCE", "OPENING BALANCE", "STARTING BALANCE"]
                if any(keyword in upper for keyword in opening_keywords) and ":" not in line:
                    amount = extract_amount_from_line(line) or find_amount_nearby(idx)
                    if amount:
                        checking_summary_balances["opening"] = amount

                # Look for ending/closing balance WITHOUT a colon
                ending_keywords = ["ENDING BALANCE", "CLOSING BALANCE", "FINAL BALANCE"]
                if any(keyword in upper for keyword in ending_keywords) and ":" not in line:
                    amount = extract_amount_from_line(line) or find_amount_nearby(idx)
                    if amount:
                        checking_summary_balances["ending"] = amount

        # If we found balances in CHECKING SUMMARY, use those EXCLUSIVELY
        if checking_summary_balances:
            if "opening" in checking_summary_balances:
                balance_fields["opening_balance"] = checking_summary_balances["opening"]
            if "ending" in checking_summary_balances:
                balance_fields["ending_balance"] = checking_summary_balances["ending"]

        # Strategy 2: If not found in CHECKING SUMMARY, look for other patterns
        # But SKIP any lines with colons (these are from balance summary boxes)
        if not balance_fields["opening_balance"] or not balance_fields["ending_balance"]:
            for idx, raw_line in enumerate(lines):
                line = raw_line.strip()
                upper = line.upper()

                # SKIP lines that contain colons (Balance Summary format)
                if ":" in line:
                    continue

                # Look for opening/beginning/starting balance
                if not balance_fields["opening_balance"]:
                    opening_keywords = ["BEGINNING BALANCE", "OPENING BALANCE", "STARTING BALANCE"]
                    if any(keyword in upper for keyword in opening_keywords):
                        amount = extract_amount_from_line(line) or find_amount_nearby(idx)
                        if amount:
                            balance_fields["opening_balance"] = amount

                # Look for ending/closing/final balance
                if not balance_fields["ending_balance"]:
                    ending_keywords = ["ENDING BALANCE", "CLOSING BALANCE", "FINAL BALANCE"]
                    if any(keyword in upper for keyword in ending_keywords):
                        amount = extract_amount_from_line(line) or find_amount_nearby(idx)
                        if amount:
                            balance_fields["ending_balance"] = amount

        # Strategy 3: Available and Current balance (these are OK to get from anywhere)
        for idx, raw_line in enumerate(lines):
            line = raw_line.strip()
            upper = line.upper()

            if "AVAILABLE BALANCE" in upper:
                amount = extract_amount_from_line(line) or find_amount_nearby(idx)
                if amount and not balance_fields["available_balance"]:
                    balance_fields["available_balance"] = amount

            if "CURRENT BALANCE" in upper:
                amount = extract_amount_from_line(line) or find_amount_nearby(idx)
                if amount and not balance_fields["current_balance"]:
                    balance_fields["current_balance"] = amount

        return balance_fields

    def _infer_missing_balances(self, balances: Dict[str, Optional[str]], transactions: List[Dict]) -> Dict[str, Optional[str]]:
        """Infer missing balances from transactions."""
        if not transactions:
            return balances

        # Infer opening balance if missing
        if not balances.get("opening_balance"):
            first_transaction = transactions[0]
            if first_transaction.get("balance"):
                balances["opening_balance"] = first_transaction["balance"]

        # Infer ending balance if missing
        if not balances.get("ending_balance"):
            for transaction in reversed(transactions):
                if transaction.get("balance"):
                    balances["ending_balance"] = transaction["balance"]
                    break

        return balances

    def _extract_transactions(self, lines: List[str]) -> List[Dict]:
        """Extract transaction details."""
        transactions = []
        date_regex = re.compile(r'^(?P<date>\d{2}/\d{2})\b')
        amount_regex = re.compile(r'([+-]?\$?\(?\d[\d,]*\.\d{2}\)?)')

        idx = 0
        while idx < len(lines):
            line = lines[idx].strip()

            # Skip header lines
            if line.upper().startswith(("DATE", "TOTAL", "PAGE")):
                idx += 1
                continue

            match = date_regex.match(line)
            if match:
                date = match.group("date")
                remainder = line[match.end():].strip()
                body_lines = [remainder] if remainder else []

                # Look ahead for continuation lines
                lookahead = idx + 1
                while lookahead < len(lines):
                    next_line = lines[lookahead].strip()
                    if not next_line:
                        lookahead += 1
                        continue
                    if date_regex.match(next_line) or next_line.upper().startswith(("TOTAL", "PAGE")):
                        break
                    body_lines.append(next_line)
                    lookahead += 1

                combined = " ".join(body_lines).strip()
                amount = balance = None
                description = combined

                matches = list(amount_regex.finditer(combined))
                if len(matches) >= 2:
                    amount = matches[-2].group(1)
                    balance = matches[-1].group(1)
                    description = combined[:matches[-2].start()].strip()
                elif len(matches) == 1:
                    amount = matches[0].group(1)
                    description = combined[:matches[0].start()].strip()

                transactions.append({
                    "date": date,
                    "description": description,
                    "amount": amount,
                    "amount_value": self._parse_amount(amount) if amount else None,
                    "balance": balance,
                    "balance_value": self._parse_amount(balance) if balance else None,
                })

                idx = lookahead
                if len(transactions) >= 100:  # Limit to 100 transactions
                    break
                continue
            idx += 1

        return transactions

    @staticmethod
    def _parse_amount(value: str) -> Optional[float]:
        """Parse amount string to float."""
        if not value:
            return None
        cleaned = value.replace("$", "").replace(",", "").replace("(", "-").replace(")", "")
        try:
            return float(cleaned)
        except ValueError:
            return None

    def _build_summary(self, details: Dict) -> Dict:
        """Build summary statistics."""
        transactions = details.get("transactions", [])
        amounts = [t["amount_value"] for t in transactions if t.get("amount_value") is not None]

        total_debits = sum(a for a in amounts if a < 0) if amounts else None
        total_credits = sum(a for a in amounts if a > 0) if amounts else None

        summary = {
            "transaction_count": len(transactions),
            "total_debits": total_debits,
            "total_credits": total_credits,
            "net_activity": (total_credits + total_debits) if (total_credits is not None and total_debits is not None) else None,
            "confidence": self._calculate_confidence(details),
        }
        return summary

    def _calculate_confidence(self, details: Dict) -> float:
        """Calculate extraction confidence score."""
        required_fields = ["bank_name", "account_number", "statement_period"]
        filled = sum(1 for field in required_fields if details.get(field))

        transactions = details.get("transactions", [])
        transaction_bonus = min(len(transactions), 10) / 10

        base_score = (filled / len(required_fields)) * 80
        bonus_score = transaction_bonus * 20

        return round(min(base_score + bonus_score, 100.0), 1)
