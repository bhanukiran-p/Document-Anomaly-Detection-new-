"""
Enhanced Rule-Based Fraud Detection Engine for Bank Statements

This module provides comprehensive fraud detection rules with:
- Behavioral pattern analysis (transaction sequences, velocity, timing)
- Structural validation (balance consistency, date ordering)
- Metadata inspection (editing tools detection)
- Formatting analysis (cloned rows, inconsistent fonts)
- Weighted scoring system with explainability
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FraudRule:
    """Represents a single fraud detection rule."""
    rule_id: str
    category: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    weight: float  # 0.0 to 1.0
    triggered: bool = False
    score_contribution: float = 0.0
    explanation: str = ""
    evidence: List[str] = None

    def __post_init__(self):
        if self.evidence is None:
            self.evidence = []


class EnhancedFraudRuleEngine:
    """
    Enhanced fraud detection engine with multiple rule categories.

    Scoring: 0-100 (0=clean, 100=definite fraud)
    """

    # Suspicious editing tools (including XMP metadata creators)
    SUSPICIOUS_CREATORS = {
        'adobe': 10,
        'photoshop': 15,  # High risk - image editing
        'illustrator': 10,
        'indesign': 10,
        'microsoft': 8,
        'word': 8,
        'excel': 8,
        'libreoffice': 8,
        'pages': 8,
        'itextsharp': 12,  # PDF manipulation tool
        'wkhtmltopdf': 10,
        'pdfkit': 10,
        'pdf expert': 12,  # Suspicious editing app
        'smallpdf': 12,
        'pdffiller': 12,
        'foxit': 12,
        'ilovepdf': 12,
        'unknown': 5,
    }

    # Suspicious keywords (behavioral fraud indicators)
    SUSPICIOUS_KEYWORDS = {
        # Extreme risk (14-18 points)
        'money laundering': 18,
        'dark web': 15,
        'shell company': 14,
        'structuring': 14,
        'smurfing': 14,

        # Very high risk (10-13 points)
        'structured deposit': 12,
        'offshore': 10,
        'crypto': 10,
        'bitcoin': 10,
        'coinbase': 10,
        'tor': 12,

        # High risk (8-9 points)
        'wire transfer': 8,
        'western union': 8,
        'moneygram': 8,
        'casino': 12,
        'gambling': 12,
        'poker': 10,
        'betting': 8,

        # Medium risk (6-7 points)
        'international': 6,
        'ripple': 8,
        'ethereum': 8,
        'cash advance': 6,
        'atm withdrawal': 2,

        # Low risk
        'anonymous': 8,
    }

    # Normal, whitelisted transaction patterns (reduce false positives)
    NORMAL_PATTERNS = [
        ('salary', 'grocery|supermarket|walmart|costco'),  # Income → groceries
        ('salary', 'utility|electric|water|gas'),  # Income → utilities
        ('salary', 'mortgage|rent|landlord'),  # Income → housing
        ('salary', 'insurance'),  # Income → insurance
        ('deposit', 'withdrawal'),  # Normal deposit-withdraw cycle
    ]

    # Known recurring merchants (reduce false positives)
    KNOWN_MERCHANTS = {
        'salary', 'payroll', 'direct deposit',
        'amazon', 'walmart', 'target', 'costco',
        'netflix', 'spotify', 'apple',
        'utility', 'electric', 'water', 'gas',
        'mortgage', 'rent', 'landlord',
        'insurance', 'healthcare',
        'grocery', 'supermarket',
    }

    def __init__(self):
        """Initialize the fraud detection engine."""
        self.rules: Dict[str, FraudRule] = {}
        self.rules_by_category: Dict[str, List[FraudRule]] = defaultdict(list)
        self.total_score = 0.0
        self.transaction_list = []
        self.running_balance = 0.0

    # ==================== METADATA CHECKS ====================

    def check_suspicious_creators(self, creator: str, producer: str = "") -> FraudRule:
        """Detect suspicious PDF creators/editors."""
        rule = FraudRule(
            rule_id='metadata_suspicious_creator',
            category='metadata',
            severity='high',
            weight=0.12
        )

        if not creator and not producer:
            return rule

        combined_text = f"{creator} {producer}".lower()
        max_risk = 0
        found_tools = []

        for tool, risk_score in self.SUSPICIOUS_CREATORS.items():
            if tool in combined_text:
                found_tools.append(f"{tool} ({risk_score})")
                max_risk = max(max_risk, risk_score)

        if found_tools:
            rule.triggered = True
            rule.score_contribution = min(max_risk / 18.0, 1.0)
            rule.explanation = "Suspicious PDF creator/editor tools detected"
            rule.evidence = found_tools

            # Photoshop is extremely suspicious
            if 'photoshop' in combined_text:
                rule.severity = 'critical'
                rule.score_contribution = 0.95

        return rule

    def check_metadata_completeness(self, metadata: Dict) -> FraudRule:
        """Check for missing standard metadata fields."""
        rule = FraudRule(
            rule_id='metadata_incomplete',
            category='metadata',
            severity='medium',
            weight=0.08
        )

        required_fields = ['/Creator', '/CreationDate', '/Producer', '/ModDate']
        missing = []

        for field in required_fields:
            if field not in metadata or not metadata.get(field):
                missing.append(field)

        if len(missing) >= 2:
            rule.triggered = True
            rule.score_contribution = len(missing) / len(required_fields)
            rule.explanation = "Missing standard metadata fields (real banks include these)"
            rule.evidence = missing

        return rule

    def check_creation_date_anomalies(self, created_date: str, modified_date: str = "") -> FraudRule:
        """Check for impossible or suspicious creation dates."""
        rule = FraudRule(
            rule_id='metadata_date_anomaly',
            category='metadata',
            severity='critical',
            weight=0.15
        )

        try:
            created = self._parse_pdf_date(created_date)

            # Future date = definite tampering
            if created > datetime.now():
                rule.triggered = True
                rule.score_contribution = 1.0
                rule.explanation = "Creation date is in the future (impossible - document tampering)"
                rule.evidence = [f"Created: {created.date()}"]
                return rule

            # Modified after creation = editing
            if modified_date:
                modified = self._parse_pdf_date(modified_date)
                if modified > created:
                    rule.triggered = True
                    rule.score_contribution = 0.6
                    rule.explanation = "Document modified after creation"
                    rule.evidence = [f"Created: {created.date()}", f"Modified: {modified.date()}"]

        except Exception as e:
            logger.warning(f"Could not parse dates: {e}")

        return rule

    # ==================== BEHAVIORAL CHECKS ====================

    def check_transaction_sequence_anomalies(self, transactions: List[Dict]) -> FraudRule:
        """Detect unusual transaction sequences (e.g., large deposit → rapid withdrawals)."""
        rule = FraudRule(
            rule_id='behavior_sequence_anomaly',
            category='behavioral',
            severity='high',
            weight=0.20
        )

        if len(transactions) < 3:
            return rule

        anomalies = []

        # Pattern: Large deposit followed by rapid small withdrawals (money laundering)
        for i in range(len(transactions) - 3):
            trans = transactions[i]

            if trans.get('type') == 'credit' and trans.get('amount', 0) > 5000:
                # Check next 3 transactions
                following = transactions[i+1:i+4]
                small_debits = sum(
                    1 for t in following
                    if t.get('type') == 'debit' and 0 < t.get('amount', 0) < 1000
                )

                if small_debits >= 2:
                    anomalies.append({
                        'pattern': 'deposit_then_rapid_withdrawals',
                        'date': trans.get('date'),
                        'amount': trans.get('amount')
                    })

        if anomalies:
            rule.triggered = True
            rule.score_contribution = min(len(anomalies) / 3, 1.0)
            rule.explanation = "Suspicious sequence: large deposits followed by rapid small withdrawals"
            rule.evidence = [f"{a['pattern']} on {a['date']}" for a in anomalies]

        return rule

    def check_transaction_velocity(self, transactions: List[Dict]) -> FraudRule:
        """Detect unusually high transaction velocity."""
        rule = FraudRule(
            rule_id='behavior_high_velocity',
            category='behavioral',
            severity='high',
            weight=0.15
        )

        if len(transactions) < 20:
            return rule  # Not enough data

        # Normal: 20-30 transactions per month
        # Suspicious: 50+
        if len(transactions) > 50:
            rule.triggered = True
            rule.severity = 'high'
            rule.score_contribution = min((len(transactions) - 50) / 50, 1.0)
            rule.explanation = f"Extremely high transaction velocity: {len(transactions)} transactions"
            rule.evidence = [f"Expected: 20-30/month, Found: {len(transactions)}"]
        elif len(transactions) > 40:
            rule.triggered = True
            rule.severity = 'medium'
            rule.score_contribution = 0.4
            rule.explanation = f"High transaction velocity: {len(transactions)} transactions"
            rule.evidence = [f"Expected: 20-30/month, Found: {len(transactions)}"]

        return rule

    def check_round_amount_pattern(self, transactions: List[Dict]) -> FraudRule:
        """Detect repeated round-amount transactions (structuring indicator)."""
        rule = FraudRule(
            rule_id='behavior_round_amounts',
            category='behavioral',
            severity='high',
            weight=0.18
        )

        round_transactions = []
        for trans in transactions:
            amount = trans.get('amount', 0)
            # Check if amount is round: $1000.00, $5000.00, etc
            if amount > 0 and amount % 1000 == 0:
                round_transactions.append({
                    'amount': amount,
                    'date': trans.get('date'),
                    'description': trans.get('description', '')
                })

        if len(round_transactions) >= 3:
            rule.triggered = True
            rule.severity = 'critical'
            rule.score_contribution = min(len(round_transactions) / 5, 1.0)
            rule.explanation = "Structuring pattern: Multiple transactions in round amounts ($1000, $5000)"
            rule.evidence = [f"${t['amount']:.2f} on {t['date']}" for t in round_transactions[:5]]

        return rule

    def check_late_night_activity(self, transactions: List[Dict]) -> FraudRule:
        """Detect unusual late-night or weekend activity."""
        rule = FraudRule(
            rule_id='behavior_unusual_timing',
            category='behavioral',
            severity='medium',
            weight=0.10
        )

        suspicious_times = []

        for trans in transactions:
            date_str = trans.get('date', '')
            if not date_str:
                continue

            try:
                trans_date = datetime.strptime(date_str, '%m/%d/%Y')

                # Weekend activity is unusual for business transactions
                if trans_date.weekday() >= 5:  # Saturday=5, Sunday=6
                    suspicious_times.append({
                        'date': date_str,
                        'day': trans_date.strftime('%A'),
                        'amount': trans.get('amount')
                    })
            except:
                pass

        if len(suspicious_times) >= 3:
            rule.triggered = True
            rule.score_contribution = min(len(suspicious_times) / 10, 0.6)
            rule.explanation = "Multiple weekend transactions (unusual timing)"
            rule.evidence = [f"{t['day']} {t['date']}" for t in suspicious_times[:3]]

        return rule

    # ==================== STRUCTURAL CHECKS ====================

    def check_balance_consistency(self, opening_balance: float, closing_balance: float,
                                  credits: float, debits: float) -> FraudRule:
        """Verify: opening + credits - debits = closing."""
        rule = FraudRule(
            rule_id='structural_balance_mismatch',
            category='structural',
            severity='critical',
            weight=0.25
        )

        calculated_closing = opening_balance + credits - debits
        difference = abs(calculated_closing - closing_balance)

        # Allow small rounding differences (< $0.01)
        if difference > 0.01:
            rule.triggered = True
            rule.score_contribution = min(difference / 1000, 1.0)  # Normalize
            rule.severity = 'critical' if difference > 100 else 'high'
            rule.explanation = f"Balance calculation error: Expected ${calculated_closing:.2f}, got ${closing_balance:.2f}"
            rule.evidence = [
                f"Opening: ${opening_balance:.2f}",
                f"Credits: ${credits:.2f}",
                f"Debits: ${debits:.2f}",
                f"Calculated: ${calculated_closing:.2f}",
                f"Actual: ${closing_balance:.2f}",
                f"Difference: ${difference:.2f}"
            ]

        return rule

    def check_impossible_negative_balance(self, transactions: List[Dict]) -> FraudRule:
        """Detect impossible negative balances (balance < 0 with no overdraft notice)."""
        rule = FraudRule(
            rule_id='structural_impossible_balance',
            category='structural',
            severity='high',
            weight=0.15
        )

        negative_balances = []

        for trans in transactions:
            balance = trans.get('balance', 0)
            if balance < 0:
                negative_balances.append({
                    'date': trans.get('date'),
                    'balance': balance
                })

        if len(negative_balances) > 2:
            rule.triggered = True
            rule.score_contribution = min(len(negative_balances) / 5, 0.8)
            rule.explanation = "Multiple negative balances detected (unusual without overdraft notices)"
            rule.evidence = [f"${n['balance']:.2f} on {n['date']}" for n in negative_balances[:3]]

        return rule

    def check_duplicate_rows(self, text_content: str) -> FraudRule:
        """Detect cloned/copy-pasted transaction rows."""
        rule = FraudRule(
            rule_id='structural_duplicate_rows',
            category='structural',
            severity='high',
            weight=0.14
        )

        # Extract potential transaction lines (date pattern + amount)
        transaction_pattern = r'\d{1,2}/\d{1,2}\s+.{20,80}\$[\d,]+\.\d{2}'
        matches = re.findall(transaction_pattern, text_content)

        if matches:
            unique_matches = set(matches)
            duplication_ratio = 1 - (len(unique_matches) / len(matches))

            if duplication_ratio > 0.3:  # >30% duplication
                rule.triggered = True
                rule.score_contribution = min(duplication_ratio, 1.0)
                rule.explanation = "Possible cloned transaction rows (copy-paste fraud)"
                rule.evidence = [f"Duplication ratio: {duplication_ratio:.1%}"]

        return rule

    # ==================== FORMATTING CHECKS ====================

    def check_font_consistency(self, fonts_list: List[str]) -> FraudRule:
        """Detect inconsistent font usage (editing artifact)."""
        rule = FraudRule(
            rule_id='format_font_mismatch',
            category='formatting',
            severity='medium',
            weight=0.10
        )

        if len(fonts_list) > 3:
            rule.triggered = True
            rule.score_contribution = min((len(fonts_list) - 2) / 5, 0.7)
            rule.explanation = f"Inconsistent fonts detected ({len(fonts_list)} different fonts)"
            rule.evidence = [str(f) for f in fonts_list[:5]]

        return rule

    def check_line_spacing_anomalies(self, text_content: str) -> FraudRule:
        """Detect unusual spacing patterns (editing/overlay artifact)."""
        rule = FraudRule(
            rule_id='format_spacing_anomaly',
            category='formatting',
            severity='medium',
            weight=0.08
        )

        # Check for excessive spaces (5+ consecutive)
        excessive_spaces = len(re.findall(r'\s{5,}', text_content))

        if excessive_spaces > 5:
            rule.triggered = True
            rule.score_contribution = min(excessive_spaces / 20, 0.6)
            rule.explanation = f"Unusual spacing patterns detected ({excessive_spaces} instances)"
            rule.evidence = [f"Excessive whitespace instances: {excessive_spaces}"]

        return rule

    def check_text_alignment_shifts(self, lines: List[str]) -> FraudRule:
        """Detect alignment shifts (possible copy-paste)."""
        rule = FraudRule(
            rule_id='format_alignment_shift',
            category='formatting',
            severity='low',
            weight=0.06
        )

        # Check leading whitespace changes
        indents = [len(line) - len(line.lstrip()) for line in lines if line.strip()]

        if len(set(indents)) > len(lines) * 0.5:  # >50% indent variation
            rule.triggered = True
            rule.score_contribution = 0.4
            rule.explanation = "Text alignment inconsistencies detected"
            rule.evidence = [f"Indent variation: {len(set(indents))} different indents"]

        return rule

    # ==================== KEYWORD & BEHAVIORAL CHECKS ====================

    def check_fraud_keywords(self, text_content: str) -> FraudRule:
        """Detect high-risk transaction keywords."""
        rule = FraudRule(
            rule_id='behavior_fraud_keywords',
            category='behavioral',
            severity='critical',
            weight=0.20
        )

        text_lower = text_content.lower()
        keyword_score = 0
        found_keywords = []

        for keyword, weight in self.SUSPICIOUS_KEYWORDS.items():
            count = text_lower.count(keyword)
            if count > 0:
                keyword_score += count * weight
                found_keywords.append(f"{keyword} (×{count}, risk:{weight})")

        if found_keywords:
            rule.triggered = True
            rule.score_contribution = min(keyword_score / 100, 1.0)
            rule.explanation = "High-risk fraud-related keywords detected"
            rule.evidence = found_keywords[:8]  # Top 8

        return rule

    # ==================== UTILITY METHODS ====================

    def _parse_pdf_date(self, date_string: str) -> Optional[datetime]:
        """Parse PDF date format."""
        formats = [
            '%Y%m%d%H%M%S',
            '%Y%m%d',
            '%Y-%m-%d',
            '%m/%d/%Y',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except:
                continue

        return None

    def run_all_checks(self, metadata: Dict, text_content: str, transactions: List[Dict],
                      balances: Dict, fonts: List[str]) -> Dict:
        """
        Run all fraud detection checks and return comprehensive results.

        Args:
            metadata: PDF metadata dict
            text_content: Extracted text content
            transactions: List of parsed transactions
            balances: Dict with opening_balance, closing_balance, credits, debits
            fonts: List of font names found

        Returns:
            Dict with fraud score (0-100), rules triggered, and explanations
        """

        results = {
            'fraud_score': 0.0,
            'fraud_level': 'CLEAN',
            'rules_triggered': [],
            'rules_by_category': defaultdict(list),
            'summary': '',
            'details': {}
        }

        # Run all checks
        all_rules = []

        # Metadata checks
        all_rules.append(self.check_suspicious_creators(
            metadata.get('/Creator', ''),
            metadata.get('/Producer', '')
        ))
        all_rules.append(self.check_metadata_completeness(metadata))
        all_rules.append(self.check_creation_date_anomalies(
            metadata.get('/CreationDate', ''),
            metadata.get('/ModDate', '')
        ))

        # Behavioral checks
        all_rules.append(self.check_transaction_sequence_anomalies(transactions))
        all_rules.append(self.check_transaction_velocity(transactions))
        all_rules.append(self.check_round_amount_pattern(transactions))
        all_rules.append(self.check_late_night_activity(transactions))
        all_rules.append(self.check_fraud_keywords(text_content))

        # Structural checks
        all_rules.append(self.check_balance_consistency(
            balances.get('opening_balance', 0),
            balances.get('closing_balance', 0),
            balances.get('credits', 0),
            balances.get('debits', 0)
        ))
        all_rules.append(self.check_impossible_negative_balance(transactions))
        all_rules.append(self.check_duplicate_rows(text_content))

        # Formatting checks
        all_rules.append(self.check_font_consistency(fonts))
        all_rules.append(self.check_line_spacing_anomalies(text_content))
        all_rules.append(self.check_text_alignment_shifts(text_content.split('\n')))

        # Calculate weighted fraud score
        total_weight = 0
        weighted_score = 0

        for rule in all_rules:
            if rule.triggered:
                weighted_score += rule.score_contribution * rule.weight
                total_weight += rule.weight
                results['rules_triggered'].append({
                    'rule_id': rule.rule_id,
                    'category': rule.category,
                    'severity': rule.severity,
                    'explanation': rule.explanation,
                    'evidence': rule.evidence,
                    'contribution': round(rule.score_contribution * rule.weight, 4)
                })
                results['rules_by_category'][rule.category].append(rule.rule_id)

        # Normalize to 0-100 scale
        if total_weight > 0:
            results['fraud_score'] = min((weighted_score / total_weight) * 100, 100)

        # Determine fraud level
        if results['fraud_score'] >= 70:
            results['fraud_level'] = 'CRITICAL'
        elif results['fraud_score'] >= 50:
            results['fraud_level'] = 'HIGH'
        elif results['fraud_score'] >= 30:
            results['fraud_level'] = 'MEDIUM'
        elif results['fraud_score'] >= 15:
            results['fraud_level'] = 'LOW'
        else:
            results['fraud_level'] = 'CLEAN'

        # Generate summary
        results['summary'] = self._generate_summary(
            results['fraud_score'],
            results['fraud_level'],
            results['rules_triggered']
        )

        results['details'] = {
            'total_rules_checked': len(all_rules),
            'rules_triggered': len(results['rules_triggered']),
            'categories_affected': list(results['rules_by_category'].keys())
        }

        return results

    def _generate_summary(self, score: float, level: str, triggered_rules: List[Dict]) -> str:
        """Generate human-readable fraud summary."""

        summary_lines = [
            f"Fraud Risk Level: {level}",
            f"Fraud Score: {score:.1f}/100",
            ""
        ]

        if level == 'CRITICAL':
            summary_lines.append("⚠️ CRITICAL: Strong evidence of fraud detected.")
            summary_lines.append("Multiple high-severity indicators suggest document tampering or fraudulent activity.")
        elif level == 'HIGH':
            summary_lines.append("⚠️ HIGH RISK: Multiple suspicious indicators detected.")
            summary_lines.append("This document warrants further investigation and verification.")
        elif level == 'MEDIUM':
            summary_lines.append("🔶 MEDIUM RISK: Some suspicious indicators present.")
            summary_lines.append("Further review recommended, but patterns are not conclusive.")
        elif level == 'LOW':
            summary_lines.append("📌 LOW RISK: Minor concerns detected.")
            summary_lines.append("Isolated suspicious elements, but overall document appears legitimate.")
        else:
            summary_lines.append("✅ CLEAN: No significant fraud indicators detected.")
            summary_lines.append("Document appears to be authentic and unmodified.")

        if triggered_rules:
            summary_lines.append("")
            summary_lines.append("Triggered Rules:")
            for i, rule in enumerate(triggered_rules[:5], 1):
                summary_lines.append(f"  {i}. {rule['explanation']} ({rule['severity'].upper()})")

        return "\n".join(summary_lines)
