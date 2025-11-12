# Google Cloud Credentials Setup

## ⚠️ IMPORTANT: Setting Up Your Credentials

The Google Cloud Vision API requires valid credentials to function. These credentials are NOT included in the repository for security reasons.

---

## 📋 Steps to Set Up Credentials

### Step 1: Get Your Google Cloud Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project or select existing project
3. Enable the **Vision API**
4. Go to **IAM & Admin > Service Accounts**
5. Create a service account with Vision API access
6. Generate a JSON key file
7. Download the JSON file

### Step 2: Add Credentials to Backend

1. Rename your downloaded JSON file to:
   ```
   check-ocr-project-469619-d18e1cdc414d.json
   ```
   
   Or use any name and update the code to reference it.

2. Place the file in the `Backend/` directory:
   ```
   Backend/
   ├── check-ocr-project-469619-d18e1cdc414d.json  ← Your credentials here
   ├── api_server.py
   └── ...
   ```

3. The `.gitignore` is configured to NOT commit credential files

### Step 3: Verify Credentials Work

Run the test:
```bash
cd Backend
python -c "from google.cloud import vision; from google.oauth2 import service_account; creds = service_account.Credentials.from_service_account_file('check-ocr-project-469619-d18e1cdc414d.json'); client = vision.ImageAnnotatorClient(credentials=creds); print('Credentials working!')"
```

---

## 🔒 Security Best Practices

### For Development:
✅ Keep credentials in `Backend/` directory
✅ `.gitignore` excludes them from git
✅ Don't share credentials in public repos

### For Production:
✅ Use environment variables
✅ Use cloud secret managers (AWS Secrets Manager, Azure Key Vault, etc.)
✅ Rotate credentials regularly
✅ Use least-privilege access

---

## 🌍 Using Environment Variables (Recommended for Production)

Instead of a JSON file, you can use environment variables:

### Windows (PowerShell):
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\credentials.json"
```

### Linux/Mac:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

### Python Code:
```python
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/path/to/credentials.json'
```

---

## 📄 Credentials File Structure

Your credentials JSON should look like `credentials.template.json`:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "service-account@project.iam.gserviceaccount.com",
  ...
}
```

---

## ❗ Troubleshooting

### Error: "Credentials file not found"
- Ensure file is in `Backend/` directory
- Check filename matches exactly
- Verify file is valid JSON

### Error: "Permission denied"
- Check service account has Vision API access
- Verify API is enabled in Google Cloud Console

### Error: "Invalid credentials"
- Re-download credentials from Google Cloud
- Ensure no extra characters in JSON file

---

## 🔗 Useful Links

- [Google Cloud Vision API Setup](https://cloud.google.com/vision/docs/setup)
- [Creating Service Accounts](https://cloud.google.com/iam/docs/creating-managing-service-accounts)
- [Vision API Pricing](https://cloud.google.com/vision/pricing)

---

## ✅ Quick Test

After setting up credentials, test the API server:

```bash
cd Backend
python api_server.py
```

You should see:
```
XFORIA DAD API Server
Server running on: http://localhost:5000
```

Then upload a test document in the React app to verify everything works!

---

**Remember: Never commit real credentials to public repositories!**

