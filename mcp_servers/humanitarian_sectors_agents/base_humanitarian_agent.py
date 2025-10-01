"""
Base Humanitarian Agent for UnityAid Platform
Foundation class for all humanitarian sector agents using LangChain
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.callbacks import CallbackManagerForChainRun

# Sudan-specific context
SUDAN_CONTEXT = {
    "country": "Sudan",
    "iso3_code": "SDN",
    "crisis_start": "April 2023",
    "crisis_type": "Armed Conflict and Humanitarian Emergency",
    "affected_population": 25600000,
    "displaced_population": 6200000,
    "priority_states": ["West Darfur", "South Darfur", "North Darfur", "Central Darfur", "East Darfur", "Blue Nile", "South Kordofan", "Kassala"],
    "coordinates": {"lat": 15.5007, "lon": 32.5599}  # Sudan center
}

class HumanitarianRequest(BaseModel):
    """Schema for humanitarian requests"""
    request_type: str = Field(description="Type of humanitarian request")
    location: Optional[str] = Field(description="Location in Sudan")
    urgency: str = Field(description="Urgency level: low, medium, high, critical")
    beneficiaries: Optional[int] = Field(description="Number of beneficiaries")
    details: Dict[str, Any] = Field(description="Additional request details")

class HumanitarianResponse(BaseModel):
    """Schema for humanitarian responses"""
    status: str = Field(description="Response status")
    sector: str = Field(description="Humanitarian sector")
    recommendations: List[str] = Field(description="Recommended actions")
    resources_needed: List[str] = Field(description="Required resources")
    timeline: Optional[str] = Field(description="Implementation timeline")
    risk_assessment: str = Field(description="Risk assessment")

class BaseHumanitarianAgent(ABC):
    """Base class for all humanitarian sector agents"""

    def __init__(self, sector_name: str, lead_agency: str, llm=None):
        self.sector_name = sector_name
        self.lead_agency = lead_agency
        self.llm = llm  # LangChain LLM instance (would be configured)
        self.logger = logging.getLogger(f"humanitarian.{sector_name.lower().replace(' ', '_')}")

        # Initialize memory for conversation context
        self.memory = ConversationBufferWindowMemory(
            k=10,
            return_messages=True,
            memory_key="chat_history"
        )

        # Initialize tools specific to this sector
        self.tools = self._initialize_tools()

        # Create agent
        self.agent = self._create_agent()

    @abstractmethod
    def _initialize_tools(self) -> List[Tool]:
        """Initialize sector-specific tools"""
        pass

    @abstractmethod
    def get_sector_specific_context(self) -> Dict[str, Any]:
        """Get sector-specific context for Sudan"""
        pass

    def _create_agent(self) -> Optional[AgentExecutor]:
        """Create LangChain agent with sector-specific configuration"""
        if not self.llm:
            # Return mock agent for demonstration
            return None

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""You are a specialized {self.sector_name} humanitarian agent for Sudan operations.

            CONTEXT:
            - Country: Sudan
            - Crisis: Armed conflict since April 2023
            - Population in need: 25.6 million
            - Displaced population: 6.2 million
            - Lead Agency: {self.lead_agency}
            - Sector: {self.sector_name}

            RESPONSIBILITIES:
            - Provide expert {self.sector_name} humanitarian guidance
            - Focus exclusively on Sudan operations
            - Consider local context and cultural factors
            - Prioritize life-saving interventions
            - Coordinate with other sectors when needed

            Always provide practical, actionable recommendations based on humanitarian standards and Sudan-specific conditions."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        # Create structured agent
        agent = create_structured_chat_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

        # Create agent executor
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )

    async def process_request(self, request: Union[str, HumanitarianRequest]) -> Dict[str, Any]:
        """Process humanitarian request"""
        try:
            if isinstance(request, str):
                # Convert string to structured request
                input_text = f"Sudan {self.sector_name} request: {request}"
            else:
                input_text = f"Sudan {self.sector_name} request: {request.request_type} in {request.location or 'Sudan'} - {request.details}"

            # Add Sudan context
            context = self.get_sector_specific_context()
            context_text = f"Sudan Context: {context}"

            full_input = f"{context_text}\n\nRequest: {input_text}"

            # Process with agent (mock response for demonstration)
            if self.agent:
                response = await self.agent.arun(input=full_input)
            else:
                response = await self._mock_response(request)

            return {
                "success": True,
                "sector": self.sector_name,
                "lead_agency": self.lead_agency,
                "country": "Sudan",
                "response": response,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "context": context
            }

        except Exception as e:
            self.logger.error(f"Error processing {self.sector_name} request: {e}")
            return {
                "success": False,
                "error": str(e),
                "sector": self.sector_name,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    @abstractmethod
    async def _mock_response(self, request: Union[str, HumanitarianRequest]) -> str:
        """Generate mock response for demonstration"""
        pass

    async def assess_needs(self, location: str, population: int) -> Dict[str, Any]:
        """Assess sector-specific needs in a location"""
        try:
            context = self.get_sector_specific_context()

            assessment = {
                "location": location,
                "population": population,
                "sector": self.sector_name,
                "country": "Sudan",
                "assessment": await self._conduct_needs_assessment(location, population),
                "priorities": await self._identify_priorities(location, population),
                "resources_needed": await self._calculate_resources_needed(location, population),
                "context": context,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            return {"success": True, "assessment": assessment}

        except Exception as e:
            return {"success": False, "error": str(e)}

    @abstractmethod
    async def _conduct_needs_assessment(self, location: str, population: int) -> Dict[str, Any]:
        """Conduct sector-specific needs assessment"""
        pass

    @abstractmethod
    async def _identify_priorities(self, location: str, population: int) -> List[str]:
        """Identify sector-specific priorities"""
        pass

    @abstractmethod
    async def _calculate_resources_needed(self, location: str, population: int) -> List[str]:
        """Calculate sector-specific resource needs"""
        pass

    def get_sector_info(self) -> Dict[str, Any]:
        """Get sector information"""
        return {
            "sector_name": self.sector_name,
            "lead_agency": self.lead_agency,
            "country_focus": "Sudan",
            "tools_available": len(self.tools),
            "context": self.get_sector_specific_context(),
            "status": "active"
        }

    async def coordinate_with_sector(self, target_sector: str, message: str) -> Dict[str, Any]:
        """Coordinate with another humanitarian sector"""
        return {
            "from_sector": self.sector_name,
            "to_sector": target_sector,
            "message": f"{self.sector_name} coordination: {message}",
            "country": "Sudan",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "coordination_type": "inter_sector"
        }

def create_base_tools() -> List[Tool]:
    """Create base tools available to all humanitarian agents"""

    def get_sudan_population_data(query: str) -> str:
        """Get population data for Sudan locations"""
        population_data = {
            "khartoum": 5274321,
            "darfur": 8000000,  # Combined Darfur states
            "kassala": 1800000,
            "blue_nile": 1200000,
            "south_kordofan": 2500000
        }

        location = query.lower()
        for place, pop in population_data.items():
            if place in location:
                return f"Population data for {place}: {pop:,} people"

        return "Population data not available for specified location"

    def get_sudan_crisis_info(query: str) -> str:
        """Get Sudan crisis information"""
        return f"""Sudan Crisis Information:
        - Crisis start: April 2023
        - Type: Armed conflict and humanitarian emergency
        - Total population: 48 million
        - People in need: 25.6 million
        - Internally displaced: 6.2 million
        - Most affected areas: Greater Darfur, Kordofan, Blue Nile
        - Crisis level: Level 3 Emergency (highest)"""

    def get_access_constraints(location: str) -> str:
        """Get humanitarian access constraints for Sudan locations"""
        constraints = {
            "darfur": "Severely constrained - active conflict, insecurity",
            "khartoum": "Constrained - urban conflict, infrastructure damage",
            "blue_nile": "Partially constrained - limited infrastructure",
            "kassala": "Accessible - refugee hosting area"
        }

        location_lower = location.lower()
        for area, constraint in constraints.items():
            if area in location_lower:
                return f"Access level for {area}: {constraint}"

        return "Access information not available for specified location"

    return [
        Tool(
            name="get_sudan_population_data",
            func=get_sudan_population_data,
            description="Get population data for Sudan locations"
        ),
        Tool(
            name="get_sudan_crisis_info",
            func=get_sudan_crisis_info,
            description="Get information about Sudan humanitarian crisis"
        ),
        Tool(
            name="get_access_constraints",
            func=get_access_constraints,
            description="Get humanitarian access constraints for Sudan locations"
        )
    ]