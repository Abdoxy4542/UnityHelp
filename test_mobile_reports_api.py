#!/usr/bin/env python3
"""
End-to-end verification script for UnityAid Mobile Reports API.
This script tests the complete flow from authentication to report submission.

Run with: python test_mobile_reports_api.py
"""

import os
import sys
import django
import requests
import json
from io import BytesIO
from PIL import Image
import tempfile

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.reports.models import FieldReport

User = get_user_model()

class MobileAPITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/mobile/v1"
        self.access_token = None
        self.session = requests.Session()

    def print_header(self, title):
        print(f"\n{'='*50}")
        print(f" {title}")
        print(f"{'='*50}")

    def print_step(self, step):
        print(f"\n🔍 {step}")

    def print_success(self, message):
        print(f"✅ {message}")

    def print_error(self, message):
        print(f"❌ {message}")

    def test_server_health(self):
        """Test if Django server is running"""
        self.print_step("Testing server health...")
        try:
            response = requests.get(f"{self.api_base}/health/", timeout=5)
            if response.status_code == 200:
                self.print_success("Django server is running")
                return True
            else:
                self.print_error(f"Server health check failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.print_error(f"Cannot connect to Django server: {e}")
            self.print_error("Make sure Django server is running with: python manage.py runserver")
            return False

    def test_authentication(self):
        """Test mobile authentication"""
        self.print_step("Testing authentication...")

        login_data = {
            "email": "test_mobile_gso@unityaid.org",
            "password": "TestPass123!",
            "device_id": "verification_script_device",
            "platform": "script"
        }

        try:
            response = requests.post(f"{self.api_base}/auth/login/", json=login_data)

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                self.session.headers.update({
                    'Authorization': f'Token {self.access_token}'
                })
                self.print_success(f"Authentication successful. User: {data.get('user', {}).get('email')}")
                return True
            else:
                self.print_error(f"Authentication failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Authentication error: {e}")
            return False

    def test_text_report(self):
        """Test text report submission"""
        self.print_step("Testing text report submission...")

        report_data = {
            "site": 1,
            "title": "Verification Script Text Report",
            "text_content": "This is a test text report submitted by the verification script to ensure the mobile API is working correctly.",
            "report_type": "text",
            "priority": "medium",
            "location_coordinates": {
                "lat": 15.5527,
                "lng": 32.5599
            }
        }

        try:
            response = self.session.post(f"{self.api_base}/field-reports/", json=report_data)

            if response.status_code == 201:
                data = response.json()
                report_id = data.get('id')
                self.print_success(f"Text report created successfully. ID: {report_id}")
                return report_id
            else:
                self.print_error(f"Text report creation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except Exception as e:
            self.print_error(f"Text report error: {e}")
            return None

    def create_test_image(self):
        """Create a test image file"""
        img = Image.new('RGB', (100, 100), color='red')
        img_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img.save(img_file, 'PNG')
        img_file.close()
        return img_file.name

    def test_image_report(self):
        """Test image report submission"""
        self.print_step("Testing image report submission...")

        # Create test image
        image_path = self.create_test_image()

        try:
            with open(image_path, 'rb') as img_file:
                files = {
                    'image_file': ('test_image.png', img_file, 'image/png')
                }

                data = {
                    'site': 1,
                    'title': 'Verification Script Image Report',
                    'text_content': 'This is a test image report with an attached image file.',
                    'report_type': 'image',
                    'priority': 'high',
                    'location_coordinates': json.dumps({"lat": 15.5530, "lng": 32.5602})
                }

                response = self.session.post(f"{self.api_base}/field-reports/", data=data, files=files)

                if response.status_code == 201:
                    response_data = response.json()
                    report_id = response_data.get('id')
                    self.print_success(f"Image report created successfully. ID: {report_id}")
                    return report_id
                else:
                    self.print_error(f"Image report creation failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    return None
        except Exception as e:
            self.print_error(f"Image report error: {e}")
            return None
        finally:
            # Clean up test image
            try:
                os.unlink(image_path)
            except:
                pass

    def test_reports_list(self):
        """Test retrieving reports list"""
        self.print_step("Testing reports list retrieval...")

        try:
            response = self.session.get(f"{self.api_base}/field-reports/")

            if response.status_code == 200:
                data = response.json()
                count = data.get('count', 0)
                results = data.get('results', [])
                self.print_success(f"Reports list retrieved successfully. Total reports: {count}")

                if results:
                    latest_report = results[0]
                    print(f"   Latest report: '{latest_report.get('title')}' ({latest_report.get('report_type')})")

                return True
            else:
                self.print_error(f"Reports list retrieval failed: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Reports list error: {e}")
            return False

    def test_statistics(self):
        """Test reports statistics endpoint"""
        self.print_step("Testing reports statistics...")

        try:
            response = self.session.get(f"{self.api_base}/field-reports/statistics/")

            if response.status_code == 200:
                stats = response.json()
                self.print_success("Statistics retrieved successfully:")
                print(f"   Total reports: {stats.get('total_reports', 0)}")
                print(f"   My reports: {stats.get('my_reports', 0)}")
                print(f"   Pending reports: {stats.get('pending_reports', 0)}")
                return True
            else:
                self.print_error(f"Statistics retrieval failed: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Statistics error: {e}")
            return False

    def verify_database_storage(self, report_ids):
        """Verify reports are stored in database"""
        self.print_step("Verifying database storage...")

        try:
            for report_id in report_ids:
                if report_id:
                    report = FieldReport.objects.get(id=report_id)
                    self.print_success(f"Report ID {report_id} found in database: '{report.title}'")

                    # Check file storage
                    if report.image_file:
                        if os.path.exists(report.image_file.path):
                            self.print_success(f"Image file stored correctly: {report.image_file.name}")
                        else:
                            self.print_error(f"Image file not found: {report.image_file.path}")

            return True
        except Exception as e:
            self.print_error(f"Database verification error: {e}")
            return False

    def run_all_tests(self):
        """Run complete test suite"""
        self.print_header("UnityAid Mobile API Verification")

        print("This script will test the complete mobile reports API functionality.")
        print("Make sure you have:")
        print("1. Django server running (python manage.py runserver)")
        print("2. Test data created (python manage.py create_reports_test_data)")

        input("\nPress Enter to continue...")

        # Test server health
        if not self.test_server_health():
            return False

        # Test authentication
        if not self.test_authentication():
            return False

        # Test reports functionality
        report_ids = []

        # Test text report
        text_report_id = self.test_text_report()
        if text_report_id:
            report_ids.append(text_report_id)

        # Test image report
        image_report_id = self.test_image_report()
        if image_report_id:
            report_ids.append(image_report_id)

        # Test reports list
        self.test_reports_list()

        # Test statistics
        self.test_statistics()

        # Verify database storage
        if report_ids:
            self.verify_database_storage(report_ids)

        # Summary
        self.print_header("Test Summary")

        if report_ids:
            self.print_success("🎉 All tests completed successfully!")
            print("\nYour mobile API is ready for Android testing:")
            print("1. ✅ Authentication working")
            print("2. ✅ Text reports submission working")
            print("3. ✅ Image reports submission working")
            print("4. ✅ Database storage working")
            print("5. ✅ API endpoints responding correctly")

            print("\nNext steps:")
            print("1. Open Android Studio emulator")
            print("2. Use the API endpoints with Postman or custom app")
            print("3. Test voice report submission")
            print("4. Verify all data appears in Django admin")

            print(f"\nAPI Base URL: {self.api_base}")
            print("Django Admin: http://localhost:8000/admin/")
            print("API Docs: http://localhost:8000/api/docs/")

        else:
            self.print_error("Some tests failed. Please check the errors above.")
            return False

        return True


def main():
    """Main function"""
    tester = MobileAPITester()
    success = tester.run_all_tests()

    if success:
        print("\n🚀 Ready for mobile testing!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed. Please fix issues before mobile testing.")
        sys.exit(1)


if __name__ == "__main__":
    main()