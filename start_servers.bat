@echo off
echo ================================================================
echo           XFORIA DAD - Starting Application Servers
echo ================================================================
echo.

echo [1/2] Starting Backend Server on http://localhost:5001
start "DAD Backend Server" cmd /k "cd /d "%~dp0Backend" && python api_server.py"

echo Waiting for backend to initialize...
timeout /t 5 /nobreak > nul

echo.
echo [2/2] Starting Frontend Server on http://localhost:3000
start "DAD Frontend Server" cmd /k "cd /d "%~dp0Frontend" && npm start"

echo.
echo ================================================================
echo                    Servers Started!
echo ================================================================
echo.
echo Backend API:  http://localhost:5001
echo Frontend App: http://localhost:3000 (will open automatically)
echo.
echo IMPORTANT: Keep both command windows open!
echo            Close them to stop the servers.
echo.
echo If you see any errors, check NETWORK_ERROR_FIX.md
echo ================================================================
pause
