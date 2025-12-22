@echo off
echo ============================================================
echo Starting Backend Server with Correct OpenAI API Key
echo ============================================================
echo.

REM Set the correct API key from .env file
set OPENAI_API_KEY=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

echo API Key set: %OPENAI_API_KEY:~0,15%...
echo.
echo Starting server...
echo.

python api_server.py

pause
