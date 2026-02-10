# Libraries & Dependencies

**Complete list of all libraries and frameworks used in XFORIA DAD**

---

## 📦 Backend Libraries (Python)

### Core Web Framework

| Library | Version | Purpose | Usage |
|---------|---------|---------|-------|
| **Flask** | 3.0.0 | Web framework for API server | Main API server (`api_server.py`) |
| **flask-cors** | 4.0.0 | Cross-Origin Resource Sharing | Enable CORS for React frontend |
| **werkzeug** | (bundled) | WSGI utilities | File upload handling (`secure_filename`) |

### OCR & Document Processing

| Library | Version | Purpose | Usage |
|---------|---------|---------|-------|
| **mindee** | ≥4.31.0 | Document OCR API | Primary OCR extraction for all document types |
| **google-cloud-vision** | (latest) | Google Cloud Vision API | Fallback OCR, text extraction |
| **PyMuPDF (fitz)** | 1.23.26 | PDF processing | PDF to image conversion, text extraction |
| **pdf2image** | 1.16.3 | PDF to image conversion | Convert PDF pages to images |
| **Pillow (PIL)** | 10.3.0 | Image processing | Image manipulation, format conversion |
| **opencv-python** | 4.9.0.80 | Computer vision | Additional image processing (optional) |
| **pytesseract** | 0.3.10 | Tesseract OCR wrapper | Fallback OCR (optional) |

### Machine Learning

| Library | Version | Purpose | Usage |
|---------|---------|---------|-------|
| **scikit-learn** | 1.4.2 | ML framework | Random Forest, StandardScaler, train_test_split, metrics |
| **xgboost** | 2.0.3 | Gradient boosting | XGBoost regressor models for fraud detection |
| **lightgbm** | 4.1.0 | Light gradient boosting | Alternative ML model (optional) |
| **joblib** | 1.3.2 | Model serialization | Save/load trained models (.pkl files) |
| **imbalanced-learn** | 0.11.0 | Imbalanced datasets | SMOTE for handling class imbalance |
| **numpy** | 1.26.4 | Numerical computing | Array operations, feature arrays |
| **pandas** | 2.3.3 | Data manipulation | CSV processing, dataframes, real-time analysis |

### AI & LLM

| Library | Version | Purpose | Usage |
|---------|---------|---------|-------|
| **openai** | 1.6.1 | OpenAI API client | GPT-4 API calls for fraud analysis |
| **langchain** | 0.1.0 | LangChain framework | AI agent orchestration |
| **langchain-openai** | 0.0.2 | LangChain OpenAI integration | OpenAI integration for LangChain |
| **tiktoken** | 0.5.2 | Token counting | Count tokens for OpenAI API |
| **chromadb** | 0.4.22 | Vector database | Vector storage (future use) |

### Database & Storage

| Library | Version | Purpose | Usage |
|---------|---------|---------|-------|
| **supabase** | 2.10.0 | Supabase client | PostgreSQL database operations |
| **psycopg2** | (implicit) | PostgreSQL adapter | Database connection (via Supabase) |

### Authentication & Security

| Library | Version | Purpose | Usage |
|---------|---------|---------|-------|
| **PyJWT** | 2.10.1 | JWT token handling | JWT token generation and verification |
| **bcrypt** | (via Supabase) | Password hashing | Password encryption (via Supabase Auth) |

### Utilities & Helpers

| Library | Version | Purpose | Usage |
|---------|---------|---------|-------|
| **python-dotenv** | 1.0.0 | Environment variables | Load `.env` files |
| **python-dateutil** | 2.9.0 | Date parsing | Date manipulation and parsing |
| **requests** | 2.31.0 | HTTP client | API calls (if needed) |
| **uuid** | (built-in) | UUID generation | Generate unique IDs |
| **logging** | (built-in) | Logging | Application logging |
| **json** | (built-in) | JSON handling | JSON serialization/deserialization |
| **re** | (built-in) | Regular expressions | Text pattern matching |
| **datetime** | (built-in) | Date/time handling | Timestamp generation |
| **os** | (built-in) | OS interface | File system operations |
| **sys** | (built-in) | System parameters | System-level operations |
| **io** | (built-in) | I/O operations | File I/O operations |
| **typing** | (built-in) | Type hints | Type annotations |

### Task Scheduling

| Library | Version | Purpose | Usage |
|---------|---------|---------|-------|
| **apscheduler** | 3.10.4 | Task scheduler | Automated model retraining scheduler |

### Web Interface (Optional)

| Library | Version | Purpose | Usage |
|---------|---------|---------|-------|
| **streamlit** | 1.33.0 | Web interface | Alternative web UI (optional) |

### Development & Testing

| Library | Version | Purpose | Usage |
|---------|---------|---------|-------|
| **pytest** | 8.1.1 | Testing framework | Unit and integration tests |
| **black** | 24.3.0 | Code formatter | Code formatting |
| **flake8** | 7.0.0 | Linter | Code quality checks |

---

## 🎨 Frontend Libraries (JavaScript/React)

### Core Framework

| Library | Version | Purpose | Usage |
|---------|---------|---------|-------|
| **react** | 18.2.0 | UI framework | Main React framework |
| **react-dom** | 18.2.0 | React DOM renderer | DOM rendering |
| **react-scripts** | 5.0.1 | Create React App scripts | Build tooling, webpack config |

### Routing

| Library | Version | Purpose | Usage |
|---------|---------|---------|-------|
| **react-router-dom** | 6.20.0 | Client-side routing | Page navigation, route management |

### HTTP Client

| Library | Version | Purpose | Usage |
|---------|---------|---------|-------|
| **axios** | 1.6.2 | HTTP client | API calls to backend |

### Data Visualization

| Library | Version | Purpose | Usage |
|---------|---------|---------|-------|
| **recharts** | 3.5.1 | Chart library | Pie charts, bar charts, line charts |
| **echarts** | 6.0.0 | Chart library | Advanced charts, geographic maps |
| **echarts-for-react** | 3.0.5 | React wrapper for ECharts | React integration for ECharts |
| **echarts-extension-gmap** | 1.7.0 | Google Maps extension | Geographic visualizations |

### File Handling

| Library | Version | Purpose | Usage |
|---------|---------|---------|-------|
| **react-dropzone** | 14.2.3 | File upload | Drag-and-drop file upload |
| **pdfjs-dist** | 3.11.174 | PDF.js | PDF rendering and viewing |

### UI Components

| Library | Version | Purpose | Usage |
|---------|---------|---------|-------|
| **react-icons** | 5.5.0 | Icon library | UI icons (Font Awesome, Material Design, etc.) |

---

## 🔧 Standard Library Modules (Python)

### Built-in Modules Used

| Module | Purpose | Usage |
|--------|---------|-------|
| **os** | Operating system interface | File paths, environment variables |
| **sys** | System-specific parameters | Path manipulation, system info |
| **json** | JSON encoder/decoder | JSON serialization |
| **logging** | Logging facility | Application logging |
| **datetime** | Date/time handling | Timestamps, date operations |
| **re** | Regular expressions | Pattern matching, text parsing |
| **uuid** | UUID objects | Unique ID generation |
| **io** | Core I/O operations | File I/O, StringIO |
| **typing** | Type hints | Type annotations |
| **importlib** | Import machinery | Dynamic module loading |
| **pathlib** | Object-oriented filesystem paths | Path operations |
| **collections** | Specialized container datatypes | Data structures |
| **itertools** | Iterator functions | Iteration utilities |
| **functools** | Higher-order functions | Function utilities |
| **unittest** | Unit testing framework | Testing (via pytest) |

---

## 📊 Library Usage by Component

### API Server (`api_server.py`)
- Flask, flask-cors
- werkzeug (secure_filename)
- PyMuPDF (fitz)
- google.cloud.vision
- supabase
- PyJWT
- logging

### Document Extractors
- mindee (ClientV2)
- numpy, pandas
- datetime, re
- logging

### ML Models
- scikit-learn (RandomForestRegressor, StandardScaler, metrics)
- xgboost (XGBRegressor)
- joblib (model serialization)
- numpy (array operations)
- pandas (dataframes)

### AI Agents
- openai (ChatOpenAI)
- langchain (prompts, agents)
- langchain-openai
- tiktoken (token counting)

### Database Operations
- supabase (PostgreSQL client)
- psycopg2 (via Supabase)

### Frontend Components
- React (all components)
- react-router-dom (routing)
- axios (API calls)
- recharts/echarts (visualizations)
- react-dropzone (file upload)

---

## 🔍 Key Library Details

### Mindee API (`mindee>=4.31.0`)
**Purpose**: Primary OCR and document field extraction  
**Usage**:
```python
from mindee import ClientV2, InferenceParameters, PathInput
client = ClientV2(api_key=MINDEE_API_KEY)
response = client.enqueue_and_get_inference(input_source, params)
```
**Document Types Supported**: Checks, Paystubs, Money Orders, Bank Statements

### scikit-learn (`scikit-learn==1.4.2`)
**Purpose**: Machine learning framework  
**Key Classes Used**:
- `RandomForestRegressor` - Random Forest model
- `StandardScaler` - Feature scaling
- `train_test_split` - Data splitting
- `mean_squared_error`, `r2_score` - Evaluation metrics
- `GridSearchCV` - Hyperparameter tuning

### XGBoost (`xgboost==2.0.3`)
**Purpose**: Gradient boosting model  
**Usage**:
```python
import xgboost as xgb
model = xgb.XGBRegressor(
    n_estimators=200,
    max_depth=8,
    learning_rate=0.1
)
```

### OpenAI (`openai==1.6.1`)
**Purpose**: GPT-4 API for fraud analysis  
**Usage**:
```python
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)
response = client.chat.completions.create(
    model="gpt-4-mini",
    messages=[...]
)
```

### Supabase (`supabase==2.10.0`)
**Purpose**: PostgreSQL database client  
**Usage**:
```python
from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
response = supabase.table('checks').select('*').execute()
```

### Flask (`Flask==3.0.0`)
**Purpose**: Web framework  
**Usage**:
```python
from flask import Flask, request, jsonify
app = Flask(__name__)
@app.route('/api/check/analyze', methods=['POST'])
def analyze_check():
    ...
```

---

## 📦 Installation

### Backend Dependencies
```bash
cd Backend
pip install -r requirements.txt
```

### Frontend Dependencies
```bash
cd Frontend
npm install
```

---

## 🔄 Version Compatibility

### Python Version
- **Required**: Python 3.12+
- **Tested**: Python 3.12, 3.13

### Node.js Version
- **Required**: Node.js 18+
- **Tested**: Node.js 18.x, 20.x

### Key Version Constraints
- **mindee**: ≥4.31.0 (requires ClientV2 API)
- **Flask**: 3.0.0 (latest stable)
- **React**: 18.2.0 (latest stable)
- **scikit-learn**: 1.4.2 (compatible with Python 3.12)
- **xgboost**: 2.0.3 (latest stable)

---

## 🚨 Critical Dependencies

### Required for Core Functionality
1. **mindee** - OCR extraction (no fallback)
2. **openai** - AI analysis (required for recommendations)
3. **supabase** - Database (required for data storage)
4. **scikit-learn** - ML models (required for fraud detection)
5. **xgboost** - ML models (required for fraud detection)
6. **Flask** - API server (core framework)
7. **React** - Frontend (core framework)

### Optional Dependencies
- **google-cloud-vision** - Fallback OCR
- **opencv-python** - Additional image processing
- **pytesseract** - Fallback OCR
- **lightgbm** - Alternative ML model
- **streamlit** - Alternative web UI
- **chromadb** - Vector database (future use)

---

## 📝 Notes

### Library Selection Rationale

**Mindee vs Tesseract:**
- Mindee chosen for better accuracy and structured field extraction
- Tesseract kept as optional fallback

**XGBoost vs LightGBM:**
- XGBoost chosen for better performance on this dataset
- LightGBM available as alternative

**scikit-learn:**
- Industry standard for ML
- Well-documented and stable
- Good integration with XGBoost

**React:**
- Modern, component-based UI framework
- Large ecosystem and community support
- Good performance for dashboards

**Flask:**
- Lightweight and flexible
- Easy to extend
- Good for REST APIs

---

## 🤔 Why Flask Instead of FastAPI?

### Decision Rationale

Flask was chosen over FastAPI for this project based on several factors:

#### 1. **Simplicity & Maturity**
- **Flask**: Established since 2010, mature ecosystem, extensive documentation
- **FastAPI**: Newer (2018), less mature ecosystem
- **Impact**: Easier onboarding, more Stack Overflow answers, proven stability

#### 2. **Use Case Fit**
- **Flask**: Perfect for synchronous REST APIs (this project's primary need)
- **FastAPI**: Better for async/WebSocket applications (not needed here)
- **Impact**: Flask is sufficient - no need for async complexity

#### 3. **Learning Curve**
- **Flask**: Simple, minimal boilerplate, easy to understand
- **FastAPI**: Requires understanding async/await, Pydantic models, type hints
- **Impact**: Faster development, easier maintenance

#### 4. **Library Integration**
- **Flask**: Excellent integration with existing libraries (Mindee, Supabase, OpenAI)
- **FastAPI**: May require async wrappers for some libraries
- **Impact**: Simpler integration, fewer compatibility issues

#### 5. **Team Familiarity**
- **Flask**: More widely known, larger developer pool
- **FastAPI**: Newer, smaller community
- **Impact**: Easier to find developers, faster development

#### 6. **Project Requirements**
- **Synchronous Processing**: Document analysis is CPU-bound, not I/O-bound
- **Simple REST API**: No need for WebSockets, SSE, or complex async patterns   
- **File Uploads**: Flask handles multipart/form-data well
- **Impact**: Flask perfectly matches requirements

### When FastAPI Would Be Better

FastAPI would be a better choice if:
- **High Concurrency**: Need to handle 1000+ concurrent requests
- **Async Operations**: Heavy I/O-bound operations (many external API calls)
- **WebSockets**: Real-time bidirectional communication needed
- **Type Safety**: Strict type checking with Pydantic models required
- **Auto Documentation**: Need automatic OpenAPI/Swagger docs
- **Performance Critical**: Need maximum request throughput

### Current Flask Implementation

**API Server Structure:**
```python
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=Config.CORS_ORIGINS)

@app.route('/api/check/analyze', methods=['POST'])
def analyze_check():
    # Synchronous processing
    file = request.files['file']
    result = extractor.extract_and_analyze(filepath)
    return jsonify(result)
```

**Why This Works Well:**
- Document processing is CPU-bound (OCR, ML inference)
- Each request processes one document (no need for async)
- Simple request/response pattern
- File uploads handled synchronously

### Performance Comparison

**Flask Performance (Current):**
- Request handling: ~5-15 seconds per document
- Concurrent requests: ~100+ (sufficient for this use case)
- Memory usage: Moderate
- CPU usage: High during ML inference (expected)

**FastAPI Performance (Hypothetical):**
- Request handling: ~5-15 seconds per document (same - CPU-bound)
- Concurrent requests: ~1000+ (not needed)
- Memory usage: Similar
- CPU usage: Same (ML inference is the bottleneck)

**Conclusion**: FastAPI wouldn't provide significant performance benefits for this use case since the bottleneck is CPU-bound ML inference, not I/O.

### Migration Considerations

If migrating to FastAPI in the future:

**Advantages:**
- Automatic OpenAPI documentation
- Better type safety with Pydantic
- Async support for future scalability
- Built-in data validation

**Challenges:**
- Rewrite all endpoints to async
- Update all library calls to async versions
- Add Pydantic models for request/response
- Update frontend to handle async patterns
- Learning curve for team

**Recommendation**: Stay with Flask unless:
1. Need to handle 1000+ concurrent requests
2. Add real-time features (WebSockets)
3. Need automatic API documentation
4. Team prefers FastAPI's type safety

---

**Last Updated:** December 2024

