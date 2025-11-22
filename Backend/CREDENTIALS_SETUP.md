# Mindee API Setup

## ⚠️ IMPORTANT

The backend now relies on [Mindee](https://developers.mindee.com/) for OCR and document parsing.  
You must provide a valid API key (and optionally custom model IDs) via environment variables.

---

## 📋 Steps

### 1. Create/Get Your Mindee API Key

1. Sign in at [Mindee Console](https://platform.mindee.com/).
2. Open **API Keys** → generate a key (or reuse an existing one).
3. Copy the key (it starts with `md_...`).

### 2. (Optional) Custom Model IDs

If you have fine-tuned models per document type, note their IDs:
- `MINDEE_MODEL_ID_GLOBAL`
- `MINDEE_MODEL_ID_CHECK`
- `MINDEE_MODEL_ID_PAYSTUB`
- `MINDEE_MODEL_ID_BANK_STATEMENT`
- `MINDEE_MODEL_ID_MONEY_ORDER`

If a specific ID isn't provided, the backend falls back to the global model.

### 3. Set Environment Variables

#### Windows (PowerShell)
```powershell
setx MINDEE_API_KEY "md_xxxxxxx"
setx MINDEE_MODEL_ID_CHECK "your-check-model-id"
setx MINDEE_MODEL_ID_PAYSTUB "your-paystub-model-id"
# repeat for other IDs if needed
```
Restart your terminal/IDE after running `setx`.  
To set variables only for the current session, use:
```powershell
$env:MINDEE_API_KEY = "md_xxxxxxx"
```

#### macOS / Linux
```bash
export MINDEE_API_KEY="md_xxxxxxx"
export MINDEE_MODEL_ID_CHECK="your-check-model-id"
# etc.
```
Consider adding them to your shell profile (`~/.bashrc`, `~/.zshrc`, ...).

---

## 🔒 Best Practices

- Never commit API keys to git.
- Use a secrets manager (AWS Secrets Manager, Azure Key Vault, GCP Secret Manager) for production.
- Rotate keys periodically.
- Grant the least privilege required (one key per app/environment).

---

## ✅ Quick Verification

1. Set the environment variables.
2. Install backend deps: `pip install -r Backend/requirements.txt`
3. Run the API: `python Backend/api_server.py`
4. Call `/api/health` or upload a sample document.

If the API key is missing/invalid you'll see an error like:
```
RuntimeError: MINDEE_API_KEY is not set
```

---

**Reminder:** treat your Mindee keys like passwords. Rotate and revoke when necessary.***

