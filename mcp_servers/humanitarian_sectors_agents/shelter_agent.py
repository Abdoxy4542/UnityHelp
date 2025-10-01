"""
Shelter/NFI Cluster Agent - UNHCR & IFRC Co-Lead
Handles emergency shelter, non-food items, and settlement planning
"""

from typing import Dict, List, Any
from langchain.tools import BaseTool
from langchain.schema import BaseMessage
import json

from .base_humanitarian_agent import BaseHumanitarianAgent, HumanitarianRequest, HumanitarianResponse


class ShelterAssessmentTool(BaseTool):
    name = "shelter_assessment"
    description = "Assess shelter needs and conditions in Sudan displacement sites"

    def _run(self, location: str, population: int = None) -> str:
        shelter_data = {
            "Nyala IDP Settlement": {
                "population": 45000,
                "shelter_type": "Emergency tents, makeshift structures",
                "condition": "Overcrowded, 8-10 people per tent",
                "needs": ["Weatherproof materials", "Family separation screens", "Cooking areas"],
                "nfi_gaps": "Blankets (60%), cooking sets (45%), hygiene kits (40%)"
            },
            "El Geneina Emergency Camp": {
                "population": 32000,
                "shelter_type": "Plastic sheeting, communal structures",
                "condition": "Inadequate protection from elements",
                "needs": ["Durable shelter materials", "Site planning", "Drainage"],
                "nfi_gaps": "Sleeping mats (70%), clothing (55%), buckets (50%)"
            },
            "Kassala Reception Center": {
                "population": 18000,
                "shelter_type": "Transit accommodation",
                "condition": "Temporary, overcrowded",
                "needs": ["Permanent shelter solutions", "Privacy partitions"],
                "nfi_gaps": "Household items (65%), lighting (80%)"
            }
        }

        if location in shelter_data:
            data = shelter_data[location]
            return f"Shelter Assessment - {location}:\n" + \
                   f"Population: {data['population']:,}\n" + \
                   f"Shelter Type: {data['shelter_type']}\n" + \
                   f"Condition: {data['condition']}\n" + \
                   f"Priority Needs: {', '.join(data['needs'])}\n" + \
                   f"NFI Gaps: {data['nfi_gaps']}"

        return f"Conducting shelter assessment for {location} with {population or 'unknown'} population"


class NFIDistributionTool(BaseTool):
    name = "nfi_distribution"
    description = "Plan and track non-food item distributions in Sudan"

    def _run(self, item_type: str, quantity: int, location: str) -> str:
        nfi_standards = {
            "blankets": {"per_person": 2, "seasonal_factor": 1.5},
            "cooking_sets": {"per_family": 1, "family_size": 6},
            "hygiene_kits": {"per_person": 1, "duration_months": 3},
            "sleeping_mats": {"per_person": 1, "replacement_months": 6},
            "buckets": {"per_family": 2, "capacity_liters": 20}
        }

        if item_type.lower() in nfi_standards:
            standards = nfi_standards[item_type.lower()]
            coverage = quantity / max(standards.get('per_person', standards.get('per_family', 1)), 1)

            return f"NFI Distribution Plan - {location}:\n" + \
                   f"Item: {item_type.title()}\n" + \
                   f"Quantity: {quantity:,}\n" + \
                   f"Coverage: ~{int(coverage):,} {'people' if 'per_person' in standards else 'families'}\n" + \
                   f"Standards: {standards}"

        return f"Planning distribution of {quantity:,} {item_type} in {location}"


class ShelterUpgradeTool(BaseTool):
    name = "shelter_upgrade"
    description = "Plan shelter improvements and transitional solutions in Sudan"

    def _run(self, current_type: str, target_type: str, timeline: str) -> str:
        upgrade_paths = {
            "emergency_tents": {
                "transitional_shelter": {
                    "materials": ["Timber frame", "Corrugated iron sheets", "Concrete foundation"],
                    "cost_per_unit": 1500,
                    "timeline": "2-3 months",
                    "durability": "2-3 years"
                }
            },
            "plastic_sheeting": {
                "semi_permanent": {
                    "materials": ["Brick walls", "Metal roofing", "Windows/doors"],
                    "cost_per_unit": 2500,
                    "timeline": "3-4 months",
                    "durability": "5+ years"
                }
            }
        }

        current_key = current_type.lower().replace(" ", "_").replace("/", "_")
        target_key = target_type.lower().replace(" ", "_").replace("/", "_")

        if current_key in upgrade_paths and target_key in upgrade_paths[current_key]:
            upgrade = upgrade_paths[current_key][target_key]
            return f"Shelter Upgrade Plan:\n" + \
                   f"From: {current_type} → To: {target_type}\n" + \
                   f"Materials: {', '.join(upgrade['materials'])}\n" + \
                   f"Cost per unit: ${upgrade['cost_per_unit']:,}\n" + \
                   f"Timeline: {upgrade['timeline']}\n" + \
                   f"Expected durability: {upgrade['durability']}"

        return f"Planning upgrade from {current_type} to {target_type} over {timeline}"


class ShelterAgent(BaseHumanitarianAgent):
    def __init__(self):
        super().__init__(
            sector="Shelter/NFI",
            lead_agencies=["UNHCR", "IFRC"],
            sudan_context={
                "displaced_population": "6.2 million internally displaced",
                "shelter_gaps": "85% of IDPs in inadequate shelter",
                "priority_locations": ["Nyala", "El Geneina", "Kassala", "Zalingei"],
                "challenges": [
                    "Lack of durable shelter materials",
                    "Overcrowding in displacement sites",
                    "Limited land for camp expansion",
                    "Seasonal weather impacts"
                ],
                "nfi_priorities": ["Blankets", "Cooking sets", "Hygiene items", "Sleeping materials"]
            }
        )

        # Add shelter-specific tools
        self.tools.extend([
            ShelterAssessmentTool(),
            NFIDistributionTool(),
            ShelterUpgradeTool()
        ])

    def process_request(self, request: HumanitarianRequest) -> HumanitarianResponse:
        """Process shelter/NFI related requests for Sudan context"""

        # Extract key information
        query_lower = request.query.lower()
        location = self._extract_location(request.query)

        # Determine response based on query type
        if any(word in query_lower for word in ["assess", "assessment", "condition"]):
            tool_result = self.tools[0]._run(location or "Nyala IDP Settlement")
            analysis = f"Shelter assessment indicates critical gaps in {location or 'displacement sites'}"

        elif any(word in query_lower for word in ["distribute", "nfi", "items"]):
            # Extract item type and quantity if mentioned
            tool_result = self.tools[1]._run("blankets", 10000, location or "Multiple locations")
            analysis = "NFI distribution planning shows significant coverage gaps"

        elif any(word in query_lower for word in ["upgrade", "improve", "transitional"]):
            tool_result = self.tools[2]._run("emergency tents", "transitional shelter", "3 months")
            analysis = "Shelter upgrade options available but require substantial resources"

        else:
            # General shelter information
            tool_result = "Sudan Shelter Overview: 6.2M IDPs, 85% in inadequate shelter, priority on weatherproof materials"
            analysis = "Massive shelter needs across Sudan requiring coordinated response"

        # Generate recommendations
        recommendations = self._generate_shelter_recommendations(request.query, location)

        return HumanitarianResponse(
            sector=self.sector,
            analysis=analysis,
            data=tool_result,
            recommendations=recommendations,
            priority_level="HIGH",
            locations=[location] if location else ["Nyala", "El Geneina", "Kassala"]
        )

    def _generate_shelter_recommendations(self, query: str, location: str = None) -> List[str]:
        """Generate shelter-specific recommendations"""
        base_recommendations = [
            "Conduct rapid shelter assessments in priority locations",
            "Establish supply chains for weather-resistant materials",
            "Implement site planning standards for new settlements",
            "Coordinate with Protection cluster on safety/privacy concerns"
        ]

        if location:
            base_recommendations.append(f"Deploy mobile teams to {location} for immediate assessment")

        if "winter" in query.lower() or "seasonal" in query.lower():
            base_recommendations.append("Prioritize winterization materials before cold season")

        return base_recommendations