"""
Health Cluster Agent - WHO Lead
Specialized LangChain agent for Health humanitarian sector in Sudan
"""

from typing import Any, Dict, List, Union
from langchain.tools import Tool
from .base_humanitarian_agent import BaseHumanitarianAgent, HumanitarianRequest, create_base_tools

class HealthAgent(BaseHumanitarianAgent):
    """Health Cluster agent for Sudan operations"""

    def __init__(self, llm=None):
        super().__init__("Health", "WHO", llm)

    def get_sector_specific_context(self) -> Dict[str, Any]:
        """Get Health sector context for Sudan"""
        return {
            "sector": "Health",
            "lead_agency": "WHO",
            "sudan_health_situation": {
                "functional_health_facilities": "20% of pre-crisis levels",
                "people_without_healthcare": 12400000,
                "health_workers_displaced": "60% of workforce",
                "medical_supplies": "Critical shortage"
            },
            "disease_outbreaks": [
                "Cholera (ongoing)",
                "Measles (confirmed cases)",
                "Dengue fever (seasonal)",
                "Malaria (endemic)",
                "Acute watery diarrhea"
            ],
            "priority_interventions": [
                "Emergency medical care",
                "Disease outbreak response",
                "Maternal and child health",
                "Mental health and psychosocial support",
                "Health system strengthening"
            ],
            "sudan_statistics": {
                "people_in_need": 12400000,
                "people_targeted": 8900000,
                "funding_required": "USD 456M",
                "funding_received": "USD 180M",
                "gap": "USD 276M"
            },
            "vulnerable_populations": [
                "Pregnant and lactating women",
                "Children under 5",
                "Elderly persons",
                "Persons with chronic conditions",
                "Conflict-injured persons"
            ]
        }

    def _initialize_tools(self) -> List[Tool]:
        """Initialize Health-specific tools"""
        base_tools = create_base_tools()

        def assess_disease_outbreak_risk(location: str) -> str:
            """Assess disease outbreak risks in Sudan"""
            outbreak_risks = {
                "darfur": "Critical - cholera, measles, poor WASH conditions",
                "khartoum": "High - urban overcrowding, damaged infrastructure",
                "kassala": "Medium - refugee camps, vector-borne diseases",
                "blue_nile": "Medium - limited surveillance, remote areas"
            }

            location_lower = location.lower()
            for area, risk in outbreak_risks.items():
                if area in location_lower:
                    return f"Disease outbreak risk in {area}: {risk}"

            return "Disease outbreak risk assessment not available for location"

        def get_health_facility_status(location: str) -> str:
            """Get health facility functionality status"""
            facility_status = {
                "darfur": "15% functional, most damaged by conflict",
                "khartoum": "25% functional, urban facilities partially operational",
                "kassala": "40% functional, refugee area facilities maintained",
                "blue_nile": "10% functional, remote areas severely affected"
            }

            location_lower = location.lower()
            for area, status in facility_status.items():
                if area in location_lower:
                    return f"Health facility status in {area}: {status}"

            return "Health facility status not available for location"

        def calculate_medical_supplies(population: int) -> str:
            """Calculate medical supply needs based on population"""
            return f"""Medical Supply Needs for {population:,} people:

            Emergency supplies (1 month):
            - Basic medicines: {population // 100} kits
            - Trauma kits: {max(10, population // 5000)} units
            - Emergency surgical kits: {max(2, population // 20000)} units
            - Cholera kits: {max(5, population // 10000)} units
            - Measles vaccines: {int(population * 0.15)} doses (children)
            - IV fluids: {population // 50} bags
            - Antibiotics: {population // 20} courses"""

        health_tools = [
            Tool(
                name="assess_disease_outbreak_risk",
                func=assess_disease_outbreak_risk,
                description="Assess disease outbreak risks in Sudan locations"
            ),
            Tool(
                name="get_health_facility_status",
                func=get_health_facility_status,
                description="Get status of health facilities in Sudan locations"
            ),
            Tool(
                name="calculate_medical_supplies",
                func=calculate_medical_supplies,
                description="Calculate medical supply needs for population"
            )
        ]

        return base_tools + health_tools

    async def _mock_response(self, request: Union[str, HumanitarianRequest]) -> str:
        """Generate mock Health response"""
        if isinstance(request, str):
            if "outbreak" in request.lower() or "cholera" in request.lower():
                return """Health Response - Disease Outbreak:

                IMMEDIATE ACTIONS:
                - Activate outbreak response team
                - Establish cholera treatment centers
                - Deploy rapid diagnostic testing
                - Implement case management protocols

                RESOURCES NEEDED:
                - Outbreak investigation team
                - Cholera treatment supplies (ORS, IV fluids, antibiotics)
                - Isolation and treatment facilities
                - Laboratory support

                COORDINATION:
                - WASH cluster for water quality and sanitation
                - Protection cluster for safe access to facilities
                - Logistics cluster for supply delivery

                TIMELINE: Response team deployed within 24 hours"""

            elif "maternal" in request.lower() or "child" in request.lower():
                return """Health Response - Maternal and Child Health:

                IMMEDIATE ACTIONS:
                - Deploy mobile maternal health teams
                - Establish emergency obstetric care
                - Provide child immunization services
                - Set up malnutrition screening

                RESOURCES NEEDED:
                - Skilled birth attendants
                - Clean delivery kits
                - Emergency obstetric care supplies
                - Child health and immunization supplies

                COORDINATION:
                - Nutrition cluster for malnutrition treatment
                - Protection cluster for safe access
                - Education cluster for health education

                TIMELINE: Services operational within 48 hours"""

        return f"""Health Cluster Response for Sudan:

        HEALTH SITUATION ANALYSIS: {request}

        PRIORITY INTERVENTIONS:
        1. Emergency medical care for conflict-affected
        2. Disease outbreak prevention and response
        3. Maternal and child health services
        4. Mental health and psychosocial support

        IMMEDIATE ACTIONS:
        - Deploy emergency medical teams
        - Establish mobile health clinics
        - Provide essential medical supplies
        - Activate disease surveillance

        COORDINATION NEEDS:
        - WASH cluster for prevention activities
        - Nutrition cluster for integrated services
        - Protection cluster for safe access

        LEAD AGENCY: WHO coordination with health partners"""

    async def _conduct_needs_assessment(self, location: str, population: int) -> Dict[str, Any]:
        """Conduct Health needs assessment"""
        return {
            "health_priorities": [
                "Emergency medical care",
                "Disease outbreak response",
                "Maternal and child health",
                "Mental health support"
            ],
            "at_risk_population": {
                "children_under_5": int(population * 0.18),
                "pregnant_women": int(population * 0.05),
                "elderly": int(population * 0.08),
                "chronic_conditions": int(population * 0.12)
            },
            "health_facility_access": "Limited - 20% of facilities functional",
            "disease_risks": "High - cholera, measles, malaria endemic",
            "health_workforce": f"Need {max(5, population // 2000)} health workers"
        }

    async def _identify_priorities(self, location: str, population: int) -> List[str]:
        """Identify Health priorities"""
        return [
            "Establish emergency medical services",
            "Deploy mobile health teams",
            "Implement disease surveillance and response",
            "Provide maternal and child health services",
            "Ensure essential medicine supply",
            "Establish mental health and psychosocial support",
            "Restore basic health infrastructure"
        ]

    async def _calculate_resources_needed(self, location: str, population: int) -> List[str]:
        """Calculate Health resource needs"""
        return [
            f"Medical teams: {max(2, population // 5000)} teams",
            f"Health workers: {max(5, population // 2000)} persons",
            f"Mobile clinics: {max(1, population // 10000)} units",
            "Emergency medical supplies (3-month stock)",
            "Disease outbreak investigation kits",
            "Trauma and surgical supplies",
            "Cold chain equipment for vaccines",
            "Mental health support materials"
        ]