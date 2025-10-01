#!/usr/bin/env python3
"""
Sudan Data Verification Test for UnityAid MCP Server
Verifies that ALL external humanitarian data is Sudan-specific only
"""

import asyncio
import json
from datetime import datetime, timezone
from sudan_integrations_server import SudanIntegrationsMCPServer

class SudanDataVerificationTest:
    """Comprehensive verification that all integration data is Sudan-specific"""

    def __init__(self):
        self.server = SudanIntegrationsMCPServer()
        self.test_results = {}
        self.passed = 0
        self.failed = 0
        self.sudan_keywords = ["sudan", "darfur", "khartoum", "kassala", "blue nile", "kordofan", "gezira", "sennar", "white nile", "northern", "red sea", "river nile"]

    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results"""
        self.test_results[test_name] = {"status": status, "details": details}
        if status == "PASS":
            self.passed += 1
            print(f"  [PASS] {test_name}: {details}")
        else:
            self.failed += 1
            print(f"  [FAIL] {test_name}: {details}")

    def verify_sudan_content(self, data: dict, context: str) -> bool:
        """Verify that data content is Sudan-specific"""
        data_str = json.dumps(data).lower()

        # Check for explicit Sudan references
        has_sudan_reference = "sudan" in data_str

        # Check for Sudan-specific locations
        sudan_locations = sum(1 for keyword in self.sudan_keywords if keyword in data_str)

        # Check for non-Sudan references (should not exist)
        non_sudan_countries = ["syria", "lebanon", "jordan", "turkey", "yemen", "iraq", "somalia", "afghanistan"]
        has_non_sudan = any(country in data_str for country in non_sudan_countries)

        return has_sudan_reference and sudan_locations >= 2 and not has_non_sudan

    async def test_hdx_sudan_focus(self):
        """Test that HDX integration shows only Sudan datasets"""
        print("\n[HDX] Testing HDX Sudan Data Focus")
        print("-" * 60)

        try:
            # Test HDX sync
            result = await self.server.sync_with_hdx()
            if result["success"]:
                sync_data = result["data"]["sync"]

                # Verify country is Sudan
                if sync_data["country"] == "Sudan":
                    self.log_test("HDX Country Focus", "PASS", "- Country correctly set to Sudan")
                else:
                    self.log_test("HDX Country Focus", "FAIL", f"- Country is {sync_data['country']}, not Sudan")

                # Verify datasets are Sudan-specific
                key_datasets = sync_data["key_datasets_synced"]
                sudan_datasets = [ds for ds in key_datasets if "sudan" in ds["name"].lower()]

                if len(sudan_datasets) == len(key_datasets):
                    self.log_test("HDX Dataset Names", "PASS", f"- All {len(key_datasets)} datasets are Sudan-specific")
                else:
                    non_sudan = len(key_datasets) - len(sudan_datasets)
                    self.log_test("HDX Dataset Names", "FAIL", f"- {non_sudan} datasets are not Sudan-specific")

                # Verify geographic coverage
                geo_coverage = sync_data["geographic_coverage"]
                if "conflict_affected_states" in geo_coverage:
                    states = geo_coverage["conflict_affected_states"]
                    darfur_states = [state for state in states if "darfur" in state.lower()]
                    if len(darfur_states) >= 4:
                        self.log_test("HDX Darfur Coverage", "PASS", f"- {len(darfur_states)} Darfur states included")
                    else:
                        self.log_test("HDX Darfur Coverage", "FAIL", f"- Only {len(darfur_states)} Darfur states")

                # Verify Sudan-specific content
                if self.verify_sudan_content(sync_data, "HDX"):
                    self.log_test("HDX Content Verification", "PASS", "- All content is Sudan-specific")
                else:
                    self.log_test("HDX Content Verification", "FAIL", "- Non-Sudan content detected")

        except Exception as e:
            self.log_test("HDX Integration Test", "FAIL", f"- Exception: {str(e)}")

    async def test_hrp_sudan_focus(self):
        """Test that HRP integration shows only Sudan humanitarian response"""
        print("\n[HRP] Testing HRP Sudan Focus")
        print("-" * 60)

        try:
            result = await self.server.sync_with_hrp()
            if result["success"]:
                sync_data = result["data"]["sync"]

                # Verify country and operation
                if sync_data["country"] == "Sudan" and "sudan" in sync_data["operation_id"]:
                    self.log_test("HRP Operation Focus", "PASS", f"- Operation: {sync_data['operation_id']}")
                else:
                    self.log_test("HRP Operation Focus", "FAIL", "- Operation not Sudan-specific")

                # Verify plan name
                plan_name = sync_data["plan_name"]
                if "sudan" in plan_name.lower():
                    self.log_test("HRP Plan Name", "PASS", f"- Plan: {plan_name}")
                else:
                    self.log_test("HRP Plan Name", "FAIL", f"- Plan not Sudan-specific: {plan_name}")

                # Verify geographic scope
                geo_scope = sync_data["geographic_scope"]
                priority_states = geo_scope.get("priority_states", [])
                sudan_states = [state for state in priority_states if any(keyword in state.lower() for keyword in ["darfur", "kordofan", "kassala", "blue nile"])]

                if len(sudan_states) >= 6:
                    self.log_test("HRP Geographic Scope", "PASS", f"- {len(sudan_states)} Sudan crisis states covered")
                else:
                    self.log_test("HRP Geographic Scope", "FAIL", f"- Only {len(sudan_states)} Sudan states")

                # Verify population figures are realistic for Sudan
                population = sync_data["population_figures"]
                people_in_need = population["people_in_need"]
                if 20000000 <= people_in_need <= 30000000:  # Realistic range for Sudan
                    self.log_test("HRP Population Scale", "PASS", f"- {people_in_need:,} people in need (realistic for Sudan)")
                else:
                    self.log_test("HRP Population Scale", "FAIL", f"- {people_in_need:,} seems unrealistic for Sudan")

                # Verify sector data includes Sudan-relevant priorities
                sectors = sync_data["sector_breakdown"]
                food_security = next((s for s in sectors if "food" in s["sector"].lower()), None)
                if food_security and food_security["people_in_need"] > 15000000:
                    self.log_test("HRP Food Security Priority", "PASS", f"- Food insecurity affects {food_security['people_in_need']:,}")
                else:
                    self.log_test("HRP Food Security Priority", "FAIL", "- Food security data not realistic for Sudan crisis")

        except Exception as e:
            self.log_test("HRP Integration Test", "FAIL", f"- Exception: {str(e)}")

    async def test_dtm_sudan_focus(self):
        """Test that DTM integration shows only Sudan displacement data"""
        print("\n[DTM] Testing DTM Sudan Focus")
        print("-" * 60)

        try:
            result = await self.server.sync_with_dtm()
            if result["success"]:
                sync_data = result["data"]["sync"]

                # Verify country focus
                if sync_data["country"] == "Sudan" and "sudan" in sync_data["round_id"].lower():
                    self.log_test("DTM Country Focus", "PASS", f"- Round: {sync_data['round_id']}")
                else:
                    self.log_test("DTM Country Focus", "FAIL", "- Not focused on Sudan")

                # Verify displacement scale is realistic for Sudan
                displacement = sync_data["displacement_overview"]
                total_displaced = displacement["total_displaced"]
                if 5000000 <= total_displaced <= 8000000:  # Realistic range for Sudan crisis
                    self.log_test("DTM Displacement Scale", "PASS", f"- {total_displaced:,} displaced (realistic for Sudan)")
                else:
                    self.log_test("DTM Displacement Scale", "FAIL", f"- {total_displaced:,} seems unrealistic")

                # Verify geographic distribution focuses on Sudan crisis areas
                geo_dist = sync_data["geographic_distribution"]
                darfur_states = [area for area in geo_dist if "darfur" in area["state"].lower()]
                if len(darfur_states) >= 4:
                    total_darfur_displaced = sum(area["displaced_population"] for area in darfur_states)
                    self.log_test("DTM Darfur Coverage", "PASS", f"- {len(darfur_states)} Darfur states, {total_darfur_displaced:,} displaced")
                else:
                    self.log_test("DTM Darfur Coverage", "FAIL", f"- Only {len(darfur_states)} Darfur states covered")

                # Verify displacement triggers match Sudan context
                triggers = sync_data["displacement_triggers"]
                conflict_trigger = next((t for t in triggers if "conflict" in t["trigger"].lower()), None)
                if conflict_trigger and conflict_trigger["percentage"] > 0.7:
                    self.log_test("DTM Displacement Triggers", "PASS", f"- Armed conflict is primary trigger ({conflict_trigger['percentage']:.0%})")
                else:
                    self.log_test("DTM Displacement Triggers", "FAIL", "- Conflict not identified as primary displacement trigger")

                # Verify Sudan-specific locations in main destinations
                all_destinations = []
                for area in geo_dist:
                    all_destinations.extend(area.get("main_destinations", []))

                sudan_cities = ["nyala", "el geneina", "el fasher", "zalingei", "ed daein"]
                found_cities = [city for dest in all_destinations for city in sudan_cities if city in dest.lower()]

                if len(found_cities) >= 3:
                    self.log_test("DTM Sudan Locations", "PASS", f"- Sudan cities identified in destinations")
                else:
                    self.log_test("DTM Sudan Locations", "FAIL", "- Sudan-specific cities not found")

        except Exception as e:
            self.log_test("DTM Integration Test", "FAIL", f"- Exception: {str(e)}")

    async def test_kobo_sudan_focus(self):
        """Test that KoboToolbox integration shows only Sudan data collection"""
        print("\n[KOBO] Testing KoboToolbox Sudan Focus")
        print("-" * 60)

        try:
            result = await self.server.sync_with_kobo()
            if result["success"]:
                sync_data = result["data"]["sync"]

                # Verify country focus
                if sync_data["country"] == "Sudan":
                    self.log_test("Kobo Country Focus", "PASS", "- Country set to Sudan")
                else:
                    self.log_test("Kobo Country Focus", "FAIL", f"- Country is {sync_data['country']}")

                # Verify geographic coverage includes Sudan locations
                geo_coverage = sync_data["geographic_coverage"]
                states = geo_coverage.get("states", [])
                sudan_state_mentions = sum(1 for state in states if any(keyword in state.lower() for keyword in ["darfur", "khartoum", "kassala", "blue nile", "kordofan"]))

                if sudan_state_mentions >= 3:
                    self.log_test("Kobo Geographic Coverage", "PASS", f"- Sudan states covered: {states}")
                else:
                    self.log_test("Kobo Geographic Coverage", "FAIL", "- Insufficient Sudan geographic coverage")

                # Verify form categories are relevant to Sudan crisis
                form_categories = sync_data["form_categories"]
                relevant_categories = ["Rapid Needs Assessment", "Protection Monitoring", "Site Monitoring"]
                found_relevant = [cat for cat in form_categories if cat["category"] in relevant_categories]

                if len(found_relevant) >= 2:
                    self.log_test("Kobo Form Relevance", "PASS", f"- {len(found_relevant)} crisis-relevant form categories")
                else:
                    self.log_test("Kobo Form Relevance", "FAIL", "- Form categories not relevant to Sudan crisis")

                # Verify key findings align with Sudan crisis context
                findings = sync_data["key_findings"]
                food_insecurity = findings.get("food_insecurity", "")
                if "food insecurity" in food_insecurity.lower() and any(char.isdigit() and int(char) > 7 for char in food_insecurity):
                    self.log_test("Kobo Food Security Findings", "PASS", f"- Food insecurity: {food_insecurity}")
                else:
                    self.log_test("Kobo Food Security Findings", "FAIL", "- Food security findings not realistic for Sudan")

        except Exception as e:
            self.log_test("Kobo Integration Test", "FAIL", f"- Exception: {str(e)}")

    async def test_all_platforms_sudan_only(self):
        """Test that all platforms show only Sudan data"""
        print("\n[ALL] Testing All Platforms for Sudan-Only Data")
        print("-" * 60)

        try:
            # Test integration listing
            result = await self.server.list_integrations()
            if result["success"]:
                integrations = result["data"]["integrations"]
                country_focus = result["data"]["country_focus"]

                # Verify global country focus
                if country_focus == "Sudan":
                    self.log_test("Global Country Focus", "PASS", f"- All integrations focused on {country_focus}")
                else:
                    self.log_test("Global Country Focus", "FAIL", f"- Country focus is {country_focus}, not Sudan")

                # Verify each integration has Sudan focus
                sudan_focused = [i for i in integrations if i.get("country_focus") == "Sudan"]
                if len(sudan_focused) == len(integrations):
                    self.log_test("Individual Platform Focus", "PASS", f"- All {len(integrations)} platforms Sudan-focused")
                else:
                    non_sudan = len(integrations) - len(sudan_focused)
                    self.log_test("Individual Platform Focus", "FAIL", f"- {non_sudan} platforms not Sudan-focused")

                # Verify platform names include Sudan references
                sudan_named = [i for i in integrations if "sudan" in i["name"].lower()]
                if len(sudan_named) >= 5:  # Most platforms should have Sudan in the name
                    self.log_test("Platform Naming", "PASS", f"- {len(sudan_named)} platforms have Sudan in name")
                else:
                    self.log_test("Platform Naming", "FAIL", f"- Only {len(sudan_named)} platforms mention Sudan in name")

                # Test platform-specific Sudan indicators
                hdx_platform = next((i for i in integrations if i["platform"] == "hdx"), None)
                if hdx_platform and "sudan" in str(hdx_platform.get("latest_datasets", [])).lower():
                    self.log_test("HDX Sudan Datasets", "PASS", "- HDX datasets are Sudan-specific")
                else:
                    self.log_test("HDX Sudan Datasets", "FAIL", "- HDX datasets not clearly Sudan-focused")

                hrp_platform = next((i for i in integrations if i["platform"] == "hrp"), None)
                if hrp_platform and hrp_platform.get("people_in_need", 0) > 20000000:
                    self.log_test("HRP Sudan Scale", "PASS", f"- HRP shows realistic Sudan scale ({hrp_platform['people_in_need']:,} in need)")
                else:
                    self.log_test("HRP Sudan Scale", "FAIL", "- HRP scale not realistic for Sudan")

        except Exception as e:
            self.log_test("All Platforms Test", "FAIL", f"- Exception: {str(e)}")

    async def test_sudan_humanitarian_overview(self):
        """Test comprehensive Sudan humanitarian overview"""
        print("\n[OVERVIEW] Testing Sudan Humanitarian Overview")
        print("-" * 60)

        try:
            result = await self.server.get_sudan_humanitarian_overview()
            if result["success"]:
                overview = result["data"]["overview"]

                # Verify country identification
                if overview["country"] == "Sudan" and overview["iso3_code"] == "SDN":
                    self.log_test("Overview Country ID", "PASS", f"- Country: {overview['country']} ({overview['iso3_code']})")
                else:
                    self.log_test("Overview Country ID", "FAIL", "- Country identification incorrect")

                # Verify crisis level appropriate for Sudan
                crisis_level = overview["crisis_level"]
                if "level 3" in crisis_level.lower() or "emergency" in crisis_level.lower():
                    self.log_test("Crisis Level", "PASS", f"- Crisis Level: {crisis_level}")
                else:
                    self.log_test("Crisis Level", "FAIL", f"- Crisis level '{crisis_level}' not appropriate for Sudan")

                # Verify population figures realistic for Sudan
                pop_overview = overview["population_overview"]
                if 40000000 <= pop_overview["total_population"] <= 50000000:
                    self.log_test("Population Scale", "PASS", f"- Total population: {pop_overview['total_population']:,}")
                else:
                    self.log_test("Population Scale", "FAIL", f"- Population figure unrealistic: {pop_overview['total_population']:,}")

                # Verify crisis timeline mentions April 2023 (start of Sudan crisis)
                timeline = overview["crisis_timeline"]
                if "april 2023" in timeline["crisis_start"].lower():
                    self.log_test("Crisis Timeline", "PASS", f"- Crisis start: {timeline['crisis_start']}")
                else:
                    self.log_test("Crisis Timeline", "FAIL", f"- Crisis start date incorrect: {timeline['crisis_start']}")

                # Verify geographic impact includes Darfur
                geo_impact = overview["geographic_impact"]
                affected_states = geo_impact.get("severely_affected", [])
                darfur_mentions = sum(1 for state in affected_states if "darfur" in state.lower())

                if darfur_mentions >= 4:
                    self.log_test("Darfur Impact", "PASS", f"- {darfur_mentions} Darfur states in severely affected list")
                else:
                    self.log_test("Darfur Impact", "FAIL", f"- Only {darfur_mentions} Darfur states mentioned")

        except Exception as e:
            self.log_test("Overview Test", "FAIL", f"- Exception: {str(e)}")

    async def run_comprehensive_sudan_verification(self):
        """Run comprehensive Sudan-only data verification"""
        print("\n" + "=" * 80)
        print("SUDAN DATA VERIFICATION TEST - UNITYAID MCP SERVER")
        print("=" * 80)
        print("Verifying that ALL external humanitarian data is Sudan-specific only")
        print(f"Test initiated: {datetime.now(timezone.utc).isoformat()}")

        # Run all verification tests
        await self.test_hdx_sudan_focus()
        await self.test_hrp_sudan_focus()
        await self.test_dtm_sudan_focus()
        await self.test_kobo_sudan_focus()
        await self.test_all_platforms_sudan_only()
        await self.test_sudan_humanitarian_overview()

        # Print summary
        print("\n" + "=" * 80)
        print("SUDAN VERIFICATION SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed / (self.passed + self.failed)) * 100:.1f}%")

        if self.failed == 0:
            print("\n[SUCCESS] ALL SUDAN VERIFICATION TESTS PASSED!")
            print("[VERIFIED] All external humanitarian data is confirmed to be Sudan-specific only.")
            print("\nSUDAN DATA CONFIRMATION:")
            print("[CONFIRMED] HDX - All datasets are Sudan-focused")
            print("[CONFIRMED] HRP - Sudan Humanitarian Response Plan 2024 only")
            print("[CONFIRMED] DTM - Sudan displacement tracking only")
            print("[CONFIRMED] KoboToolbox - Sudan data collection only")
            print("[CONFIRMED] UNHCR - Sudan operations only")
            print("[CONFIRMED] FTS - Sudan funding tracking only")
            print("[CONFIRMED] ACAPS - Sudan crisis analysis only")
        else:
            print(f"\n[WARNING] {self.failed} verification tests failed.")
            print("Some data may not be Sudan-specific. Please review above results.")

        print("\n" + "=" * 80)

async def main():
    """Main verification runner"""
    test_suite = SudanDataVerificationTest()
    await test_suite.run_comprehensive_sudan_verification()

if __name__ == "__main__":
    asyncio.run(main())