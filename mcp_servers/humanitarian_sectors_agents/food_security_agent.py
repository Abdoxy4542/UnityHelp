"""
Food Security Cluster Agent - WFP & FAO Co-Lead
Specialized LangChain agent for Food Security humanitarian sector in Sudan
"""

from typing import Any, Dict, List, Union
from langchain.tools import Tool
from .base_humanitarian_agent import BaseHumanitarianAgent, HumanitarianRequest, create_base_tools

class FoodSecurityAgent(BaseHumanitarianAgent):
    """Food Security Cluster agent for Sudan operations"""

    def __init__(self, llm=None):
        super().__init__("Food Security", "WFP & FAO", llm)

    def get_sector_specific_context(self) -> Dict[str, Any]:
        """Get Food Security sector context for Sudan"""
        return {
            "sector": "Food Security",
            "co_lead_agencies": ["WFP", "FAO"],
            "sudan_food_security_situation": {
                "ipc_phase_3_plus": 17800000,  # Crisis, Emergency, Famine levels
                "percentage_food_insecure": 0.69,
                "children_malnourished": 3400000,
                "harvest_impact": "75% crop loss in conflict areas",
                "livestock_losses": "60% in Darfur states",
                "market_disruption": "Severe - prices increased 300%"
            },
            "key_interventions": [
                "Emergency food assistance",
                "Nutrition support",
                "Livelihood protection",
                "Agricultural recovery",
                "Market support",
                "Food security monitoring"
            ],
            "sudan_statistics": {
                "people_in_need": 17800000,
                "people_targeted": 9200000,
                "funding_required": "USD 1.2B",
                "funding_received": "USD 425M",
                "gap": "USD 775M"
            },
            "seasonal_calendar": {
                "planting_season": "May - July",
                "harvest_season": "October - December",
                "lean_season": "March - September",
                "current_phase": "Extended lean season due to conflict"
            },
            "vulnerable_groups": [
                "IDPs in camps and settlements",
                "Host communities in conflict areas",
                "Pastoralists with livestock losses",
                "Smallholder farmers",
                "Female-headed households",
                "Malnourished children and pregnant women"
            ]
        }

    def _initialize_tools(self) -> List[Tool]:
        """Initialize Food Security-specific tools"""
        base_tools = create_base_tools()

        def assess_food_security_phase(location: str) -> str:
            """Assess IPC food security phase"""
            ipc_phases = {
                "darfur": "Phase 4 (Emergency) - widespread acute malnutrition",
                "khartoum": "Phase 3 (Crisis) - displacement, market disruption",
                "blue_nile": "Phase 3 (Crisis) - conflict impact on production",
                "kassala": "Phase 2-3 (Stressed/Crisis) - refugee burden, drought"
            }

            location_lower = location.lower()
            for area, phase in ipc_phases.items():
                if area in location_lower:
                    return f"Food security phase in {area}: {phase}"

            return "Food security assessment not available for location"

        def calculate_food_assistance_needs(population: int) -> str:
            """Calculate food assistance requirements"""
            return f"""Food Assistance Needs for {population:,} people:

            Monthly Requirements:
            - Cereal: {population * 15} kg (15kg/person/month)
            - Pulses: {population * 3.75} kg (3.75kg/person/month)
            - Vegetable oil: {population * 0.9} liters (0.9L/person/month)
            - Salt: {population * 0.15} kg (0.15kg/person/month)
            - Sugar: {population * 0.6} kg (0.6kg/person/month)

            Special Requirements:
            - Nutritious food for children U5: {int(population * 0.18)} children
            - Food for pregnant/lactating women: {int(population * 0.05)} women
            - Therapeutic food for SAM cases: {int(population * 0.03)} cases

            Total monthly food tonnage: {population * 20.4 / 1000:.1f} MT"""

        def get_market_prices(location: str) -> str:
            """Get current market prices for key commodities"""
            market_data = {
                "darfur": "Sorghum: 180 SDG/kg (+320%), Millet: 200 SDG/kg (+400%)",
                "khartoum": "Wheat: 250 SDG/kg (+380%), Rice: 300 SDG/kg (+350%)",
                "kassala": "Sorghum: 150 SDG/kg (+280%), Sesame: 400 SDG/kg (+200%)",
                "blue_nile": "Sorghum: 160 SDG/kg (+300%), Groundnuts: 350 SDG/kg (+250%)"
            }

            location_lower = location.lower()
            for area, prices in market_data.items():
                if area in location_lower:
                    return f"Market prices in {area}: {prices} (% increase from pre-crisis)"

            return "Market price information not available for location"

        food_security_tools = [
            Tool(
                name="assess_food_security_phase",
                func=assess_food_security_phase,
                description="Assess IPC food security classification for Sudan locations"
            ),
            Tool(
                name="calculate_food_assistance_needs",
                func=calculate_food_assistance_needs,
                description="Calculate food assistance requirements for population"
            ),
            Tool(
                name="get_market_prices",
                func=get_market_prices,
                description="Get current market prices for key food commodities"
            )
        ]

        return base_tools + food_security_tools

    async def _mock_response(self, request: Union[str, HumanitarianRequest]) -> str:
        """Generate mock Food Security response"""
        if isinstance(request, str):
            if "emergency" in request.lower() or "famine" in request.lower():
                return """Food Security Response - Emergency Food Assistance:

                IMMEDIATE ACTIONS:
                - Scale up emergency food distributions
                - Deploy rapid response teams
                - Establish mobile food distribution points
                - Implement emergency cash transfers where markets function

                RESOURCES NEEDED:
                - Emergency food stocks (cereal, pulses, oil)
                - Distribution logistics and transport
                - Cash transfer mechanisms
                - Nutrition screening equipment

                COORDINATION:
                - Nutrition cluster for integrated programming
                - Logistics cluster for food transport
                - Protection cluster for safe access

                TIMELINE: Emergency distributions within 72 hours"""

            elif "nutrition" in request.lower() or "malnutrition" in request.lower():
                return """Food Security Response - Nutrition Integration:

                IMMEDIATE ACTIONS:
                - Distribute specialized nutritious foods
                - Screen for acute malnutrition
                - Provide food for nutrition programs
                - Support feeding programs

                RESOURCES NEEDED:
                - Fortified blended foods
                - Ready-to-use therapeutic foods (RUTF)
                - Specialized nutritious foods for children
                - Micronutrient supplements

                COORDINATION:
                - Nutrition cluster for treatment protocols
                - Health cluster for medical screening
                - WASH cluster for hygiene practices

                TIMELINE: Nutrition support operational within 48 hours"""

        return f"""Food Security Cluster Response for Sudan:

        FOOD SECURITY ANALYSIS: {request}

        SITUATION OVERVIEW:
        - 17.8 million people in IPC Phase 3+ (Crisis or worse)
        - 69% of population food insecure
        - Crop losses up to 75% in conflict areas
        - Market prices increased 300% from pre-crisis

        PRIORITY INTERVENTIONS:
        1. Emergency food assistance for most vulnerable
        2. Nutrition support for malnourished children and women
        3. Livelihood protection and recovery support
        4. Market support where feasible

        IMMEDIATE ACTIONS:
        - Scale emergency food distributions
        - Deploy mobile teams to hard-to-reach areas
        - Implement cash transfers in functioning markets
        - Establish food security monitoring systems

        COORDINATION NEEDS:
        - Nutrition cluster for integrated approach
        - Logistics cluster for supply chain
        - Protection cluster for safe access to food

        CO-LEAD AGENCIES: WFP and FAO coordination"""

    async def _conduct_needs_assessment(self, location: str, population: int) -> Dict[str, Any]:
        """Conduct Food Security needs assessment"""
        return {
            "food_security_phase": "IPC Phase 3-4 (Crisis to Emergency)",
            "food_insecure_population": int(population * 0.75),
            "malnourished_children": int(population * 0.18 * 0.25),  # 25% of children U5
            "monthly_food_needs": f"{population * 20.4 / 1000:.1f} MT",
            "livelihood_impact": "75% crop loss, 60% livestock loss",
            "market_functionality": "Severely disrupted, prices increased 300%",
            "access_constraints": "Security limitations, damaged infrastructure"
        }

    async def _identify_priorities(self, location: str, population: int) -> List[str]:
        """Identify Food Security priorities"""
        return [
            "Provide emergency food assistance to most vulnerable",
            "Scale up specialized nutritious food support",
            "Implement cash transfers where markets function",
            "Protect remaining livelihood assets",
            "Support emergency agricultural activities",
            "Establish food security monitoring systems",
            "Coordinate with nutrition for integrated programming"
        ]

    async def _calculate_resources_needed(self, location: str, population: int) -> List[str]:
        """Calculate Food Security resource needs"""
        return [
            f"Monthly food assistance: {population * 20.4 / 1000:.1f} MT",
            f"Distribution points: {max(5, population // 5000)} locations",
            f"Mobile teams: {max(2, population // 10000)} teams",
            f"Cash transfer recipients: {int(population * 0.3)} people",
            f"Agricultural inputs for {int(population * 0.6 // 5)} farming households",
            "Emergency livelihood kits",
            "Food security assessment tools",
            "Logistics and transport capacity"
        ]