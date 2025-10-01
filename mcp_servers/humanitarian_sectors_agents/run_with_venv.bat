@echo off
REM Run usage dashboard with proper virtual environment

echo ================================================
echo Sudan Humanitarian AI - Usage Monitor (with venv)
echo ================================================
echo Starting at %date% %time%
echo.

REM Change to the script directory
cd /d "C:\Users\Lenovo\Desktop\unityaid_platform\mcp_servers\humanitarian_sectors_agents"

REM Use the virtual environment Python directly
set PYTHON_PATH=C:\Users\Lenovo\Desktop\unityaid_platform\venv\Scripts\python.exe

echo [INFO] Using Python from virtual environment...
echo [INFO] Python path: %PYTHON_PATH%

REM Check if virtual environment Python exists
if exist "%PYTHON_PATH%" (
    echo [SUCCESS] Virtual environment Python found

    REM Run the usage dashboard with venv Python
    echo [INFO] Running usage monitoring...
    "%PYTHON_PATH%" usage_dashboard.py

) else (
    echo [WARNING] Virtual environment Python not found
    echo [INFO] Trying system Python...
    python usage_dashboard.py
)

echo.
echo [INFO] Checking local usage data...
if exist "local_usage_tracking.json" (
    echo [FOUND] Usage tracking file exists
    echo [INFO] Recent usage data:
    type local_usage_tracking.json | findstr /C:"total_requests" /C:"total_cost_estimate"
) else (
    echo [WARNING] Usage tracking file not found
)

echo.
echo [INFO] Monitor completed at %date% %time%
echo ================================================

REM Keep window open for 10 seconds
timeout /t 10