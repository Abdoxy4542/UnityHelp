"""
WASH Cluster Agent - UNICEF Lead
Specialized LangChain agent for Water, Sanitation and Hygiene sector in Sudan
"""

from typing import Any, Dict, List, Union
from langchain.tools import Tool
from .base_humanitarian_agent import BaseHumanitarianAgent, HumanitarianRequest, create_base_tools

class WASHAgent(BaseHumanitarianAgent):
    """WASH Cluster agent for Sudan operations"""

    def __init__(self, llm=None):
        super().__init__("WASH", "UNICEF", llm)

    def get_sector_specific_context(self) -> Dict[str, Any]:
        """Get WASH sector context for Sudan"""
        return {
            "sector": "WASH",
            "lead_agency": "UNICEF",
            "sudan_wash_situation": {
                "people_without_safe_water": 15600000,
                "people_without_sanitation": 18500000,
                "water_system_functionality": "30% of pre-crisis levels",
                "cholera_outbreak_risk": "Critical due to poor WASH conditions"
            },
            "key_challenges": [
                "Damaged water infrastructure",
                "Fuel shortages for water pumping",
                "Overcrowded displacement sites",
                "Limited waste management",
                "Poor hygiene practices",
                "Contaminated water sources"
            ],
            "priority_interventions": [
                "Emergency water supply",
                "Sanitation facilities in camps",
                "Hygiene promotion",
                "Water system rehabilitation",
                "Solid waste management",
                "Vector control"
            ],
            "sudan_statistics": {
                "people_in_need": 15600000,
                "people_targeted": 7800000,
                "funding_required": "USD 389M",
                "funding_received": "USD 155M",
                "gap": "USD 234M"
            },
            "standards": {
                "water_quantity": "15L/person/day minimum, 20L/person/day target",
                "water_quality": "0 CFU/100ml E.coli",
                "distance_to_water": "Maximum 500m",
                "latrine_ratio": "1 latrine per 20 people",
                "gender_facilities": "Separate facilities with locks and lighting"
            }
        }

    def _initialize_tools(self) -> List[Tool]:
        """Initialize WASH-specific tools"""
        base_tools = create_base_tools()

        def assess_water_system_status(location: str) -> str:
            """Assess water system functionality"""
            water_status = {
                "darfur": "10% functional - most systems damaged, rely on unprotected sources",
                "khartoum": "35% functional - urban systems partially operational",
                "kassala": "45% functional - refugee areas have improved systems",
                "blue_nile": "20% functional - remote areas, limited infrastructure"
            }

            location_lower = location.lower()
            for area, status in water_status.items():
                if area in location_lower:
                    return f"Water system status in {area}: {status}"

            return "Water system status not available for location"

        def calculate_wash_needs(population: int) -> str:
            """Calculate WASH infrastructure needs"""
            return f"""WASH Needs for {population:,} people:

            Water Supply:
            - Daily water requirement: {population * 20} liters/day
            - Water points needed: {max(1, population // 250)} water points
            - Storage capacity: {population * 7.5} liters storage
            - Trucked water (if needed): {population * 15 // 1000} m3/day

            Sanitation:
            - Latrines needed: {max(10, population // 20)} latrines
            - Handwashing stations: {max(5, population // 50)} stations
            - Bathing facilities: {max(2, population // 100)} facilities

            Hygiene:
            - Hygiene kits: {population // 5} family kits
            - Soap distribution: {population * 0.25} kg/month
            - Water containers: {population // 5} jerry cans"""

        def assess_cholera_risk(location: str) -> str:
            """Assess cholera outbreak risk based on WASH conditions"""
            cholera_risk = {
                "darfur": "Critical - poor sanitation, open defecation, contaminated water",
                "khartoum": "High - overcrowding, damaged sewage systems",
                "kassala": "Medium - improved camp conditions, better water quality",
                "blue_nile": "Medium-High - limited WASH facilities, remote areas"
            }

            location_lower = location.lower()
            for area, risk in cholera_risk.items():
                if area in location_lower:
                    return f"Cholera risk in {area}: {risk}"

            return "Cholera risk assessment not available for location"

        wash_tools = [
            Tool(
                name="assess_water_system_status",
                func=assess_water_system_status,
                description="Assess water system functionality in Sudan locations"
            ),
            Tool(
                name="calculate_wash_needs",
                func=calculate_wash_needs,
                description="Calculate WASH infrastructure needs for population"
            ),
            Tool(
                name="assess_cholera_risk",
                func=assess_cholera_risk,
                description="Assess cholera outbreak risk based on WASH conditions"
            )
        ]

        return base_tools + wash_tools

    async def _mock_response(self, request: Union[str, HumanitarianRequest]) -> str:
        """Generate mock WASH response"""
        if isinstance(request, str):
            if "cholera" in request.lower() or "outbreak" in request.lower():
                return """WASH Response - Cholera Prevention/Response:

                IMMEDIATE ACTIONS:
                - Deploy water quality testing teams
                - Establish emergency water treatment
                - Set up emergency sanitation facilities
                - Implement intensive hygiene promotion

                RESOURCES NEEDED:
                - Water testing and treatment supplies
                - Emergency latrine construction materials
                - Hygiene promotion materials and soap
                - Chlorination equipment and supplies

                COORDINATION:
                - Health cluster for case management
                - Food Security cluster for food safety
                - Protection cluster for safe access to facilities

                TIMELINE: Emergency WASH response within 24 hours"""

            elif "camp" in request.lower() or "displacement" in request.lower():
                return """WASH Response - Displacement Site WASH:

                IMMEDIATE ACTIONS:
                - Establish emergency water supply (trucking if needed)
                - Construct gender-segregated latrines
                - Set up handwashing stations
                - Implement solid waste management

                RESOURCES NEEDED:
                - Water storage tanks and distribution
                - Latrine construction materials
                - Hygiene supplies and soap
                - Solid waste management equipment

                COORDINATION:
                - Shelter cluster for site planning
                - Protection cluster for safety and dignity
                - Health cluster for disease prevention

                TIMELINE: Basic WASH services within 72 hours"""

        return f"""WASH Cluster Response for Sudan:

        WASH SITUATION ANALYSIS: {request}

        CURRENT CHALLENGES:
        - 15.6 million people lack access to safe water
        - 18.5 million people lack adequate sanitation
        - Water systems only 30% functional
        - Critical cholera outbreak risk

        PRIORITY INTERVENTIONS:
        1. Emergency water supply through trucking and treatment
        2. Construction of emergency sanitation facilities
        3. Intensive hygiene promotion campaigns
        4. Water system rehabilitation where possible

        IMMEDIATE ACTIONS:
        - Deploy emergency WASH teams
        - Establish water trucking operations
        - Construct gender-appropriate sanitation facilities
        - Distribute hygiene supplies

        COORDINATION NEEDS:
        - Health cluster for disease prevention
        - Protection cluster for safe access
        - Shelter cluster for site planning

        LEAD AGENCY: UNICEF coordination"""

    async def _conduct_needs_assessment(self, location: str, population: int) -> Dict[str, Any]:
        """Conduct WASH needs assessment"""
        return {
            "water_access": f"{int(population * 0.4)} people lack safe water access",
            "sanitation_access": f"{int(population * 0.6)} people lack adequate sanitation",
            "hygiene_practices": "Poor due to lack of supplies and knowledge",
            "infrastructure_damage": "70% of water systems non-functional",
            "disease_risk": "High risk of waterborne diseases",
            "gender_considerations": "Women and girls face safety risks accessing facilities",
            "emergency_response_time": "72 hours for basic services"
        }

    async def _identify_priorities(self, location: str, population: int) -> List[str]:
        """Identify WASH priorities"""
        return [
            "Establish emergency water supply",
            "Construct emergency sanitation facilities",
            "Implement intensive hygiene promotion",
            "Ensure gender-appropriate and safe WASH facilities",
            "Establish solid waste management systems",
            "Implement vector control measures",
            "Begin rehabilitation of damaged water systems"
        ]

    async def _calculate_resources_needed(self, location: str, population: int) -> List[str]:
        """Calculate WASH resource needs"""
        return [
            f"Water supply: {population * 20} liters/day capacity",
            f"Water points: {max(1, population // 250)} installations",
            f"Latrines: {max(10, population // 20)} emergency latrines",
            f"Handwashing stations: {max(5, population // 50)} stations",
            f"WASH teams: {max(2, population // 5000)} teams",
            f"Hygiene kits: {population // 5} family kits",
            "Water testing and treatment supplies",
            "Latrine construction materials",
            "Solid waste management equipment"
        ]