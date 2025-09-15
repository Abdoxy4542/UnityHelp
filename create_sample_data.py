#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.sites.models import State, Locality, Site

def create_sample_data():
    print("Creating sample data for Sudan...")
    
    # Create some Sudanese states with center points
    states_data = [
        {
            "name": "Khartoum", 
            "name_ar": "الخرطوم",
            "center_point": {"type": "Point", "coordinates": [32.5599, 15.5519]}
        },
        {
            "name": "Red Sea", 
            "name_ar": "البحر الأحمر",
            "center_point": {"type": "Point", "coordinates": [37.2162, 19.6348]}
        },
        {
            "name": "Northern", 
            "name_ar": "الشمالية",
            "center_point": {"type": "Point", "coordinates": [30.1632, 19.5654]}
        },
        {
            "name": "Kassala", 
            "name_ar": "كسلا",
            "center_point": {"type": "Point", "coordinates": [36.4020, 15.4510]}
        },
        {
            "name": "Gedaref", 
            "name_ar": "القضارف",
            "center_point": {"type": "Point", "coordinates": [35.3837, 14.0354]}
        },
    ]
    
    states = {}
    for state_data in states_data:
        state, created = State.objects.get_or_create(
            name=state_data["name"],
            defaults={
                "name_ar": state_data["name_ar"],
                "center_point": state_data["center_point"]
            }
        )
        states[state.name] = state
        print(f"{'Created' if created else 'Found'} state: {state.name}")
    
    # Create localities with center points
    localities_data = [
        {
            "name": "Khartoum", 
            "name_ar": "الخرطوم", 
            "state": "Khartoum",
            "center_point": {"type": "Point", "coordinates": [32.5599, 15.5519]}
        },
        {
            "name": "Bahri", 
            "name_ar": "بحري", 
            "state": "Khartoum",
            "center_point": {"type": "Point", "coordinates": [32.6279, 15.6405]}
        },
        {
            "name": "Omdurman", 
            "name_ar": "أم درمان", 
            "state": "Khartoum",
            "center_point": {"type": "Point", "coordinates": [32.4747, 15.6445]}
        },
        {
            "name": "Port Sudan", 
            "name_ar": "بورتسودان", 
            "state": "Red Sea",
            "center_point": {"type": "Point", "coordinates": [37.2162, 19.6348]}
        },
        {
            "name": "Kassala", 
            "name_ar": "كسلا", 
            "state": "Kassala",
            "center_point": {"type": "Point", "coordinates": [36.4020, 15.4510]}
        },
        {
            "name": "Gedaref", 
            "name_ar": "القضارف", 
            "state": "Gedaref",
            "center_point": {"type": "Point", "coordinates": [35.3837, 14.0354]}
        },
    ]
    
    localities = {}
    for locality_data in localities_data:
        locality, created = Locality.objects.get_or_create(
            name=locality_data["name"],
            state=states[locality_data["state"]],
            defaults={
                "name_ar": locality_data["name_ar"],
                "center_point": locality_data["center_point"]
            }
        )
        localities[f"{locality.name}_{locality.state.name}"] = locality
        print(f"{'Created' if created else 'Found'} locality: {locality.name}, {locality.state.name}")
    
    # Create sample sites
    sites_data = [
        {
            "name": "Al-Salam Gathering Site",
            "name_ar": "موقع تجمع السلام",
            "description": "Main gathering site for displaced families from conflict areas",
            "site_type": "gathering",
            "operational_status": "active",
            "state": "Khartoum",
            "locality": "Khartoum",
            "location": {"type": "Point", "coordinates": [32.5599, 15.5519]},
            "population": 1250,
            "families": 280,
            "vulnerable_population": 420,
            "contact_person": "Ahmed Mohammed",
            "contact_phone": "+249-123-456-789"
        },
        {
            "name": "Unity Camp",
            "name_ar": "مخيم الوحدة",
            "description": "IDP camp established for families from Blue Nile state",
            "site_type": "camp",
            "operational_status": "active",
            "state": "Khartoum",
            "locality": "Bahri",
            "location": {"type": "Point", "coordinates": [32.6279, 15.6405]},
            "population": 2100,
            "families": 450,
            "vulnerable_population": 850,
            "contact_person": "Fatima Hassan",
            "contact_phone": "+249-987-654-321"
        },
        {
            "name": "Port Sudan Health Center",
            "name_ar": "مركز بورتسودان الصحي",
            "description": "Primary healthcare facility serving displaced populations",
            "site_type": "health",
            "operational_status": "active",
            "state": "Red Sea",
            "locality": "Port Sudan",
            "location": {"type": "Point", "coordinates": [37.2162, 19.6348]},
            "population": 850,
            "families": 180,
            "vulnerable_population": 340,
            "contact_person": "Dr. Ibrahim Ali",
            "contact_email": "ibrahim.ali@health.gov.sd"
        },
        {
            "name": "Al-Amal School Site",
            "name_ar": "موقع مدرسة الأمل",
            "description": "Temporary education facility for displaced children",
            "site_type": "school",
            "operational_status": "active",
            "state": "Kassala",
            "locality": "Kassala",
            "location": {"type": "Point", "coordinates": [36.4020, 15.4510]},
            "population": 650,
            "families": 140,
            "vulnerable_population": 200,
            "contact_person": "Maryam Osman",
            "contact_phone": "+249-555-123-456"
        },
        {
            "name": "Water Distribution Point - Gedaref",
            "name_ar": "نقطة توزيع المياه - القضارف",
            "description": "Clean water distribution point for rural communities",
            "site_type": "water",
            "operational_status": "active",
            "state": "Gedaref",
            "locality": "Gedaref",
            "location": {"type": "Point", "coordinates": [35.3837, 14.0354]},
            "population": 300,
            "families": 65,
            "vulnerable_population": 90,
            "contact_person": "Hassan Ahmed",
            "contact_phone": "+249-777-888-999"
        }
    ]
    
    for site_data in sites_data:
        state_key = site_data["state"]
        locality_key = f"{site_data['locality']}_{site_data['state']}"
        
        site, created = Site.objects.get_or_create(
            name=site_data["name"],
            defaults={
                "name_ar": site_data.get("name_ar", ""),
                "description": site_data.get("description", ""),
                "site_type": site_data["site_type"],
                "operational_status": site_data["operational_status"],
                "state": states[state_key],
                "locality": localities[locality_key],
                "location": site_data.get("location"),
                "population": site_data.get("population"),
                "families": site_data.get("families"),
                "vulnerable_population": site_data.get("vulnerable_population"),
                "contact_person": site_data.get("contact_person", ""),
                "contact_phone": site_data.get("contact_phone", ""),
                "contact_email": site_data.get("contact_email", "")
            }
        )
        print(f"{'Created' if created else 'Found'} site: {site.name}")
    
    print(f"\nSample data creation complete!")
    print(f"States: {State.objects.count()}")
    print(f"Localities: {Locality.objects.count()}")
    print(f"Sites: {Site.objects.count()}")

if __name__ == "__main__":
    create_sample_data()