"""
Test base MCP server functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from base import UnityAidMCPBase

class TestUnityAidMCPBase:
    """Test the base MCP server class"""

    def setup_method(self):
        """Set up test environment"""
        self.server = UnityAidMCPBase()

    def test_format_timestamp(self):
        """Test timestamp formatting"""
        # Test with specific datetime
        test_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.utc)
        formatted = self.server.format_timestamp(test_time)
        assert formatted == "2024-01-15T14:30:00Z"

        # Test with current time (should not raise error)
        current_formatted = self.server.format_timestamp()
        assert isinstance(current_formatted, str)
        assert current_formatted.endswith("Z")

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self):
        """Test successful user authentication"""
        with patch('django.contrib.auth.authenticate') as mock_auth:
            # Mock successful authentication
            mock_user = Mock()
            mock_user.is_active = True
            mock_user.id = 1
            mock_user.username = "testuser"
            mock_auth.return_value = mock_user

            result = await self.server.authenticate_user("testuser", "password")

            assert result["success"] is True
            assert result["user"]["id"] == 1
            assert result["user"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_authenticate_user_failure(self):
        """Test failed user authentication"""
        with patch('django.contrib.auth.authenticate') as mock_auth:
            # Mock failed authentication
            mock_auth.return_value = None

            result = await self.server.authenticate_user("testuser", "wrongpassword")

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self):
        """Test getting user by ID"""
        with patch('apps.accounts.models.User.objects.get') as mock_get:
            # Mock successful user lookup
            mock_user = Mock()
            mock_user.id = 1
            mock_user.username = "testuser"
            mock_user.email = "test@example.com"
            mock_get.return_value = mock_user

            result = await self.server.get_user_by_id(1)

            assert result["success"] is True
            assert result["user"]["id"] == 1
            assert result["user"]["username"] == "testuser"
            assert result["user"]["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self):
        """Test getting user by ID when user doesn't exist"""
        from django.contrib.auth.models import User

        with patch('apps.accounts.models.User.objects.get') as mock_get:
            # Mock user not found
            mock_get.side_effect = User.DoesNotExist

            result = await self.server.get_user_by_id(999)

            assert result["success"] is False
            assert "error" in result

    def test_validate_required_fields_success(self):
        """Test successful field validation"""
        data = {"name": "Test Site", "location": {"lat": 10.0, "lon": 20.0}}
        required = ["name", "location"]

        result = self.server.validate_required_fields(data, required)
        assert result is True

    def test_validate_required_fields_missing(self):
        """Test field validation with missing fields"""
        data = {"name": "Test Site"}
        required = ["name", "location"]

        with pytest.raises(ValueError, match="Missing required fields"):
            self.server.validate_required_fields(data, required)

    def test_validate_required_fields_empty_value(self):
        """Test field validation with empty values"""
        data = {"name": "", "location": {"lat": 10.0, "lon": 20.0}}
        required = ["name", "location"]

        with pytest.raises(ValueError, match="Missing required fields"):
            self.server.validate_required_fields(data, required)

    def test_format_error_response(self):
        """Test error response formatting"""
        error_msg = "Test error message"
        error_code = "TEST_ERROR"
        details = {"field": "value"}

        result = self.server.format_error_response(error_msg, error_code, details)

        assert result["success"] is False
        assert result["error"] == error_msg
        assert result["error_code"] == error_code
        assert result["details"] == details
        assert "timestamp" in result

    def test_format_success_response(self):
        """Test success response formatting"""
        data = {"id": 1, "name": "Test"}
        metadata = {"count": 1}

        result = self.server.format_success_response(data, metadata)

        assert result["success"] is True
        assert result["data"] == data
        assert result["metadata"] == metadata
        assert "timestamp" in result["metadata"]

    def test_parse_date_string_valid(self):
        """Test parsing valid date strings"""
        # Test ISO format
        date_str = "2024-01-15T14:30:00Z"
        result = self.server.parse_date_string(date_str)
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

        # Test date only
        date_str = "2024-01-15"
        result = self.server.parse_date_string(date_str)
        assert result is not None
        assert result.year == 2024

    def test_parse_date_string_invalid(self):
        """Test parsing invalid date strings"""
        with pytest.raises(ValueError):
            self.server.parse_date_string("invalid-date")

        with pytest.raises(ValueError):
            self.server.parse_date_string("")

    def test_clean_data_basic(self):
        """Test basic data cleaning"""
        data = {
            "name": "  Test Site  ",
            "description": "",
            "active": True,
            "null_field": None
        }

        cleaned = self.server.clean_data(data)

        assert cleaned["name"] == "Test Site"
        assert "description" not in cleaned  # Empty strings removed
        assert cleaned["active"] is True
        assert "null_field" not in cleaned  # None values removed

    def test_clean_data_nested(self):
        """Test cleaning nested data structures"""
        data = {
            "site": {
                "name": "  Test Site  ",
                "location": {
                    "lat": 10.0,
                    "lon": "",
                    "address": "  123 Main St  "
                }
            },
            "tags": ["  tag1  ", "", "tag2"]
        }

        cleaned = self.server.clean_data(data)

        assert cleaned["site"]["name"] == "Test Site"
        assert cleaned["site"]["location"]["address"] == "123 Main St"
        assert "lon" not in cleaned["site"]["location"]  # Empty string removed
        assert cleaned["tags"] == ["tag1", "tag2"]  # Empty string removed from list

if __name__ == "__main__":
    pytest.main([__file__])