"""
Logistics Cluster Agent - WFP Lead
Handles supply chain coordination, transportation, and storage for humanitarian operations
"""

from typing import Dict, List, Any
from langchain.tools import BaseTool
from langchain.schema import BaseMessage
import json

from .base_humanitarian_agent import BaseHumanitarianAgent, HumanitarianRequest, HumanitarianResponse


class TransportationTool(BaseTool):
    name = "transportation_coordination"
    description = "Coordinate transportation and logistics for humanitarian supplies in Sudan"

    def _run(self, cargo_type: str, destination: str, urgency: str = "normal") -> str:
        transportation_data = {
            "Nyala": {
                "access_status": "Partially accessible",
                "road_conditions": "Poor, requires 4WD vehicles",
                "security_escorts": "Required for convoys",
                "travel_time_from_khartoum": "18-24 hours",
                "fuel_availability": "Limited",
                "storage_capacity": "2500 MT"
            },
            "El Geneina": {
                "access_status": "Limited access",
                "road_conditions": "Severely damaged, seasonal closures",
                "security_escorts": "Essential",
                "travel_time_from_khartoum": "20-30 hours",
                "fuel_availability": "Very limited",
                "storage_capacity": "1800 MT"
            },
            "Kassala": {
                "access_status": "Good access",
                "road_conditions": "Acceptable, paved sections",
                "security_escorts": "Recommended",
                "travel_time_from_khartoum": "8-12 hours",
                "fuel_availability": "Available",
                "storage_capacity": "3200 MT"
            }
        }

        transport_modes = {
            "emergency": {
                "method": "Air transport + road distribution",
                "cost_multiplier": 3.5,
                "timeline": "24-48 hours"
            },
            "urgent": {
                "method": "Truck convoy with priority routing",
                "cost_multiplier": 1.8,
                "timeline": "3-5 days"
            },
            "normal": {
                "method": "Regular truck convoy",
                "cost_multiplier": 1.0,
                "timeline": "1-2 weeks"
            }
        }

        if destination in transportation_data:
            dest_info = transportation_data[destination]
            transport_info = transport_modes.get(urgency, transport_modes["normal"])

            return f"Transportation Plan to {destination}:\n" + \
                   f"Cargo: {cargo_type}\n" + \
                   f"Access status: {dest_info['access_status']}\n" + \
                   f"Road conditions: {dest_info['road_conditions']}\n" + \
                   f"Security requirements: {dest_info['security_escorts']}\n" + \
                   f"Travel time: {dest_info['travel_time_from_khartoum']}\n" + \
                   f"Transport method: {transport_info['method']}\n" + \
                   f"Timeline: {transport_info['timeline']}\n" + \
                   f"Storage capacity: {dest_info['storage_capacity']}"

        return f"Planning transport of {cargo_type} to {destination} with {urgency} priority"


class WarehouseTool(BaseTool):
    name = "warehouse_management"
    description = "Manage warehouse operations and inventory tracking in Sudan"

    def _run(self, location: str, operation_type: str = "status_check") -> str:
        warehouse_data = {
            "Khartoum_Hub": {
                "capacity": 8500,
                "current_stock": 6200,
                "utilization": "73%",
                "key_items": ["Food supplies", "Medical kits", "NFI items"],
                "staff_level": "Adequate",
                "security_status": "Secure"
            },
            "Port_Sudan": {
                "capacity": 12000,
                "current_stock": 4800,
                "utilization": "40%",
                "key_items": ["Bulk food", "Construction materials", "Fuel"],
                "staff_level": "Reduced",
                "security_status": "Monitoring required"
            },
            "Nyala_Forward": {
                "capacity": 2500,
                "current_stock": 1900,
                "utilization": "76%",
                "key_items": ["Emergency rations", "Water treatment", "Blankets"],
                "staff_level": "Minimal",
                "security_status": "Protected"
            }
        }

        operations = {
            "status_check": "Current warehouse status and inventory levels",
            "receiving": "Plan receiving operations for incoming supplies",
            "dispatch": "Coordinate dispatch to field locations",
            "inventory": "Conduct inventory management and tracking"
        }

        if location in warehouse_data:
            data = warehouse_data[location]
            available_capacity = data['capacity'] - data['current_stock']

            return f"Warehouse {operation_type.replace('_', ' ').title()} - {location.replace('_', ' ')}:\n" + \
                   f"Total capacity: {data['capacity']} MT\n" + \
                   f"Current stock: {data['current_stock']} MT ({data['utilization']})\n" + \
                   f"Available space: {available_capacity} MT\n" + \
                   f"Key commodities: {', '.join(data['key_items'])}\n" + \
                   f"Staffing: {data['staff_level']}\n" + \
                   f"Security: {data['security_status']}\n" + \
                   f"Operation: {operations.get(operation_type, operation_type)}"

        return f"Managing {operation_type.replace('_', ' ')} operations at {location.replace('_', ' ')}"


class SupplyChainTool(BaseTool):
    name = "supply_chain_tracking"
    description = "Track supply chain and procurement for humanitarian operations in Sudan"

    def _run(self, item_category: str, tracking_stage: str = "procurement") -> str:
        supply_categories = {
            "food_supplies": {
                "lead_time": "45-60 days",
                "key_suppliers": ["WFP Global", "Local mills", "Regional traders"],
                "procurement_challenges": ["Currency fluctuation", "Import restrictions"],
                "current_pipeline": "2.5 months stock"
            },
            "medical_supplies": {
                "lead_time": "30-45 days",
                "key_suppliers": ["WHO Emergency Health Kits", "UNICEF Supply Division"],
                "procurement_challenges": ["Cold chain requirements", "Regulatory approvals"],
                "current_pipeline": "1.8 months stock"
            },
            "nfi_items": {
                "lead_time": "30-40 days",
                "key_suppliers": ["UNHCR Global stockpile", "Regional procurement"],
                "procurement_challenges": ["Quality standards", "Bulk shipping"],
                "current_pipeline": "3.2 months stock"
            },
            "construction_materials": {
                "lead_time": "60-90 days",
                "key_suppliers": ["Local manufacturers", "Regional imports"],
                "procurement_challenges": ["Transportation costs", "Security clearances"],
                "current_pipeline": "1.2 months stock"
            }
        }

        tracking_stages = {
            "procurement": "Sourcing and purchasing phase",
            "shipping": "International and domestic transportation",
            "clearance": "Customs and regulatory processing",
            "distribution": "Last-mile delivery to beneficiaries"
        }

        if item_category in supply_categories:
            supply_info = supply_categories[item_category]
            stage_desc = tracking_stages.get(tracking_stage, tracking_stage)

            return f"Supply Chain Tracking - {item_category.replace('_', ' ').title()}:\n" + \
                   f"Tracking stage: {stage_desc}\n" + \
                   f"Typical lead time: {supply_info['lead_time']}\n" + \
                   f"Key suppliers: {', '.join(supply_info['key_suppliers'])}\n" + \
                   f"Current challenges: {', '.join(supply_info['procurement_challenges'])}\n" + \
                   f"Pipeline status: {supply_info['current_pipeline']}"

        return f"Tracking {item_category.replace('_', ' ')} through {tracking_stage} stage"


class LogisticsAgent(BaseHumanitarianAgent):
    def __init__(self):
        super().__init__(
            sector="Logistics",
            lead_agencies=["WFP"],
            sudan_context={
                "operational_constraints": "Severe access limitations due to conflict",
                "fuel_shortages": "Critical fuel shortages affecting all operations",
                "damaged_infrastructure": "Roads, bridges, and facilities require repair",
                "priority_routes": ["Khartoum-Port Sudan", "Khartoum-Kassala", "Chad border crossings"],
                "challenges": [
                    "Fuel shortages and high transportation costs",
                    "Security restrictions limiting convoy movements",
                    "Damaged roads and infrastructure",
                    "Limited warehouse capacity in field locations"
                ],
                "key_hubs": ["Khartoum", "Port Sudan", "Kassala", "Nyala", "El Geneina"]
            }
        )

        # Add logistics-specific tools
        self.tools.extend([
            TransportationTool(),
            WarehouseTool(),
            SupplyChainTool()
        ])

    def process_request(self, request: HumanitarianRequest) -> HumanitarianResponse:
        """Process logistics-related requests for Sudan context"""

        # Extract key information
        query_lower = request.query.lower()
        location = self._extract_location(request.query)

        # Determine response based on query type
        if any(word in query_lower for word in ["transport", "convoy", "delivery", "move"]):
            cargo_type = "humanitarian supplies"
            urgency = "urgent" if any(word in query_lower for word in ["urgent", "emergency", "critical"]) else "normal"
            tool_result = self.tools[0]._run(cargo_type, location or "Nyala", urgency)
            analysis = f"Transportation planning shows significant challenges for {location or 'field locations'}"

        elif any(word in query_lower for word in ["warehouse", "storage", "inventory", "stock"]):
            operation = "inventory" if "inventory" in query_lower or "stock" in query_lower else "status_check"
            warehouse_loc = location.replace(" ", "_") + "_Hub" if location else "Khartoum_Hub"
            tool_result = self.tools[1]._run(warehouse_loc, operation)
            analysis = "Warehouse capacity constraints affecting supply distribution"

        elif any(word in query_lower for word in ["supply", "procurement", "pipeline"]):
            item_category = "food_supplies" if "food" in query_lower else "medical_supplies" if "medical" in query_lower else "nfi_items"
            stage = "procurement" if "procure" in query_lower else "distribution"
            tool_result = self.tools[2]._run(item_category, stage)
            analysis = "Supply chain disruptions impacting humanitarian operations"

        else:
            # General logistics information
            tool_result = "Sudan Logistics Overview: Severe access constraints, fuel shortages, damaged infrastructure limiting operations"
            analysis = "Logistics operations face unprecedented challenges requiring coordinated solutions"

        # Generate recommendations
        recommendations = self._generate_logistics_recommendations(request.query, location)

        return HumanitarianResponse(
            sector=self.sector,
            analysis=analysis,
            data=tool_result,
            recommendations=recommendations,
            priority_level="HIGH",
            locations=[location] if location else ["Khartoum", "Port Sudan", "Kassala"]
        )

    def _generate_logistics_recommendations(self, query: str, location: str = None) -> List[str]:
        """Generate logistics-specific recommendations"""
        base_recommendations = [
            "Establish fuel reserve stockpiles at key hubs",
            "Coordinate convoy scheduling with security partners",
            "Pre-position critical supplies in forward locations",
            "Strengthen supply chain partnerships with local vendors"
        ]

        if location:
            base_recommendations.append(f"Assess road conditions and access routes to {location}")

        if "transport" in query.lower() or "convoy" in query.lower():
            base_recommendations.append("Implement convoy tracking and communication systems")

        if "warehouse" in query.lower() or "storage" in query.lower():
            base_recommendations.append("Explore additional warehouse capacity in field locations")

        if "fuel" in query.lower():
            base_recommendations.append("Coordinate with authorities on fuel allocation for humanitarian operations")

        return base_recommendations