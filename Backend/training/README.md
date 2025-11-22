# Training Scripts

This folder contains scripts for training ML models used in fraud detection and risk scoring.

## Files

- `train_fraud_models.py` - Train fraud detection models
- `train_risk_model.py` - Train risk scoring models for different document types

## Usage

To train models, run the training scripts from the Backend directory:

```bash
cd Backend
python training/train_risk_model.py
python training/train_fraud_models.py
```

Trained models will be saved to the `models/` directory.
