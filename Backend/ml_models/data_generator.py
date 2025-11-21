"""
Synthetic Training Data Generator for Money Order Fraud Detection
Generates balanced dataset with legitimate and fraudulent samples
"""

import random
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict


class SyntheticDataGenerator:
    """
    Generate synthetic money order data for ML training
    Creates both legitimate and fraudulent samples
    """

    def __init__(self):
        # Sample data pools
        self.issuers = ['Western Union', 'MoneyGram', 'USPS']

        self.first_names = [
            'John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Robert', 'Lisa',
            'William', 'Mary', 'James', 'Patricia', 'Richard', 'Jennifer', 'Thomas',
            'Linda', 'Charles', 'Barbara', 'Christopher', 'Susan'
        ]

        self.last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
            'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
            'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin'
        ]

        self.streets = [
            'Main St', 'Oak Ave', 'Maple Dr', 'Elm St', 'Washington Blvd',
            'Park Ave', 'Broadway', 'Cedar Ln', 'Pine St', 'First Ave',
            'Second St', 'Market St', 'Church St', 'Spring St', 'Hill Rd'
        ]

        self.cities = [
            'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix',
            'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose',
            'Austin', 'Jacksonville', 'Fort Worth', 'Columbus', 'Charlotte'
        ]

        self.states = ['NY', 'CA', 'TX', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI']

        self.amount_words = {
            50: "FIFTY AND 00/100 DOLLARS",
            100: "ONE HUNDRED AND 00/100 DOLLARS",
            150: "ONE HUNDRED FIFTY AND 00/100 DOLLARS",
            200: "TWO HUNDRED AND 00/100 DOLLARS",
            250: "TWO HUNDRED FIFTY AND 00/100 DOLLARS",
            300: "THREE HUNDRED AND 00/100 DOLLARS",
            500: "FIVE HUNDRED AND 00/100 DOLLARS",
            750: "SEVEN HUNDRED FIFTY AND 00/100 DOLLARS",
            1000: "ONE THOUSAND AND 00/100 DOLLARS",
            1500: "ONE THOUSAND FIVE HUNDRED AND 00/100 DOLLARS",
            2000: "TWO THOUSAND AND 00/100 DOLLARS",
            3000: "THREE THOUSAND AND 00/100 DOLLARS",
            5000: "FIVE THOUSAND AND 00/100 DOLLARS"
        }

        self.fraud_types = [
            'amount_mismatch',
            'missing_fields',
            'date_inconsistency',
            'invalid_serial',
            'altered_amount',
            'counterfeit',
            'duplicate_serial',
            'stolen_form'
        ]

    def _generate_name(self) -> str:
        """Generate random full name"""
        first = random.choice(self.first_names)
        last = random.choice(self.last_names)
        return f"{first} {last}"

    def _generate_address(self) -> str:
        """Generate random address"""
        number = random.randint(100, 9999)
        street = random.choice(self.streets)
        city = random.choice(self.cities)
        state = random.choice(self.states)
        zipcode = random.randint(10000, 99999)
        return f"{number} {street}, {city}, {state} {zipcode}"

    def _generate_serial(self, issuer: str) -> str:
        """Generate issuer-specific serial number"""
        if issuer == 'Western Union':
            return f"WU{random.randint(100000000, 999999999)}"
        elif issuer == 'MoneyGram':
            return f"MG{random.randint(100000000, 999999999)}"
        elif issuer == 'USPS':
            return f"{random.randint(10000000000, 99999999999)}"
        else:
            return f"{random.randint(1000000000, 9999999999)}"

    def _generate_date(self, days_ago_range: tuple = (1, 90)) -> str:
        """Generate date in MM-DD-YYYY format"""
        days_ago = random.randint(days_ago_range[0], days_ago_range[1])
        date = datetime.now() - timedelta(days=days_ago)
        return date.strftime('%m-%d-%Y')

    def _generate_future_date(self) -> str:
        """Generate future date (fraud indicator)"""
        days_future = random.randint(1, 30)
        date = datetime.now() + timedelta(days=days_future)
        return date.strftime('%m-%d-%Y')

    def _generate_old_date(self) -> str:
        """Generate very old date (fraud indicator)"""
        days_ago = random.randint(200, 500)
        date = datetime.now() - timedelta(days=days_ago)
        return date.strftime('%m-%d-%Y')

    def generate_legitimate_sample(self) -> Dict:
        """
        Generate single legitimate money order sample

        Returns:
            Dictionary with money order fields
        """
        issuer = random.choice(self.issuers)
        amount_value = random.choice(list(self.amount_words.keys()))

        return {
            'issuer_name': issuer,
            'serial_primary': self._generate_serial(issuer),
            'serial_secondary': f"REF{random.randint(100000, 999999)}",
            'recipient': self._generate_name(),
            'sender_name': self._generate_name(),
            'sender_address': self._generate_address(),
            'amount_value': amount_value,
            'amount_currency': 'USD',
            'amount_written': self.amount_words[amount_value],
            'date': self._generate_date(),
            'signature': f"Agent {random.choice(self.last_names)}",
            'is_fraud': 0,
            'fraud_type': 'none',
            'fraud_confidence': 1.0
        }

    def generate_fraud_sample(self, fraud_type: str = None) -> Dict:
        """
        Generate single fraudulent money order sample

        Args:
            fraud_type: Type of fraud to generate (random if None)

        Returns:
            Dictionary with fraudulent money order fields
        """
        if fraud_type is None:
            fraud_type = random.choice(self.fraud_types)

        issuer = random.choice(self.issuers)
        base_sample = self.generate_legitimate_sample()
        base_sample['is_fraud'] = 1
        base_sample['fraud_type'] = fraud_type
        base_sample['fraud_confidence'] = random.uniform(0.85, 1.0)

        # Apply fraud-specific modifications
        if fraud_type == 'amount_mismatch':
            # Numeric amount doesn't match written amount
            amount_value = random.choice(list(self.amount_words.keys()))
            wrong_amount_value = random.choice([v for v in self.amount_words.keys() if v != amount_value])
            base_sample['amount_value'] = amount_value
            base_sample['amount_written'] = self.amount_words[wrong_amount_value]

        elif fraud_type == 'missing_fields':
            # Remove critical fields
            fields_to_remove = random.sample(['sender_name', 'recipient', 'sender_address', 'signature'],
                                            random.randint(1, 3))
            for field in fields_to_remove:
                base_sample[field] = None

        elif fraud_type == 'date_inconsistency':
            # Use future date or very old date
            if random.random() > 0.5:
                base_sample['date'] = self._generate_future_date()
            else:
                base_sample['date'] = self._generate_old_date()

        elif fraud_type == 'invalid_serial':
            # Invalid serial format
            base_sample['serial_primary'] = f"INVALID{random.randint(1000, 9999)}"

        elif fraud_type == 'altered_amount':
            # Amount has been altered (suspicious round amount + mismatch)
            suspicious_amounts = [999, 1499, 2999, 4999, 9999]
            base_sample['amount_value'] = random.choice(suspicious_amounts)
            # Written amount is different
            base_sample['amount_written'] = self.amount_words[random.choice(list(self.amount_words.keys()))]

        elif fraud_type == 'counterfeit':
            # Missing multiple fields + invalid serial
            base_sample['serial_primary'] = f"FAKE{random.randint(10000, 99999)}"
            base_sample['signature'] = None
            base_sample['serial_secondary'] = None

        elif fraud_type == 'duplicate_serial':
            # Serial number pattern looks suspicious (repeated digits)
            repeated_digit = str(random.randint(1, 9))
            base_sample['serial_primary'] = f"WU{repeated_digit * 9}"

        elif fraud_type == 'stolen_form':
            # Legitimate looking but missing signature and has old date
            base_sample['signature'] = None
            base_sample['date'] = self._generate_old_date()

        return base_sample

    def generate_balanced_dataset(self, total_samples: int = 1000) -> pd.DataFrame:
        """
        Generate balanced dataset with 50% fraud, 50% legitimate

        Args:
            total_samples: Total number of samples to generate

        Returns:
            pandas DataFrame with generated data
        """
        legitimate_count = total_samples // 2
        fraud_count = total_samples - legitimate_count

        samples = []

        # Generate legitimate samples
        print(f"Generating {legitimate_count} legitimate samples...")
        for i in range(legitimate_count):
            samples.append(self.generate_legitimate_sample())
            if (i + 1) % 100 == 0:
                print(f"  Generated {i + 1}/{legitimate_count} legitimate samples")

        # Generate fraud samples (distributed across fraud types)
        print(f"Generating {fraud_count} fraud samples...")
        fraud_per_type = fraud_count // len(self.fraud_types)
        remainder = fraud_count % len(self.fraud_types)

        for i, fraud_type in enumerate(self.fraud_types):
            count = fraud_per_type + (1 if i < remainder else 0)
            for j in range(count):
                samples.append(self.generate_fraud_sample(fraud_type))

            print(f"  Generated {count} samples for '{fraud_type}'")

        # Shuffle the dataset
        random.shuffle(samples)

        # Convert to DataFrame
        df = pd.DataFrame(samples)

        print(f"\nDataset generated successfully!")
        print(f"Total samples: {len(df)}")
        print(f"Fraud samples: {df['is_fraud'].sum()} ({df['is_fraud'].sum()/len(df)*100:.1f}%)")
        print(f"Legitimate samples: {(1-df['is_fraud']).sum()} ({(1-df['is_fraud']).sum()/len(df)*100:.1f}%)")

        return df

    def save_to_csv(self, df: pd.DataFrame, filepath: str = 'training_data.csv'):
        """
        Save generated dataset to CSV

        Args:
            df: DataFrame to save
            filepath: Output file path
        """
        df.to_csv(filepath, index=False)
        print(f"Dataset saved to: {filepath}")

    def generate_and_save(self, total_samples: int = 1000,
                         output_path: str = 'ml_models/training_data.csv'):
        """
        Generate dataset and save to CSV (convenience method)

        Args:
            total_samples: Number of samples to generate
            output_path: Path to save CSV file
        """
        df = self.generate_balanced_dataset(total_samples)
        self.save_to_csv(df, output_path)
        return df


# Convenience function for quick dataset generation
def generate_training_data(num_samples: int = 1000, output_path: str = 'training_data.csv'):
    """
    Quick function to generate and save training data

    Args:
        num_samples: Number of samples to generate
        output_path: Path to save CSV file

    Returns:
        Generated DataFrame
    """
    generator = SyntheticDataGenerator()
    return generator.generate_and_save(num_samples, output_path)


if __name__ == "__main__":
    # Example usage: Generate 2000 samples
    print("=== Money Order Fraud Detection - Training Data Generator ===\n")

    generator = SyntheticDataGenerator()
    df = generator.generate_balanced_dataset(total_samples=2000)

    # Save to CSV
    generator.save_to_csv(df, 'ml_models/training_data.csv')

    # Display sample
    print("\nSample data (first 5 rows):")
    print(df.head())

    print("\nFraud type distribution:")
    print(df['fraud_type'].value_counts())
