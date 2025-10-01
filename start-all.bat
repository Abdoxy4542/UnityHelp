@echo off
echo ========================================
echo    Starting UnityAid Platform
echo ========================================
echo.
echo Starting Django Backend Server...
start cmd /k "cd /d %~dp0 && .\venv\Scripts\activate && python manage.py runserver"

timeout /t 3 /nobreak > nul

echo Starting React Frontend...
start cmd /k "cd /d %~dp0frontend && npm start"

timeout /t 3 /nobreak > nul

echo Starting Mobile App Metro Bundler...
start cmd /k "cd /d %~dp0mobile_app && npm start"

echo.
echo ========================================
echo All services are starting...
echo.
echo Backend API:     http://localhost:8000
echo Website:         http://localhost:3000
echo Mobile App:      http://localhost:8081
echo Admin Panel:     http://localhost:8000/admin
echo ========================================
pause