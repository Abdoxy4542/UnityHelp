#!/usr/bin/env python3
"""
Startup script for UnityAid MCP Server
"""

import asyncio
import logging
import logging.config
import sys
import os
from pathlib import Path

# Add the Django project to the path
BASE_DIR = Path(__file__).resolve().parent
DJANGO_DIR = BASE_DIR.parent
sys.path.append(str(DJANGO_DIR))

try:
    from .config import get_django_settings, validate_config, LOGGING_CONFIG
    from .main import main
except ImportError:
    from config import get_django_settings, validate_config, LOGGING_CONFIG
    from main import main

def setup_logging():
    """Setup logging configuration"""
    try:
        logging.config.dictConfig(LOGGING_CONFIG)
    except:
        # Fallback to basic logging if config fails
        logging.basicConfig(level=logging.INFO)
    return logging.getLogger('mcp_server')

def check_dependencies():
    """Check if all required dependencies are available"""
    try:
        import mcp
        import django
        import psycopg2
        import httpx
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False

def initialize_django():
    """Initialize Django settings and database connection"""
    try:
        settings = get_django_settings()

        # Test database connection
        from django.db import connection
        connection.ensure_connection()

        return True
    except Exception as e:
        print(f"Django initialization failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting UnityAid MCP Server...")

    # Setup logging
    logger = setup_logging()
    logger.info("UnityAid MCP Server starting up")

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Validate configuration
    try:
        validate_config()
        logger.info("Configuration validation passed")
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        sys.exit(1)

    # Initialize Django
    if not initialize_django():
        logger.error("Failed to initialize Django")
        sys.exit(1)

    logger.info("All checks passed, starting MCP server")

    try:
        # Run the main server
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)