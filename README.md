# XFORIA DAD - Document Anomaly Detection for Finance

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![React](https://img.shields.io/badge/React-18.2.0-61dafb?logo=react)
![Flask](https://img.shields.io/badge/Flask-3.1.1-000000?logo=flask)
![Python](https://img.shields.io/badge/Python-3.13-3776ab?logo=python)

**Your Guardian against Fraud** - AI-Powered Document Extraction System

---

## 🎯 Overview

XFORIA DAD is a professional document extraction system that uses Google Cloud Vision API to analyze and extract information from financial documents including checks and paystubs.

### Features

- ✅ **Check Analysis** - Extract bank, payee, amount, date, account details
- ✅ **Paystub Analysis** - Extract employee, company, pay, tax information  
- ✅ **PDF Support** - Process both images and PDF documents
- ✅ **High Accuracy** - Improved confidence scoring (60-95%)
- ✅ **Modern UI** - React.js with XFORIA DAD branding
- ✅ **API Architecture** - Separated frontend and backend
- ✅ **Production Ready** - Scalable and deployable

---

## 🎨 Design

**XFORIA DAD Color Scheme:**
- **Primary Navy:** `#1a365d` - Headers, Footer, Primary text
- **Light Blue:** `#e6f2ff` - Info boxes, Success states
- **Red Accent:** `#dc2626` - Action buttons, Error states
- **White/Gray:** Backgrounds and content

---

## 🏗️ Architecture

```
┌─────────────────┐         ┌──────────────────┐
│   React.js      │ HTTP    │   Flask API      │
│   Frontend      │ ──────> │   Backend        │
│   Port 3002     │         │   Port 5000      │
└─────────────────┘         └──────────────────┘
        │                            │
        │                            ▼
        │                   ┌────────────────┐
        │                   │ Google Vision  │
        └──────────────────>│      API       │
                           └────────────────┘
```

---

## 📦 Installation

### Prerequisites
- Node.js 16+ and npm
- Python 3.13+
- **Google Cloud Vision API credentials** (see setup below)

### Step 1: Set Up Google Cloud Credentials

**IMPORTANT:** You must add your own credentials before running the application.

1. Get credentials from [Google Cloud Console](https://console.cloud.google.com/)
2. Download the JSON key file
3. Rename it to: `check-ocr-project-469619-d18e1cdc414d.json`
4. Place it in the `Backend/` directory

📖 **Detailed instructions:** See `Backend/CREDENTIALS_SETUP.md`

### Step 2: Install Backend Dependencies

```bash
cd Backend
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd Frontend
npm install
```

---

## 🚀 Running the Application

### Start Backend (Terminal 1)
```bash
cd Backend
python api_server.py
```
Backend runs on: **http://localhost:5000**

### Start Frontend (Terminal 2)
```bash
cd Frontend
npm start
```
Frontend runs on: **http://localhost:3002**

---

## 📚 Usage

1. **Open Browser:** http://localhost:3002

2. **Check Analysis:**
   - Navigate to "Check Analysis"
   - Upload check image (JPG, PNG, PDF)
   - Click "Analyze Check"
   - View extracted details with confidence score
   - Download JSON results

3. **Paystub Analysis:**
   - Navigate to "Paystub Analysis"
   - Upload paystub document
   - Click "Analyze Paystub"
   - View employee, pay, and tax details
   - Download JSON results

---

## 🔌 API Endpoints

### Health Check
```
GET /api/health
```

### Check Analysis
```
POST /api/check/analyze
Content-Type: multipart/form-data
Body: file (image or PDF)
```

### Paystub Analysis
```
POST /api/paystub/analyze
Content-Type: multipart/form-data
Body: file (image or PDF)
```

---

## 📂 Project Structure

```
XFORIA-DAD/
├── Frontend/               # React.js Application
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API integration
│   │   └── styles/         # Color palette & CSS
│   └── package.json
│
├── Backend/                # Flask API Server
│   ├── api_server.py       # Main API
│   ├── production_google_vision-extractor.py
│   ├── pages/
│   │   └── paystub_extractor.py
│   └── requirements.txt
│
└── README.md               # This file
```

---

## 🔒 Security Note

**IMPORTANT:** Google Cloud credentials are NOT included in this repository for security.

**To run this application:**
1. You must add your own credentials file to `Backend/`
2. See `Backend/CREDENTIALS_SETUP.md` for detailed setup instructions
3. Use `Backend/credentials.example.json` as a template

**The `.gitignore` is configured to exclude:**
- `check-ocr-project-*.json`
- All other credential JSON files
- Sensitive configuration

**Never commit real credentials to public repositories!**

---

## 🛠️ Technologies

**Frontend:**
- React 18
- React Router v6
- Axios
- React Dropzone

**Backend:**
- Flask
- Google Cloud Vision API
- PyMuPDF (PDF processing)
- Pillow (Image processing)

---

## 📊 Supported Banks & Formats

**Checks:**
- Axis Bank, Bank of America, ICICI, HDFC, Chase, Wells Fargo, Citibank
- US and Indian bank formats

**Paystubs:**
- US payroll formats
- International paystub formats

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is proprietary software for XFORIA DAD.

---

## 👥 Contact

**XFORIA DAD** - Your Guardian against Fraud

- Website: [Your website]
- Email: [Your email]

---

## 🙏 Acknowledgments

- Google Cloud Vision API for OCR capabilities
- React.js community
- Flask framework

---

**Where Innovation Meets Security | Zero Tolerance for Fraud**

© 2025 XFORIA DAD. All rights reserved.

