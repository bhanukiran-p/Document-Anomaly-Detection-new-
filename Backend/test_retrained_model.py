"""
Test the retrained paystub model with a sample paystub
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paystub.ml.paystub_fraud_detector import PaystubFraudDetector

# Sample paystub similar to the one shown in the screenshot
# Professional Services Corp, Lisa Anderson, $4,500 gross/net
sample_paystub = {
    'employer_name': 'Professional Services Corp',
    'employee_name': 'Lisa Anderson',
    'employee_id': 'EMP-006',
    'gross_pay': 4500.00,
    'net_pay': 4500.00,  # Suspicious: net = gross (no deductions!)
    'pay_period_start': '2025-02-01',
    'pay_period_end': '2025-02-15',
    'pay_date': '2025-02-17',
    'deductions': [],  # No deductions = zero withholding!
    'federal_tax': 0,
    'state_tax': 0,
    'social_security': 0,
    'medicare': 0
}

print("=" * 80)
print("TESTING RETRAINED PAYSTUB FRAUD DETECTOR")
print("=" * 80)
print("\nSample Paystub:")
print(f"  Employer: {sample_paystub['employer_name']}")
print(f"  Employee: {sample_paystub['employee_name']} ({sample_paystub['employee_id']})")
print(f"  Gross Pay: ${sample_paystub['gross_pay']:,.2f}")
print(f"  Net Pay: ${sample_paystub['net_pay']:,.2f}")
print(f"  Federal Tax: ${sample_paystub['federal_tax']}")
print(f"  State Tax: ${sample_paystub['state_tax']}")
print(f"  Social Security: ${sample_paystub['social_security']}")
print(f"  Medicare: ${sample_paystub['medicare']}")
print(f"  Total Deductions: $0.00")
print()

# Initialize detector
detector = PaystubFraudDetector()

# Run fraud detection
result = detector.predict_fraud(sample_paystub, raw_text="")

print("=" * 80)
print("FRAUD DETECTION RESULTS")
print("=" * 80)
print(f"\n🎯 Fraud Risk Score: {result['fraud_risk_score']*100:.1f}%")
print(f"⚠️  Risk Level: {result['risk_level']}")
print(f"📊 Model Confidence: {result['model_confidence']*100:.1f}%")
print()
print("Model Scores:")
print(f"  Random Forest: {result['model_scores']['random_forest']*100:.1f}%")
print(f"  XGBoost: {result['model_scores']['xgboost']*100:.1f}%")
print(f"  Ensemble: {result['model_scores']['ensemble']*100:.1f}%")
print()

if result['anomalies']:
    print("🚨 Detected Anomalies:")
    for anomaly in result['anomalies']:
        print(f"  - {anomaly}")
    print()

if result['fraud_types']:
    print("🔍 Fraud Types:")
    for fraud_type in result['fraud_types']:
        print(f"  - {fraud_type}")
    print()

if result['fraud_reasons']:
    print("📝 Fraud Reasons:")
    for reason in result['fraud_reasons']:
        print(f"  - {reason}")
    print()

if result['feature_importance']:
    print("📈 Top Features:")
    for feature in result['feature_importance']:
        print(f"  - {feature}")

print()
print("=" * 80)
print("EXPECTED: This paystub should be flagged as HIGH/CRITICAL risk")
print("          due to ZERO_WITHHOLDING_SUSPICIOUS (no taxes on $4,500)")
print("=" * 80)
