@echo off
REM Quick manual check of OpenAI usage and tracking data
REM Run this anytime to check your current usage status

title Sudan Humanitarian AI - Usage Check

echo ================================================
echo Sudan Humanitarian AI - Quick Usage Check
echo ================================================
echo Checking usage at %date% %time%
echo.

REM Change to the script directory
cd /d "C:\Users\Lenovo\Desktop\unityaid_platform\mcp_servers\humanitarian_sectors_agents"

REM Check if usage tracking file exists and show summary
if exist "local_usage_tracking.json" (
    echo [FOUND] Usage tracking data:
    echo ----------------------------------------

    REM Extract key information from JSON file
    for /f "tokens=2 delims=:" %%a in ('findstr "total_requests" local_usage_tracking.json') do (
        set total_requests=%%a
    )

    for /f "tokens=2 delims=:" %%b in ('findstr "total_cost_estimate" local_usage_tracking.json') do (
        set total_cost=%%b
    )

    echo Total Requests: %total_requests%
    echo Total Cost Estimate: %total_cost%
    echo.
    echo [INFO] Full data file: local_usage_tracking.json
    echo [TIP] Open this file in notepad to see detailed usage

) else (
    echo [NOT FOUND] Usage tracking file does not exist
    echo [INFO] Run 'python usage_dashboard.py' to start tracking
    echo.
)

REM Show recent log entries if they exist
if exist "api_usage_log.json" (
    echo ----------------------------------------
    echo [RECENT] API usage log:
    type api_usage_log.json
    echo.
)

REM Quick API key test
echo ----------------------------------------
echo [TEST] Testing API key status...
python test_api_key.py

echo.
echo ================================================
echo QUICK ACTIONS:
echo ================================================
echo 1. Run full dashboard: python usage_dashboard.py
echo 2. Open web monitor: start usage_monitor.html
echo 3. Check OpenAI dashboard: start https://platform.openai.com/usage
echo 4. View tracking data: notepad local_usage_tracking.json
echo.

echo Press any key to exit...
pause >nul