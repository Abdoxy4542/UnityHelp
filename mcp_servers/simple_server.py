#!/usr/bin/env python3
"""
Simple MCP Server for UnityAid Platform - Demo Version
This is a simplified version that demonstrates the MCP server functionality
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict

# Basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnityAidDemoServer:
    """Demo MCP server for UnityAid"""

    def __init__(self):
        self.name = "UnityAid Demo MCP Server"
        self.version = "1.0.0"
        logger.info(f"{self.name} v{self.version} initialized")

    def format_timestamp(self, dt: datetime = None) -> str:
        """Format datetime to ISO 8601 string"""
        if dt is None:
            dt = datetime.now(timezone.utc)
        return dt.isoformat().replace('+00:00', 'Z')

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

    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        status = {
            "status": "healthy",
            "timestamp": self.format_timestamp(),
            "server": {
                "name": self.name,
                "version": self.version
            },
            "modules": {
                "sites": "active",
                "reports": "active",
                "assessments": "active",
                "integrations": "active"
            },
            "demo_mode": True
        }
        return self.format_success_response(status)

    async def list_sites(self) -> Dict[str, Any]:
        """List demo sites - Sudan focused"""
        sites = [
            {
                "id": 1,
                "name": "Nyala IDP Settlement",
                "location": {"type": "Point", "coordinates": [24.8816, 14.3616]},
                "site_type": "displacement",
                "capacity": 8000,
                "current_population": 7200,
                "is_active": True,
                "facilities": ["medical", "education", "water", "food_distribution"],
                "state": "South Darfur",
                "country": "Sudan",
                "last_updated": self.format_timestamp()
            },
            {
                "id": 2,
                "name": "El Geneina Emergency Camp",
                "location": {"type": "Point", "coordinates": [22.4453, 13.4527]},
                "site_type": "emergency",
                "capacity": 6000,
                "current_population": 5800,
                "is_active": True,
                "facilities": ["medical", "protection", "wash"],
                "state": "West Darfur",
                "country": "Sudan",
                "last_updated": self.format_timestamp()
            },
            {
                "id": 3,
                "name": "Kassala Reception Center",
                "location": {"type": "Point", "coordinates": [36.4000, 15.4667]},
                "site_type": "reception",
                "capacity": 3000,
                "current_population": 2100,
                "is_active": True,
                "facilities": ["registration", "food_distribution", "health"],
                "state": "Kassala",
                "country": "Sudan",
                "last_updated": self.format_timestamp()
            }
        ]

        return self.format_success_response({
            "sites": sites
        }, {
            "total_count": len(sites),
            "active_count": len([s for s in sites if s["is_active"]])
        })

    async def list_reports(self) -> Dict[str, Any]:
        """List demo reports"""
        reports = [
            {
                "id": 1,
                "title": "Weekly Displacement Summary",
                "report_type": "summary",
                "status": "completed",
                "data_sources": ["sites", "assessments"],
                "created_at": self.format_timestamp(),
                "summary": "3 active sites with 6,800 total population"
            },
            {
                "id": 2,
                "title": "Monthly Needs Assessment",
                "report_type": "needs_assessment",
                "status": "completed",
                "data_sources": ["assessments", "surveys"],
                "created_at": self.format_timestamp(),
                "summary": "Food assistance needed for 75% of population"
            },
            {
                "id": 3,
                "title": "Resource Allocation Analysis",
                "report_type": "analytics",
                "status": "in_progress",
                "data_sources": ["sites", "resources"],
                "created_at": self.format_timestamp(),
                "summary": "Analyzing resource distribution efficiency"
            }
        ]

        return self.format_success_response({
            "reports": reports
        }, {
            "total_count": len(reports),
            "completed_count": len([r for r in reports if r["status"] == "completed"])
        })

    async def list_assessments(self) -> Dict[str, Any]:
        """List demo assessments - Sudan focused"""
        assessments = [
            {
                "id": 1,
                "title": "Emergency Needs Assessment - Darfur Region, Sudan",
                "assessment_type": "needs",
                "status": "active",
                "response_count": 1247,
                "target_population": 25000,
                "country": "Sudan",
                "regions": ["West Darfur", "South Darfur", "North Darfur"],
                "questions": [
                    "How many people in your household need food assistance?",
                    "What is your primary source of water?",
                    "Do you have adequate shelter?",
                    "Have you been displaced due to conflict?"
                ],
                "created_at": self.format_timestamp()
            },
            {
                "id": 2,
                "title": "Sudan Healthcare Access Survey - Conflict Affected Areas",
                "assessment_type": "health",
                "status": "completed",
                "response_count": 2340,
                "target_population": 50000,
                "country": "Sudan",
                "regions": ["Darfur States", "Blue Nile", "South Kordofan"],
                "questions": [
                    "How far is the nearest functional healthcare facility?",
                    "Have you accessed medical care since the conflict began?",
                    "What health issues are most common in your community?",
                    "Do you have access to essential medicines?"
                ],
                "created_at": self.format_timestamp(),
                "completion_rate": 0.87
            }
        ]

        return self.format_success_response({
            "assessments": assessments
        }, {
            "total_count": len(assessments),
            "active_count": len([a for a in assessments if a["status"] == "active"])
        })

    async def list_integrations(self) -> Dict[str, Any]:
        """List comprehensive humanitarian platform integrations"""
        integrations = [
            {
                "id": 1,
                "platform": "hdx",
                "name": "Humanitarian Data Exchange",
                "status": "active",
                "last_sync": self.format_timestamp(),
                "sync_count": 1247,
                "datasets": 45,
                "description": "OCHA's primary data sharing platform - 45 datasets synced"
            },
            {
                "id": 2,
                "platform": "hrp",
                "name": "Humanitarian Response Plans",
                "status": "active",
                "last_sync": self.format_timestamp(),
                "sync_count": 89,
                "funding_gap": "USD 2.18B",
                "description": "OCHA coordination platform - tracking $4.07B in funding requirements"
            },
            {
                "id": 3,
                "platform": "dtm",
                "name": "Displacement Tracking Matrix",
                "status": "active",
                "last_sync": self.format_timestamp(),
                "sync_count": 456,
                "individuals_tracked": 2456789,
                "description": "IOM displacement monitoring - 2.46M individuals tracked across 234 locations"
            },
            {
                "id": 4,
                "platform": "kobo",
                "name": "KoboToolbox",
                "status": "active",
                "last_sync": self.format_timestamp(),
                "sync_count": 2341,
                "active_forms": 18,
                "description": "Data collection platform - 18 active forms, 15.6K submissions"
            },
            {
                "id": 5,
                "platform": "unhcr",
                "name": "UNHCR Global Focus",
                "status": "configured",
                "last_sync": None,
                "sync_count": 0,
                "description": "UNHCR operational data - ready for population and protection data sync"
            },
            {
                "id": 6,
                "platform": "fts",
                "name": "Financial Tracking Service",
                "status": "active",
                "last_sync": self.format_timestamp(),
                "sync_count": 156,
                "funding_tracked": "USD 1.2B",
                "description": "OCHA funding tracker - monitoring $1.2B across 8 humanitarian appeals"
            },
            {
                "id": 7,
                "platform": "acaps",
                "name": "ACAPS Crisis Analysis",
                "status": "active",
                "last_sync": self.format_timestamp(),
                "sync_count": 78,
                "analysis_products": 45,
                "description": "Crisis analysis platform - 45 analysis products for Syria crisis"
            }
        ]

        return self.format_success_response({
            "integrations": integrations
        }, {
            "total_count": len(integrations),
            "active_count": len([i for i in integrations if i["status"] == "active"]),
            "platforms": ["HDX", "HRP", "DTM", "KoboToolbox", "UNHCR", "FTS", "ACAPS"]
        })

    async def run_demo(self):
        """Run a demo of all server functions"""
        print(f"\n[LAUNCH] {self.name} v{self.version}")
        print("=" * 60)

        # System Status
        print("\n[STATUS] System Status:")
        status = await self.get_system_status()
        print(json.dumps(status, indent=2))

        # Sites
        print("\n[SITES] Sites:")
        sites = await self.list_sites()
        print(f"Found {sites['metadata']['total_count']} sites:")
        for site in sites['data']['sites']:
            print(f"  - {site['name']} ({site['current_population']}/{site['capacity']} people)")

        # Reports
        print("\n[REPORTS] Reports:")
        reports = await self.list_reports()
        print(f"Found {reports['metadata']['total_count']} reports:")
        for report in reports['data']['reports']:
            print(f"  - {report['title']} [{report['status']}]")

        # Assessments
        print("\n[ASSESSMENTS] Assessments:")
        assessments = await self.list_assessments()
        print(f"Found {assessments['metadata']['total_count']} assessments:")
        for assessment in assessments['data']['assessments']:
            print(f"  - {assessment['title']} ({assessment['response_count']} responses)")

        # Integrations
        print("\n[INTEGRATIONS] External Integrations:")
        integrations = await self.list_integrations()
        print(f"Found {integrations['metadata']['total_count']} integrations:")
        for integration in integrations['data']['integrations']:
            print(f"  - {integration['name']} [{integration['status']}]")

        print(f"\n[SUCCESS] Demo completed successfully!")
        print(f"[TIME] Timestamp: {self.format_timestamp()}")
        print("=" * 60)

async def main():
    """Main entry point"""
    server = UnityAidDemoServer()
    await server.run_demo()

if __name__ == "__main__":
    asyncio.run(main())