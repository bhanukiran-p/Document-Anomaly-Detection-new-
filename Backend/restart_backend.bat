@echo off
echo ============================================================
echo Restarting Backend Server
echo ============================================================
echo.

echo [1] Killing existing backend server on port 5001...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5001 ^| findstr LISTENING') do (
    echo    Killing process %%a
    taskkill /F /PID %%a
)

echo.
echo [2] Starting backend server...
echo.
cd /d "%~dp0"
python api_server.py

pause
