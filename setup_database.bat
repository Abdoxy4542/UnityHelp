@echo off
echo Setting up UnityAid PostGIS database...
echo.

REM Set PostgreSQL path
set PGPATH=C:\Program Files\PostgreSQL\15\bin

REM Add PostgreSQL to PATH temporarily
set PATH=%PGPATH%;%PATH%

echo Creating database and enabling PostGIS extension...
echo Please enter your PostgreSQL password when prompted.
echo.

REM Run the setup script
psql -U postgres -h localhost -f setup_postgis.sql

echo.
echo Database setup complete!
echo.
echo Next steps:
echo 1. Update the DB_PASSWORD in your .env file
echo 2. Run: python manage.py migrate
echo.
pause