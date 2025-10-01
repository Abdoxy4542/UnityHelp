"""
LangGraph Humanitarian Coordination System
Orchestrates multiple humanitarian sector agents using LangGraph workflows
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, TypedDict, Annotated, Union
from datetime import datetime, timezone

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# Import sector agents
from .protection_agent import ProtectionAgent
from .health_agent import HealthAgent
from .food_security_agent import FoodSecurityAgent
from .wash_agent import WASHAgent

# Create placeholder agents for remaining sectors
class ShelterAgent:
    def __init__(self):
        self.sector_name = "Shelter"
        self.lead_agency = "UNHCR & IFRC"
    async def process_request(self, request):
        return {"success": True, "sector": "Shelter", "response": "Mock shelter response"}

class NutritionAgent:
    def __init__(self):
        self.sector_name = "Nutrition"
        self.lead_agency = "UNICEF"
    async def process_request(self, request):
        return {"success": True, "sector": "Nutrition", "response": "Mock nutrition response"}

class EducationAgent:
    def __init__(self):
        self.sector_name = "Education"
        self.lead_agency = "UNICEF"
    async def process_request(self, request):
        return {"success": True, "sector": "Education", "response": "Mock education response"}

class LogisticsAgent:
    def __init__(self):
        self.sector_name = "Logistics"
        self.lead_agency = "WFP"
    async def process_request(self, request):
        return {"success": True, "sector": "Logistics", "response": "Mock logistics response"}

class CCCMAgent:
    def __init__(self):
        self.sector_name = "CCCM"
        self.lead_agency = "UNHCR & IOM"
    async def process_request(self, request):
        return {"success": True, "sector": "CCCM", "response": "Mock CCCM response"}

class EarlyRecoveryAgent:
    def __init__(self):
        self.sector_name = "Early Recovery"
        self.lead_agency = "UNDP"
    async def process_request(self, request):
        return {"success": True, "sector": "Early Recovery", "response": "Mock early recovery response"}

class ETCAgent:
    def __init__(self):
        self.sector_name = "Emergency Telecommunications"
        self.lead_agency = "WFP"
    async def process_request(self, request):
        return {"success": True, "sector": "ETC", "response": "Mock ETC response"}

# Define the state structure for LangGraph
class HumanitarianState(TypedDict):
    """State for humanitarian coordination workflow"""
    request: str
    location: str
    urgency: str
    affected_population: Optional[int]
    sectors_involved: List[str]
    sector_responses: Dict[str, Any]
    coordination_plan: Optional[Dict[str, Any]]
    final_response: Optional[Dict[str, Any]]
    messages: List[BaseMessage]
    iteration_count: int

class HumanitarianCoordinator:
    """LangGraph-based coordinator for humanitarian sectors"""

    def __init__(self):
        self.logger = logging.getLogger("humanitarian.coordinator")

        # Initialize all sector agents
        self.agents = {
            "protection": ProtectionAgent(),
            "health": HealthAgent(),
            "food_security": FoodSecurityAgent(),
            "wash": WASHAgent(),
            "shelter": ShelterAgent(),
            "nutrition": NutritionAgent(),
            "education": EducationAgent(),
            "logistics": LogisticsAgent(),
            "cccm": CCCMAgent(),
            "early_recovery": EarlyRecoveryAgent(),
            "etc": ETCAgent()
        }

        # Create LangGraph workflow
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile(checkpointer=MemorySaver())

    def _create_workflow(self) -> StateGraph:
        """Create LangGraph workflow for humanitarian coordination"""

        # Create workflow graph
        workflow = StateGraph(HumanitarianState)

        # Add nodes
        workflow.add_node("analyze_request", self.analyze_request)
        workflow.add_node("determine_sectors", self.determine_sectors)
        workflow.add_node("coordinate_sectors", self.coordinate_sectors)
        workflow.add_node("synthesize_response", self.synthesize_response)

        # Add conditional routing for sector coordination
        workflow.add_node("protection_response", self.protection_response)
        workflow.add_node("health_response", self.health_response)
        workflow.add_node("food_security_response", self.food_security_response)
        workflow.add_node("wash_response", self.wash_response)
        workflow.add_node("multi_sector_response", self.multi_sector_response)

        # Define workflow edges
        workflow.set_entry_point("analyze_request")
        workflow.add_edge("analyze_request", "determine_sectors")
        workflow.add_edge("determine_sectors", "coordinate_sectors")

        # Conditional edges for sector routing
        workflow.add_conditional_edges(
            "coordinate_sectors",
            self.route_to_sectors,
            {
                "protection": "protection_response",
                "health": "health_response",
                "food_security": "food_security_response",
                "wash": "wash_response",
                "multi_sector": "multi_sector_response"
            }
        )

        # All sector responses flow to synthesis
        workflow.add_edge("protection_response", "synthesize_response")
        workflow.add_edge("health_response", "synthesize_response")
        workflow.add_edge("food_security_response", "synthesize_response")
        workflow.add_edge("wash_response", "synthesize_response")
        workflow.add_edge("multi_sector_response", "synthesize_response")

        workflow.add_edge("synthesize_response", END)

        return workflow

    async def analyze_request(self, state: HumanitarianState) -> HumanitarianState:
        """Analyze incoming humanitarian request"""
        request = state["request"]

        # Simple analysis logic (in production, would use LLM)
        analysis = {
            "location": self._extract_location(request),
            "urgency": self._assess_urgency(request),
            "affected_population": self._estimate_population(request),
            "request_type": self._classify_request(request)
        }

        state["location"] = analysis["location"]
        state["urgency"] = analysis["urgency"]
        state["affected_population"] = analysis["affected_population"]

        state["messages"].append(
            AIMessage(content=f"Analyzed humanitarian request: {analysis}")
        )

        self.logger.info(f"Analyzed request: {analysis}")
        return state

    async def determine_sectors(self, state: HumanitarianState) -> HumanitarianState:
        """Determine which humanitarian sectors need to be involved"""
        request = state["request"].lower()

        # Determine sectors based on keywords
        sectors_needed = []

        if any(word in request for word in ["protection", "violence", "gbv", "child", "safety"]):
            sectors_needed.append("protection")

        if any(word in request for word in ["health", "medical", "disease", "outbreak", "hospital"]):
            sectors_needed.append("health")

        if any(word in request for word in ["food", "nutrition", "hunger", "malnutrition", "feeding"]):
            sectors_needed.extend(["food_security", "nutrition"])

        if any(word in request for word in ["water", "sanitation", "hygiene", "wash", "toilet", "cholera"]):
            sectors_needed.append("wash")

        if any(word in request for word in ["shelter", "housing", "tent", "camp"]):
            sectors_needed.extend(["shelter", "cccm"])

        if any(word in request for word in ["school", "education", "learning"]):
            sectors_needed.append("education")

        # If no specific sectors identified, involve primary life-saving sectors
        if not sectors_needed:
            sectors_needed = ["protection", "health", "food_security", "wash"]

        state["sectors_involved"] = list(set(sectors_needed))

        state["messages"].append(
            AIMessage(content=f"Determined sectors needed: {state['sectors_involved']}")
        )

        self.logger.info(f"Sectors determined: {state['sectors_involved']}")
        return state

    def route_to_sectors(self, state: HumanitarianState) -> str:
        """Route to appropriate sector response based on analysis"""
        sectors = state["sectors_involved"]

        if len(sectors) == 1:
            return sectors[0]
        else:
            return "multi_sector"

    async def coordinate_sectors(self, state: HumanitarianState) -> HumanitarianState:
        """Coordinate between multiple humanitarian sectors"""
        coordination_plan = {
            "primary_sectors": state["sectors_involved"],
            "coordination_mechanism": "cluster_coordination",
            "location": state["location"],
            "urgency_level": state["urgency"],
            "estimated_beneficiaries": state["affected_population"]
        }

        state["coordination_plan"] = coordination_plan
        state["messages"].append(
            AIMessage(content=f"Created coordination plan: {coordination_plan}")
        )

        return state

    async def protection_response(self, state: HumanitarianState) -> HumanitarianState:
        """Handle Protection sector response"""
        try:
            response = await self.agents["protection"].process_request(state["request"])
            state["sector_responses"]["protection"] = response

            state["messages"].append(
                AIMessage(content=f"Protection sector response: {response.get('response', 'Completed')}")
            )
        except Exception as e:
            self.logger.error(f"Protection response error: {e}")
            state["sector_responses"]["protection"] = {"success": False, "error": str(e)}

        return state

    async def health_response(self, state: HumanitarianState) -> HumanitarianState:
        """Handle Health sector response"""
        try:
            response = await self.agents["health"].process_request(state["request"])
            state["sector_responses"]["health"] = response

            state["messages"].append(
                AIMessage(content=f"Health sector response: {response.get('response', 'Completed')}")
            )
        except Exception as e:
            self.logger.error(f"Health response error: {e}")
            state["sector_responses"]["health"] = {"success": False, "error": str(e)}

        return state

    async def food_security_response(self, state: HumanitarianState) -> HumanitarianState:
        """Handle Food Security sector response"""
        try:
            response = await self.agents["food_security"].process_request(state["request"])
            state["sector_responses"]["food_security"] = response

            state["messages"].append(
                AIMessage(content=f"Food Security sector response: {response.get('response', 'Completed')}")
            )
        except Exception as e:
            self.logger.error(f"Food Security response error: {e}")
            state["sector_responses"]["food_security"] = {"success": False, "error": str(e)}

        return state

    async def wash_response(self, state: HumanitarianState) -> HumanitarianState:
        """Handle WASH sector response"""
        try:
            response = await self.agents["wash"].process_request(state["request"])
            state["sector_responses"]["wash"] = response

            state["messages"].append(
                AIMessage(content=f"WASH sector response: {response.get('response', 'Completed')}")
            )
        except Exception as e:
            self.logger.error(f"WASH response error: {e}")
            state["sector_responses"]["wash"] = {"success": False, "error": str(e)}

        return state

    async def multi_sector_response(self, state: HumanitarianState) -> HumanitarianState:
        """Handle multi-sector coordination response"""
        responses = {}

        for sector in state["sectors_involved"]:
            if sector in self.agents:
                try:
                    response = await self.agents[sector].process_request(state["request"])
                    responses[sector] = response
                except Exception as e:
                    self.logger.error(f"{sector} response error: {e}")
                    responses[sector] = {"success": False, "error": str(e)}

        state["sector_responses"] = responses

        state["messages"].append(
            AIMessage(content=f"Multi-sector coordination completed for {len(responses)} sectors")
        )

        return state

    async def synthesize_response(self, state: HumanitarianState) -> HumanitarianState:
        """Synthesize final coordinated response"""

        successful_responses = {k: v for k, v in state["sector_responses"].items() if v.get("success", False)}
        failed_responses = {k: v for k, v in state["sector_responses"].items() if not v.get("success", False)}

        synthesis = {
            "request_summary": state["request"],
            "location": state["location"],
            "urgency": state["urgency"],
            "affected_population": state["affected_population"],
            "sectors_activated": list(successful_responses.keys()),
            "coordination_status": "completed",
            "response_summary": self._create_response_summary(successful_responses),
            "next_steps": self._generate_next_steps(state),
            "failed_sectors": list(failed_responses.keys()) if failed_responses else [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        state["final_response"] = synthesis
        state["messages"].append(
            AIMessage(content=f"Synthesized humanitarian response: {len(successful_responses)} sectors coordinated")
        )

        self.logger.info(f"Response synthesis completed: {synthesis}")
        return state

    def _extract_location(self, request: str) -> str:
        """Extract location from request"""
        locations = ["darfur", "khartoum", "kassala", "blue nile", "kordofan", "nyala", "el geneina", "el fasher"]
        request_lower = request.lower()

        for location in locations:
            if location in request_lower:
                return location.title()

        return "Sudan (location not specified)"

    def _assess_urgency(self, request: str) -> str:
        """Assess urgency level"""
        request_lower = request.lower()

        if any(word in request_lower for word in ["emergency", "critical", "urgent", "immediate"]):
            return "critical"
        elif any(word in request_lower for word in ["acute", "severe", "high"]):
            return "high"
        elif any(word in request_lower for word in ["moderate", "medium"]):
            return "medium"
        else:
            return "standard"

    def _estimate_population(self, request: str) -> Optional[int]:
        """Estimate affected population"""
        # Simple extraction logic (in production, would be more sophisticated)
        import re
        numbers = re.findall(r'\d+', request)

        if numbers:
            # Return the largest number found (likely population figure)
            return max(int(num) for num in numbers)

        # Default estimates based on location
        if "camp" in request.lower():
            return 10000
        elif "village" in request.lower():
            return 5000
        else:
            return 25000  # Default for Sudan context

    def _classify_request(self, request: str) -> str:
        """Classify type of humanitarian request"""
        request_lower = request.lower()

        if any(word in request_lower for word in ["outbreak", "epidemic", "disease"]):
            return "health_emergency"
        elif any(word in request_lower for word in ["violence", "attack", "conflict"]):
            return "protection_emergency"
        elif any(word in request_lower for word in ["displacement", "flee", "camp"]):
            return "displacement_emergency"
        elif any(word in request_lower for word in ["food", "hunger", "malnutrition"]):
            return "food_security_emergency"
        else:
            return "general_humanitarian_need"

    def _create_response_summary(self, responses: Dict[str, Any]) -> str:
        """Create summary of all sector responses"""
        summary_parts = []

        for sector, response in responses.items():
            if response.get("success"):
                summary_parts.append(f"{sector.upper()}: {response.get('response', 'Response provided')[:100]}...")

        return " | ".join(summary_parts)

    def _generate_next_steps(self, state: HumanitarianState) -> List[str]:
        """Generate coordinated next steps"""
        next_steps = [
            "Activate field coordination mechanisms",
            "Deploy inter-sector assessment teams",
            "Establish coordination hub at field level",
            "Implement joint monitoring and evaluation",
            "Schedule regular coordination meetings"
        ]

        if state["urgency"] == "critical":
            next_steps.insert(0, "Immediate emergency response deployment")

        return next_steps

    async def process_humanitarian_request(self, request: str, config: Optional[Dict] = None) -> Dict[str, Any]:
        """Process humanitarian request through LangGraph workflow"""

        # Initialize state
        initial_state: HumanitarianState = {
            "request": request,
            "location": "",
            "urgency": "",
            "affected_population": None,
            "sectors_involved": [],
            "sector_responses": {},
            "coordination_plan": None,
            "final_response": None,
            "messages": [HumanMessage(content=request)],
            "iteration_count": 0
        }

        try:
            # Run the workflow
            final_state = await self.app.ainvoke(
                initial_state,
                config={"configurable": {"thread_id": "humanitarian_coordination"}}
            )

            return {
                "success": True,
                "final_response": final_state.get("final_response"),
                "workflow_messages": [msg.content for msg in final_state.get("messages", [])],
                "sectors_involved": final_state.get("sectors_involved", []),
                "coordination_plan": final_state.get("coordination_plan"),
            }

        except Exception as e:
            self.logger.error(f"Workflow processing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "request": request
            }

    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about all available agents"""
        return {
            "total_agents": len(self.agents),
            "agents": {
                name: {
                    "sector": agent.sector_name,
                    "lead_agency": agent.lead_agency,
                    "status": "active"
                }
                for name, agent in self.agents.items()
            },
            "coordination_framework": "LangGraph workflow",
            "country_focus": "Sudan",
            "workflow_nodes": [
                "analyze_request",
                "determine_sectors",
                "coordinate_sectors",
                "synthesize_response"
            ]
        }