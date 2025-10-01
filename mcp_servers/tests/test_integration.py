"""
Integration tests for UnityAid MCP servers
Tests the complete workflow and interaction between components
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json
from datetime import datetime, timezone

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from main import UnityAidMainMCPServer

class TestMCPIntegration:
    """Integration tests for the main MCP server"""

    def setup_method(self):
        """Set up test environment"""
        self.server = UnityAidMainMCPServer()

    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test that the server initializes properly"""
        assert self.server.sites_server is not None
        assert self.server.reports_server is not None
        assert self.server.assessments_server is not None
        assert self.server.integrations_server is not None

    @pytest.mark.asyncio
    async def test_complete_site_workflow(self):
        """Test a complete site management workflow"""
        with patch.multiple(
            'apps.sites.models.Site.objects',
            create=Mock(),
            get=Mock(),
            filter=Mock()
        ) as mocks:
            # Step 1: Create a site
            mock_site = Mock()
            mock_site.id = 1
            mock_site.name = "Test Workflow Site"
            mock_site.save = Mock()
            mocks['create'].return_value = mock_site

            create_result = await self.server.sites_server.create_site(
                name="Test Workflow Site",
                location_data={"type": "Point", "coordinates": [30.0, 15.0]},
                site_type="displacement"
            )

            assert create_result["success"] is True

            # Step 2: Get site details
            mocks['get'].return_value = mock_site

            details_result = await self.server.sites_server.get_site_details(1)

            assert details_result["success"] is True
            assert details_result["data"]["site"]["id"] == 1

            # Step 3: Update the site
            update_result = await self.server.sites_server.update_site(
                1, {"capacity": 1500}
            )

            assert update_result["success"] is True

    @pytest.mark.asyncio
    async def test_assessment_creation_and_response_workflow(self):
        """Test creating an assessment and submitting responses"""
        with patch.multiple(
            'apps.assessments.models',
            Assessment=Mock(),
            AssessmentResponse=Mock()
        ) as mocks:
            # Mock assessment
            mock_assessment = Mock()
            mock_assessment.id = 1
            mock_assessment.title = "Test Assessment"
            mock_assessment.status = "active"
            mock_assessment.save = Mock()

            # Mock Assessment.objects
            assessment_objects = Mock()
            assessment_objects.create.return_value = mock_assessment
            assessment_objects.get.return_value = mock_assessment
            mocks['Assessment'].objects = assessment_objects

            # Step 1: Create assessment
            create_result = await self.server.assessments_server.create_assessment(
                title="Test Assessment",
                assessment_type="needs",
                questions=[
                    {"question": "How many people need food assistance?", "type": "number"},
                    {"question": "What is the main source of water?", "type": "choice"}
                ]
            )

            assert create_result["success"] is True

            # Step 2: Submit response
            mock_response = Mock()
            mock_response.id = 1
            response_objects = Mock()
            response_objects.create.return_value = mock_response
            mocks['AssessmentResponse'].objects = response_objects

            response_result = await self.server.assessments_server.submit_assessment_response(
                assessment_id=1,
                responses={"question_1": 150, "question_2": "well"}
            )

            assert response_result["success"] is True

    @pytest.mark.asyncio
    async def test_report_generation_workflow(self):
        """Test creating and generating a report"""
        with patch.multiple(
            'apps.reports.models.Report.objects',
            create=Mock(),
            get=Mock()
        ) as mocks:
            # Mock report
            mock_report = Mock()
            mock_report.id = 1
            mock_report.title = "Test Report"
            mock_report.status = "draft"
            mock_report.save = Mock()
            mocks['create'].return_value = mock_report
            mocks['get'].return_value = mock_report

            # Step 1: Create report
            create_result = await self.server.reports_server.create_report(
                title="Test Report",
                report_type="summary",
                data_sources=["sites", "assessments"]
            )

            assert create_result["success"] is True

            # Step 2: Generate report
            mock_report.status = "completed"
            generate_result = await self.server.reports_server.generate_report(1)

            assert generate_result["success"] is True

    @pytest.mark.asyncio
    async def test_cross_module_data_flow(self):
        """Test data flow between different modules"""
        with patch.multiple(
            'apps.sites.models.Site.objects',
            filter=Mock()
        ), patch.multiple(
            'apps.assessments.models.Assessment.objects',
            create=Mock()
        ), patch.multiple(
            'apps.reports.models.Report.objects',
            create=Mock()
        ) as report_mocks:

            # Step 1: Get sites for assessment targeting
            mock_site = Mock()
            mock_site.id = 1
            mock_site.name = "Target Site"

            mock_queryset = Mock()
            mock_queryset.__aiter__ = AsyncMock(return_value=iter([mock_site]))
            mock_queryset.count = AsyncMock(return_value=1)

            with patch('apps.sites.models.Site.objects.filter', return_value=mock_queryset):
                sites_result = await self.server.sites_server.list_sites()

            assert sites_result["success"] is True
            target_site_id = sites_result["data"]["sites"][0]["id"]

            # Step 2: Create assessment for the site
            mock_assessment = Mock()
            mock_assessment.id = 1
            mock_assessment.save = Mock()

            with patch('apps.assessments.models.Assessment.objects.create', return_value=mock_assessment):
                assessment_result = await self.server.assessments_server.create_assessment(
                    title="Site Assessment",
                    assessment_type="needs",
                    questions=[{"question": "Population count?", "type": "number"}],
                    target_sites=[target_site_id]
                )

            assert assessment_result["success"] is True

            # Step 3: Create report combining site and assessment data
            mock_report = Mock()
            mock_report.id = 1
            mock_report.save = Mock()
            report_mocks['create'].return_value = mock_report

            report_result = await self.server.reports_server.create_report(
                title="Combined Site-Assessment Report",
                report_type="combined",
                data_sources=["sites", "assessments"]
            )

            assert report_result["success"] is True

    @pytest.mark.asyncio
    async def test_error_handling_chain(self):
        """Test error handling across multiple operations"""
        # Test cascade of errors
        with patch('apps.sites.models.Site.objects.get') as mock_get:
            from django.core.exceptions import ObjectDoesNotExist
            mock_get.side_effect = ObjectDoesNotExist

            # This should fail gracefully
            result = await self.server.sites_server.get_site_details(999)

            assert result["success"] is False
            assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_system_status_comprehensive(self):
        """Test comprehensive system status check"""
        # Mock all required components
        with patch('django.db.connection.ensure_connection'):
            result = await self.server.get_system_status()

            assert result["success"] is True
            assert "status" in result["data"]
            assert "modules" in result["data"]
            assert "timestamp" in result["data"]

    @pytest.mark.asyncio
    async def test_data_validation_across_modules(self):
        """Test data validation consistency across modules"""
        # Test that all modules handle validation consistently

        # Sites validation
        site_result = await self.server.sites_server.create_site(
            name="",  # Invalid empty name
            location_data={"invalid": "data"}
        )
        assert site_result["success"] is False

        # Assessment validation
        assessment_result = await self.server.assessments_server.create_assessment(
            title="",  # Invalid empty title
            assessment_type="invalid_type",
            questions=[]  # Invalid empty questions
        )
        assert assessment_result["success"] is False

        # Report validation
        report_result = await self.server.reports_server.create_report(
            title="",  # Invalid empty title
            report_type="invalid_type",
            data_sources=[]  # Invalid empty data sources
        )
        assert report_result["success"] is False

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test handling of concurrent operations"""
        # This would test concurrent access to the same resources
        # In a real implementation, this would involve multiple async tasks

        tasks = []
        for i in range(3):
            # Create multiple concurrent system status requests
            task = asyncio.create_task(self.server.get_system_status())
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # All should succeed
        for result in results:
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_resource_cleanup(self):
        """Test that resources are properly cleaned up"""
        # This would test database connections, file handles, etc.
        # For now, we test that the server can handle multiple operations

        operations = [
            self.server.get_system_status(),
            self.server.get_system_status(),
            self.server.get_system_status()
        ]

        results = await asyncio.gather(*operations, return_exceptions=True)

        # No exceptions should occur
        for result in results:
            assert not isinstance(result, Exception)
            if isinstance(result, dict):
                assert result["success"] is True

if __name__ == "__main__":
    pytest.main([__file__])