"""
Early Recovery Agent - UNDP Lead
Handles recovery planning, livelihoods restoration, and resilience building
"""

from typing import Dict, List, Any
from langchain.tools import BaseTool
from langchain.schema import BaseMessage
import json

from .base_humanitarian_agent import BaseHumanitarianAgent, HumanitarianRequest, HumanitarianResponse


class LivelihoodsAssessmentTool(BaseTool):
    name = "livelihoods_assessment"
    description = "Assess livelihood opportunities and economic recovery potential in Sudan"

    def _run(self, location: str, sector: str = "all_sectors") -> str:
        livelihoods_data = {
            "Nyala": {
                "primary_livelihoods": ["Agriculture", "Livestock", "Small trade", "Casual labor"],
                "employment_rate": "35%",
                "main_disruptions": ["Market access", "Asset loss", "Insecurity"],
                "recovery_potential": "Medium - Existing market infrastructure",
                "priority_interventions": ["Cash-for-work", "Market rehabilitation", "Skills training"]
            },
            "El_Geneina": {
                "primary_livelihoods": ["Cross-border trade", "Agriculture", "Handicrafts", "Services"],
                "employment_rate": "28%",
                "main_disruptions": ["Border closure", "Asset destruction", "Population displacement"],
                "recovery_potential": "Low - Severe infrastructure damage",
                "priority_interventions": ["Emergency employment", "Market system recovery", "Border trade facilitation"]
            },
            "Kassala": {
                "primary_livelihoods": ["Agriculture", "Trade", "Remittances", "Transport services"],
                "employment_rate": "45%",
                "main_disruptions": ["Seasonal unemployment", "Limited access to finance"],
                "recovery_potential": "High - Stable economic base",
                "priority_interventions": ["Microfinance", "Agricultural support", "Skills development"]
            }
        }

        sector_details = {
            "agriculture": {
                "season_status": "Post-harvest period",
                "main_crops": ["Sorghum", "Millet", "Sesame", "Groundnuts"],
                "challenges": ["Seed access", "Tools shortage", "Land tenure"],
                "support_needed": ["Agricultural inputs", "Extension services", "Market linkages"]
            },
            "livestock": {
                "herd_status": "Reduced due to conflict",
                "main_animals": ["Cattle", "Sheep", "Goats", "Camels"],
                "challenges": ["Veterinary services", "Pasture access", "Market disruption"],
                "support_needed": ["Animal health", "Feed supplies", "Restocking programs"]
            },
            "trade": {
                "market_status": "Partially functional",
                "main_commodities": ["Food items", "Household goods", "Construction materials"],
                "challenges": ["Capital shortage", "Transport costs", "Security concerns"],
                "support_needed": ["Working capital", "Market rehabilitation", "Business training"]
            }
        }

        if location in livelihoods_data:
            data = livelihoods_data[location]
            result = f"Livelihoods Assessment - {location}:\n" + \
                    f"Primary livelihoods: {', '.join(data['primary_livelihoods'])}\n" + \
                    f"Employment rate: {data['employment_rate']}\n" + \
                    f"Main disruptions: {', '.join(data['main_disruptions'])}\n" + \
                    f"Recovery potential: {data['recovery_potential']}\n" + \
                    f"Priority interventions: {', '.join(data['priority_interventions'])}"

            if sector != "all_sectors" and sector in sector_details:
                sector_info = sector_details[sector]
                result += f"\n\n{sector.title()} Sector Details:\n" + \
                         f"Status: {sector_info.get('season_status', sector_info.get('herd_status', sector_info.get('market_status', 'Available')))}\n" + \
                         f"Key focus: {', '.join(sector_info.get('main_crops', sector_info.get('main_animals', sector_info.get('main_commodities', []))))}\n" + \
                         f"Support needed: {', '.join(sector_info['support_needed'])}"

            return result

        return f"Assessing livelihoods opportunities in {location} with focus on {sector}"


class RecoveryPlanningTool(BaseTool):
    name = "recovery_planning"
    description = "Develop early recovery and resilience building plans for Sudan"

    def _run(self, planning_timeframe: str, focus_area: str, location: str = "multiple") -> str:
        recovery_frameworks = {
            "immediate": {
                "timeframe": "3-6 months",
                "objectives": ["Stabilize basic services", "Emergency employment", "Damage assessment"],
                "key_activities": ["Cash-for-work programs", "Debris removal", "Basic infrastructure repair"],
                "success_indicators": ["Employment creation", "Service restoration", "Market functionality"]
            },
            "short_term": {
                "timeframe": "6-18 months",
                "objectives": ["Restore livelihoods", "Strengthen institutions", "Build resilience"],
                "key_activities": ["Skills training", "Market rehabilitation", "Community planning"],
                "success_indicators": ["Income generation", "Service quality", "Community cohesion"]
            },
            "medium_term": {
                "timeframe": "18 months - 3 years",
                "objectives": ["Sustainable recovery", "Economic growth", "Social cohesion"],
                "key_activities": ["Infrastructure development", "Enterprise development", "Governance strengthening"],
                "success_indicators": ["Economic indicators", "Social stability", "Reduced vulnerabilities"]
            }
        }

        focus_areas = {
            "economic": "Income generation, market systems, financial services",
            "social": "Education, health, social cohesion, gender equality",
            "infrastructure": "Housing, transport, utilities, communications",
            "governance": "Local institutions, rule of law, public services"
        }

        if planning_timeframe in recovery_frameworks:
            framework = recovery_frameworks[planning_timeframe]
            area_desc = focus_areas.get(focus_area, focus_area)

            return f"Recovery Planning - {location} ({planning_timeframe.replace('_', '-').title()} Phase):\n" + \
                   f"Timeframe: {framework['timeframe']}\n" + \
                   f"Focus area: {area_desc}\n" + \
                   f"Key objectives: {', '.join(framework['objectives'])}\n" + \
                   f"Main activities: {', '.join(framework['key_activities'])}\n" + \
                   f"Success indicators: {', '.join(framework['success_indicators'])}"

        return f"Developing {planning_timeframe.replace('_', '-')} recovery plan for {focus_area} in {location}"


class ResilienceBuildingTool(BaseTool):
    name = "resilience_building"
    description = "Design resilience building interventions for Sudan communities"

    def _run(self, resilience_type: str, target_group: str = "communities") -> str:
        resilience_approaches = {
            "economic_resilience": {
                "definition": "Ability to withstand and recover from economic shocks",
                "interventions": ["Diversified livelihoods", "Savings groups", "Insurance schemes"],
                "indicators": ["Income stability", "Asset protection", "Financial inclusion"],
                "target_groups": ["Households", "Small businesses", "Cooperatives"]
            },
            "social_resilience": {
                "definition": "Community capacity to maintain cohesion during crises",
                "interventions": ["Social protection", "Conflict resolution", "Leadership development"],
                "indicators": ["Social capital", "Collective efficacy", "Reduced tensions"],
                "target_groups": ["Communities", "Youth", "Women's groups", "Traditional leaders"]
            },
            "environmental_resilience": {
                "definition": "Sustainable management of natural resources",
                "interventions": ["Climate adaptation", "Natural resource management", "Disaster risk reduction"],
                "indicators": ["Environmental health", "Adaptive capacity", "Risk reduction"],
                "target_groups": ["Farmers", "Pastoralists", "Communities", "Local authorities"]
            },
            "institutional_resilience": {
                "definition": "Strong local institutions and governance systems",
                "interventions": ["Capacity building", "Participatory planning", "Transparency mechanisms"],
                "indicators": ["Institutional capacity", "Service delivery", "Accountability"],
                "target_groups": ["Local government", "Community organizations", "Service providers"]
            }
        }

        if resilience_type in resilience_approaches:
            approach = resilience_approaches[resilience_type]

            return f"Resilience Building - {resilience_type.replace('_', ' ').title()}:\n" + \
                   f"Definition: {approach['definition']}\n" + \
                   f"Target group: {target_group}\n" + \
                   f"Key interventions: {', '.join(approach['interventions'])}\n" + \
                   f"Applicable to: {', '.join(approach['target_groups'])}\n" + \
                   f"Success indicators: {', '.join(approach['indicators'])}"

        return f"Building {resilience_type.replace('_', ' ')} resilience for {target_group}"


class EarlyRecoveryAgent(BaseHumanitarianAgent):
    def __init__(self):
        super().__init__(
            sector="Early Recovery",
            lead_agencies=["UNDP"],
            sudan_context={
                "recovery_challenges": "Ongoing conflict limiting recovery opportunities",
                "displacement_impact": "6.2M IDPs need livelihood restoration support",
                "economic_disruption": "75% of businesses disrupted or destroyed",
                "priority_areas": ["Darfur", "Blue Nile", "South Kordofan", "Khartoum periphery"],
                "challenges": [
                    "Ongoing insecurity preventing sustainable recovery",
                    "Massive unemployment and livelihood loss",
                    "Weakened local institutions and governance",
                    "Limited access to finance and markets"
                ],
                "key_approaches": ["Do No Harm", "Conflict sensitivity", "Community-based recovery", "Market-based programming"]
            }
        )

        # Add early recovery-specific tools
        self.tools.extend([
            LivelihoodsAssessmentTool(),
            RecoveryPlanningTool(),
            ResilienceBuildingTool()
        ])

    def process_request(self, request: HumanitarianRequest) -> HumanitarianResponse:
        """Process early recovery-related requests for Sudan context"""

        # Extract key information
        query_lower = request.query.lower()
        location = self._extract_location(request.query)

        # Determine response based on query type
        if any(word in query_lower for word in ["livelihood", "employment", "job", "income"]):
            sector = "agriculture" if "farm" in query_lower or "crop" in query_lower else \
                    "livestock" if "animal" in query_lower or "cattle" in query_lower else \
                    "trade" if "market" in query_lower or "business" in query_lower else "all_sectors"
            tool_result = self.tools[0]._run(location or "Nyala", sector)
            analysis = f"Livelihoods assessment shows critical needs for economic recovery in {location or 'affected areas'}"

        elif any(word in query_lower for word in ["recovery", "planning", "strategy", "plan"]):
            timeframe = "immediate" if "immediate" in query_lower or "emergency" in query_lower else \
                       "medium_term" if "medium" in query_lower or "long" in query_lower else "short_term"
            focus_area = "economic" if "economic" in query_lower else \
                        "social" if "social" in query_lower else \
                        "infrastructure" if "infrastructure" in query_lower else "governance"
            tool_result = self.tools[1]._run(timeframe, focus_area, location or "multiple")
            analysis = "Recovery planning requires coordinated approach addressing multiple sectors"

        elif any(word in query_lower for word in ["resilience", "adaptation", "capacity", "strength"]):
            resilience_type = "economic_resilience" if "economic" in query_lower else \
                             "social_resilience" if "social" in query_lower else \
                             "environmental_resilience" if "environment" in query_lower else \
                             "institutional_resilience"
            target_group = "women" if "women" in query_lower else \
                          "youth" if "youth" in query_lower else "communities"
            tool_result = self.tools[2]._run(resilience_type, target_group)
            analysis = "Resilience building essential for sustainable recovery and conflict prevention"

        else:
            # General early recovery information
            tool_result = "Sudan Early Recovery: 6.2M IDPs need livelihood support, 75% businesses disrupted, ongoing conflict challenges"
            analysis = "Early recovery operations require conflict-sensitive programming and sustained support"

        # Generate recommendations
        recommendations = self._generate_early_recovery_recommendations(request.query, location)

        return HumanitarianResponse(
            sector=self.sector,
            analysis=analysis,
            data=tool_result,
            recommendations=recommendations,
            priority_level="MEDIUM",
            locations=[location] if location else ["Nyala", "El Geneina", "Kassala"]
        )

    def _generate_early_recovery_recommendations(self, query: str, location: str = None) -> List[str]:
        """Generate early recovery-specific recommendations"""
        base_recommendations = [
            "Implement conflict-sensitive programming approaches",
            "Establish cash-for-work programs for immediate employment",
            "Support market system recovery and rehabilitation",
            "Strengthen community-based recovery planning processes"
        ]

        if location:
            base_recommendations.append(f"Conduct detailed recovery needs assessment in {location}")

        if "livelihood" in query.lower() or "employment" in query.lower():
            base_recommendations.append("Scale up skills training and job placement programs")

        if "women" in query.lower():
            base_recommendations.append("Ensure gender-responsive recovery programming")

        if "youth" in query.lower():
            base_recommendations.append("Design youth-focused enterprise development programs")

        if "resilience" in query.lower():
            base_recommendations.append("Integrate climate adaptation and disaster risk reduction measures")

        return base_recommendations