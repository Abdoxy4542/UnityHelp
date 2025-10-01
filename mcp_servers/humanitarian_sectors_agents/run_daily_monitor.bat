@echo off
REM Daily OpenAI Usage Monitor for Sudan Humanitarian Platform
REM This batch file runs the usage monitoring script daily

echo ================================================
echo Sudan Humanitarian AI - Daily Usage Monitor
echo ================================================
echo Starting at %date% %time%
echo.

REM Change to the script directory
cd /d "C:\Users\Lenovo\Desktop\unityaid_platform\mcp_servers\humanitarian_sectors_agents"

REM Activate virtual environment (corrected path)
if exist "..\..\..\..\venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call "..\..\..\..\venv\Scripts\activate.bat"
) else (
    echo [INFO] Trying alternative venv path...
    if exist "..\..\..\venv\Scripts\activate.bat" (
        call "..\..\..\venv\Scripts\activate.bat"
        echo [INFO] Virtual environment activated
    ) else (
        echo [INFO] No virtual environment found, using system Python
        echo [WARNING] You may need to install openai: pip install openai
    )
)

REM Run the usage dashboard
echo [INFO] Running usage monitoring...
python usage_dashboard.py

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

REM Keep window open for 10 seconds so you can see the results
timeout /t 10

REM Optional: Open usage log in notepad for review
REM notepad local_usage_tracking.json