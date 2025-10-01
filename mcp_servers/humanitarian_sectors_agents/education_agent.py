"""
Education Cluster Agent - UNICEF Lead
Handles emergency education, temporary learning spaces, and education continuity
"""

from typing import Dict, List, Any
from langchain.tools import BaseTool
from langchain.schema import BaseMessage
import json

from .base_humanitarian_agent import BaseHumanitarianAgent, HumanitarianRequest, HumanitarianResponse


class EducationAssessmentTool(BaseTool):
    name = "education_assessment"
    description = "Assess education needs and access in Sudan displacement areas"

    def _run(self, location: str, education_level: str = "primary") -> str:
        education_data = {
            "Nyala IDP Settlement": {
                "primary": {
                    "school_age_children": 12500,
                    "enrolled": 4200,
                    "attendance_rate": "68%",
                    "temporary_learning_spaces": 8,
                    "teacher_shortage": 35
                },
                "secondary": {
                    "school_age_children": 6800,
                    "enrolled": 1900,
                    "attendance_rate": "45%",
                    "temporary_learning_spaces": 3,
                    "teacher_shortage": 18
                }
            },
            "El Geneina Emergency Camp": {
                "primary": {
                    "school_age_children": 9200,
                    "enrolled": 3100,
                    "attendance_rate": "62%",
                    "temporary_learning_spaces": 6,
                    "teacher_shortage": 28
                },
                "secondary": {
                    "school_age_children": 4900,
                    "enrolled": 1200,
                    "attendance_rate": "38%",
                    "temporary_learning_spaces": 2,
                    "teacher_shortage": 15
                }
            },
            "Kassala Reception Center": {
                "primary": {
                    "school_age_children": 5400,
                    "enrolled": 2800,
                    "attendance_rate": "75%",
                    "temporary_learning_spaces": 4,
                    "teacher_shortage": 12
                },
                "secondary": {
                    "school_age_children": 2800,
                    "enrolled": 980,
                    "attendance_rate": "52%",
                    "temporary_learning_spaces": 2,
                    "teacher_shortage": 8
                }
            }
        }

        if location in education_data and education_level in education_data[location]:
            data = education_data[location][education_level]
            enrollment_rate = (data['enrolled'] / data['school_age_children']) * 100

            return f"Education Assessment - {location} ({education_level.title()}):\n" + \
                   f"School-age children: {data['school_age_children']:,}\n" + \
                   f"Currently enrolled: {data['enrolled']:,} ({enrollment_rate:.1f}%)\n" + \
                   f"Attendance rate: {data['attendance_rate']}\n" + \
                   f"Temporary learning spaces: {data['temporary_learning_spaces']}\n" + \
                   f"Teacher shortage: {data['teacher_shortage']} teachers needed"

        return f"Assessing education needs in {location} for {education_level} level"


class LearningSpaceTool(BaseTool):
    name = "learning_space_setup"
    description = "Plan and establish temporary learning spaces in Sudan"

    def _run(self, space_type: str, capacity: int, location: str) -> str:
        space_specifications = {
            "tent_classroom": {
                "capacity": 40,
                "materials": ["Large tent", "Plastic flooring", "Benches", "Blackboard"],
                "setup_time": "2-3 days",
                "cost": 800,
                "durability": "6-12 months"
            },
            "semi_permanent": {
                "capacity": 60,
                "materials": ["Timber frame", "Corrugated sheets", "Concrete floor", "Windows"],
                "setup_time": "2-3 weeks",
                "cost": 3500,
                "durability": "2-3 years"
            },
            "community_space": {
                "capacity": 30,
                "materials": ["Repurposed building", "Basic furniture", "Teaching materials"],
                "setup_time": "1 week",
                "cost": 500,
                "durability": "Variable"
            }
        }

        if space_type in space_specifications:
            spec = space_specifications[space_type]
            num_spaces_needed = max(1, capacity // spec['capacity'])
            total_cost = num_spaces_needed * spec['cost']

            return f"Learning Space Plan - {location}:\n" + \
                   f"Type: {space_type.replace('_', ' ').title()}\n" + \
                   f"Target capacity: {capacity} children\n" + \
                   f"Spaces needed: {num_spaces_needed}\n" + \
                   f"Materials per space: {', '.join(spec['materials'])}\n" + \
                   f"Setup time: {spec['setup_time']}\n" + \
                   f"Total cost: ${total_cost:,}\n" + \
                   f"Expected durability: {spec['durability']}"

        return f"Planning {space_type.replace('_', ' ')} for {capacity} children in {location}"


class TeacherSupportTool(BaseTool):
    name = "teacher_support"
    description = "Recruit, train, and support teachers in Sudan emergency education"

    def _run(self, support_type: str, number_teachers: int, location: str) -> str:
        support_programs = {
            "recruitment": {
                "sources": ["Displaced qualified teachers", "Community volunteers", "Retired teachers"],
                "screening_process": "Document verification, interview, reference check",
                "timeline": "2-4 weeks",
                "cost_per_teacher": 150
            },
            "training": {
                "modules": ["Emergency pedagogy", "Psychosocial support", "Multi-grade teaching"],
                "duration": "5 days intensive + ongoing support",
                "materials": ["Training manual", "Teaching aids", "Curriculum guide"],
                "cost_per_teacher": 200
            },
            "incentives": {
                "monthly_stipend": 100,
                "transportation": 25,
                "materials_allowance": 20,
                "recognition": "Certificate, community acknowledgment",
                "cost_per_teacher": 145
            }
        }

        if support_type in support_programs:
            program = support_programs[support_type]
            total_cost = number_teachers * program['cost_per_teacher']

            if support_type == "recruitment":
                return f"Teacher Recruitment - {location}:\n" + \
                       f"Target teachers: {number_teachers}\n" + \
                       f"Recruitment sources: {', '.join(program['sources'])}\n" + \
                       f"Process: {program['screening_process']}\n" + \
                       f"Timeline: {program['timeline']}\n" + \
                       f"Total cost: ${total_cost:,}"

            elif support_type == "training":
                return f"Teacher Training Program - {location}:\n" + \
                       f"Teachers to train: {number_teachers}\n" + \
                       f"Training modules: {', '.join(program['modules'])}\n" + \
                       f"Duration: {program['duration']}\n" + \
                       f"Materials: {', '.join(program['materials'])}\n" + \
                       f"Total cost: ${total_cost:,}"

            else:  # incentives
                monthly_total = total_cost * number_teachers
                return f"Teacher Incentive Program - {location}:\n" + \
                       f"Teachers supported: {number_teachers}\n" + \
                       f"Monthly stipend: ${program['monthly_stipend']}\n" + \
                       f"Additional support: Transportation + materials\n" + \
                       f"Recognition: {program['recognition']}\n" + \
                       f"Monthly program cost: ${monthly_total:,}"

        return f"Developing {support_type} program for {number_teachers} teachers in {location}"


class EducationAgent(BaseHumanitarianAgent):
    def __init__(self):
        super().__init__(
            sector="Education",
            lead_agencies=["UNICEF"],
            sudan_context={
                "affected_children": "7.1 million school-age children affected by crisis",
                "out_of_school": "3.2 million children out of school",
                "damaged_schools": "10,400 schools damaged or occupied",
                "priority_states": ["North Darfur", "South Darfur", "Blue Nile", "Khartoum"],
                "challenges": [
                    "Massive teacher shortages due to displacement",
                    "Lack of learning materials and supplies",
                    "Damaged or occupied school infrastructure",
                    "Language barriers for displaced children"
                ],
                "key_interventions": ["Temporary learning spaces", "Teacher training", "Learning materials", "Psychosocial support"]
            }
        )

        # Add education-specific tools
        self.tools.extend([
            EducationAssessmentTool(),
            LearningSpaceTool(),
            TeacherSupportTool()
        ])

    def process_request(self, request: HumanitarianRequest) -> HumanitarianResponse:
        """Process education-related requests for Sudan context"""

        # Extract key information
        query_lower = request.query.lower()
        location = self._extract_location(request.query)

        # Determine response based on query type
        if any(word in query_lower for word in ["assess", "enrollment", "access", "children"]):
            education_level = "secondary" if "secondary" in query_lower or "adolescent" in query_lower else "primary"
            tool_result = self.tools[0]._run(location or "Nyala IDP Settlement", education_level)
            analysis = f"Education assessment shows critical gaps in access and quality in {location or 'displacement areas'}"

        elif any(word in query_lower for word in ["classroom", "learning space", "tent", "school"]):
            capacity = 200  # Default capacity
            space_type = "tent_classroom" if "tent" in query_lower else "semi_permanent"
            tool_result = self.tools[1]._run(space_type, capacity, location or "Multiple locations")
            analysis = "Urgent need for additional learning spaces to accommodate displaced children"

        elif any(word in query_lower for word in ["teacher", "training", "staff", "recruitment"]):
            support_type = "training" if "train" in query_lower else "recruitment"
            tool_result = self.tools[2]._run(support_type, 25, location or "Multiple locations")
            analysis = "Teacher shortage is critical barrier to education service delivery"

        else:
            # General education information
            tool_result = "Sudan Education Crisis: 7.1M children affected, 3.2M out of school, 10,400 schools damaged"
            analysis = "Education sector faces unprecedented disruption requiring immediate intervention"

        # Generate recommendations
        recommendations = self._generate_education_recommendations(request.query, location)

        return HumanitarianResponse(
            sector=self.sector,
            analysis=analysis,
            data=tool_result,
            recommendations=recommendations,
            priority_level="HIGH",
            locations=[location] if location else ["North Darfur", "South Darfur", "Blue Nile"]
        )

    def _generate_education_recommendations(self, query: str, location: str = None) -> List[str]:
        """Generate education-specific recommendations"""
        base_recommendations = [
            "Establish temporary learning spaces in all displacement sites",
            "Launch accelerated teacher training program",
            "Distribute emergency education kits and supplies",
            "Coordinate with Protection cluster on child safety measures"
        ]

        if location:
            base_recommendations.append(f"Conduct detailed education assessment in {location}")

        if "teacher" in query.lower():
            base_recommendations.append("Implement teacher incentive scheme to retain qualified staff")

        if "secondary" in query.lower() or "adolescent" in query.lower():
            base_recommendations.append("Develop alternative education pathways for over-age learners")

        if "girl" in query.lower() or "female" in query.lower():
            base_recommendations.append("Address gender-specific barriers to girls' education")

        return base_recommendations