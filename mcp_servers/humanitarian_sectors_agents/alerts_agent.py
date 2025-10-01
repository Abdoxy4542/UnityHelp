"""
Alerts Agent - Crisis Notification & Escalation Management
Receives inputs from Assessment and Sectoral Agents, prioritizes alerts based on severity
and population impact, generates crisis notifications with recommended actions
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain.schema import BaseMessage
import json
from datetime import datetime, timedelta
from enum import Enum

from .base_humanitarian_agent import BaseHumanitarianAgent, HumanitarianRequest, HumanitarianResponse


class AlertSeverity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    WATCH = "WATCH"


class AlertPrioritizationTool(BaseTool):
    name = "alert_prioritization"
    description = "Prioritize humanitarian alerts based on severity, population impact, and urgency in Sudan"

    def _run(self, alert_data: Dict[str, Any], population_affected: int = 0) -> str:
        # Alert scoring matrix
        severity_scores = {
            "CRITICAL": 5.0,
            "HIGH": 4.0,
            "MEDIUM": 3.0,
            "LOW": 2.0,
            "WATCH": 1.0
        }

        # Population impact multipliers
        population_multipliers = {
            "massive": 2.0,      # >50,000 people
            "large": 1.5,        # 10,000-50,000
            "significant": 1.2,  # 5,000-10,000
            "moderate": 1.0,     # 1,000-5,000
            "small": 0.8         # <1,000
        }

        # Sector urgency weights
        sector_weights = {
            "Protection": 1.8,
            "Health": 1.7,
            "Food Security": 1.6,
            "WASH": 1.5,
            "Nutrition": 1.4,
            "Shelter": 1.3,
            "Education": 1.1,
            "Logistics": 1.2,
            "CCCM": 1.3,
            "Early Recovery": 1.0,
            "ETC": 1.1
        }

        # Extract alert details
        severity = alert_data.get("severity", "MEDIUM")
        sector = alert_data.get("sector", "General")
        alert_type = alert_data.get("type", "general")
        location = alert_data.get("location", "Unknown")

        # Calculate population impact category
        if population_affected > 50000:
            pop_category = "massive"
        elif population_affected > 10000:
            pop_category = "large"
        elif population_affected > 5000:
            pop_category = "significant"
        elif population_affected > 1000:
            pop_category = "moderate"
        else:
            pop_category = "small"

        # Calculate priority score
        base_score = severity_scores.get(severity, 3.0)
        population_factor = population_multipliers.get(pop_category, 1.0)
        sector_factor = sector_weights.get(sector, 1.0)

        # Time-sensitive adjustments
        time_factors = {
            "disease_outbreak": 1.5,
            "mass_displacement": 1.4,
            "security_incident": 1.3,
            "natural_disaster": 1.2,
            "service_disruption": 1.1
        }
        time_factor = time_factors.get(alert_type, 1.0)

        priority_score = base_score * population_factor * sector_factor * time_factor

        # Determine final priority level
        if priority_score >= 8.0:
            priority_level = "IMMEDIATE ACTION REQUIRED"
            response_timeframe = "Within 2 hours"
            escalation_level = "Emergency Response Team + UN Humanitarian Coordinator"
        elif priority_score >= 6.0:
            priority_level = "URGENT RESPONSE NEEDED"
            response_timeframe = "Within 6 hours"
            escalation_level = "Cluster Coordinators + OCHA"
        elif priority_score >= 4.0:
            priority_level = "HIGH PRIORITY"
            response_timeframe = "Within 24 hours"
            escalation_level = "Sector leads + Field coordinators"
        elif priority_score >= 2.5:
            priority_level = "MODERATE PRIORITY"
            response_timeframe = "Within 72 hours"
            escalation_level = "Field teams + Implementing partners"
        else:
            priority_level = "ROUTINE MONITORING"
            response_timeframe = "Within 1 week"
            escalation_level = "Regular reporting channels"

        return f"Alert Prioritization Analysis - {location}:\n\n" + \
               f"Alert Type: {alert_type.replace('_', ' ').title()}\n" + \
               f"Sector: {sector}\n" + \
               f"Severity: {severity}\n" + \
               f"Population Affected: {population_affected:,} ({pop_category} impact)\n" + \
               f"Priority Score: {priority_score:.2f}/10.0\n\n" + \
               f"PRIORITY LEVEL: {priority_level}\n" + \
               f"Response Timeframe: {response_timeframe}\n" + \
               f"Escalation Level: {escalation_level}\n\n" + \
               f"Calculation Factors:\n" + \
               f"- Base severity score: {base_score}\n" + \
               f"- Population multiplier: {population_factor}x\n" + \
               f"- Sector weight: {sector_factor}x\n" + \
               f"- Time sensitivity: {time_factor}x"


class CrisisNotificationTool(BaseTool):
    name = "crisis_notification_generator"
    description = "Generate crisis notifications with recommended actions for Sudan humanitarian response"

    def _run(self, alert_type: str, severity: str, location: str, affected_population: int = 0) -> str:
        # Crisis notification templates
        notification_templates = {
            "disease_outbreak": {
                "title_template": "{severity} Disease Outbreak Alert - {location}",
                "immediate_actions": [
                    "Activate health emergency response protocols",
                    "Deploy rapid response medical teams",
                    "Implement isolation and contact tracing measures",
                    "Coordinate with WASH cluster for sanitation response",
                    "Alert WHO and health authorities"
                ],
                "required_resources": ["Medical supplies", "Isolation facilities", "Health workers", "PPE", "Laboratory support"],
                "coordination_needs": ["Health", "WASH", "Protection", "CCCM", "ETC"]
            },
            "mass_displacement": {
                "title_template": "{severity} Mass Displacement Alert - {location}",
                "immediate_actions": [
                    "Activate emergency shelter and NFI response",
                    "Conduct rapid needs assessments",
                    "Establish reception and registration points",
                    "Coordinate with Protection cluster for screening",
                    "Alert CCCM for site management support"
                ],
                "required_resources": ["Emergency shelter", "NFI kits", "Registration materials", "Transport", "Site management"],
                "coordination_needs": ["CCCM", "Protection", "Shelter", "WASH", "Health"]
            },
            "food_crisis": {
                "title_template": "{severity} Food Security Crisis - {location}",
                "immediate_actions": [
                    "Scale up emergency food distributions",
                    "Conduct rapid food security assessments",
                    "Activate nutrition screening programs",
                    "Coordinate with Logistics cluster for supply delivery",
                    "Alert WFP and food security partners"
                ],
                "required_resources": ["Emergency food rations", "Nutrition supplies", "Transport capacity", "Distribution sites"],
                "coordination_needs": ["Food Security", "Nutrition", "Logistics", "CCCM"]
            },
            "protection_incident": {
                "title_template": "{severity} Protection Crisis Alert - {location}",
                "immediate_actions": [
                    "Deploy protection rapid response teams",
                    "Activate GBV and child protection services",
                    "Coordinate with local authorities and security",
                    "Establish safe spaces and protection monitoring",
                    "Alert UNHCR and protection partners"
                ],
                "required_resources": ["Protection specialists", "Safe spaces", "Psychosocial support", "Legal assistance"],
                "coordination_needs": ["Protection", "Health", "CCCM", "Education"]
            },
            "service_disruption": {
                "title_template": "{severity} Critical Service Disruption - {location}",
                "immediate_actions": [
                    "Assess scope and impact of service disruption",
                    "Activate backup service delivery mechanisms",
                    "Coordinate with affected sector clusters",
                    "Implement emergency service restoration",
                    "Update beneficiary communications"
                ],
                "required_resources": ["Backup equipment", "Alternative facilities", "Emergency supplies", "Technical support"],
                "coordination_needs": ["All relevant sectors", "ETC", "Logistics"]
            }
        }

        if alert_type in notification_templates:
            template = notification_templates[alert_type]
            title = template["title_template"].format(severity=severity, location=location)

            # Generate notification message
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

            notification = f"HUMANITARIAN CRISIS NOTIFICATION\n" + \
                          f"{'='*60}\n\n" + \
                          f"ALERT: {title}\n" + \
                          f"Timestamp: {timestamp}\n" + \
                          f"Location: {location}, Sudan\n" + \
                          f"Estimated Affected Population: {affected_population:,}\n" + \
                          f"Severity Level: {severity}\n\n" + \
                          f"IMMEDIATE ACTIONS REQUIRED:\n"

            for i, action in enumerate(template["immediate_actions"], 1):
                notification += f"{i}. {action}\n"

            notification += f"\nREQUIRED RESOURCES:\n"
            for resource in template["required_resources"]:
                notification += f"- {resource}\n"

            notification += f"\nCOORDINATION REQUIREMENTS:\n"
            notification += f"Primary clusters: {', '.join(template['coordination_needs'])}\n"

            notification += f"\nREPORTING REQUIREMENTS:\n"
            notification += f"- Immediate: Situation report within 2 hours\n"
            notification += f"- Regular: Daily updates until situation stabilized\n"
            notification += f"- Escalation: Inform UN Humanitarian Coordinator if no response within timeframe\n"

            return notification

        return f"Crisis notification generated for {alert_type} in {location}: {severity} level alert"


class AlertEscalationTool(BaseTool):
    name = "alert_escalation_workflow"
    description = "Manage alert escalation workflows and notifications in Sudan humanitarian response"

    def _run(self, alert_id: str, current_level: int, escalation_reason: str) -> str:
        # Escalation matrix
        escalation_levels = {
            1: {
                "level_name": "Field Level",
                "recipients": ["Site managers", "Implementing partners", "Field coordinators"],
                "response_time": "2-6 hours",
                "authority": "Local program adjustments"
            },
            2: {
                "level_name": "Area Coordination",
                "recipients": ["Area coordinators", "Sector leads", "State authorities"],
                "response_time": "6-24 hours",
                "authority": "Resource reallocation within areas"
            },
            3: {
                "level_name": "National Cluster",
                "recipients": ["Cluster coordinators", "OCHA", "UN agencies"],
                "response_time": "24-48 hours",
                "authority": "National resource mobilization"
            },
            4: {
                "level_name": "Humanitarian Country Team",
                "recipients": ["Humanitarian Coordinator", "Agency country reps", "Donor representatives"],
                "response_time": "48-72 hours",
                "authority": "Strategic response decisions"
            },
            5: {
                "level_name": "Regional/Global",
                "recipients": ["Regional directors", "Global clusters", "Emergency response funds"],
                "response_time": "72+ hours",
                "authority": "Global resource mobilization"
            }
        }

        # Alert escalation history simulation
        escalation_history = {
            "SUD_001": [
                {"timestamp": "2024-01-15 08:00", "level": 1, "action": "Initial field response", "status": "Insufficient resources"},
                {"timestamp": "2024-01-15 14:00", "level": 2, "action": "Area coordination activated", "status": "Partial response"},
                {"timestamp": "2024-01-16 09:00", "level": 3, "action": "National cluster engaged", "status": "In progress"}
            ]
        }

        if current_level in escalation_levels:
            level_info = escalation_levels[current_level]

            escalation_msg = f"Alert Escalation Workflow - Alert ID: {alert_id}\n\n" + \
                           f"ESCALATION TO LEVEL {current_level}: {level_info['level_name']}\n" + \
                           f"Escalation Reason: {escalation_reason}\n" + \
                           f"Expected Response Time: {level_info['response_time']}\n" + \
                           f"Decision Authority: {level_info['authority']}\n\n" + \
                           f"NOTIFICATION RECIPIENTS:\n"

            for recipient in level_info["recipients"]:
                escalation_msg += f"- {recipient}\n"

            escalation_msg += f"\nESCALATION TRIGGERS FOR NEXT LEVEL:\n"
            if current_level < 5:
                escalation_msg += f"- No adequate response within {level_info['response_time']}\n"
                escalation_msg += f"- Situation deterioration beyond current authority level\n"
                escalation_msg += f"- Resource requirements exceed current level capacity\n"
                escalation_msg += f"- Multi-sector coordination needs beyond current scope\n"
            else:
                escalation_msg += f"- Maximum escalation level reached\n"

            # Add escalation history if available
            if alert_id in escalation_history:
                escalation_msg += f"\nESCALATION HISTORY:\n"
                for event in escalation_history[alert_id]:
                    escalation_msg += f"- {event['timestamp']}: Level {event['level']} - {event['action']} ({event['status']})\n"

            escalation_msg += f"\nNEXT STEPS:\n"
            escalation_msg += f"1. Notify all level {current_level} recipients immediately\n"
            escalation_msg += f"2. Set response deadline based on timeframe\n"
            escalation_msg += f"3. Monitor response adequacy\n"
            escalation_msg += f"4. Prepare for level {min(current_level + 1, 5)} escalation if needed\n"

            return escalation_msg

        return f"Managing escalation for Alert {alert_id} to level {current_level}: {escalation_reason}"


class AlertsAgent(BaseHumanitarianAgent):
    def __init__(self):
        super().__init__(
            sector="Crisis Alerts & Emergency Coordination",
            lead_agencies=["OCHA", "UN Humanitarian Coordinator"],
            sudan_context={
                "alert_categories": [
                    "Disease outbreaks", "Mass displacement events", "Protection incidents",
                    "Food security crises", "Service disruptions", "Natural disasters",
                    "Security incidents", "Supply chain failures"
                ],
                "monitoring_scope": "25.6 million people in need across 18 states",
                "response_network": "450+ humanitarian partners, 2,800+ sites monitored",
                "escalation_protocols": "5-level escalation from field to global response",
                "alert_sources": [
                    "Assessment Agent findings", "Sectoral cluster reports",
                    "Field situation reports", "Government notifications",
                    "Community feedback", "Media monitoring"
                ],
                "response_timeframes": {
                    "CRITICAL": "Within 2 hours",
                    "HIGH": "Within 6 hours",
                    "MEDIUM": "Within 24 hours",
                    "LOW": "Within 72 hours"
                },
                "challenges": [
                    "Overwhelming number of simultaneous crises",
                    "Limited communication infrastructure",
                    "Coordination complexity across 450+ partners",
                    "Resource scarcity affecting response capacity"
                ]
            }
        )

        # Add alert-specific tools
        self.tools.extend([
            AlertPrioritizationTool(),
            CrisisNotificationTool(),
            AlertEscalationTool()
        ])

    def process_request(self, request: HumanitarianRequest) -> HumanitarianResponse:
        """Process alert-related requests for Sudan humanitarian crisis"""

        query_lower = request.query.lower()
        location = self._extract_location(request.query)

        # Extract alert parameters
        alert_data = self._extract_alert_parameters(request)

        # Determine response based on query type
        if any(word in query_lower for word in ["prioritize", "priority", "severity", "urgent"]):
            population_affected = self._extract_population_number(request.query)
            tool_result = self.tools[0]._run(alert_data, population_affected)
            analysis = f"Alert prioritization analysis shows {alert_data.get('severity', 'MEDIUM')} level crisis requiring coordinated response"

        elif any(word in query_lower for word in ["notification", "crisis", "outbreak", "displacement"]):
            alert_type = self._determine_alert_type(query_lower)
            population_affected = self._extract_population_number(request.query)
            tool_result = self.tools[1]._run(alert_type, alert_data.get('severity', 'HIGH'), location or "Multiple locations", population_affected)
            analysis = f"Crisis notification generated for {alert_type.replace('_', ' ')} requiring immediate multi-sector response"

        elif any(word in query_lower for word in ["escalate", "escalation", "no response", "insufficient"]):
            alert_id = f"SUD_{datetime.now().strftime('%m%d_%H%M')}"
            current_level = self._extract_escalation_level(request.query)
            escalation_reason = self._extract_escalation_reason(query_lower)
            tool_result = self.tools[2]._run(alert_id, current_level, escalation_reason)
            analysis = f"Alert escalation workflow activated due to {escalation_reason}"

        else:
            # General alert management overview
            tool_result = "Sudan Alert System Overview: Multi-level crisis monitoring, 5-stage escalation, 450+ partners coordinated"
            analysis = "Alert management system monitoring 25.6 million people across multiple crisis dimensions"

        # Generate alert-specific recommendations
        recommendations = self._generate_alert_recommendations(request.query, alert_data)

        return HumanitarianResponse(
            sector=self.sector,
            analysis=analysis,
            data=tool_result,
            recommendations=recommendations,
            priority_level=alert_data.get('severity', 'MEDIUM'),
            locations=[location] if location else self._get_priority_locations(alert_data),
            metadata={
                "alert_type": alert_data.get('type', 'general'),
                "escalation_ready": True,
                "multi_sector_coordination": True
            }
        )

    def _extract_alert_parameters(self, request: HumanitarianRequest) -> Dict[str, Any]:
        """Extract alert parameters from request"""
        query_lower = request.query.lower()

        # Determine severity
        if any(word in query_lower for word in ["critical", "crisis", "emergency"]):
            severity = "CRITICAL"
        elif any(word in query_lower for word in ["high", "urgent", "serious"]):
            severity = "HIGH"
        elif any(word in query_lower for word in ["medium", "moderate"]):
            severity = "MEDIUM"
        else:
            severity = request.priority or "MEDIUM"

        # Determine alert type
        alert_type = self._determine_alert_type(query_lower)

        # Extract sector if mentioned
        sectors = ["protection", "health", "wash", "food", "nutrition", "shelter", "education"]
        sector = "General"
        for s in sectors:
            if s in query_lower:
                sector = s.title()
                break

        return {
            "severity": severity,
            "type": alert_type,
            "sector": sector,
            "location": self._extract_location(request.query) or "Multiple locations"
        }

    def _determine_alert_type(self, query: str) -> str:
        """Determine alert type from query"""
        alert_types = {
            "disease_outbreak": ["disease", "outbreak", "cholera", "measles", "covid", "epidemic"],
            "mass_displacement": ["displacement", "flee", "refugees", "idp", "evacuation"],
            "food_crisis": ["food", "famine", "hunger", "malnutrition", "starvation"],
            "protection_incident": ["gbv", "violence", "attack", "safety", "protection"],
            "service_disruption": ["service", "disruption", "closure", "breakdown", "failure"]
        }

        for alert_type, keywords in alert_types.items():
            if any(keyword in query for keyword in keywords):
                return alert_type

        return "general_emergency"

    def _extract_population_number(self, query: str) -> int:
        """Extract population numbers from query"""
        import re

        # Look for number patterns
        numbers = re.findall(r'(\d+(?:,\d+)?)\s*(?:people|persons|individuals|families)', query.lower())
        if numbers:
            return int(numbers[0].replace(',', ''))

        # Default estimates based on context
        if "massive" in query.lower():
            return 75000
        elif "large" in query.lower():
            return 25000
        elif "significant" in query.lower():
            return 8000
        else:
            return 5000

    def _extract_escalation_level(self, query: str) -> int:
        """Extract escalation level from query"""
        if "field" in query.lower():
            return 1
        elif "area" in query.lower() or "regional" in query.lower():
            return 2
        elif "national" in query.lower() or "cluster" in query.lower():
            return 3
        elif "country" in query.lower() or "humanitarian coordinator" in query.lower():
            return 4
        elif "global" in query.lower():
            return 5
        else:
            return 2  # Default to area level

    def _extract_escalation_reason(self, query: str) -> str:
        """Extract escalation reason from query"""
        reasons = {
            "no response": "Inadequate response from current level",
            "insufficient": "Insufficient resources at current level",
            "deteriorating": "Situation deteriorating beyond current capacity",
            "capacity": "Resource requirements exceed current authority",
            "coordination": "Multi-sector coordination needs beyond scope"
        }

        for key, reason in reasons.items():
            if key in query:
                return reason

        return "Situation requires higher level intervention"

    def _get_priority_locations(self, alert_data: Dict[str, Any]) -> List[str]:
        """Get priority locations based on alert data"""
        alert_type = alert_data.get('type', 'general')

        priority_maps = {
            "disease_outbreak": ["El Geneina", "Nyala", "Kassala"],
            "mass_displacement": ["Nyala", "El Geneina", "Zalingei"],
            "food_crisis": ["North Darfur", "South Darfur", "Blue Nile"],
            "protection_incident": ["El Geneina", "Nyala", "Geneina"]
        }

        return priority_maps.get(alert_type, ["Nyala", "El Geneina", "Kassala"])

    def _generate_alert_recommendations(self, query: str, alert_data: Dict[str, Any]) -> List[str]:
        """Generate alert-specific recommendations"""
        base_recommendations = [
            "Activate appropriate emergency response protocols immediately",
            "Coordinate with all relevant sector clusters for integrated response",
            "Establish real-time monitoring and reporting systems",
            "Ensure adequate resource mobilization for sustained response"
        ]

        severity = alert_data.get('severity', 'MEDIUM')
        alert_type = alert_data.get('type', 'general')

        if severity in ['CRITICAL', 'HIGH']:
            base_recommendations.append("Consider activating Emergency Response Fund allocations")

        if alert_type == "disease_outbreak":
            base_recommendations.append("Implement disease outbreak containment protocols immediately")

        if alert_type == "mass_displacement":
            base_recommendations.append("Activate emergency shelter and protection response mechanisms")

        if "escalation" in query.lower():
            base_recommendations.append("Prepare detailed situation report for higher-level decision makers")

        return base_recommendations