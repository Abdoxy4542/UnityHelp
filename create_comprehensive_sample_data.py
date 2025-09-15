#!/usr/bin/env python
import os
import sys
import django
from datetime import date, timedelta

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.sites.models import State, Locality, Site

def create_comprehensive_sample_data():
    print("Creating comprehensive sample data for Sudan...")
    
    # Get existing states and localities
    states = {state.name: state for state in State.objects.all()}
    localities = {f"{locality.name}_{locality.state.name}": locality for locality in Locality.objects.all()}
    
    # Comprehensive site data with full demographics
    sites_data = [
        {
            "name": "Al-Salam Gathering Site",
            "name_ar": "موقع تجمع السلام",
            "description": "Main gathering site for displaced families from conflict areas in South Kordofan",
            "site_type": "gathering",
            "operational_status": "active",
            "state": "Khartoum",
            "locality": "Khartoum",
            "location": {"type": "Point", "coordinates": [32.5599, 15.5519]},
            "size_of_location": "Large (15 hectares)",
            
            # Demographics
            "total_population": 1250,
            "total_households": 280,
            "children_under_18": 520,  # 41.6%
            "adults_18_59": 630,       # 50.4%
            "elderly_60_plus": 100,    # 8%
            "male_count": 600,         # 48%
            "female_count": 650,       # 52%
            "disabled_count": 45,      # 3.6%
            "pregnant_women": 25,      # 2%
            "chronically_ill": 65,     # 5.2%
            
            # Reporting
            "report_date": date.today() - timedelta(days=5),
            "reported_by": "UNHCR Field Office - Khartoum",
            
            # Contact
            "contact_person": "Ahmed Mohammed Ali",
            "contact_phone": "+249-123-456-789"
        },
        {
            "name": "Unity Camp",
            "name_ar": "مخيم الوحدة",
            "description": "IDP camp established for families displaced from Blue Nile and White Nile conflicts",
            "site_type": "camp",
            "operational_status": "active",
            "state": "Khartoum",
            "locality": "Bahri",
            "location": {"type": "Point", "coordinates": [32.6279, 15.6405]},
            "size_of_location": "Medium (8 hectares)",
            
            # Demographics
            "total_population": 2100,
            "total_households": 450,
            "children_under_18": 945,  # 45%
            "adults_18_59": 1050,      # 50%
            "elderly_60_plus": 105,    # 5%
            "male_count": 1029,        # 49%
            "female_count": 1071,      # 51%
            "disabled_count": 84,      # 4%
            "pregnant_women": 42,      # 2%
            "chronically_ill": 126,    # 6%
            
            # Reporting
            "report_date": date.today() - timedelta(days=2),
            "reported_by": "IOM Field Assessment Team",
            
            # Contact
            "contact_person": "Fatima Hassan Osman",
            "contact_phone": "+249-987-654-321"
        },
        {
            "name": "Port Sudan Health Center",
            "name_ar": "مركز بورتسودان الصحي",
            "description": "Primary healthcare facility serving displaced populations and host communities",
            "site_type": "health",
            "operational_status": "active",
            "state": "Red Sea",
            "locality": "Port Sudan",
            "location": {"type": "Point", "coordinates": [37.2162, 19.6348]},
            "size_of_location": "Small (2 hectares)",
            
            # Demographics (served population, not residential)
            "total_population": 850,
            "total_households": 180,
            "children_under_18": 340,  # 40%
            "adults_18_59": 425,       # 50%
            "elderly_60_plus": 85,     # 10%
            "male_count": 408,         # 48%
            "female_count": 442,       # 52%
            "disabled_count": 51,      # 6%
            "pregnant_women": 35,      # 4.1%
            "chronically_ill": 128,    # 15%
            
            # Reporting
            "report_date": date.today() - timedelta(days=7),
            "reported_by": "WHO Health Cluster - Red Sea",
            
            # Contact
            "contact_person": "Dr. Ibrahim Ali Hassan",
            "contact_email": "ibrahim.ali@health.gov.sd",
            "contact_phone": "+249-555-111-222"
        },
        {
            "name": "Al-Amal School Site",
            "name_ar": "موقع مدرسة الأمل",
            "description": "Temporary education facility and gathering point for displaced children and families",
            "site_type": "school",
            "operational_status": "active",
            "state": "Kassala",
            "locality": "Kassala",
            "location": {"type": "Point", "coordinates": [36.4020, 15.4510]},
            "size_of_location": "Medium (5 hectares)",
            
            # Demographics
            "total_population": 650,
            "total_households": 140,
            "children_under_18": 390,  # 60% (school-centered)
            "adults_18_59": 234,       # 36%
            "elderly_60_plus": 26,     # 4%
            "male_count": 325,         # 50%
            "female_count": 325,       # 50%
            "disabled_count": 19,      # 3%
            "pregnant_women": 18,      # 2.8%
            "chronically_ill": 26,     # 4%
            
            # Reporting
            "report_date": date.today() - timedelta(days=10),
            "reported_by": "UNICEF Education Cluster",
            
            # Contact
            "contact_person": "Maryam Osman Ahmed",
            "contact_phone": "+249-555-123-456"
        },
        {
            "name": "Water Distribution Point - Gedaref",
            "name_ar": "نقطة توزيع المياه - القضارف",
            "description": "Clean water distribution point serving rural communities and pastoral populations",
            "site_type": "water",
            "operational_status": "active",
            "state": "Gedaref",
            "locality": "Gedaref",
            "location": {"type": "Point", "coordinates": [35.3837, 14.0354]},
            "size_of_location": "Small (1 hectare)",
            
            # Demographics (served population)
            "total_population": 300,
            "total_households": 65,
            "children_under_18": 135,  # 45%
            "adults_18_59": 150,       # 50%
            "elderly_60_plus": 15,     # 5%
            "male_count": 147,         # 49%
            "female_count": 153,       # 51%
            "disabled_count": 12,      # 4%
            "pregnant_women": 8,       # 2.7%
            "chronically_ill": 18,     # 6%
            
            # Reporting
            "report_date": date.today() - timedelta(days=3),
            "reported_by": "WASH Cluster - Gedaref State",
            
            # Contact
            "contact_person": "Hassan Ahmed Ibrahim",
            "contact_phone": "+249-777-888-999"
        }
    ]
    
    # Create/update sites with comprehensive data
    for site_data in sites_data:
        state_key = site_data["state"]
        locality_key = f"{site_data['locality']}_{site_data['state']}"
        
        defaults = {k: v for k, v in site_data.items() if k not in ['state', 'locality']}
        defaults['state'] = states[state_key]
        defaults['locality'] = localities[locality_key]
        
        site, created = Site.objects.update_or_create(
            name=site_data["name"],
            defaults=defaults
        )
        print(f"{'Created' if created else 'Updated'} site: {site.name}")
        
        # Display demographic calculations
        if site.total_population:
            print(f"  - Population: {site.total_population}")
            print(f"  - Average household size: {site.average_household_size}")
            print(f"  - Vulnerability rate: {site.vulnerability_rate}%")
            print(f"  - Child dependency ratio: {site.child_dependency_ratio}")
            print(f"  - Age demographics verified: {site.population_by_age_verified}")
            print(f"  - Gender demographics verified: {site.population_by_gender_verified}")
        print('---')
    
    print(f"\nComprehensive sample data creation complete!")
    print(f"States: {State.objects.count()}")
    print(f"Localities: {Locality.objects.count()}")
    print(f"Sites: {Site.objects.count()}")

if __name__ == "__main__":
    create_comprehensive_sample_data()