"""
Nutrition Cluster Agent - UNICEF Lead
Handles malnutrition prevention, treatment, and nutrition surveillance
"""

from typing import Dict, List, Any
from langchain.tools import BaseTool
from langchain.schema import BaseMessage
import json

from .base_humanitarian_agent import BaseHumanitarianAgent, HumanitarianRequest, HumanitarianResponse


class NutritionScreeningTool(BaseTool):
    name = "nutrition_screening"
    description = "Conduct nutrition screening and assessment in Sudan"

    def _run(self, location: str, age_group: str = "children_under5") -> str:
        nutrition_data = {
            "Nyala IDP Settlement": {
                "children_under5": {
                    "sam_cases": 450,  # Severe Acute Malnutrition
                    "mam_cases": 820,  # Moderate Acute Malnutrition
                    "screening_coverage": "65%",
                    "prevalence_gam": "18.5%"  # Global Acute Malnutrition
                },
                "pregnant_women": {
                    "acute_malnutrition": 180,
                    "anemia_cases": 340,
                    "screening_coverage": "45%"
                }
            },
            "El Geneina Emergency Camp": {
                "children_under5": {
                    "sam_cases": 320,
                    "mam_cases": 580,
                    "screening_coverage": "70%",
                    "prevalence_gam": "16.2%"
                },
                "pregnant_women": {
                    "acute_malnutrition": 125,
                    "anemia_cases": 220,
                    "screening_coverage": "50%"
                }
            },
            "Kassala Reception Center": {
                "children_under5": {
                    "sam_cases": 180,
                    "mam_cases": 290,
                    "screening_coverage": "80%",
                    "prevalence_gam": "14.8%"
                },
                "pregnant_women": {
                    "acute_malnutrition": 75,
                    "anemia_cases": 140,
                    "screening_coverage": "60%"
                }
            }
        }

        if location in nutrition_data and age_group in nutrition_data[location]:
            data = nutrition_data[location][age_group]
            if age_group == "children_under5":
                return f"Nutrition Screening - {location} (Children U5):\n" + \
                       f"SAM Cases: {data['sam_cases']}\n" + \
                       f"MAM Cases: {data['mam_cases']}\n" + \
                       f"GAM Prevalence: {data['prevalence_gam']} (Emergency threshold: >15%)\n" + \
                       f"Screening Coverage: {data['screening_coverage']}"
            else:
                return f"Nutrition Screening - {location} (Pregnant Women):\n" + \
                       f"Acute Malnutrition: {data['acute_malnutrition']}\n" + \
                       f"Anemia Cases: {data['anemia_cases']}\n" + \
                       f"Screening Coverage: {data['screening_coverage']}"

        return f"Conducting nutrition screening in {location} for {age_group.replace('_', ' ')}"


class NutritionTreatmentTool(BaseTool):
    name = "nutrition_treatment"
    description = "Plan and track nutrition treatment programs in Sudan"

    def _run(self, treatment_type: str, cases: int, location: str) -> str:
        treatment_protocols = {
            "sam_treatment": {
                "program": "Outpatient Therapeutic Program (OTP)",
                "supplies": ["RUTF sachets", "Amoxicillin", "Vitamin A"],
                "duration_weeks": 6-8,
                "cure_rate_target": "75%",
                "cost_per_child": 200
            },
            "mam_treatment": {
                "program": "Targeted Supplementary Feeding Program (TSFP)",
                "supplies": ["Super Cereal Plus", "Fortified oil"],
                "duration_weeks": 10-12,
                "cure_rate_target": "70%",
                "cost_per_child": 120
            },
            "iycf_support": {
                "program": "Infant and Young Child Feeding Support",
                "supplies": ["Counseling materials", "Growth monitoring tools"],
                "duration_weeks": "Ongoing",
                "coverage_target": "80%",
                "cost_per_beneficiary": 50
            }
        }

        if treatment_type in treatment_protocols:
            protocol = treatment_protocols[treatment_type]
            total_cost = cases * protocol['cost_per_child' if 'cost_per_child' in protocol else 'cost_per_beneficiary']

            return f"Nutrition Treatment Plan - {location}:\n" + \
                   f"Program: {protocol['program']}\n" + \
                   f"Cases/Beneficiaries: {cases:,}\n" + \
                   f"Key supplies: {', '.join(protocol['supplies'])}\n" + \
                   f"Treatment duration: {protocol['duration_weeks']} weeks\n" + \
                   f"Target outcome: {protocol.get('cure_rate_target', protocol.get('coverage_target'))}\n" + \
                   f"Estimated cost: ${total_cost:,}"

        return f"Planning {treatment_type} for {cases:,} cases in {location}"


class NutritionSurveillanceTool(BaseTool):
    name = "nutrition_surveillance"
    description = "Monitor nutrition trends and early warning indicators in Sudan"

    def _run(self, indicator_type: str, timeframe: str = "monthly") -> str:
        surveillance_data = {
            "malnutrition_trends": {
                "sam_admissions": "+15% compared to last month",
                "seasonal_pattern": "Peak expected during lean season (May-September)",
                "geographic_hotspots": ["North Darfur", "South Darfur", "Blue Nile"],
                "alert_level": "HIGH"
            },
            "feeding_practices": {
                "exclusive_breastfeeding": "42% (target: 50%)",
                "complementary_feeding": "65% appropriate practices",
                "dietary_diversity": "3.2 food groups average (target: >4)",
                "alert_level": "MEDIUM"
            },
            "supply_pipeline": {
                "rutf_stock": "3 months remaining",
                "super_cereal_stock": "2 months remaining",
                "therapeutic_milk_stock": "1.5 months remaining",
                "alert_level": "HIGH"
            }
        }

        if indicator_type in surveillance_data:
            data = surveillance_data[indicator_type]
            alert_level = data.pop('alert_level')
            indicators = '\n'.join([f"- {k}: {v}" for k, v in data.items()])

            return f"Nutrition Surveillance ({timeframe}) - {indicator_type.replace('_', ' ').title()}:\n" + \
                   f"{indicators}\n" + \
                   f"Alert Level: {alert_level}"

        return f"Monitoring {indicator_type.replace('_', ' ')} indicators over {timeframe} period"


class NutritionAgent(BaseHumanitarianAgent):
    def __init__(self):
        super().__init__(
            sector="Nutrition",
            lead_agencies=["UNICEF"],
            sudan_context={
                "malnutrition_burden": "2.5 million children under 5 at risk",
                "gam_prevalence": "16.7% (emergency threshold exceeded)",
                "sam_caseload": "650,000 children need treatment",
                "priority_states": ["North Darfur", "South Darfur", "Blue Nile", "White Nile"],
                "challenges": [
                    "Limited access to therapeutic feeding sites",
                    "Supply pipeline disruptions",
                    "Poor infant feeding practices",
                    "Displacement affecting service delivery"
                ],
                "key_programs": ["OTP", "TSFP", "IYCF", "SMART surveys"]
            }
        )

        # Add nutrition-specific tools
        self.tools.extend([
            NutritionScreeningTool(),
            NutritionTreatmentTool(),
            NutritionSurveillanceTool()
        ])

    def process_request(self, request: HumanitarianRequest) -> HumanitarianResponse:
        """Process nutrition-related requests for Sudan context"""

        # Extract key information
        query_lower = request.query.lower()
        location = self._extract_location(request.query)

        # Determine response based on query type
        if any(word in query_lower for word in ["screen", "assess", "prevalence"]):
            age_group = "pregnant_women" if "pregnant" in query_lower or "women" in query_lower else "children_under5"
            tool_result = self.tools[0]._run(location or "Nyala IDP Settlement", age_group)
            analysis = f"Nutrition screening reveals emergency-level malnutrition in {location or 'multiple locations'}"

        elif any(word in query_lower for word in ["treat", "sam", "mam", "therapeutic"]):
            treatment = "sam_treatment" if "sam" in query_lower else "mam_treatment"
            tool_result = self.tools[1]._run(treatment, 500, location or "Multiple sites")
            analysis = "Treatment capacity needs urgent scaling up to meet demand"

        elif any(word in query_lower for word in ["monitor", "surveillance", "trends"]):
            indicator = "malnutrition_trends" if "trend" in query_lower else "supply_pipeline"
            tool_result = self.tools[2]._run(indicator)
            analysis = "Surveillance data indicates deteriorating nutrition situation"

        else:
            # General nutrition information
            tool_result = "Sudan Nutrition Crisis: 2.5M children at risk, 16.7% GAM prevalence, 650K SAM cases need treatment"
            analysis = "Emergency-level malnutrition crisis requiring immediate scale-up"

        # Generate recommendations
        recommendations = self._generate_nutrition_recommendations(request.query, location)

        return HumanitarianResponse(
            sector=self.sector,
            analysis=analysis,
            data=tool_result,
            recommendations=recommendations,
            priority_level="CRITICAL",
            locations=[location] if location else ["North Darfur", "South Darfur", "Blue Nile"]
        )

    def _generate_nutrition_recommendations(self, query: str, location: str = None) -> List[str]:
        """Generate nutrition-specific recommendations"""
        base_recommendations = [
            "Scale up Outpatient Therapeutic Programs (OTP) immediately",
            "Ensure adequate RUTF supply pipeline for next 6 months",
            "Strengthen IYCF counseling and support programs",
            "Coordinate with Food Security cluster on food assistance"
        ]

        if location:
            base_recommendations.append(f"Deploy rapid response team to {location} for assessment")

        if "sam" in query.lower() or "severe" in query.lower():
            base_recommendations.append("Prioritize severe acute malnutrition treatment capacity")

        if "survey" in query.lower() or "data" in query.lower():
            base_recommendations.append("Conduct SMART surveys in high-risk areas")

        return base_recommendations