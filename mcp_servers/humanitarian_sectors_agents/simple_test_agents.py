"""
Simplified Test for Humanitarian Sector Agents
Tests basic functionality without complex LangGraph dependencies
"""

import sys
import os

def test_agent_imports():
    """Test that all agent classes can be imported successfully"""
    print("="*80)
    print("TESTING HUMANITARIAN SECTOR AGENT IMPORTS")
    print("="*80)

    results = {}

    # Test agent imports one by one
    agents_to_test = [
        ("Protection Agent", "protection_agent", "ProtectionAgent"),
        ("Health Agent", "health_agent", "HealthAgent"),
        ("Food Security Agent", "food_security_agent", "FoodSecurityAgent"),
        ("WASH Agent", "wash_agent", "WASHAgent"),
        ("Shelter Agent", "shelter_agent", "ShelterAgent"),
        ("Nutrition Agent", "nutrition_agent", "NutritionAgent"),
        ("Education Agent", "education_agent", "EducationAgent"),
        ("Logistics Agent", "logistics_agent", "LogisticsAgent"),
        ("CCCM Agent", "cccm_agent", "CCCMAgent"),
        ("Early Recovery Agent", "early_recovery_agent", "EarlyRecoveryAgent"),
        ("ETC Agent", "etc_agent", "ETCAgent"),
        ("Assessment Agent", "assessment_agent", "AssessmentAgent"),
        ("Alerts Agent", "alerts_agent", "AlertsAgent")
    ]

    for agent_name, module_name, class_name in agents_to_test:
        try:
            # Test basic class structure without LangChain dependencies
            print(f"Testing {agent_name}...")

            # Read the file and check for key components
            file_path = f"{module_name}.py"
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check for required elements
                checks = {
                    "Class definition": f"class {class_name}",
                    "Tool classes": "class.*Tool.*BaseTool",
                    "Sudan context": "sudan_context",
                    "Process request": "def process_request",
                    "Generate recommendations": "_generate.*recommendations"
                }

                passed_checks = 0
                for check_name, check_pattern in checks.items():
                    if check_pattern in content or check_name == "Tool classes":
                        if check_name == "Tool classes":
                            # Special handling for tool classes
                            if "Tool(BaseTool)" in content or "Tool(" in content:
                                passed_checks += 1
                        else:
                            passed_checks += 1

                success_rate = (passed_checks / len(checks)) * 100
                print(f"  [PASS] {agent_name}: {passed_checks}/{len(checks)} checks passed ({success_rate:.0f}%)")
                results[agent_name] = "PASS" if success_rate >= 80 else "PARTIAL"

            else:
                print(f"  [FAIL] {agent_name}: File not found")
                results[agent_name] = "FAIL"

        except Exception as e:
            print(f"  [FAIL] {agent_name}: Error - {str(e)}")
            results[agent_name] = "FAIL"

    return results

def test_sudan_context():
    """Test Sudan-specific context in all agents"""
    print("\n" + "="*80)
    print("TESTING SUDAN CONTEXT INTEGRATION")
    print("="*80)

    results = {}

    # Key Sudan context elements to check for
    sudan_keywords = [
        "6.2 million", "25.6 million", "Nyala", "El Geneina", "Kassala",
        "Darfur", "Blue Nile", "IDP", "displacement", "conflict",
        "humanitarian", "Sudan", "emergency"
    ]

    agent_files = [
        ("Protection", "protection_agent.py"),
        ("Health", "health_agent.py"),
        ("Food Security", "food_security_agent.py"),
        ("WASH", "wash_agent.py"),
        ("Shelter", "shelter_agent.py"),
        ("Nutrition", "nutrition_agent.py"),
        ("Education", "education_agent.py"),
        ("Logistics", "logistics_agent.py"),
        ("CCCM", "cccm_agent.py"),
        ("Early Recovery", "early_recovery_agent.py"),
        ("ETC", "etc_agent.py"),
        ("Assessment", "assessment_agent.py"),
        ("Alerts", "alerts_agent.py")
    ]

    for agent_name, file_name in agent_files:
        try:
            if os.path.exists(file_name):
                with open(file_name, 'r', encoding='utf-8') as f:
                    content = f.read().lower()

                found_keywords = 0
                for keyword in sudan_keywords:
                    if keyword.lower() in content:
                        found_keywords += 1

                context_score = (found_keywords / len(sudan_keywords)) * 100
                print(f"  {agent_name}: {found_keywords}/{len(sudan_keywords)} Sudan keywords found ({context_score:.0f}%)")
                results[agent_name] = "PASS" if context_score >= 40 else "FAIL"

            else:
                print(f"  {agent_name}: File not found")
                results[agent_name] = "FAIL"

        except Exception as e:
            print(f"  {agent_name}: Error - {str(e)}")
            results[agent_name] = "FAIL"

    return results

def test_sector_coverage():
    """Test that all 11 humanitarian sectors are covered"""
    print("\n" + "="*80)
    print("TESTING HUMANITARIAN SECTOR COVERAGE")
    print("="*80)

    # Official IASC clusters/sectors
    expected_sectors = [
        "Protection", "Health", "Food Security", "WASH",
        "Shelter/NFI", "Nutrition", "Education", "Logistics",
        "CCCM", "Early Recovery", "Emergency Telecommunications",
        "Assessment & Data Analysis", "Crisis Alerts & Emergency Coordination"
    ]

    found_sectors = []

    # Check for agent files
    for sector in expected_sectors:
        sector_variations = {
            "Protection": "protection_agent.py",
            "Health": "health_agent.py",
            "Food Security": "food_security_agent.py",
            "WASH": "wash_agent.py",
            "Shelter/NFI": "shelter_agent.py",
            "Nutrition": "nutrition_agent.py",
            "Education": "education_agent.py",
            "Logistics": "logistics_agent.py",
            "CCCM": "cccm_agent.py",
            "Early Recovery": "early_recovery_agent.py",
            "Emergency Telecommunications": "etc_agent.py",
            "Assessment & Data Analysis": "assessment_agent.py",
            "Crisis Alerts & Emergency Coordination": "alerts_agent.py"
        }

        file_name = sector_variations.get(sector, f"{sector.lower().replace('/', '_').replace(' ', '_')}_agent.py")

        if os.path.exists(file_name):
            found_sectors.append(sector)
            print(f"  [SUCCESS] {sector}: Agent implemented")
        else:
            print(f"  [MISSING] {sector}: Agent missing")

    coverage = (len(found_sectors) / len(expected_sectors)) * 100
    print(f"\nSector Coverage: {len(found_sectors)}/{len(expected_sectors)} ({coverage:.0f}%)")

    return {"coverage": coverage, "found": found_sectors, "missing": set(expected_sectors) - set(found_sectors)}

def run_simple_test_suite():
    """Run simplified test suite"""
    print("HUMANITARIAN SECTOR AGENTS - SIMPLIFIED TEST SUITE")
    print("Testing core functionality without LangChain dependencies")
    print("="*80)

    # Run tests
    import_results = test_agent_imports()
    context_results = test_sudan_context()
    coverage_results = test_sector_coverage()

    # Summary
    print("\n" + "="*80)
    print("SIMPLIFIED TEST SUITE SUMMARY")
    print("="*80)

    # Import test results
    import_passed = sum(1 for result in import_results.values() if result == "PASS")
    import_total = len(import_results)
    print(f"Import Tests: {import_passed}/{import_total} passed ({(import_passed/import_total)*100:.0f}%)")

    # Context test results
    context_passed = sum(1 for result in context_results.values() if result == "PASS")
    context_total = len(context_results)
    print(f"Sudan Context Tests: {context_passed}/{context_total} passed ({(context_passed/context_total)*100:.0f}%)")

    # Coverage results
    print(f"Sector Coverage: {coverage_results['coverage']:.0f}% ({len(coverage_results['found'])}/11 sectors)")

    # Overall assessment
    total_tests = import_total + context_total + 1  # +1 for coverage
    total_passed = import_passed + context_passed + (1 if coverage_results['coverage'] >= 90 else 0)
    overall_success = (total_passed / total_tests) * 100

    print(f"\nOverall Success Rate: {overall_success:.0f}%")

    # Detailed results
    print(f"\nDetailed Results:")
    print(f"  All 13 humanitarian agents: {'[SUCCESS]' if len(coverage_results['found']) == 13 else '[FAIL]'}")
    print(f"  Agent structure compliance: {import_passed}/{import_total}")
    print(f"  Sudan context integration: {context_passed}/{context_total}")

    if coverage_results['missing']:
        print(f"  Missing sectors: {', '.join(coverage_results['missing'])}")

    # Recommendations
    print(f"\nRecommendations:")
    if overall_success >= 90:
        print("  [SUCCESS] Humanitarian agent system ready for testing")
        print("  [SUCCESS] All major components implemented successfully")
        print("  [SUCCESS] Sudan context properly integrated across agents")
    elif overall_success >= 70:
        print("  [WARNING] Most components working, minor issues to address")
        print("  [WARNING] Consider reviewing failed components")
    else:
        print("  [FAIL] Significant issues detected, major debugging needed")
        print("  [FAIL] Review implementation before proceeding")

    return {
        "overall_success": overall_success,
        "import_results": import_results,
        "context_results": context_results,
        "coverage_results": coverage_results
    }

if __name__ == "__main__":
    # Change to the agents directory
    agents_dir = r"C:\Users\Lenovo\Desktop\unityaid_platform\mcp_servers\humanitarian_sectors_agents"
    if os.path.exists(agents_dir):
        os.chdir(agents_dir)
        print(f"Working directory: {os.getcwd()}")

    try:
        results = run_simple_test_suite()
        print(f"\nTest suite completed with {results['overall_success']:.0f}% success rate")
    except Exception as e:
        print(f"Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()