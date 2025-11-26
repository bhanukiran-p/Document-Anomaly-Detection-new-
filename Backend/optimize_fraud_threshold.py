"""
Optimize the fraud detection threshold to balance precision and recall
This finds the best threshold to minimize false positives while catching fraud
"""

import pickle
import json
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score, roc_curve, auc
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Load the model and scaler
with open('models/bank_statement_risk_model_latest.pkl', 'rb') as f:
    model = pickle.load(f)

with open('models/bank_statement_scaler_latest.pkl', 'rb') as f:
    scaler = pickle.load(f)

with open('models/bank_statement_model_metadata_latest.json', 'r') as f:
    metadata = json.load(f)

# Load training data to get test set probabilities
df = pd.read_csv('../dataset/staement_fraud_5000.csv')
df = df.dropna(subset=['is_fraud', 'opening_balance', 'ending_balance'])

# Use original 19 features to engineer new ones
base_features = [
    'opening_balance', 'ending_balance', 'total_credits', 'total_debits',
    'amount', 'balance_after', 'is_credit', 'is_debit', 'abs_amount',
    'is_large_transaction', 'amount_to_balance_ratio',
    'transactions_past_1_day', 'transactions_past_7_days',
    'cumulative_monthly_credits', 'cumulative_monthly_debits',
    'is_new_merchant', 'weekday', 'day_of_month', 'is_weekend'
]

X = df[base_features].copy().fillna(df[base_features].mean())

# Engineer features to match training
X['high_transaction_frequency'] = (X['transactions_past_7_days'] > X['transactions_past_7_days'].quantile(0.75)).astype(int)
X['balance_health'] = X['opening_balance'] / (X['total_credits'] + X['total_debits'] + 1)
X['balance_health'] = X['balance_health'].fillna(0)
total_activity = X['total_credits'] + X['total_debits']
X['credit_debit_imbalance'] = np.abs(X['total_credits'] - X['total_debits']) / (total_activity + 1)
X['large_transaction_dominance'] = (X['is_large_transaction'] > 0).astype(int)
X['transaction_regularity'] = np.where(X['is_large_transaction'] > 0, 1, 0)

y = df['is_fraud'].copy()

# Split to get test set
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Scale
X_test_scaled = scaler.transform(X_test)

# Get probability predictions
y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]

# Find optimal threshold
thresholds = np.arange(0.1, 0.9, 0.05)
results = []

print("=" * 100)
print("FRAUD DETECTION THRESHOLD OPTIMIZATION")
print("=" * 100)
print(f"\n{'Threshold':<12} {'Precision':<12} {'Recall':<12} {'F1 Score':<12} {'FPR':<12} {'FNR':<12}")
print("-" * 100)

for threshold in thresholds:
    y_pred_binary = (y_pred_proba >= threshold).astype(int)

    precision = precision_score(y_test, y_pred_binary, zero_division=0)
    recall = recall_score(y_test, y_pred_binary, zero_division=0)
    f1 = f1_score(y_test, y_pred_binary, zero_division=0)

    # Calculate false positive and false negative rates
    tn = ((y_pred_binary == 0) & (y_test == 0)).sum()
    fp = ((y_pred_binary == 1) & (y_test == 0)).sum()
    fn = ((y_pred_binary == 0) & (y_test == 1)).sum()
    tp = ((y_pred_binary == 1) & (y_test == 1)).sum()

    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0

    results.append({
        'threshold': threshold,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'fpr': fpr,
        'fnr': fnr
    })

    print(f"{threshold:<12.2f} {precision:<12.4f} {recall:<12.4f} {f1:<12.4f} {fpr:<12.2%} {fnr:<12.2%}")

# Find best threshold based on F1 score
best_result = max(results, key=lambda x: x['f1'])
best_threshold = best_result['threshold']

print("-" * 100)
print(f"\n🎯 RECOMMENDED THRESHOLD: {best_threshold:.2f}")
print(f"   Precision: {best_result['precision']:.4f} (% of fraud predictions that are correct)")
print(f"   Recall: {best_result['recall']:.4f} (% of actual fraud detected)")
print(f"   F1 Score: {best_result['f1']:.4f}")
print(f"   False Positive Rate: {best_result['fpr']:.2%} ⚠️ (legitimate marked as fraud)")
print(f"   False Negative Rate: {best_result['fnr']:.2%} ⚠️ (fraud marked as legitimate)")

# Also find threshold that minimizes false positives while maintaining good recall
good_recall_results = [r for r in results if r['recall'] >= 0.75]  # Catch at least 75% of fraud
if good_recall_results:
    best_balanced = min(good_recall_results, key=lambda x: x['fpr'])
    print(f"\n⚖️  BALANCED THRESHOLD (75%+ fraud detection): {best_balanced['threshold']:.2f}")
    print(f"   False Positive Rate: {best_balanced['fpr']:.2%}")
    print(f"   Recall: {best_balanced['recall']:.4f}")

# Save optimal threshold to metadata
metadata['optimal_threshold'] = float(best_threshold)
metadata['balanced_threshold'] = float(best_balanced['threshold']) if good_recall_results else float(best_threshold)

with open('models/bank_statement_model_metadata_latest.json', 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"\n✅ Thresholds saved to metadata!")
print("=" * 100)
