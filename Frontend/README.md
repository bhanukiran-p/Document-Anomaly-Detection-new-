# XFORIA DAD - Document Anomaly Detection for Finance
## React.js Frontend Application

### Overview
This is a complete React.js conversion of the Streamlit application with the XFORIA DAD color scheme and branding.

### Color Palette
- **Primary Navy**: #1a365d (Headers, Footer)
- **Light Blue**: #e6f2ff (Info boxes)
- **Red**: #dc2626 (Buttons, Errors)
- **White**: #ffffff (Background, Cards)
- **Gray tones**: For text and borders

### Project Structure
```
Frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── Header.jsx
│   │   ├── Footer.jsx
│   │   └── FileUploader.jsx
│   ├── pages/
│   │   ├── HomePage.jsx
│   │   ├── CheckAnalysis.jsx
│   │   └── PaystubAnalysis.jsx
│   ├── services/
│   │   └── api.js
│   ├── styles/
│   │   ├── colors.js
│   │   └── GlobalStyles.css
│   ├── App.js
│   └── index.js
└── package.json
```

### Installation

```bash
cd Frontend
npm install
```

### Running the Application

```bash
# Start frontend (runs on http://localhost:3000)
npm start

# Start backend (runs on http://localhost:5000)
cd ../Backend
python api_server.py
```

### Features
- Check Analysis with OCR extraction
- Paystub Analysis with field detection
- PDF and Image file support
- Real-time analysis with progress indicators
- Downloadable JSON results
- XFORIA DAD branded UI

### API Endpoints
- POST `/api/check/analyze` - Analyze check image
- POST `/api/paystub/analyze` - Analyze paystub document

### Technologies
- React 18
- React Router v6
- Axios for API calls
- React Dropzone for file uploads
- Google Cloud Vision API (backend)

