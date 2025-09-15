-- Setup script for UnityAid PostGIS database
-- Run this as the postgres superuser

-- Create the database
CREATE DATABASE unityaid_db;

-- Connect to the database
\c unityaid_db;

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Enable PostGIS topology extension (optional)
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Enable PostGIS raster extension (optional)
CREATE EXTENSION IF NOT EXISTS postgis_raster;

-- Enable fuzzystrmatch for fuzzy string matching
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;

-- Enable address standardizer (optional, for geocoding)
-- CREATE EXTENSION IF NOT EXISTS address_standardizer;

-- Verify PostGIS installation
SELECT PostGIS_Version();

-- Grant privileges to the postgres user (or create a dedicated user)
-- If you want to create a dedicated user:
-- CREATE USER unityaid_user WITH PASSWORD 'secure_password';
-- GRANT ALL PRIVILEGES ON DATABASE unityaid_db TO unityaid_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO unityaid_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO unityaid_user;

-- Show installed extensions
SELECT name, default_version, installed_version 
FROM pg_available_extensions 
WHERE name LIKE '%postgis%' OR name = 'fuzzystrmatch';