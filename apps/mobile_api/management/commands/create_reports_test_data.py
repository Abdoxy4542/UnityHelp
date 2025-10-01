"""
Django management command to create test data for mobile reports testing.
Run with: python manage.py create_reports_test_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.accounts.models import Organization
from apps.sites.models import Site, State, Locality, SiteType
from apps.reports.models import FieldReport, ReportTag

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test data for mobile reports testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing test data before creating new data',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating test data for mobile reports testing...'))

        if options['reset']:
            self.stdout.write('Deleting existing test data...')
            User.objects.filter(email__contains='test_mobile').delete()
            Organization.objects.filter(name__contains='Test Mobile').delete()
            Site.objects.filter(name__contains='Test Mobile').delete()
            FieldReport.objects.filter(title__contains='Test Mobile').delete()

        # Create organizations
        ngo_org = Organization.objects.get_or_create(
            name='Test Mobile NGO',
            defaults={
                'organization_type': 'ngo',
                'is_active': True,
                'description': 'Test NGO for mobile reports testing'
            }
        )[0]

        un_org = Organization.objects.get_or_create(
            name='Test Mobile UN Agency',
            defaults={
                'organization_type': 'un_agency',
                'is_active': True,
                'description': 'Test UN Agency for mobile reports testing'
            }
        )[0]

        # Create geographic data
        state = State.objects.get_or_create(
            name='Test Mobile State',
            defaults={
                'name_ar': 'ولاية تجريبية للموبايل',
                'code': 'TMS'
            }
        )[0]

        locality = Locality.objects.get_or_create(
            name='Test Mobile Locality',
            state=state,
            defaults={
                'name_ar': 'محلية تجريبية للموبايل',
                'code': 'TML'
            }
        )[0]

        # Create site type
        site_type = SiteType.objects.get_or_create(
            name='Test Mobile Camp',
            defaults={
                'category': 'camp',
                'description': 'Test camp type for mobile testing'
            }
        )[0]

        # Create test users
        gso_user = User.objects.get_or_create(
            email='test_mobile_gso@unityaid.org',
            defaults={
                'username': 'test_mobile_gso',
                'first_name': 'Test',
                'last_name': 'GSO',
                'role': 'gso',
                'organization': ngo_org,
                'is_active': True,
                'phone_number': '+249123456789',
                'preferred_language': 'en'
            }
        )[0]
        gso_user.set_password('TestPass123!')
        gso_user.save()

        ngo_user = User.objects.get_or_create(
            email='test_mobile_ngo@unityaid.org',
            defaults={
                'username': 'test_mobile_ngo',
                'first_name': 'Test',
                'last_name': 'NGO User',
                'role': 'ngo_user',
                'organization': ngo_org,
                'is_active': True,
                'phone_number': '+249123456788',
                'preferred_language': 'en'
            }
        )[0]
        ngo_user.set_password('TestPass123!')
        ngo_user.save()

        admin_user = User.objects.get_or_create(
            email='test_mobile_admin@unityaid.org',
            defaults={
                'username': 'test_mobile_admin',
                'first_name': 'Test',
                'last_name': 'Admin',
                'role': 'admin',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True,
                'phone_number': '+249123456787',
                'preferred_language': 'en'
            }
        )[0]
        admin_user.set_password('TestPass123!')
        admin_user.save()

        cluster_lead = User.objects.get_or_create(
            email='test_mobile_cluster@unityaid.org',
            defaults={
                'username': 'test_mobile_cluster',
                'first_name': 'Test',
                'last_name': 'Cluster Lead',
                'role': 'cluster_lead',
                'organization': un_org,
                'is_active': True,
                'phone_number': '+249123456786',
                'preferred_language': 'en'
            }
        )[0]
        cluster_lead.set_password('TestPass123!')
        cluster_lead.save()

        # Create test sites
        site1 = Site.objects.get_or_create(
            name='Test Mobile Camp Alpha',
            defaults={
                'name_ar': 'مخيم الفا التجريبي للموبايل',
                'site_type': site_type,
                'state': state,
                'locality': locality,
                'organization': ngo_org,
                'latitude': 15.5527,
                'longitude': 32.5599,
                'status': 'active',
                'total_population': 1500,
                'description': 'Test mobile camp for reports testing'
            }
        )[0]

        site2 = Site.objects.get_or_create(
            name='Test Mobile Camp Beta',
            defaults={
                'name_ar': 'مخيم بيتا التجريبي للموبايل',
                'site_type': site_type,
                'state': state,
                'locality': locality,
                'organization': ngo_org,
                'latitude': 15.5627,
                'longitude': 32.5699,
                'status': 'active',
                'total_population': 2000,
                'description': 'Second test mobile camp for reports testing'
            }
        )[0]

        # Assign GSO to sites
        site1.assigned_gsos.add(gso_user)
        site2.assigned_gsos.add(gso_user)

        # Create report tags
        tags_data = [
            {'name': 'Emergency', 'color': '#dc3545'},
            {'name': 'Security', 'color': '#fd7e14'},
            {'name': 'Health', 'color': '#198754'},
            {'name': 'Water', 'color': '#0dcaf0'},
            {'name': 'Food', 'color': '#ffc107'},
            {'name': 'Shelter', 'color': '#6f42c1'},
        ]

        for tag_data in tags_data:
            ReportTag.objects.get_or_create(
                name=tag_data['name'],
                defaults={'color': tag_data['color']}
            )

        # Create sample reports
        sample_reports = [
            {
                'site': site1,
                'reporter': gso_user,
                'title': 'Test Mobile Text Report',
                'text_content': 'This is a test text report submitted via mobile API for testing purposes.',
                'report_type': 'text',
                'priority': 'medium',
                'location_coordinates': {'lat': 15.5527, 'lng': 32.5599}
            },
            {
                'site': site1,
                'reporter': ngo_user,
                'title': 'Test Mobile High Priority Report',
                'text_content': 'This is a high priority test report to verify mobile functionality.',
                'report_type': 'text',
                'priority': 'high',
                'location_coordinates': {'lat': 15.5530, 'lng': 32.5602}
            },
            {
                'site': site2,
                'reporter': gso_user,
                'title': 'Test Mobile Mixed Media Report',
                'text_content': 'This is a mixed media report that would include voice and image files.',
                'report_type': 'mixed',
                'priority': 'urgent',
                'location_coordinates': {'lat': 15.5627, 'lng': 32.5699}
            }
        ]

        for report_data in sample_reports:
            FieldReport.objects.get_or_create(
                title=report_data['title'],
                defaults=report_data
            )

        # Output summary
        self.stdout.write(self.style.SUCCESS('\n=== Test Data Created Successfully ===\n'))

        self.stdout.write(self.style.SUCCESS('Test Users:'))
        self.stdout.write(f'  GSO User: test_mobile_gso@unityaid.org (password: TestPass123!)')
        self.stdout.write(f'  NGO User: test_mobile_ngo@unityaid.org (password: TestPass123!)')
        self.stdout.write(f'  Admin User: test_mobile_admin@unityaid.org (password: TestPass123!)')
        self.stdout.write(f'  Cluster Lead: test_mobile_cluster@unityaid.org (password: TestPass123!)')

        self.stdout.write(self.style.SUCCESS('\nTest Sites:'))
        self.stdout.write(f'  Site 1: {site1.name} (ID: {site1.id})')
        self.stdout.write(f'  Site 2: {site2.name} (ID: {site2.id})')

        self.stdout.write(self.style.SUCCESS('\nMobile API Endpoints:'))
        self.stdout.write('  Login: POST /api/mobile/v1/auth/login/')
        self.stdout.write('  Reports: GET/POST /api/mobile/v1/field-reports/')
        self.stdout.write('  Statistics: GET /api/mobile/v1/field-reports/statistics/')

        self.stdout.write(self.style.SUCCESS('\nSample Login Request:'))
        self.stdout.write('''{
    "email": "test_mobile_gso@unityaid.org",
    "password": "TestPass123!",
    "device_id": "android_test_device",
    "platform": "android"
}''')

        self.stdout.write(self.style.SUCCESS('\nSample Report Creation Request:'))
        self.stdout.write('''{
    "site": ''' + str(site1.id) + ''',
    "title": "Test Mobile Report from Android",
    "text_content": "This is a test report submitted from Android emulator",
    "report_type": "text",
    "priority": "medium",
    "location_coordinates": {"lat": 15.5527, "lng": 32.5599}
}''')

        self.stdout.write(self.style.SUCCESS('\n=== Ready for Mobile Testing! ==='))
        self.stdout.write('1. Start Django server: python manage.py runserver')
        self.stdout.write('2. Test login endpoint with Postman or mobile app')
        self.stdout.write('3. Submit reports with different media types')
        self.stdout.write('4. Verify data in Django admin or database')