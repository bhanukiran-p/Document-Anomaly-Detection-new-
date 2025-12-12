"""
Flask API Server for XFORIA DAD (MODULAR VERSION)
Handles Check, Paystub, Money Order, and Bank Statement Analysis
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from werkzeug.utils import secure_filename
import importlib.util
import re
import fitz
import uuid
from datetime import datetime
from pathlib import Path
from google.cloud import vision
from auth import login_user, register_user
from database.supabase_client import get_supabase, check_connection as check_supabase_connection
from auth.supabase_auth import login_user_supabase, register_user_supabase, verify_token
from database.document_storage import store_money_order_analysis, store_bank_statement_analysis, store_paystub_analysis, store_check_analysis

# Import centralized configuration
from config import Config

# Ensure necessary directories exist
Config.ensure_directories()

# Setup centralized logging
Config.setup_logging()

# Get logger for this module
logger = Config.get_logger(__name__)
logger.info(f"Logging configured. Log directory: {Config.LOG_DIR}")

# Validate configuration
config_errors = Config.validate()
if config_errors:
    logger.warning("Configuration issues detected:")
    for error in config_errors:
        logger.warning(f"  - {error}")

# Check for critical environment variables
if Config.OPENAI_API_KEY:
    logger.info("OPENAI_API_KEY found in environment")
else:
    logger.error("OPENAI_API_KEY NOT found in environment")

if Config.GOOGLE_APPLICATION_CREDENTIALS:
    logger.info(f"Google Credentials path: {Config.GOOGLE_APPLICATION_CREDENTIALS}")
else:
    logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set")

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

# Enable CORS with configured origins
CORS(app, origins=Config.CORS_ORIGINS)

# Configuration from centralized config
UPLOAD_FOLDER = Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS
CREDENTIALS_PATH = Config.GOOGLE_APPLICATION_CREDENTIALS or 'google-credentials.json'

# Initialize Vision API client once
try:
    vision_client = vision.ImageAnnotatorClient.from_service_account_file(CREDENTIALS_PATH)
    logger.info(f"Successfully loaded Google Cloud Vision credentials from {CREDENTIALS_PATH}")
except Exception as e:
    logger.warning(f"Failed to load Vision API credentials: {e}")
    vision_client = None

# Initialize Supabase client
try:
    supabase = get_supabase()
    supabase_status = check_supabase_connection()
    logger.info(f"Supabase initialization: {supabase_status['message']}")
except Exception as e:
    logger.warning(f"Failed to initialize Supabase: {e}")
    supabase = None


# ========================================
# IMPORT AND REGISTER BLUEPRINTS
# ========================================
from routes.health_routes import health_bp
from routes.auth_routes import auth_bp
from routes.check_routes import check_bp
from routes.paystub_routes import paystub_bp
from routes.money_order_routes import money_order_bp
from routes.bank_statement_routes import bank_statement_bp

app.register_blueprint(health_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(check_bp, url_prefix='/api/check')
app.register_blueprint(paystub_bp, url_prefix='/api/paystub')
app.register_blueprint(money_order_bp, url_prefix='/api/money-order')
app.register_blueprint(bank_statement_bp, url_prefix='/api/bank-statement')

logger.info("✅ Blueprints registered: health, auth, check, paystub, money_order, bank_statement")


# ========================================
# REMAINING ROUTES (TO BE MODULARIZED)
# Document query routes and real-time routes remain inline
# ========================================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# NOTE: Document query routes (/api/checks/list, /api/money-orders/search, etc.)
# and real-time routes (/api/real-time/analyze, etc.) can be extracted similarly
# For now they remain in the original api_server.py


if __name__ == '__main__':
    print("=" * 60)
    print("XFORIA DAD API Server (MODULAR VERSION)")
    print("=" * 60)
    print(f"Server running on: http://localhost:5001")
    print(f"Modular Routes (6 blueprints):")
    print(f"  ✅ /api/health (health_routes.py)")
    print(f"  ✅ /api/auth/* (auth_routes.py)")
    print(f"  ✅ /api/check/* (check_routes.py)")
    print(f"  ✅ /api/paystub/* (paystub_routes.py)")
    print(f"  ✅ /api/money-order/* (money_order_routes.py)")
    print(f"  ✅ /api/bank-statement/* (bank_statement_routes.py)")
    print(f"  ⚠️  Remaining: document queries, real-time (in original api_server.py)")
    print("=" * 60)

    app.run(debug=False, host='0.0.0.0', port=5001, use_reloader=False)
