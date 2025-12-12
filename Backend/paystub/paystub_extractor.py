"""
Paystub Extractor - Complete Fraud Detection Pipeline
Orchestrates: Mindee OCR → Normalization → ML Detection → AI Analysis → Customer Tracking
Completely self-contained - no dependencies on other document analysis modules
"""

import os
import sys
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import centralized config and logging
from config import Config
logger = Config.get_logger(__name__)
from typing import Dict, List, Optional, Tuple

# Load environment variables first (if not already loaded)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv already loaded by api_server.py or not available
    pass

# Import Mindee - use ClientV2 API (requires mindee>=4.31.0)
try:
    from mindee import ClientV2, InferenceParameters, PathInput
    MINDEE_AVAILABLE = True
except ImportError as e:
    logger.error(f"Mindee library not properly installed: {e}")
    logger.error("Requires mindee>=4.31.0. Install with: pip install --upgrade 'mindee>=4.31.0'")
    MINDEE_AVAILABLE = False
    ClientV2 = None
    InferenceParameters = None
    PathInput = None

# Import paystub-specific components from local modules
from .normalization.paystub_normalizer_factory import PaystubNormalizerFactory

# Mindee configuration - read after load_dotenv()
MINDEE_API_KEY = os.getenv("MINDEE_API_KEY", "").strip()
MINDEE_MODEL_ID_PAYSTUB = os.getenv("MINDEE_MODEL_ID_PAYSTUB", "15fab31e-ac0e-4ccc-83ed-39b9f65bb791").strip()

logger.info(f"Mindee API Key loaded: {MINDEE_API_KEY[:20]}..." if MINDEE_API_KEY else "Mindee API Key NOT SET")
logger.info(f"Mindee Model ID: {MINDEE_MODEL_ID_PAYSTUB}")

if not MINDEE_API_KEY:
    logger.warning("MINDEE_API_KEY is not set - paystub extraction may fail")
    mindee_client = None
elif not MINDEE_AVAILABLE:
    logger.error("Mindee library not available")
    mindee_client = None
else:
    mindee_client = ClientV2(api_key=MINDEE_API_KEY)
    logger.info("Mindee ClientV2 initialized successfully")


class PaystubExtractor:
    """
    Complete paystub extraction and fraud analysis pipeline
    Mindee-only OCR → Paystub-specific normalization → ML fraud detection → AI decision
    """

    def __init__(self):
        """Initialize all components"""
        # ML Fraud Detector
        try:
            from .ml.paystub_fraud_detector import PaystubFraudDetector
            model_dir = os.getenv("ML_MODEL_DIR", "models")
            self.ml_detector = PaystubFraudDetector(model_dir=model_dir)
            logger.info("Initialized PaystubFraudDetector")
        except (ImportError, RuntimeError) as e:
            logger.error(f"ML fraud detector initialization failed: {e}")
            logger.error("Paystub analysis requires ML models. Please train models using: python training/train_paystub_models.py")
            self.ml_detector = None
            # Raise RuntimeError to fail fast - paystub analysis requires ML models
            raise RuntimeError(
                f"Paystub ML fraud detector not available: {str(e)}. "
                "Paystub analysis requires trained ML models. "
                "Please train the model using: python training/train_paystub_models.py"
            ) from e

        # AI Agent
        try:
            from .ai.paystub_fraud_analysis_agent import PaystubFraudAnalysisAgent
            from .ai.paystub_tools import PaystubDataAccessTools
            openai_key = os.getenv('OPENAI_API_KEY')
            self.ai_agent = None
            if openai_key:
                data_tools = PaystubDataAccessTools()
                self.ai_agent = PaystubFraudAnalysisAgent(
                    api_key=openai_key,
                    model=os.getenv('AI_MODEL', 'o4-mini'),
                    data_tools=data_tools
                )
                logger.info("Initialized PaystubFraudAnalysisAgent")
            else:
                logger.warning("OPENAI_API_KEY not set - AI analysis will be skipped")
        except ImportError:
            logger.warning("AI agent not available - AI analysis will be skipped")
            self.ai_agent = None

    def extract_and_analyze(self, file_path: str) -> Dict:
        """
        Complete paystub analysis pipeline - NO EARLY EXITS
        Always runs full evaluation regardless of missing fields

        Args:
            file_path: Path to paystub image/PDF file

        Returns:
            Complete analysis results dict with all rule outputs, issues, and final decision
        """
        logger.info(f"Starting paystub analysis for: {file_path}")

        # Stage 1: OCR Extraction (Mindee only)
        extracted_data, raw_text = self._extract_with_mindee(file_path)
        logger.info(f"Extracted data from Mindee: {list(extracted_data.keys())}")

        # Stage 2: Normalization
        normalized_data = self._normalize_data(extracted_data)

        # Stage 3: Validation Rules (collects issues but doesn't exit early)
        validation_issues = self._collect_validation_issues(normalized_data)
        logger.info(f"Validation issues found: {len(validation_issues)}")

        # Stage 4: ML Fraud Detection
        ml_analysis = self._run_ml_fraud_detection(normalized_data, raw_text)
        logger.info(f"ML fraud analysis complete: {ml_analysis.get('risk_level')}")

        # Stage 5: Employee History & Duplicate Detection (continue regardless)
        employee_info = self._get_employee_info(normalized_data)
        duplicate_check = self._check_duplicate(normalized_data)
        if duplicate_check:
            logger.warning("Duplicate paystub detected - will be included in issues")
            validation_issues.append("Duplicate paystub submission detected")

        # Stage 6: AI Fraud Analysis (always runs unless initialization failed)
        ai_analysis = self._run_ai_analysis(normalized_data, ml_analysis, employee_info)
        logger.info(f"AI analysis complete: {ai_analysis.get('recommendation') if ai_analysis else 'N/A'}")

        # Stage 7: Generate Anomalies
        anomalies = self._generate_anomalies(normalized_data, ml_analysis, ai_analysis)

        # Stage 8: Calculate Confidence Score
        confidence_score = self._calculate_confidence(normalized_data, ml_analysis, ai_analysis)

        # Stage 9: Determine Final Decision Based on All Collected Issues
        overall_decision = self._determine_final_decision(
            validation_issues=validation_issues,
            ml_analysis=ml_analysis,
            ai_analysis=ai_analysis,
            normalized_data=normalized_data
        )

        # Stage 10: Build Final Response with ALL results
        return self._build_complete_response(
            extracted_data=extracted_data,
            normalized_data=normalized_data,
            ml_analysis=ml_analysis,
            ai_analysis=ai_analysis,
            employee_info=employee_info,
            anomalies=anomalies,
            confidence_score=confidence_score,
            validation_issues=validation_issues,
            overall_decision=overall_decision,
            duplicate_detected=duplicate_check,
            raw_text=raw_text
        )

    def _extract_with_mindee(self, file_path: str) -> Tuple[Dict, str]:
        """Extract paystub data using Mindee API only (no fallback)"""
        if not mindee_client:
            raise RuntimeError("Mindee client not initialized. Check API key and installation.")

        try:
            # Use ClientV2 API with InferenceParameters
            logger.info(f"Extracting with Mindee using model ID: {MINDEE_MODEL_ID_PAYSTUB}")
            
            # Create inference parameters with the model ID
            params = InferenceParameters(model_id=MINDEE_MODEL_ID_PAYSTUB, raw_text=True)
            input_source = PathInput(file_path)
            
            # Parse document using ClientV2 with model ID
            logger.info(f"Calling Mindee API with model ID...")
            response = mindee_client.enqueue_and_get_inference(input_source, params)
            
            # Extract fields from the response
            logger.info(f"Processing Mindee response...")
            
            if not response or not hasattr(response, 'inference'):
                raise ValueError("Invalid Mindee API response: missing inference object")
            
            if not response.inference or not hasattr(response.inference, 'result'):
                raise ValueError("Invalid Mindee API response: missing result object")
            
            result = response.inference.result
            if not result:
                raise ValueError("Invalid Mindee API response: result is None")
            
            fields = result.fields or {}
            logger.info(f"Extracted {len(fields)} fields from Mindee response")
            
            # Get raw text
            raw_text = getattr(result, "raw_text", "") or ""
            if raw_text and not isinstance(raw_text, str):
                raw_text = str(raw_text)
            
            # Convert Mindee fields to simple dict
            extracted = {}
            
            # Map Mindee field names to our schema
            # Based on Mindee Payslip schema: First Name, Last Name, Employee Address, Pay Period Start/End Date,
            # Gross Pay, Net Pay, Deductions (array), Taxes (array), Employer Name, Employer Address, SSN, Employee ID
            field_mapping = {
                'first_name': 'first_name',
                'last_name': 'last_name',
                'employee_address': 'employee_address',
                'pay_period_start_date': 'pay_period_start_date',
                'pay_period_end_date': 'pay_period_end_date',
                'gross_pay': 'gross_pay',
                'net_pay': 'net_pay',
                'deductions': 'deductions',
                'taxes': 'taxes',
                'employer_name': 'employer_name',
                'employer_address': 'employer_address',
                'social_security_number': 'social_security_number',
                'employee_id': 'employee_id',
            }

            for name, field_data in fields.items():
                logger.debug(f"Processing field {name}: {field_data} (type: {type(field_data)})")

                # Extract the actual value from SimpleField object
                value = None
                if hasattr(field_data, 'value'):
                    # SimpleField object - extract the value
                    value = field_data.value
                elif hasattr(field_data, 'items'):
                    # List field - extract items (for deductions, taxes arrays)
                    values = []
                    for item in field_data.items:
                        if hasattr(item, 'value'):
                            values.append(item.value)
                        elif hasattr(item, 'fields'):
                            # Nested object (like deduction or tax with name and amount)
                            nested_dict = {}
                            for k, v in item.fields.items():
                                if hasattr(v, 'value'):
                                    nested_dict[k] = v.value
                                else:
                                    nested_dict[k] = v
                            values.append(nested_dict)
                        else:
                            values.append(item)
                    value = values
                elif hasattr(field_data, 'fields'):
                    # Nested object (like address)
                    nested_dict = {}
                    for k, v in field_data.fields.items():
                        if hasattr(v, 'value'):
                            nested_dict[k] = v.value
                        else:
                            nested_dict[k] = v
                    value = nested_dict
                else:
                    # Already a plain value
                    value = field_data

                # Map field name to standard name if needed
                standard_name = field_mapping.get(name, name)
                extracted[standard_name] = value

                logger.info(f"  → Extracted {name}: {value}")

            # Combine first_name and last_name into employee_name
            if extracted.get('first_name') or extracted.get('last_name'):
                first = extracted.get('first_name', '')
                last = extracted.get('last_name', '')
                extracted['employee_name'] = f"{first} {last}".strip()
                logger.info(f"Combined first_name and last_name to employee_name: {extracted['employee_name']}")

            # Extract company_name from employer_name
            if extracted.get('employer_name') and not extracted.get('company_name'):
                extracted['company_name'] = extracted['employer_name']
                logger.info(f"Set company_name from employer_name: {extracted['company_name']}")

            # Process deductions array to extract individual tax fields
            deductions = extracted.get('deductions', [])
            taxes = extracted.get('taxes', [])
            
            # Combine deductions and taxes for processing
            all_deductions = []
            if isinstance(deductions, list):
                all_deductions.extend(deductions)
            if isinstance(taxes, list):
                all_deductions.extend(taxes)
            
            # Extract tax amounts from deductions/taxes arrays
            for deduction in all_deductions:
                if isinstance(deduction, dict):
                    name = str(deduction.get('name', '')).upper()
                    amount = deduction.get('amount')
                    
                    if amount is not None:
                        try:
                            amount_val = float(str(amount).replace(',', '').replace('$', ''))
                        except:
                            amount_val = None
                        
                        if amount_val is not None:
                            if 'FEDERAL' in name or 'FED' in name:
                                if not extracted.get('federal_tax'):
                                    extracted['federal_tax'] = amount_val
                            elif 'STATE' in name or 'ST ' in name:
                                if not extracted.get('state_tax'):
                                    extracted['state_tax'] = amount_val
                            elif 'SOCIAL' in name or 'SS' in name or 'OASDI' in name:
                                if not extracted.get('social_security'):
                                    extracted['social_security'] = amount_val
                            elif 'MEDICARE' in name or 'MED' in name:
                                if not extracted.get('medicare'):
                                    extracted['medicare'] = amount_val

            logger.info(f"Successfully extracted {len(extracted)} fields from Mindee: {list(extracted.keys())}")
            logger.info(f"Extracted data summary: {extracted}")
            return extracted, raw_text

        except Exception as e:
            logger.error(f"Mindee extraction failed: {e}", exc_info=True)
            raise RuntimeError(f"Failed to extract paystub data: {str(e)}") from e

    def _normalize_data(self, extracted_data: Dict) -> Dict:
        """Normalize paystub data"""
        try:
            normalizer = PaystubNormalizerFactory.get_normalizer()
            if normalizer:
                normalized_paystub = normalizer.normalize(extracted_data)
                normalized_data = normalized_paystub.to_dict()
                logger.info("Normalization complete")
                return normalized_data
            else:
                logger.warning("No normalizer found - using raw extracted data")
                return extracted_data
        except Exception as e:
            logger.warning(f"Normalization failed: {e}. Using raw extracted data.")
            return extracted_data

    def _collect_validation_issues(self, normalized_data: Dict) -> List[str]:
        """Collect validation issues without exiting early"""
        issues = []
        
        # Check for missing critical fields
        # Use pay_period_start or pay_period_end instead of pay_date
        critical_fields = ['company_name', 'employee_name', 'gross_pay', 'net_pay']
        missing_critical = [field for field in critical_fields if not normalized_data.get(field)]
        # Check for date fields
        if not (normalized_data.get('pay_period_start') or normalized_data.get('pay_period_end')):
            missing_critical.append('pay_period')
        if missing_critical:
            issues.append(f"Missing critical fields: {', '.join(missing_critical)}")
        
        # Check for impossible values
        gross = normalized_data.get('gross_pay', 0)
        net = normalized_data.get('net_pay', 0)
        try:
            gross_val = float(str(gross).replace(',', '').replace('$', '')) if gross else 0
            net_val = float(str(net).replace(',', '').replace('$', '')) if net else 0
            if gross_val > 0 and net_val > gross_val:
                issues.append("CRITICAL: Net pay is greater than gross pay (impossible)")
        except:
            pass
        
        return issues

    def _run_ml_fraud_detection(self, normalized_data: Dict, raw_text: str) -> Dict:
        """Run ML fraud detection"""
        if not self.ml_detector:
            raise RuntimeError(
                "ML detector not initialized. Please ensure the ML model is properly configured."
            )
        
        # Propagate exceptions - no fallback
        return self.ml_detector.predict_fraud(normalized_data, raw_text)

    def _get_employee_info(self, normalized_data: Dict) -> Dict:
        """Get employee history information"""
        employee_name = normalized_data.get('employee_name')
        if not employee_name:
            return {}
        
        try:
            from .database.paystub_customer_storage import PaystubCustomerStorage
            storage = PaystubCustomerStorage()
            return storage.get_employee_history(employee_name)
        except Exception as e:
            logger.warning(f"Failed to get employee history: {e}")
            return {}

    def _check_duplicate(self, normalized_data: Dict) -> bool:
        """Check if this paystub is a duplicate"""
        employee_name = normalized_data.get('employee_name')
        pay_period_start = normalized_data.get('pay_period_start')
        pay_period_end = normalized_data.get('pay_period_end')
        # Use pay_period_end as pay_date for duplicate check if pay_date doesn't exist
        pay_date = normalized_data.get('pay_date') or pay_period_end
        
        if not (employee_name and pay_period_start):
            return False
        
        try:
            from .database.paystub_customer_storage import PaystubCustomerStorage
            storage = PaystubCustomerStorage()
            return storage.check_duplicate_paystub(employee_name, pay_date, pay_period_start)
        except Exception as e:
            logger.warning(f"Failed to check duplicate: {e}")
            return False

    def _run_ai_analysis(self, normalized_data: Dict, ml_analysis: Dict, employee_info: Dict) -> Optional[Dict]:
        """Run AI fraud analysis"""
        if not self.ai_agent:
            raise RuntimeError(
                "AI agent not initialized. Please ensure OpenAI API key is configured."
            )
        
        # Propagate exceptions - no fallback
        employee_name = normalized_data.get('employee_name')
        ai_analysis = self.ai_agent.analyze_fraud(
            extracted_data=normalized_data,
            ml_analysis=ml_analysis,
            employee_name=employee_name
        )
        
        # UPDATED POLICY: Post-AI validation - Force REJECT only if escalate_count > 0 AND fraud risk >= 20%
        # If fraud risk < 20%, allow approval even for repeat offenders
        if employee_info and employee_info.get('escalate_count', 0) > 0:
            escalate_count = employee_info.get('escalate_count', 0)
            fraud_risk_score = ml_analysis.get('fraud_risk_score', 0.0)
            fraud_risk_percent = fraud_risk_score * 100
            
            if fraud_risk_percent >= 20:
                if ai_analysis and ai_analysis.get('recommendation') != 'REJECT':
                    logger.warning(
                        f"[POST_AI_VALIDATION] Employee {employee_name} has escalate_count={escalate_count} "
                        f"and fraud_risk_score={fraud_risk_percent:.1f}% (>= 20%) "
                        f"but AI returned {ai_analysis.get('recommendation')}. "
                        f"Overriding to REJECT per updated repeat offender policy."
                    )
                    # Force REJECT for repeat offenders with high fraud risk
                    ai_analysis['recommendation'] = 'REJECT'
                    ai_analysis['confidence_score'] = 1.0
                    if 'reasoning' not in ai_analysis:
                        ai_analysis['reasoning'] = []
                    ai_analysis['reasoning'].insert(0, 
                        f"CRITICAL: Overridden to REJECT because employee has escalate_count={escalate_count} "
                        f"and fraud risk score ({fraud_risk_percent:.1f}%) >= 20%. "
                        f"Repeat offenders with elevated fraud risk are automatically rejected per policy."
                    )
                    if 'key_indicators' not in ai_analysis:
                        ai_analysis['key_indicators'] = []
                    ai_analysis['key_indicators'].insert(0, f"Repeat offender detected (escalate_count: {escalate_count}, fraud risk: {fraud_risk_percent:.1f}%)")
            else:
                logger.info(
                    f"[POST_AI_VALIDATION] Employee {employee_name} has escalate_count={escalate_count} "
                    f"but fraud_risk_score={fraud_risk_percent:.1f}% (< 20%). "
                    f"Allowing AI recommendation to proceed per updated policy."
                )
        
        return ai_analysis

    def _generate_anomalies(self, normalized_data: Dict, ml_analysis: Dict, ai_analysis: Optional[Dict]) -> list:
        """Generate list of anomalies"""
        anomalies = []
        
        # Add ML-detected anomalies
        if ml_analysis.get('feature_importance'):
            anomalies.extend(ml_analysis['feature_importance'])
        
        # Add AI-detected key indicators
        if ai_analysis and ai_analysis.get('key_indicators'):
            anomalies.extend(ai_analysis['key_indicators'])
        
        return anomalies

    def _calculate_confidence(self, normalized_data: Dict, ml_analysis: Dict, ai_analysis: Optional[Dict]) -> float:
        """Calculate overall confidence score"""
        ml_confidence = ml_analysis.get('model_confidence', 0.5)
        ai_confidence = ai_analysis.get('confidence_score', 0.5) if ai_analysis else 0.5
        
        # Weighted average
        return (ml_confidence * 0.4 + ai_confidence * 0.6)

    def _determine_final_decision(self, validation_issues: list, ml_analysis: Dict, ai_analysis: Optional[Dict], normalized_data: Dict) -> str:
        """Determine final decision based on all collected information"""
        # AI recommendation takes precedence
        if ai_analysis and ai_analysis.get('recommendation'):
            return ai_analysis['recommendation']
        
        # Edge case: If AI analysis exists but has no recommendation (should not happen)
        # Use ML score as last resort (this indicates a bug in AI analysis)
        fraud_risk_score = ml_analysis.get('fraud_risk_score', 0.0)
        if fraud_risk_score >= 0.85:
            return 'REJECT'
        elif fraud_risk_score >= 0.5:
            return 'ESCALATE'
        else:
            return 'APPROVE'

    def _build_complete_response(
        self,
        extracted_data: Dict,
        normalized_data: Dict,
        ml_analysis: Dict,
        ai_analysis: Optional[Dict],
        employee_info: Dict,
        anomalies: list,
        confidence_score: float,
        validation_issues: list,
        overall_decision: str,
        duplicate_detected: bool,
        raw_text: str
    ) -> Dict:
        """Build complete analysis response"""
        return {
            'success': True,
            'document_type': 'PAYSTUB',
            'extracted_data': extracted_data,
            'normalized_data': normalized_data,
            'ml_analysis': ml_analysis,
            'ai_analysis': ai_analysis or {},
            'employee_info': employee_info or {},
            'fraud_risk_score': ml_analysis.get('fraud_risk_score', 0.0),
            'risk_level': ml_analysis.get('risk_level', 'UNKNOWN'),
            'model_confidence': ml_analysis.get('model_confidence', 0.0),
            'ai_recommendation': ai_analysis.get('recommendation', 'UNKNOWN') if ai_analysis else 'UNKNOWN',
            'ai_confidence': ai_analysis.get('confidence_score', 0.0) if ai_analysis else 0.0,
            'anomalies': anomalies,
            'validation_issues': validation_issues,
            'confidence_score': confidence_score,
            'overall_decision': overall_decision,
            'duplicate_detected': duplicate_detected,
            'raw_text_preview': raw_text[:500] if raw_text else '',
            'extraction_timestamp': datetime.now().isoformat()
        }

