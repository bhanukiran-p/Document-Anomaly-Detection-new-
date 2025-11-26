"""
Test script to verify Random Forest model produces different predictions
for different bank statement data
"""

import pickle
import json
import numpy as np
import os

# Load the trained model and scaler
model_path = 'models/bank_statement_risk_model_latest.pkl'
scaler_path = 'models/bank_statement_scaler_latest.pkl'
metadata_path = 'models/bank_statement_model_metadata_latest.json'

print("=" * 70)
print("TESTING RANDOM FOREST MODEL PREDICTIONS")
print("=" * 70)

# Load model
with open(model_path, 'rb') as f:
    model = pickle.load(f)
print("✅ Model loaded successfully")

# Load scaler
with open(scaler_path, 'rb') as f:
    scaler = pickle.load(f)
print("✅ Scaler loaded successfully")

# Load metadata
with open(metadata_path, 'r') as f:
    metadata = json.load(f)
print("✅ Metadata loaded successfully")

feature_names = metadata.get('feature_names', [])
print(f"\nExpected features ({len(feature_names)}): {feature_names}\n")

# Test Case 1: Low-risk bank statement (all normal values)
print("=" * 70)
print("TEST CASE 1: LOW-RISK STATEMENT (Normal values)")
print("=" * 70)

test_case_1 = {
    'opening_balance': 5000.0,
    'ending_balance': 5500.0,
    'total_credits': 3000.0,
    'total_debits': 2500.0,
    'amount': 500.0,
    'balance_after': 5500.0,
    'is_credit': 1,
    'is_debit': 0,
    'abs_amount': 500.0,
    'is_large_transaction': 0,
    'amount_to_balance_ratio': 0.1,
    'transactions_past_1_day': 5,
    'transactions_past_7_days': 15,
    'cumulative_monthly_credits': 3000.0,
    'cumulative_monthly_debits': 2500.0,
    'is_new_merchant': 0,
    'weekday': 2,
    'day_of_month': 15,
    'is_weekend': 0,
}

feature_vector_1 = [test_case_1.get(f, 0) for f in feature_names]
print(f"Feature vector: {feature_vector_1}")

feature_vector_1_scaled = scaler.transform([feature_vector_1])
prediction_1 = model.predict(feature_vector_1_scaled)[0]
risk_score_1 = max(0.0, min(100.0, float(prediction_1) * 100))

print(f"Raw prediction: {prediction_1:.6f}")
print(f"Risk score (0-100): {risk_score_1:.2f}")
if risk_score_1 < 25:
    level = "LOW"
elif risk_score_1 < 50:
    level = "MEDIUM"
elif risk_score_1 < 75:
    level = "HIGH"
else:
    level = "CRITICAL"
print(f"Risk level: {level}\n")

# Test Case 2: Medium-risk bank statement (some suspicious values)
print("=" * 70)
print("TEST CASE 2: MEDIUM-RISK STATEMENT (Some anomalies)")
print("=" * 70)

test_case_2 = {
    'opening_balance': 1000.0,
    'ending_balance': 2000.0,  # Doubled
    'total_credits': 5000.0,   # High credits
    'total_debits': 1000.0,    # Low debits (unusual ratio)
    'amount': 2000.0,          # Large transaction
    'balance_after': 2000.0,
    'is_credit': 1,
    'is_debit': 0,
    'abs_amount': 2000.0,
    'is_large_transaction': 1,  # This is a large transaction
    'amount_to_balance_ratio': 2.0,  # High ratio
    'transactions_past_1_day': 2,
    'transactions_past_7_days': 8,
    'cumulative_monthly_credits': 5000.0,
    'cumulative_monthly_debits': 1000.0,
    'is_new_merchant': 1,  # New merchant flag
    'weekday': 6,          # Sunday
    'day_of_month': 1,     # First of month (unusual)
    'is_weekend': 1,       # Weekend transaction
}

feature_vector_2 = [test_case_2.get(f, 0) for f in feature_names]
print(f"Feature vector: {feature_vector_2}")

feature_vector_2_scaled = scaler.transform([feature_vector_2])
prediction_2 = model.predict(feature_vector_2_scaled)[0]
risk_score_2 = max(0.0, min(100.0, float(prediction_2) * 100))

print(f"Raw prediction: {prediction_2:.6f}")
print(f"Risk score (0-100): {risk_score_2:.2f}")
if risk_score_2 < 25:
    level = "LOW"
elif risk_score_2 < 50:
    level = "MEDIUM"
elif risk_score_2 < 75:
    level = "HIGH"
else:
    level = "CRITICAL"
print(f"Risk level: {level}\n")

# Test Case 3: High-risk bank statement (very suspicious)
print("=" * 70)
print("TEST CASE 3: HIGH-RISK STATEMENT (Very suspicious)")
print("=" * 70)

test_case_3 = {
    'opening_balance': 500.0,
    'ending_balance': 10000.0,  # Massive increase
    'total_credits': 15000.0,   # Huge credits
    'total_debits': 100.0,      # Minimal debits
    'amount': 10000.0,          # Huge transaction
    'balance_after': 10000.0,
    'is_credit': 1,
    'is_debit': 0,
    'abs_amount': 10000.0,
    'is_large_transaction': 1,
    'amount_to_balance_ratio': 20.0,  # Extreme ratio
    'transactions_past_1_day': 1,
    'transactions_past_7_days': 3,
    'cumulative_monthly_credits': 15000.0,
    'cumulative_monthly_debits': 100.0,
    'is_new_merchant': 1,
    'weekday': 0,
    'day_of_month': 31,
    'is_weekend': 1,
}

feature_vector_3 = [test_case_3.get(f, 0) for f in feature_names]
print(f"Feature vector: {feature_vector_3}")

feature_vector_3_scaled = scaler.transform([feature_vector_3])
prediction_3 = model.predict(feature_vector_3_scaled)[0]
risk_score_3 = max(0.0, min(100.0, float(prediction_3) * 100))

print(f"Raw prediction: {prediction_3:.6f}")
print(f"Risk score (0-100): {risk_score_3:.2f}")
if risk_score_3 < 25:
    level = "LOW"
elif risk_score_3 < 50:
    level = "MEDIUM"
elif risk_score_3 < 75:
    level = "HIGH"
else:
    level = "CRITICAL"
print(f"Risk level: {level}\n")

# Summary
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Test Case 1 (Low-risk):    Risk Score = {risk_score_1:.2f}")
print(f"Test Case 2 (Medium-risk): Risk Score = {risk_score_2:.2f}")
print(f"Test Case 3 (High-risk):   Risk Score = {risk_score_3:.2f}")
print()

if risk_score_1 != risk_score_2 and risk_score_2 != risk_score_3:
    print("✅ SUCCESS: Model produces DIFFERENT predictions for different inputs!")
    print("   The model is working correctly and differentiating between statements.")
else:
    print("❌ FAILURE: Model produces SAME predictions for different inputs!")
    print("   There may be an issue with feature extraction or model.")

print()
print(f"Prediction difference (Low vs High): {abs(risk_score_3 - risk_score_1):.2f} points")
print("=" * 70)
