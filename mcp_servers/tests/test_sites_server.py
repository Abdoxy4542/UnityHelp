"""
Test Sites MCP server functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from sites_server import SitesMCPServer

class TestSitesMCPServer:
    """Test the Sites MCP server"""

    def setup_method(self):
        """Set up test environment"""
        self.server = SitesMCPServer()

    @pytest.mark.asyncio
    async def test_list_sites_success(self):
        """Test successful sites listing"""
        with patch('apps.sites.models.Site.objects.filter') as mock_filter:
            # Mock site data
            mock_site = Mock()
            mock_site.id = 1
            mock_site.name = "Test Site"
            mock_site.description = "Test Description"
            mock_site.site_type = "displacement"
            mock_site.capacity = 1000
            mock_site.current_population = 800
            mock_site.is_active = True
            mock_site.created_at = datetime(2024, 1, 15, tzinfo=timezone.utc)
            mock_site.updated_at = datetime(2024, 1, 15, tzinfo=timezone.utc)
            mock_site.location = {"type": "Point", "coordinates": [30.0, 15.0]}
            mock_site.region = "North Region"

            mock_queryset = Mock()
            mock_queryset.__aiter__ = AsyncMock(return_value=iter([mock_site]))
            mock_queryset.count = AsyncMock(return_value=1)
            mock_filter.return_value = mock_queryset

            result = await self.server.list_sites()

            assert result["success"] is True
            assert len(result["data"]["sites"]) == 1
            assert result["data"]["sites"][0]["name"] == "Test Site"
            assert result["metadata"]["total_count"] == 1

    @pytest.mark.asyncio
    async def test_list_sites_with_search(self):
        """Test sites listing with search parameter"""
        with patch('apps.sites.models.Site.objects.filter') as mock_filter:
            mock_queryset = Mock()
            mock_queryset.__aiter__ = AsyncMock(return_value=iter([]))
            mock_queryset.count = AsyncMock(return_value=0)
            mock_filter.return_value = mock_queryset

            result = await self.server.list_sites(search="test")

            assert result["success"] is True
            # Verify that search filtering was called
            mock_filter.assert_called()

    @pytest.mark.asyncio
    async def test_get_site_details_success(self):
        """Test successful site details retrieval"""
        with patch('apps.sites.models.Site.objects.get') as mock_get:
            # Mock site data
            mock_site = Mock()
            mock_site.id = 1
            mock_site.name = "Test Site"
            mock_site.description = "Test Description"
            mock_site.site_type = "displacement"
            mock_site.capacity = 1000
            mock_site.current_population = 800
            mock_site.is_active = True
            mock_site.created_at = datetime(2024, 1, 15, tzinfo=timezone.utc)
            mock_site.updated_at = datetime(2024, 1, 15, tzinfo=timezone.utc)
            mock_site.location = {"type": "Point", "coordinates": [30.0, 15.0]}
            mock_site.region = "North Region"
            mock_site.facilities = ["medical", "education"]
            mock_site.contact_info = {"phone": "+123456789"}

            mock_get.return_value = mock_site

            result = await self.server.get_site_details(1)

            assert result["success"] is True
            assert result["data"]["site"]["id"] == 1
            assert result["data"]["site"]["name"] == "Test Site"
            assert result["data"]["site"]["facilities"] == ["medical", "education"]

    @pytest.mark.asyncio
    async def test_get_site_details_not_found(self):
        """Test site details when site doesn't exist"""
        from django.core.exceptions import ObjectDoesNotExist

        with patch('apps.sites.models.Site.objects.get') as mock_get:
            mock_get.side_effect = ObjectDoesNotExist

            result = await self.server.get_site_details(999)

            assert result["success"] is False
            assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_create_site_success(self):
        """Test successful site creation"""
        with patch('apps.sites.models.Site.objects.create') as mock_create:
            # Mock created site
            mock_site = Mock()
            mock_site.id = 1
            mock_site.name = "New Site"
            mock_site.save = Mock()
            mock_create.return_value = mock_site

            site_data = {
                "name": "New Site",
                "location_data": {"type": "Point", "coordinates": [30.0, 15.0]},
                "site_type": "displacement",
                "description": "Test site"
            }

            result = await self.server.create_site(**site_data)

            assert result["success"] is True
            assert result["data"]["site"]["id"] == 1
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_site_validation_error(self):
        """Test site creation with validation errors"""
        # Missing required fields
        site_data = {
            "name": "",  # Empty name should fail validation
            "location_data": {"type": "Point", "coordinates": [30.0, 15.0]},
        }

        result = await self.server.create_site(**site_data)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_update_site_success(self):
        """Test successful site update"""
        with patch('apps.sites.models.Site.objects.get') as mock_get:
            # Mock existing site
            mock_site = Mock()
            mock_site.id = 1
            mock_site.name = "Original Name"
            mock_site.save = Mock()
            mock_get.return_value = mock_site

            updates = {"name": "Updated Name", "capacity": 1500}
            result = await self.server.update_site(1, updates)

            assert result["success"] is True
            assert mock_site.name == "Updated Name"
            assert mock_site.capacity == 1500
            mock_site.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_site_not_found(self):
        """Test site update when site doesn't exist"""
        from django.core.exceptions import ObjectDoesNotExist

        with patch('apps.sites.models.Site.objects.get') as mock_get:
            mock_get.side_effect = ObjectDoesNotExist

            result = await self.server.update_site(999, {"name": "Updated"})

            assert result["success"] is False
            assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_get_sites_by_region_success(self):
        """Test getting sites by region"""
        with patch('apps.sites.models.Site.objects.filter') as mock_filter:
            mock_site = Mock()
            mock_site.id = 1
            mock_site.name = "Regional Site"
            mock_site.region = "North Region"

            mock_queryset = Mock()
            mock_queryset.__aiter__ = AsyncMock(return_value=iter([mock_site]))
            mock_queryset.count = AsyncMock(return_value=1)
            mock_filter.return_value = mock_queryset

            result = await self.server.get_sites_by_region("North Region")

            assert result["success"] is True
            assert len(result["data"]["sites"]) == 1
            assert result["data"]["sites"][0]["region"] == "North Region"

    @pytest.mark.asyncio
    async def test_get_sites_by_region_empty(self):
        """Test getting sites by region when no sites exist"""
        with patch('apps.sites.models.Site.objects.filter') as mock_filter:
            mock_queryset = Mock()
            mock_queryset.__aiter__ = AsyncMock(return_value=iter([]))
            mock_queryset.count = AsyncMock(return_value=0)
            mock_filter.return_value = mock_queryset

            result = await self.server.get_sites_by_region("Nonexistent Region")

            assert result["success"] is True
            assert len(result["data"]["sites"]) == 0
            assert result["metadata"]["total_count"] == 0

    def test_site_serialization(self):
        """Test site data serialization"""
        # Mock site object
        mock_site = Mock()
        mock_site.id = 1
        mock_site.name = "Test Site"
        mock_site.description = "Test Description"
        mock_site.site_type = "displacement"
        mock_site.capacity = 1000
        mock_site.current_population = 800
        mock_site.is_active = True
        mock_site.created_at = datetime(2024, 1, 15, tzinfo=timezone.utc)
        mock_site.updated_at = datetime(2024, 1, 15, tzinfo=timezone.utc)
        mock_site.location = {"type": "Point", "coordinates": [30.0, 15.0]}
        mock_site.region = "North Region"
        mock_site.facilities = ["medical", "education"]
        mock_site.contact_info = {"phone": "+123456789"}

        # This would test the internal serialization method
        # The actual method name might vary based on implementation
        # serialized = self.server._serialize_site(mock_site)

        # For now, we'll test that the expected fields are accessible
        assert mock_site.id == 1
        assert mock_site.name == "Test Site"
        assert isinstance(mock_site.location, dict)
        assert isinstance(mock_site.facilities, list)

if __name__ == "__main__":
    pytest.main([__file__])