"""
ETC (Emergency Telecommunications Cluster) Agent - WFP Lead
Handles emergency telecommunications, connectivity, and information management
"""

from typing import Dict, List, Any
from langchain.tools import BaseTool
from langchain.schema import BaseMessage
import json

from .base_humanitarian_agent import BaseHumanitarianAgent, HumanitarianRequest, HumanitarianResponse


class ConnectivityAssessmentTool(BaseTool):
    name = "connectivity_assessment"
    description = "Assess telecommunications and internet connectivity in Sudan humanitarian operations"

    def _run(self, location: str, service_type: str = "all_services") -> str:
        connectivity_data = {
            "Nyala": {
                "mobile_network": {
                    "coverage": "Partial - 60% area coverage",
                    "operators": ["MTN", "Sudani", "Zain"],
                    "signal_quality": "Poor to moderate",
                    "data_speeds": "2G/3G intermittent"
                },
                "internet": {
                    "availability": "Limited",
                    "bandwidth": "Low - shared connections",
                    "stability": "Frequent outages",
                    "cost": "High - $80/month for basic"
                },
                "radio_comms": {
                    "vhf_coverage": "Good for local operations",
                    "hf_capability": "Available for long distance",
                    "repeater_status": "2 operational, 1 damaged",
                    "interoperability": "Limited between agencies"
                }
            },
            "El_Geneina": {
                "mobile_network": {
                    "coverage": "Very limited - 25% area coverage",
                    "operators": ["MTN sporadic", "Others not operational"],
                    "signal_quality": "Very poor",
                    "data_speeds": "2G only when available"
                },
                "internet": {
                    "availability": "Extremely limited",
                    "bandwidth": "Dial-up speeds when working",
                    "stability": "Daily outages",
                    "cost": "Very high - $150/month basic"
                },
                "radio_comms": {
                    "vhf_coverage": "Fair - equipment damaged",
                    "hf_capability": "Essential backup option",
                    "repeater_status": "1 operational, 2 damaged",
                    "interoperability": "Poor coordination"
                }
            },
            "Kassala": {
                "mobile_network": {
                    "coverage": "Good - 80% area coverage",
                    "operators": ["MTN", "Sudani", "Zain"],
                    "signal_quality": "Moderate to good",
                    "data_speeds": "3G/4G in urban areas"
                },
                "internet": {
                    "availability": "Available",
                    "bandwidth": "Moderate - adequate for operations",
                    "stability": "Generally stable",
                    "cost": "Moderate - $60/month basic"
                },
                "radio_comms": {
                    "vhf_coverage": "Excellent coverage",
                    "hf_capability": "Full capability maintained",
                    "repeater_status": "All 3 repeaters operational",
                    "interoperability": "Good inter-agency coordination"
                }
            }
        }

        if location in connectivity_data:
            data = connectivity_data[location]

            if service_type == "all_services":
                result = f"Connectivity Assessment - {location}:\n\n"
                for service, details in data.items():
                    result += f"{service.replace('_', ' ').title()}:\n"
                    for key, value in details.items():
                        result += f"  {key.replace('_', ' ').title()}: {value}\n"
                    result += "\n"
                return result.strip()

            elif service_type in data:
                service_data = data[service_type]
                return f"{service_type.replace('_', ' ').title()} Assessment - {location}:\n" + \
                       '\n'.join([f"{key.replace('_', ' ').title()}: {value}" for key, value in service_data.items()])

        return f"Assessing {service_type.replace('_', ' ')} connectivity in {location}"


class EmergencyCommsTool(BaseTool):
    name = "emergency_communications"
    description = "Deploy and manage emergency communications systems in Sudan"

    def _run(self, deployment_type: str, location: str, urgency: str = "standard") -> str:
        deployment_options = {
            "satellite_internet": {
                "equipment": ["VSAT terminal", "Generator", "UPS backup"],
                "capacity": "2-10 Mbps shared",
                "setup_time": "4-8 hours",
                "monthly_cost": 1200,
                "coverage": "Single location, 50m radius"
            },
            "mobile_repeater": {
                "equipment": ["VHF/UHF repeater", "Antenna system", "Solar power"],
                "capacity": "20-30 simultaneous users",
                "setup_time": "1-2 days",
                "monthly_cost": 400,
                "coverage": "15-25km radius"
            },
            "emergency_network": {
                "equipment": ["Mesh network nodes", "Portable devices", "Charging station"],
                "capacity": "50+ devices offline messaging",
                "setup_time": "2-4 hours",
                "monthly_cost": 200,
                "coverage": "2-5km mesh network"
            },
            "mobile_bgan": {
                "equipment": ["BGAN terminal", "Laptop", "Cables"],
                "capacity": "384 kbps data/voice",
                "setup_time": "30 minutes",
                "monthly_cost": 800,
                "coverage": "Mobile, anywhere with satellite view"
            }
        }

        urgency_factors = {
            "emergency": {"multiplier": 2.0, "timeline": "24 hours"},
            "urgent": {"multiplier": 1.5, "timeline": "48-72 hours"},
            "standard": {"multiplier": 1.0, "timeline": "1-2 weeks"}
        }

        if deployment_type in deployment_options:
            option = deployment_options[deployment_type]
            urgency_info = urgency_factors.get(urgency, urgency_factors["standard"])
            adjusted_cost = int(option['monthly_cost'] * urgency_info['multiplier'])

            return f"Emergency Communications Deployment - {location}:\n" + \
                   f"System: {deployment_type.replace('_', ' ').title()}\n" + \
                   f"Equipment: {', '.join(option['equipment'])}\n" + \
                   f"Capacity: {option['capacity']}\n" + \
                   f"Setup time: {option['setup_time']}\n" + \
                   f"Coverage area: {option['coverage']}\n" + \
                   f"Urgency: {urgency.title()}\n" + \
                   f"Deployment timeline: {urgency_info['timeline']}\n" + \
                   f"Monthly cost: ${adjusted_cost:,}"

        return f"Deploying {deployment_type.replace('_', ' ')} system in {location} with {urgency} priority"


class DataManagementTool(BaseTool):
    name = "data_management"
    description = "Manage humanitarian data collection and information systems in Sudan"

    def _run(self, data_type: str, operation: str = "setup") -> str:
        data_systems = {
            "activity_info": {
                "purpose": "Humanitarian activity tracking and 4W (Who, What, Where, When)",
                "users": "All humanitarian partners",
                "features": ["Real-time reporting", "Geographic mapping", "Partner coordination"],
                "connectivity_needs": "Moderate - periodic sync required",
                "training_required": "2-day workshop for focal points"
            },
            "kobo_collect": {
                "purpose": "Mobile data collection and surveys",
                "users": "Field teams and enumerators",
                "features": ["Offline capability", "GPS integration", "Photo capture"],
                "connectivity_needs": "Low - sync when connection available",
                "training_required": "1-day hands-on training"
            },
            "displacement_tracking": {
                "purpose": "IDP population monitoring and movement tracking",
                "users": "CCCM and Protection partners",
                "features": ["Population dashboard", "Trend analysis", "Alert system"],
                "connectivity_needs": "High - real-time updates preferred",
                "training_required": "Half-day orientation for site managers"
            },
            "inter_agency_sharing": {
                "purpose": "Secure document sharing and collaboration",
                "users": "All humanitarian partners",
                "features": ["Document repository", "Access controls", "Version management"],
                "connectivity_needs": "Moderate - regular uploads/downloads",
                "training_required": "1-hour orientation session"
            }
        }

        operations = {
            "setup": "System installation and initial configuration",
            "training": "User training and capacity building",
            "maintenance": "Ongoing support and system updates",
            "troubleshooting": "Issue resolution and technical support"
        }

        if data_type in data_systems:
            system = data_systems[data_type]
            operation_desc = operations.get(operation, operation)

            return f"Data Management - {data_type.replace('_', ' ').title()}:\n" + \
                   f"Operation: {operation_desc}\n" + \
                   f"Purpose: {system['purpose']}\n" + \
                   f"Target users: {system['users']}\n" + \
                   f"Key features: {', '.join(system['features'])}\n" + \
                   f"Connectivity needs: {system['connectivity_needs']}\n" + \
                   f"Training requirements: {system['training_required']}"

        return f"Managing {data_type.replace('_', ' ')} system - {operation} operation"


class ETCAgent(BaseHumanitarianAgent):
    def __init__(self):
        super().__init__(
            sector="ETC (Emergency Telecommunications Cluster)",
            lead_agencies=["WFP"],
            sudan_context={
                "connectivity_challenges": "Widespread telecommunications infrastructure damage",
                "operational_sites": "Over 50 humanitarian locations requiring connectivity",
                "priority_services": ["Internet access", "VHF/UHF radio", "Data management systems"],
                "key_locations": ["Khartoum", "Nyala", "El Geneina", "Kassala", "Port Sudan"],
                "challenges": [
                    "Damaged telecommunications infrastructure",
                    "High costs of satellite communications",
                    "Limited technical expertise in field locations",
                    "Security constraints affecting equipment deployment"
                ],
                "critical_functions": ["Inter-agency coordination", "Security communications", "Data collection", "Information sharing"]
            }
        )

        # Add ETC-specific tools
        self.tools.extend([
            ConnectivityAssessmentTool(),
            EmergencyCommsTool(),
            DataManagementTool()
        ])

    def process_request(self, request: HumanitarianRequest) -> HumanitarianResponse:
        """Process ETC-related requests for Sudan context"""

        # Extract key information
        query_lower = request.query.lower()
        location = self._extract_location(request.query)

        # Determine response based on query type
        if any(word in query_lower for word in ["connectivity", "internet", "network", "mobile"]):
            service_type = "mobile_network" if "mobile" in query_lower else \
                         "internet" if "internet" in query_lower else \
                         "radio_comms" if "radio" in query_lower else "all_services"
            tool_result = self.tools[0]._run(location or "Nyala", service_type)
            analysis = f"Connectivity assessment shows critical gaps in {location or 'humanitarian locations'}"

        elif any(word in query_lower for word in ["deploy", "emergency", "communication", "equipment"]):
            deployment_type = "satellite_internet" if "satellite" in query_lower or "internet" in query_lower else \
                            "mobile_repeater" if "radio" in query_lower or "repeater" in query_lower else \
                            "mobile_bgan" if "mobile" in query_lower or "bgan" in query_lower else "emergency_network"
            urgency = "emergency" if "emergency" in query_lower or "urgent" in query_lower else "standard"
            tool_result = self.tools[1]._run(deployment_type, location or "Field location", urgency)
            analysis = "Emergency communications deployment required to maintain operations"

        elif any(word in query_lower for word in ["data", "information", "system", "kobo", "activity"]):
            data_type = "kobo_collect" if "kobo" in query_lower else \
                       "activity_info" if "activity" in query_lower or "4w" in query_lower else \
                       "displacement_tracking" if "displacement" in query_lower or "idf" in query_lower else \
                       "inter_agency_sharing"
            operation = "training" if "train" in query_lower else \
                       "maintenance" if "maintain" in query_lower or "support" in query_lower else "setup"
            tool_result = self.tools[2]._run(data_type, operation)
            analysis = "Data management systems essential for coordinated humanitarian response"

        else:
            # General ETC information
            tool_result = "Sudan ETC Overview: Widespread telecom damage, 50+ sites need connectivity, high satellite costs"
            analysis = "ETC services critical for humanitarian coordination and safety"

        # Generate recommendations
        recommendations = self._generate_etc_recommendations(request.query, location)

        return HumanitarianResponse(
            sector=self.sector,
            analysis=analysis,
            data=tool_result,
            recommendations=recommendations,
            priority_level="HIGH",
            locations=[location] if location else ["Nyala", "El Geneina", "Kassala"]
        )

    def _generate_etc_recommendations(self, query: str, location: str = None) -> List[str]:
        """Generate ETC-specific recommendations"""
        base_recommendations = [
            "Deploy satellite internet at major humanitarian hubs",
            "Establish inter-agency VHF radio networks",
            "Implement offline-capable data collection systems",
            "Provide technical training for field communications focal points"
        ]

        if location:
            base_recommendations.append(f"Conduct comprehensive connectivity assessment in {location}")

        if "emergency" in query.lower() or "urgent" in query.lower():
            base_recommendations.append("Prioritize rapid deployment of portable communication systems")

        if "security" in query.lower():
            base_recommendations.append("Ensure secure communications for safety and security coordination")

        if "data" in query.lower() or "information" in query.lower():
            base_recommendations.append("Standardize data collection tools across humanitarian partners")

        if "training" in query.lower():
            base_recommendations.append("Scale up technical training for local communications staff")

        return base_recommendations