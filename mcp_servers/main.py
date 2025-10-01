"""
Main MCP Server for UnityAid Platform
Aggregates all app-specific MCP servers into a single unified server
"""

import asyncio
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

try:
    from .base import UnityAidMCPBase
    from .sites_server import SitesMCPServer
    from .reports_server import ReportsMCPServer
    from .assessments_server import AssessmentsMCPServer
    from .integrations_server import IntegrationsMCPServer
except ImportError:
    from base import UnityAidMCPBase
    from sites_server import SitesMCPServer
    from reports_server import ReportsMCPServer
    from assessments_server import AssessmentsMCPServer
    from integrations_server import IntegrationsMCPServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnityAidMainMCPServer(UnityAidMCPBase):
    """Main MCP server that orchestrates all UnityAid functionality"""

    def __init__(self):
        super().__init__()
        self.sites_server = SitesMCPServer()
        self.reports_server = ReportsMCPServer()
        self.assessments_server = AssessmentsMCPServer()
        self.integrations_server = IntegrationsMCPServer()

    async def setup_server(self):
        """Setup the unified MCP server with all tools"""

        # Server information
        @self.mcp.list_resources()
        async def handle_list_resources() -> list[types.Resource]:
            """List all available resources across all modules"""
            resources = []

            # Add resource descriptions for each module
            resources.extend([
                types.Resource(
                    uri="unityaid://sites",
                    name="Site Management",
                    description="Manage humanitarian sites, locations, and geographic data",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="unityaid://reports",
                    name="Report Generation",
                    description="Generate, manage, and export humanitarian reports",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="unityaid://assessments",
                    name="Assessment Management",
                    description="Create, manage, and analyze humanitarian assessments",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="unityaid://integrations",
                    name="External Integrations",
                    description="Manage integrations with HDX, KoboToolbox, and other platforms",
                    mimeType="application/json"
                )
            ])

            return resources

        # Sites tools
        @self.mcp.tool()
        async def list_sites(
            active_only: bool = True,
            limit: int = 20,
            search: str = None
        ) -> dict[str, Any]:
            """List all humanitarian sites"""
            return await self.sites_server.list_sites(active_only, limit, search)

        @self.mcp.tool()
        async def get_site_details(site_id: int) -> dict[str, Any]:
            """Get detailed information about a specific site"""
            return await self.sites_server.get_site_details(site_id)

        @self.mcp.tool()
        async def create_site(
            name: str,
            location_data: dict,
            site_type: str = "displacement",
            description: str = None
        ) -> dict[str, Any]:
            """Create a new humanitarian site"""
            return await self.sites_server.create_site(name, location_data, site_type, description)

        @self.mcp.tool()
        async def update_site(
            site_id: int,
            updates: dict
        ) -> dict[str, Any]:
            """Update an existing site"""
            return await self.sites_server.update_site(site_id, updates)

        @self.mcp.tool()
        async def get_sites_by_region(region: str) -> dict[str, Any]:
            """Get all sites in a specific region"""
            return await self.sites_server.get_sites_by_region(region)

        # Reports tools
        @self.mcp.tool()
        async def list_reports(
            report_type: str = None,
            status: str = None,
            limit: int = 20
        ) -> dict[str, Any]:
            """List all reports with optional filtering"""
            return await self.reports_server.list_reports(report_type, status, limit)

        @self.mcp.tool()
        async def get_report_details(report_id: int) -> dict[str, Any]:
            """Get detailed information about a specific report"""
            return await self.reports_server.get_report_details(report_id)

        @self.mcp.tool()
        async def create_report(
            title: str,
            report_type: str,
            data_sources: list,
            parameters: dict = None
        ) -> dict[str, Any]:
            """Create a new report"""
            return await self.reports_server.create_report(title, report_type, data_sources, parameters)

        @self.mcp.tool()
        async def generate_report(report_id: int) -> dict[str, Any]:
            """Generate/compile a report"""
            return await self.reports_server.generate_report(report_id)

        @self.mcp.tool()
        async def export_report(
            report_id: int,
            format: str = "pdf"
        ) -> dict[str, Any]:
            """Export a report in the specified format"""
            return await self.reports_server.export_report(report_id, format)

        @self.mcp.tool()
        async def get_report_analytics(
            date_range: dict = None,
            report_types: list = None
        ) -> dict[str, Any]:
            """Get analytics about report generation and usage"""
            return await self.reports_server.get_report_analytics(date_range, report_types)

        # Assessments tools
        @self.mcp.tool()
        async def list_assessments(
            status: str = None,
            assessment_type: str = None,
            limit: int = 20
        ) -> dict[str, Any]:
            """List all assessments with optional filtering"""
            return await self.assessments_server.list_assessments(status, assessment_type, limit)

        @self.mcp.tool()
        async def get_assessment_details(assessment_id: int) -> dict[str, Any]:
            """Get detailed information about a specific assessment"""
            return await self.assessments_server.get_assessment_details(assessment_id)

        @self.mcp.tool()
        async def create_assessment(
            title: str,
            assessment_type: str,
            questions: list,
            target_sites: list = None
        ) -> dict[str, Any]:
            """Create a new assessment"""
            return await self.assessments_server.create_assessment(title, assessment_type, questions, target_sites)

        @self.mcp.tool()
        async def update_assessment(
            assessment_id: int,
            updates: dict
        ) -> dict[str, Any]:
            """Update an existing assessment"""
            return await self.assessments_server.update_assessment(assessment_id, updates)

        @self.mcp.tool()
        async def submit_assessment_response(
            assessment_id: int,
            responses: dict,
            respondent_info: dict = None
        ) -> dict[str, Any]:
            """Submit responses to an assessment"""
            return await self.assessments_server.submit_assessment_response(assessment_id, responses, respondent_info)

        @self.mcp.tool()
        async def get_assessment_analytics(
            assessment_id: int,
            include_responses: bool = True
        ) -> dict[str, Any]:
            """Get analytics and response data for an assessment"""
            return await self.assessments_server.get_assessment_analytics(assessment_id, include_responses)

        # Integrations tools
        @self.mcp.tool()
        async def list_integrations(
            platform: str = None,
            status: str = None
        ) -> dict[str, Any]:
            """List all external integrations"""
            return await self.integrations_server.list_integrations(platform, status)

        @self.mcp.tool()
        async def get_integration_status(integration_id: int) -> dict[str, Any]:
            """Get the status of a specific integration"""
            return await self.integrations_server.get_integration_status(integration_id)

        @self.mcp.tool()
        async def sync_with_hdx(
            dataset_id: str = None,
            full_sync: bool = False
        ) -> dict[str, Any]:
            """Synchronize data with Humanitarian Data Exchange (HDX)"""
            return await self.integrations_server.sync_with_hdx(dataset_id, full_sync)

        @self.mcp.tool()
        async def sync_with_kobo(
            form_id: str = None,
            last_sync_date: str = None
        ) -> dict[str, Any]:
            """Synchronize data with KoboToolbox"""
            return await self.integrations_server.sync_with_kobo(form_id, last_sync_date)

        @self.mcp.tool()
        async def export_to_hdx(
            dataset_config: dict,
            data_source: str
        ) -> dict[str, Any]:
            """Export data to HDX platform"""
            return await self.integrations_server.export_to_hdx(dataset_config, data_source)

        @self.mcp.tool()
        async def configure_integration(
            platform: str,
            config: dict
        ) -> dict[str, Any]:
            """Configure a new external integration"""
            return await self.integrations_server.configure_integration(platform, config)

        @self.mcp.tool()
        async def test_integration(integration_id: int) -> dict[str, Any]:
            """Test the connection and functionality of an integration"""
            return await self.integrations_server.test_integration(integration_id)

        # Utility tools
        @self.mcp.tool()
        async def get_system_status() -> dict[str, Any]:
            """Get overall system status and health metrics"""
            try:
                status = {
                    "status": "healthy",
                    "timestamp": self.format_timestamp(),
                    "modules": {
                        "sites": "active",
                        "reports": "active",
                        "assessments": "active",
                        "integrations": "active"
                    },
                    "database": "connected",
                    "version": "1.0.0"
                }
                return {"success": True, "data": status}
            except Exception as e:
                return {"success": False, "error": str(e)}

        logger.info("UnityAid MCP Server setup complete")

async def main():
    """Main entry point for the MCP server"""
    server = UnityAidMainMCPServer()
    await server.setup_server()

    # Run the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.mcp.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="unityaid-mcp",
                server_version="1.0.0",
                capabilities=server.mcp.get_capabilities()
            )
        )

if __name__ == "__main__":
    asyncio.run(main())