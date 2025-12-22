@echo off
echo ============================================================
echo Starting Backend Server with Correct OpenAI API Key
echo ============================================================
echo.

REM API key will be loaded from .env file by the application

echo Starting with API key from .env file...
echo.
echo Starting server...
echo.

python api_server.py

pause
