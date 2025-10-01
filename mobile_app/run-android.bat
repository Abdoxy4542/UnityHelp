@echo off
echo Starting UnityAid Mobile App on Android Emulator...
echo.
echo Make sure your Android emulator is running!
echo.
cd /d "%~dp0"
call npm run android
pause