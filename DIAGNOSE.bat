@echo off
echo ============================================================
echo XFORIA DAD System Diagnostic
echo ============================================================
echo.

echo [1] Checking if Backend Server is running on port 5001...
netstat -ano | findstr :5001
if %ERRORLEVEL% EQU 0 (
    echo    OK - Something is listening on port 5001
) else (
    echo    ERROR - Nothing is listening on port 5001
    echo    You need to start the backend server!
    echo.
    echo    To start backend:
    echo    1. Open a new terminal
    echo    2. Run: python api_server.py
)
echo.

echo [2] Checking if Frontend is running on port 3000...
netstat -ano | findstr :3000
if %ERRORLEVEL% EQU 0 (
    echo    OK - Something is listening on port 3000
) else (
    echo    WARNING - Nothing is listening on port 3000
    echo    You may need to start the frontend!
)
echo.

echo [3] Checking if Python is available...
python --version
if %ERRORLEVEL% EQU 0 (
    echo    OK - Python is installed
) else (
    echo    ERROR - Python not found
)
echo.

echo [4] Checking if sample CSV exists...
if exist "sample_transactions.csv" (
    echo    OK - sample_transactions.csv found
) else (
    echo    WARNING - sample_transactions.csv not found
)
echo.

echo ============================================================
echo NEXT STEPS:
echo ============================================================
echo.
echo If backend is NOT running:
echo    - Double-click: start_backend.bat
echo    - OR run: cd Backend ^&^& python api_server.py
echo.
echo If frontend is NOT running:
echo    - Double-click: start_frontend.bat
echo    - OR run: cd Frontend ^&^& npm start
echo.
echo ============================================================
pause
