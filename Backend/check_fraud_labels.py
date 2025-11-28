"""Check actual fraud labels in the dataset"""
import pandas as pd

csv_file = '../dataset/staement_fraud_5000.csv'
df = pd.read_csv(csv_file)

print("Dataset Analysis")
print("=" * 70)
print(f"Total rows: {len(df)}")
print(f"Columns: {list(df.columns)}")
print()

if 'is_fraud' in df.columns:
    print("Fraud Label Distribution:")
    print(df['is_fraud'].value_counts())
    fraud_count = df['is_fraud'].sum()
    fraud_pct = (fraud_count / len(df)) * 100
    print(f"\nActual Fraud Cases: {fraud_count} ({fraud_pct:.2f}%)")
    print(f"Legitimate Cases: {len(df) - fraud_count} ({100-fraud_pct:.2f}%)")
else:
    print("[WARNING] No 'is_fraud' column found in dataset")

print("\n" + "=" * 70)
print("Sample transactions:")
print(df.head(10)[['transaction_id', 'amount', 'category', 'merchant_name', 'is_fraud']])
