"""
Base MCP server for UnityAid Platform
Provides common functionality, authentication, and utilities
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Configure logging
logger = logging.getLogger(__name__)

class UnityAidMCPBase:
    """Base class for UnityAid MCP servers"""

    def __init__(self):
        self.name = "UnityAid MCP Server"
        logger.info("UnityAid MCP Base initialized")

    def format_timestamp(self, dt: datetime = None) -> str:
        """Format datetime to ISO 8601 string"""
        if dt is None:
            dt = datetime.now(timezone.utc)
        return dt.isoformat().replace('+00:00', 'Z')

    async def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate a user"""
        try:
            # For demo purposes, we'll simulate authentication
            # In real implementation, this would use Django's auth system
            if username and password:
                return {
                    "success": True,
                    "user": {
                        "id": 1,
                        "username": username,
                        "email": f"{username}@example.com"
                    }
                }
            else:
                return {"success": False, "error": "Invalid credentials"}
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return {"success": False, "error": str(e)}

    async def get_user_by_id(self, user_id: int) -> Dict[str, Any]:
        """Get user information by ID"""
        try:
            # Simulate user lookup
            return {
                "success": True,
                "user": {
                    "id": user_id,
                    "username": f"user{user_id}",
                    "email": f"user{user_id}@example.com"
                }
            }
        except Exception as e:
            logger.error(f"User lookup error: {e}")
            return {"success": False, "error": "User not found"}

    def validate_required_fields(self, data: Dict[str, Any], required: List[str]) -> bool:
        """Validate that required fields are present and not empty"""
        missing = []
        for field in required:
            if field not in data or not data[field]:
                missing.append(field)

        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        return True

    def format_error_response(self, error: str, error_code: str = None, details: Dict = None) -> Dict[str, Any]:
        """Format a standardized error response"""
        response = {
            "success": False,
            "error": error,
            "timestamp": self.format_timestamp()
        }

        if error_code:
            response["error_code"] = error_code

        if details:
            response["details"] = details

        return response

    def format_success_response(self, data: Any, metadata: Dict = None) -> Dict[str, Any]:
        """Format a standardized success response"""
        response = {
            "success": True,
            "data": data,
            "metadata": metadata or {}
        }

        if "timestamp" not in response["metadata"]:
            response["metadata"]["timestamp"] = self.format_timestamp()

        return response

    def parse_date_string(self, date_str: str) -> datetime:
        """Parse date string to datetime object"""
        if not date_str:
            raise ValueError("Date string cannot be empty")

        try:
            # Try ISO format first
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                # Try date only format
                return datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        except Exception as e:
            raise ValueError(f"Invalid date format: {date_str}") from e

    def clean_data(self, data: Any) -> Any:
        """Clean data by removing empty strings, None values, and stripping whitespace"""
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                cleaned_value = self.clean_data(value)
                if cleaned_value is not None and cleaned_value != "":
                    cleaned[key] = cleaned_value
            return cleaned
        elif isinstance(data, list):
            return [self.clean_data(item) for item in data if self.clean_data(item) is not None and self.clean_data(item) != ""]
        elif isinstance(data, str):
            return data.strip()
        else:
            return data