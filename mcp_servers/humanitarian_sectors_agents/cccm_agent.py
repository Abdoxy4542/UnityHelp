"""
CCCM (Camp Coordination and Camp Management) Agent - UNHCR & IOM Co-Lead
Handles displacement site coordination, management, and governance
"""

from typing import Dict, List, Any
from langchain.tools import BaseTool
from langchain.schema import BaseMessage
import json

from .base_humanitarian_agent import BaseHumanitarianAgent, HumanitarianRequest, HumanitarianResponse


class SiteManagementTool(BaseTool):
    name = "site_management"
    description = "Manage displacement sites and settlements in Sudan"

    def _run(self, site_name: str, management_area: str = "general") -> str:
        site_data = {
            "Nyala_IDP_Settlement": {
                "population": 45000,
                "families": 7500,
                "site_type": "Planned camp",
                "management_structure": "Camp Management Committee established",
                "key_services": ["Registration", "Information management", "Coordination"],
                "challenges": ["Overcrowding", "Limited water access", "Waste management"]
            },
            "El_Geneina_Emergency_Camp": {
                "population": 32000,
                "families": 5300,
                "site_type": "Emergency response site",
                "management_structure": "Temporary coordination team",
                "key_services": ["Emergency registration", "Site planning", "Service mapping"],
                "challenges": ["Site planning", "Service gaps", "Community tensions"]
            },
            "Kassala_Reception_Center": {
                "population": 18000,
                "families": 3000,
                "site_type": "Transit facility",
                "management_structure": "Reception committee active",
                "key_services": ["Reception screening", "Onward movement", "Temporary assistance"],
                "challenges": ["Extended stays", "Limited space", "Documentation issues"]
            }
        }

        management_areas = {
            "governance": "Community leadership, committees, representation",
            "information": "Population data, needs assessment, service mapping",
            "coordination": "Inter-agency coordination, service delivery planning",
            "site_planning": "Layout design, infrastructure planning, expansion"
        }

        if site_name in site_data:
            data = site_data[site_name]
            area_desc = management_areas.get(management_area, "General site management overview")

            return f"Site Management - {site_name.replace('_', ' ')}:\n" + \
                   f"Population: {data['population']:,} ({data['families']:,} families)\n" + \
                   f"Site type: {data['site_type']}\n" + \
                   f"Management structure: {data['management_structure']}\n" + \
                   f"Key services: {', '.join(data['key_services'])}\n" + \
                   f"Main challenges: {', '.join(data['challenges'])}\n" + \
                   f"Focus area: {area_desc}"

        return f"Managing {site_name.replace('_', ' ')} focusing on {management_area}"


class PopulationMonitoringTool(BaseTool):
    name = "population_monitoring"
    description = "Track population movements and demographics in Sudan displacement sites"

    def _run(self, monitoring_type: str, location: str = "multiple_sites") -> str:
        monitoring_data = {
            "arrivals_departures": {
                "weekly_arrivals": 2800,
                "weekly_departures": 450,
                "net_increase": 2350,
                "peak_arrival_days": ["Monday", "Wednesday", "Friday"],
                "common_origins": ["Khartoum suburbs", "Rural Darfur", "Blue Nile"]
            },
            "demographic_profile": {
                "children_under_18": "62%",
                "women": "54%",
                "elderly_over_60": "8%",
                "persons_with_disabilities": "12%",
                "unaccompanied_minors": "3%"
            },
            "vulnerability_mapping": {
                "female_headed_households": "45%",
                "separated_children": "2.8%",
                "chronic_illness": "15%",
                "pregnant_lactating_women": "18%",
                "special_needs_cases": "28%"
            },
            "intention_survey": {
                "remain_current_location": "65%",
                "return_home": "20%",
                "onward_movement": "10%",
                "undecided": "5%"
            }
        }

        if monitoring_type in monitoring_data:
            data = monitoring_data[monitoring_type]

            if monitoring_type == "arrivals_departures":
                return f"Population Movement Monitoring - {location}:\n" + \
                       f"Weekly arrivals: {data['weekly_arrivals']:,}\n" + \
                       f"Weekly departures: {data['weekly_departures']:,}\n" + \
                       f"Net population change: +{data['net_increase']:,}\n" + \
                       f"Peak arrival days: {', '.join(data['peak_arrival_days'])}\n" + \
                       f"Common origins: {', '.join(data['common_origins'])}"

            elif monitoring_type == "demographic_profile":
                return f"Demographic Profile - {location}:\n" + \
                       f"Children under 18: {data['children_under_18']}\n" + \
                       f"Women: {data['women']}\n" + \
                       f"Elderly (60+): {data['elderly_over_60']}\n" + \
                       f"Persons with disabilities: {data['persons_with_disabilities']}\n" + \
                       f"Unaccompanied minors: {data['unaccompanied_minors']}"

            elif monitoring_type == "vulnerability_mapping":
                return f"Vulnerability Assessment - {location}:\n" + \
                       f"Female-headed households: {data['female_headed_households']}\n" + \
                       f"Separated children: {data['separated_children']}\n" + \
                       f"Chronic illness: {data['chronic_illness']}\n" + \
                       f"Pregnant/lactating women: {data['pregnant_lactating_women']}\n" + \
                       f"Special needs cases: {data['special_needs_cases']}"

            else:  # intention_survey
                return f"Population Intention Survey - {location}:\n" + \
                       f"Want to remain: {data['remain_current_location']}\n" + \
                       f"Plan to return home: {data['return_home']}\n" + \
                       f"Onward movement: {data['onward_movement']}\n" + \
                       f"Undecided: {data['undecided']}"

        return f"Monitoring {monitoring_type.replace('_', ' ')} in {location}"


class CommunityEngagementTool(BaseTool):
    name = "community_engagement"
    description = "Facilitate community participation and feedback mechanisms in Sudan camps"

    def _run(self, engagement_type: str, target_group: str = "all_residents") -> str:
        engagement_activities = {
            "committee_formation": {
                "structure": "Camp Management Committee + thematic sub-committees",
                "representation": "Gender-balanced, diverse ethnic/age groups",
                "roles": ["Service monitoring", "Conflict resolution", "Information sharing"],
                "meeting_frequency": "Weekly plenary, bi-weekly sub-committees"
            },
            "feedback_mechanisms": {
                "channels": ["Suggestion boxes", "Community meetings", "Mobile feedback"],
                "languages": ["Arabic", "Local dialects", "Visual aids"],
                "response_timeline": "Acknowledgment within 48 hours",
                "action_tracking": "Public dashboard for issue status"
            },
            "information_sharing": {
                "methods": ["Community bulletin boards", "Megaphone announcements", "Peer networks"],
                "content": ["Service schedules", "New arrivals orientation", "Safety messages"],
                "frequency": "Daily announcements, weekly updates",
                "feedback_loop": "Community questions addressed in next session"
            },
            "conflict_resolution": {
                "mechanisms": ["Community mediation", "Elder councils", "Women's committees"],
                "common_issues": ["Resource allocation", "Space disputes", "Cultural tensions"],
                "resolution_rate": "78% resolved at community level",
                "escalation_protocol": "Protection cluster referral for serious cases"
            }
        }

        target_groups = {
            "women": "Women's committees and female-headed households",
            "youth": "Young people aged 18-35, including students",
            "elderly": "Elder councils and traditional leaders",
            "children": "Child-friendly spaces and school committees",
            "all_residents": "Whole community including all demographic groups"
        }

        if engagement_type in engagement_activities:
            activity = engagement_activities[engagement_type]
            group_desc = target_groups.get(target_group, target_group)

            return f"Community Engagement - {engagement_type.replace('_', ' ').title()}:\n" + \
                   f"Target group: {group_desc}\n" + \
                   f"Activity details: {activity}\n" + \
                   f"Key focus: Ensuring meaningful participation and accountability"

        return f"Facilitating {engagement_type.replace('_', ' ')} with {target_group.replace('_', ' ')}"


class CCCMAgent(BaseHumanitarianAgent):
    def __init__(self):
        super().__init__(
            sector="CCCM (Camp Coordination and Camp Management)",
            lead_agencies=["UNHCR", "IOM"],
            sudan_context={
                "displacement_sites": "Over 2,800 displacement sites across Sudan",
                "managed_population": "6.2 million internally displaced persons",
                "site_types": ["Planned camps", "Spontaneous settlements", "Transit sites", "Host communities"],
                "priority_locations": ["Darfur region", "Blue Nile", "South Kordofan", "Khartoum"],
                "challenges": [
                    "Overcrowded sites exceeding capacity",
                    "Limited site planning and infrastructure",
                    "Weak community governance structures",
                    "Inadequate information management systems"
                ],
                "key_functions": ["Site coordination", "Information management", "Community participation", "Service monitoring"]
            }
        )

        # Add CCCM-specific tools
        self.tools.extend([
            SiteManagementTool(),
            PopulationMonitoringTool(),
            CommunityEngagementTool()
        ])

    def process_request(self, request: HumanitarianRequest) -> HumanitarianResponse:
        """Process CCCM-related requests for Sudan context"""

        # Extract key information
        query_lower = request.query.lower()
        location = self._extract_location(request.query)

        # Determine response based on query type
        if any(word in query_lower for word in ["site", "camp", "settlement", "manage"]):
            management_area = "site_planning" if "plan" in query_lower else "governance" if "committee" in query_lower else "general"
            site_name = location.replace(" ", "_") + "_IDP_Settlement" if location else "Nyala_IDP_Settlement"
            tool_result = self.tools[0]._run(site_name, management_area)
            analysis = f"Site management shows critical gaps in coordination and service delivery at {location or 'displacement sites'}"

        elif any(word in query_lower for word in ["population", "monitoring", "movement", "demographic"]):
            monitoring_type = "arrivals_departures" if "arrival" in query_lower or "movement" in query_lower else \
                             "vulnerability_mapping" if "vulnerable" in query_lower else "demographic_profile"
            tool_result = self.tools[1]._run(monitoring_type, location or "multiple_sites")
            analysis = "Population monitoring reveals dynamic displacement patterns requiring adaptive response"

        elif any(word in query_lower for word in ["community", "participation", "committee", "feedback"]):
            engagement_type = "committee_formation" if "committee" in query_lower else \
                             "feedback_mechanisms" if "feedback" in query_lower else "information_sharing"
            target_group = "women" if "women" in query_lower else "youth" if "youth" in query_lower else "all_residents"
            tool_result = self.tools[2]._run(engagement_type, target_group)
            analysis = "Community engagement mechanisms need strengthening to ensure meaningful participation"

        else:
            # General CCCM information
            tool_result = "Sudan CCCM Overview: 2,800+ sites, 6.2M IDPs, overcrowded conditions, weak governance structures"
            analysis = "CCCM operations require urgent scaling up to address massive coordination needs"

        # Generate recommendations
        recommendations = self._generate_cccm_recommendations(request.query, location)

        return HumanitarianResponse(
            sector=self.sector,
            analysis=analysis,
            data=tool_result,
            recommendations=recommendations,
            priority_level="HIGH",
            locations=[location] if location else ["Nyala", "El Geneina", "Kassala"]
        )

    def _generate_cccm_recommendations(self, query: str, location: str = None) -> List[str]:
        """Generate CCCM-specific recommendations"""
        base_recommendations = [
            "Establish Camp Management Committees in all major sites",
            "Implement standardized population monitoring systems",
            "Strengthen inter-agency coordination at site level",
            "Develop community feedback and accountability mechanisms"
        ]

        if location:
            base_recommendations.append(f"Deploy CCCM team to {location} for immediate site assessment")

        if "overcrowding" in query.lower() or "capacity" in query.lower():
            base_recommendations.append("Identify land for site expansion or establish new sites")

        if "community" in query.lower() or "participation" in query.lower():
            base_recommendations.append("Strengthen community leadership and representative structures")

        if "information" in query.lower() or "data" in query.lower():
            base_recommendations.append("Implement digital information management systems")

        return base_recommendations