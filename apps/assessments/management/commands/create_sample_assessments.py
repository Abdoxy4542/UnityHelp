from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.assessments.models import Assessment, KoboIntegrationSettings
from apps.sites.models import Site, State, Locality

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample assessment data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample assessment data...')
        
        # Get or create a superuser
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.create_superuser(
                    username='admin',
                    email='admin@unityaid.org',
                    password='admin123',
                    role='admin'
                )
                self.stdout.write(f'Created admin user: {admin_user.username}')
            else:
                self.stdout.write(f'Using existing admin user: {admin_user.username}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating admin user: {e}'))
            return
        
        # Create sample assessments
        assessments_data = [
            {
                'title': 'Emergency Needs Assessment - Darfur',
                'title_ar': 'تقييم الاحتياجات الطارئة - دارفور',
                'description': 'Rapid assessment of humanitarian needs in Darfur region following recent displacement.',
                'assessment_type': 'rapid',
                'status': 'active',
                'kobo_form_id': 'sample_form_001',  # This would be a real Kobo form ID
                'kobo_form_url': 'https://kf.kobotoolbox.org/sample_form_001',
                'kobo_username': 'sample_kobo_user'
            },
            {
                'title': 'Education Facility Assessment',
                'title_ar': 'تقييم المرافق التعليمية',
                'description': 'Detailed assessment of education facilities and capacity in IDP camps.',
                'assessment_type': 'detailed',
                'status': 'active',
                'kobo_form_id': 'sample_form_002',
                'kobo_form_url': 'https://kf.kobotoolbox.org/sample_form_002',
                'kobo_username': 'sample_kobo_user'
            },
            {
                'title': 'Water and Sanitation Baseline',
                'title_ar': 'خط الأساس للمياه والصرف الصحي',
                'description': 'Baseline assessment of water, sanitation and hygiene conditions.',
                'assessment_type': 'baseline',
                'status': 'draft',
                'kobo_form_id': 'sample_form_003',
                'kobo_form_url': 'https://kf.kobotoolbox.org/sample_form_003',
                'kobo_username': 'sample_kobo_user'
            }
        ]
        
        created_assessments = []
        for assessment_data in assessments_data:
            assessment, created = Assessment.objects.get_or_create(
                title=assessment_data['title'],
                defaults={**assessment_data, 'created_by': admin_user}
            )
            
            if created:
                self.stdout.write(f'Created assessment: {assessment.title}')
                created_assessments.append(assessment)
            else:
                self.stdout.write(f'Assessment already exists: {assessment.title}')
        
        # Create sample Kobo integration settings for admin user
        kobo_settings, created = KoboIntegrationSettings.objects.get_or_create(
            user=admin_user,
            defaults={
                'kobo_server_url': 'https://kf.kobotoolbox.org',
                'kobo_username': 'sample_kobo_user',
                'kobo_api_token': 'sample_token_for_testing_only',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write('Created Kobo integration settings for admin user')
        else:
            self.stdout.write('Kobo integration settings already exist for admin user')
        
        # Associate assessments with existing sites
        sites = Site.objects.all()[:5]  # Get first 5 sites
        
        for assessment in created_assessments:
            if sites:
                assessment.target_sites.set(sites[:2])  # Assign first 2 sites to each assessment
                assessment.assigned_to.add(admin_user)
                self.stdout.write(f'Assigned sites to assessment: {assessment.title}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(created_assessments)} assessments and sample data!'
            )
        )
        
        # Instructions for testing
        self.stdout.write('\n' + '='*50)
        self.stdout.write('TESTING INSTRUCTIONS:')
        self.stdout.write('='*50)
        self.stdout.write('1. Start the Django server: python manage.py runserver')
        self.stdout.write('2. Visit the dashboard at: http://localhost:8000/')
        self.stdout.write('3. Login with username: admin, password: admin123')
        self.stdout.write('4. You should see assessment cards with "Launch Assessment" buttons')
        self.stdout.write('5. Click the buttons to test the Kobo integration')
        self.stdout.write('\nNote: The Kobo form URLs are examples and will not work without')
        self.stdout.write('actual Kobo forms. Set up real Kobo integration for full functionality.')
        self.stdout.write('='*50)