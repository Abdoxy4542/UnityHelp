"""
Protection Cluster Agent - UNHCR Lead
Specialized LangChain agent for Protection humanitarian sector in Sudan
"""

from typing import Any, Dict, List, Union
from langchain.tools import Tool
from .base_humanitarian_agent import BaseHumanitarianAgent, HumanitarianRequest, create_base_tools

class ProtectionAgent(BaseHumanitarianAgent):
    """Protection Cluster agent for Sudan operations"""

    def __init__(self, llm=None):
        super().__init__("Protection", "UNHCR", llm)

    def get_sector_specific_context(self) -> Dict[str, Any]:
        """Get Protection sector context for Sudan"""
        return {
            "sector": "Protection",
            "lead_agency": "UNHCR",
            "areas_of_responsibility": [
                "Child Protection (UNICEF)",
                "Gender-Based Violence (UNFPA)",
                "Housing, Land and Property (NRC)",
                "Mine Action (UNMAS)"
            ],
            "sudan_protection_concerns": [
                "Civilian casualties from conflict",
                "Sexual and gender-based violence",
                "Child recruitment and use",
                "Forced displacement",
                "Arbitrary detention",
                "Access to civil documentation",
                "Housing, land and property rights"
            ],
            "vulnerable_groups": [
                "Unaccompanied and separated children",
                "Women and girls at risk",
                "Elderly persons",
                "Persons with disabilities",
                "Ethnic minorities"
            ],
            "sudan_statistics": {
                "people_in_need": 12100000,
                "people_targeted": 4500000,
                "funding_required": "USD 234M",
                "funding_received": "USD 85M",
                "gap": "USD 149M"
            }
        }

    def _initialize_tools(self) -> List[Tool]:
        """Initialize Protection-specific tools"""
        base_tools = create_base_tools()

        def assess_protection_risks(location: str) -> str:
            """Assess protection risks in Sudan location"""
            risk_data = {
                "darfur": "Critical - widespread GBV, child recruitment, civilian targeting",
                "khartoum": "High - urban violence, arbitrary detention, displacement",
                "blue_nile": "Medium - limited services, documentation issues",
                "kassala": "Medium - refugee protection concerns, host community tensions"
            }

            location_lower = location.lower()
            for area, risk in risk_data.items():
                if area in location_lower:
                    return f"Protection risks in {area}: {risk}"

            return "Protection risk assessment not available for specified location"

        def get_child_protection_data(location: str) -> str:
            """Get child protection data for Sudan"""
            return f"""Child Protection Data for Sudan:
            - Children in need: 13.3 million
            - Unaccompanied children: ~50,000 estimated
            - Children at risk of recruitment: High in conflict areas
            - School attacks: Documented in Darfur states
            - Main concerns: Family separation, psychosocial trauma, education disruption"""

        def get_gbv_services(location: str) -> str:
            """Get GBV services availability"""
            services = {
                "darfur": "Limited - mobile teams, safe spaces in camps",
                "khartoum": "Moderate - urban centers have services",
                "kassala": "Basic - refugee camps have women's centers",
                "blue_nile": "Very limited - referral to main centers"
            }

            location_lower = location.lower()
            for area, service in services.items():
                if area in location_lower:
                    return f"GBV services in {area}: {service}"

            return "GBV service information not available"

        protection_tools = [
            Tool(
                name="assess_protection_risks",
                func=assess_protection_risks,
                description="Assess protection risks in Sudan locations"
            ),
            Tool(
                name="get_child_protection_data",
                func=get_child_protection_data,
                description="Get child protection statistics for Sudan"
            ),
            Tool(
                name="get_gbv_services",
                func=get_gbv_services,
                description="Get information about GBV services availability"
            )
        ]

        return base_tools + protection_tools

    async def _mock_response(self, request: Union[str, HumanitarianRequest]) -> str:
        """Generate mock Protection response"""
        if isinstance(request, str):
            if "child" in request.lower():
                return """Protection Response - Child Protection:

                IMMEDIATE ACTIONS:
                - Establish child-friendly spaces in displacement sites
                - Deploy child protection specialists to assess separated children
                - Set up family tracing and reunification services

                RESOURCES NEEDED:
                - Child protection officers (5 teams)
                - Recreational kits and supplies
                - Mobile child-friendly space kits

                COORDINATION:
                - Link with Education cluster for school-based protection
                - Coordinate with Health cluster for psychosocial support

                TIMELINE: Emergency response within 72 hours"""

            elif "gbv" in request.lower() or "gender" in request.lower():
                return """Protection Response - Gender-Based Violence:

                IMMEDIATE ACTIONS:
                - Deploy GBV mobile teams to affected areas
                - Establish women's safe spaces
                - Provide clinical management of rape services

                RESOURCES NEEDED:
                - GBV specialists (3 teams)
                - Dignity kits for women and girls
                - Safe space establishment materials

                COORDINATION:
                - Link with Health cluster for medical support
                - Coordinate with WASH for gender-sensitive facilities

                TIMELINE: Services operational within 48 hours"""

        return f"""Protection Cluster Response for Sudan:

        ASSESSMENT: {request}

        PROTECTION PRIORITIES:
        1. Civilian protection and safety
        2. Prevention of family separation
        3. GBV prevention and response
        4. Child protection services

        IMMEDIATE ACTIONS:
        - Deploy protection monitoring teams
        - Establish protection services in displacement sites
        - Conduct rapid protection assessments

        COORDINATION NEEDS:
        - Multi-sector coordination for holistic protection
        - Government engagement on protection issues

        LEAD AGENCY: UNHCR coordination"""

    async def _conduct_needs_assessment(self, location: str, population: int) -> Dict[str, Any]:
        """Conduct Protection needs assessment"""
        return {
            "protection_concerns": [
                "Risk of GBV",
                "Child protection issues",
                "Documentation needs",
                "Legal assistance requirements"
            ],
            "vulnerable_population": int(population * 0.4),  # 40% vulnerable
            "services_needed": [
                "Legal aid",
                "Psychosocial support",
                "Child-friendly spaces",
                "Women's safe spaces"
            ],
            "access_issues": "Security constraints limit service delivery"
        }

    async def _identify_priorities(self, location: str, population: int) -> List[str]:
        """Identify Protection priorities"""
        return [
            "Establish protection monitoring systems",
            "Deploy mobile protection teams",
            "Set up child-friendly spaces",
            "Provide GBV prevention and response services",
            "Support civil documentation processes",
            "Coordinate with law enforcement for civilian protection"
        ]

    async def _calculate_resources_needed(self, location: str, population: int) -> List[str]:
        """Calculate Protection resource needs"""
        return [
            f"Protection officers: {max(2, population // 5000)} teams",
            f"Child protection specialists: {max(1, population // 10000)} persons",
            f"GBV specialists: {max(1, population // 8000)} persons",
            "Mobile protection units",
            "Child-friendly space kits",
            "Dignity kits for women and girls",
            "Legal aid materials and documentation support"
        ]