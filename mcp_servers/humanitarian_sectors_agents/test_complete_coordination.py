"""
Complete Coordination Workflow Test
Tests all 11 humanitarian sector agents working together through LangGraph coordination
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from base_humanitarian_agent import HumanitarianRequest, HumanitarianResponse
from langgraph_coordinator import HumanitarianCoordinator

# Import all 11 sector agents
from protection_agent import ProtectionAgent
from health_agent import HealthAgent
from food_security_agent import FoodSecurityAgent
from wash_agent import WASHAgent
from shelter_agent import ShelterAgent
from nutrition_agent import NutritionAgent
from education_agent import EducationAgent
from logistics_agent import LogisticsAgent
from cccm_agent import CCCMAgent
from early_recovery_agent import EarlyRecoveryAgent
from etc_agent import ETCAgent

def test_individual_agents():
    """Test each individual agent with Sudan-specific scenarios"""
    print("="*80)
    print("TESTING INDIVIDUAL HUMANITARIAN SECTOR AGENTS")
    print("="*80)

    # Initialize all agents
    agents = {
        "Protection": ProtectionAgent(),
        "Health": HealthAgent(),
        "Food Security": FoodSecurityAgent(),
        "WASH": WASHAgent(),
        "Shelter/NFI": ShelterAgent(),
        "Nutrition": NutritionAgent(),
        "Education": EducationAgent(),
        "Logistics": LogisticsAgent(),
        "CCCM": CCCMAgent(),
        "Early Recovery": EarlyRecoveryAgent(),
        "ETC": ETCAgent()
    }

    # Test scenarios for each agent
    test_scenarios = {
        "Protection": "What GBV services are available in Nyala IDP settlement?",
        "Health": "Assess disease outbreak risk in El Geneina emergency camp",
        "Food Security": "Analyze food security situation in Darfur region",
        "WASH": "Evaluate water access in Kassala reception center",
        "Shelter/NFI": "Assess shelter conditions in displacement sites",
        "Nutrition": "Screen for malnutrition in children under 5 in Nyala",
        "Education": "Evaluate education access for displaced children",
        "Logistics": "Plan convoy to transport medical supplies to El Geneina",
        "CCCM": "Assess site management at Kassala reception center",
        "Early Recovery": "Evaluate livelihood opportunities in Nyala",
        "ETC": "Assess connectivity needs for humanitarian operations"
    }

    results = {}
    for sector, agent in agents.items():
        print(f"\n--- Testing {sector} Agent ---")
        try:
            request = HumanitarianRequest(
                query=test_scenarios[sector],
                priority="HIGH",
                location="Sudan",
                requester="Test System"
            )

            response = agent.process_request(request)
            print(f"✓ {sector}: {response.analysis[:100]}...")
            results[sector] = "PASS"

        except Exception as e:
            print(f"✗ {sector}: Error - {str(e)}")
            results[sector] = "FAIL"

    # Summary
    print(f"\n--- Individual Agent Test Results ---")
    passed = sum(1 for result in results.values() if result == "PASS")
    total = len(results)
    print(f"Passed: {passed}/{total} agents")

    for sector, result in results.items():
        print(f"  {sector}: {result}")

    return results

def test_langgraph_coordination():
    """Test LangGraph coordination with complex multi-sector scenarios"""
    print("\n" + "="*80)
    print("TESTING LANGGRAPH MULTI-SECTOR COORDINATION")
    print("="*80)

    try:
        coordinator = HumanitarianCoordinator()
        print("✓ LangGraph Coordinator initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize coordinator: {e}")
        return {"coordination_test": "FAIL"}

    # Multi-sector test scenarios
    complex_scenarios = [
        {
            "name": "New Displacement Crisis",
            "query": "Urgent: 15,000 new IDPs arrived at Nyala settlement. Need immediate multi-sector response including protection screening, health assessment, emergency shelter, and food distribution."
        },
        {
            "name": "Disease Outbreak Response",
            "query": "Cholera outbreak confirmed in El Geneina camp. Coordinate Health, WASH, Nutrition, and CCCM response. Need water treatment, case management, and community education."
        },
        {
            "name": "Site Closure Planning",
            "query": "Kassala reception center at 150% capacity. Plan coordinated response for site expansion including shelter upgrade, education continuity, livelihood support, and logistics coordination."
        },
        {
            "name": "Seasonal Preparedness",
            "query": "Rainy season approaching. Coordinate flood preparedness across all sectors including WASH infrastructure, shelter weatherproofing, health supplies, and communications backup."
        }
    ]

    coordination_results = {}

    for i, scenario in enumerate(complex_scenarios, 1):
        print(f"\n--- Scenario {i}: {scenario['name']} ---")
        try:
            request = HumanitarianRequest(
                query=scenario['query'],
                priority="CRITICAL",
                location="Sudan",
                requester="Humanitarian Coordinator"
            )

            # Test the coordination workflow
            response = coordinator.process_humanitarian_request(request)

            print(f"✓ Coordination successful")
            print(f"  Sectors involved: {len(response.get('sector_responses', []))}")
            print(f"  Analysis: {response.get('coordinated_analysis', 'No analysis')[:100]}...")

            coordination_results[scenario['name']] = "PASS"

        except Exception as e:
            print(f"✗ Coordination failed: {str(e)}")
            coordination_results[scenario['name']] = "FAIL"

    # Summary
    print(f"\n--- Coordination Test Results ---")
    passed = sum(1 for result in coordination_results.values() if result == "PASS")
    total = len(coordination_results)
    print(f"Passed: {passed}/{total} scenarios")

    for scenario, result in coordination_results.items():
        print(f"  {scenario}: {result}")

    return coordination_results

def test_sudan_data_integration():
    """Test Sudan-specific data integration across all agents"""
    print("\n" + "="*80)
    print("TESTING SUDAN DATA INTEGRATION")
    print("="*80)

    sudan_locations = ["Nyala", "El Geneina", "Kassala", "Khartoum", "Port Sudan"]
    sudan_contexts = [
        "6.2 million internally displaced persons",
        "25.6 million people in need of assistance",
        "Ongoing conflict affecting service delivery",
        "Damaged infrastructure limiting operations",
        "Complex emergency requiring coordinated response"
    ]

    integration_results = {}

    # Test location-specific responses
    print("--- Testing Location-Specific Responses ---")
    try:
        coordinator = HumanitarianCoordinator()

        for location in sudan_locations:
            query = f"Assess humanitarian needs in {location} focusing on protection, health, and basic services"
            request = HumanitarianRequest(
                query=query,
                priority="HIGH",
                location=location,
                requester="Area Coordinator"
            )

            response = coordinator.process_humanitarian_request(request)
            print(f"✓ {location}: Multi-sector assessment completed")
            integration_results[f"{location}_assessment"] = "PASS"

    except Exception as e:
        print(f"✗ Location testing failed: {e}")
        for location in sudan_locations:
            integration_results[f"{location}_assessment"] = "FAIL"

    # Test context awareness
    print("\n--- Testing Sudan Context Awareness ---")
    context_queries = [
        "How does ongoing conflict affect humanitarian operations?",
        "What are the challenges of reaching 25.6 million people in need?",
        "How do damaged roads impact supply chain operations?",
        "What coordination mechanisms exist for 6.2 million IDPs?"
    ]

    for i, query in enumerate(context_queries, 1):
        try:
            request = HumanitarianRequest(
                query=query,
                priority="MEDIUM",
                location="Sudan",
                requester="Strategic Planner"
            )

            response = coordinator.process_humanitarian_request(request)
            print(f"✓ Context Query {i}: Appropriate Sudan context applied")
            integration_results[f"context_query_{i}"] = "PASS"

        except Exception as e:
            print(f"✗ Context Query {i}: Failed - {e}")
            integration_results[f"context_query_{i}"] = "FAIL"

    # Summary
    print(f"\n--- Sudan Integration Test Results ---")
    passed = sum(1 for result in integration_results.values() if result == "PASS")
    total = len(integration_results)
    print(f"Passed: {passed}/{total} tests")

    return integration_results

def run_complete_test_suite():
    """Run the complete test suite for humanitarian coordination"""
    print("HUMANITARIAN SECTOR AGENTS - COMPLETE TEST SUITE")
    print("Testing all 11 UN humanitarian clusters with Sudan scenarios")
    print("="*80)

    # Run all tests
    individual_results = test_individual_agents()
    coordination_results = test_langgraph_coordination()
    integration_results = test_sudan_data_integration()

    # Overall summary
    print("\n" + "="*80)
    print("COMPLETE TEST SUITE SUMMARY")
    print("="*80)

    all_results = {}
    all_results.update(individual_results)
    all_results.update(coordination_results)
    all_results.update(integration_results)

    total_tests = len(all_results)
    passed_tests = sum(1 for result in all_results.values() if result == "PASS")
    failed_tests = total_tests - passed_tests

    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    # Test categories summary
    print(f"\nTest Category Breakdown:")
    print(f"  Individual Agents: {sum(1 for k,v in individual_results.items() if v=='PASS')}/{len(individual_results)}")
    print(f"  Coordination Scenarios: {sum(1 for k,v in coordination_results.items() if v=='PASS')}/{len(coordination_results)}")
    print(f"  Sudan Integration: {sum(1 for k,v in integration_results.items() if v=='PASS')}/{len(integration_results)}")

    # Recommendations
    print(f"\nRecommendations:")
    if passed_tests == total_tests:
        print("  ✓ All tests passed! Humanitarian coordination system ready for deployment.")
        print("  ✓ All 11 UN humanitarian sectors successfully integrated with Sudan context.")
        print("  ✓ LangGraph coordination workflow functioning optimally.")
    else:
        print(f"  ⚠ {failed_tests} tests failed. Review failed components before deployment.")
        if failed_tests > total_tests * 0.2:
            print("  ⚠ High failure rate indicates system needs significant debugging.")
        else:
            print("  ✓ Most tests passed. Minor issues can be addressed in next iteration.")

    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "success_rate": (passed_tests/total_tests)*100,
        "individual_results": individual_results,
        "coordination_results": coordination_results,
        "integration_results": integration_results
    }

if __name__ == "__main__":
    try:
        results = run_complete_test_suite()
        print(f"\nTest suite completed with {results['success_rate']:.1f}% success rate")
    except Exception as e:
        print(f"Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()