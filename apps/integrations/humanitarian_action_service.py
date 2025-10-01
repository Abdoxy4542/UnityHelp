import requests
import json
from datetime import datetime, date
from django.conf import settings
from django.core.exceptions import ValidationError
from typing import Dict, List, Optional, Union
import logging
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class HumanitarianActionService:
    """Service for interacting with Humanitarian Action Info platform"""

    def __init__(self, api_key: str = None):
        self.base_url = "https://humanitarianaction.info"
        self.api_key = api_key
        self.sudan_country_code = "SDN"
        self.crisis_start_date = date(2023, 4, 15)

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'UnityAid-Platform/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers

    def test_connection(self) -> bool:
        """Test connection to Humanitarian Action Info"""
        try:
            response = requests.get(
                self.base_url,
                headers=self._get_headers(),
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Humanitarian Action connection test failed: {e}")
            return False

    def get_humanitarian_plan(self, plan_id: str) -> Dict:
        """Get specific humanitarian plan details"""
        try:
            url = f"{self.base_url}/plan/{plan_id}"
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()

            # Parse HTML content to extract plan data
            soup = BeautifulSoup(response.content, 'html.parser')

            plan_data = {
                'id': plan_id,
                'url': url,
                'title': '',
                'description': '',
                'objectives': [],
                'target_population': '',
                'funding_requirements': '',
                'timeframe': '',
                'sectors': [],
                'locations': [],
                'organizations': [],
                'last_updated': date.today().isoformat(),
                'raw_html': str(soup)
            }

            # Extract title
            title_elem = soup.find('h1') or soup.find('title')
            if title_elem:
                plan_data['title'] = title_elem.get_text(strip=True)

            # Extract description from meta tags or main content
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                plan_data['description'] = meta_desc.get('content', '')
            else:
                # Try to find description in content
                desc_elem = soup.find('div', class_='description') or soup.find('p')
                if desc_elem:
                    plan_data['description'] = desc_elem.get_text(strip=True)[:500]

            # Extract objectives
            objectives = []
            obj_sections = soup.find_all(['div', 'section'], string=re.compile(r'objective|goal', re.I))
            for section in obj_sections:
                parent = section.parent if section.parent else section
                text = parent.get_text(strip=True)
                if text and len(text) > 10:
                    objectives.append(text[:200])
            plan_data['objectives'] = objectives

            # Extract funding information
            funding_patterns = [
                r'USD?\s*([\d,]+\.?\d*)\s*million',
                r'\$\s*([\d,]+\.?\d*)\s*million',
                r'([\d,]+\.?\d*)\s*million\s*USD?'
            ]
            for pattern in funding_patterns:
                match = re.search(pattern, response.text, re.I)
                if match:
                    plan_data['funding_requirements'] = match.group(0)
                    break

            # Extract target population
            pop_patterns = [
                r'([\d,]+\.?\d*)\s*million\s*people',
                r'([\d,]+\.?\d*)\s*people\s*in\s*need',
                r'targeting\s*([\d,]+\.?\d*)\s*people'
            ]
            for pattern in pop_patterns:
                match = re.search(pattern, response.text, re.I)
                if match:
                    plan_data['target_population'] = match.group(0)
                    break

            # Extract timeframe
            timeframe_patterns = [
                r'(January|February|March|April|May|June|July|August|September|October|November|December)\s*\d{4}\s*-\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s*\d{4}',
                r'\d{4}\s*-\s*\d{4}',
                r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{4}\s*-\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{4}'
            ]
            for pattern in timeframe_patterns:
                match = re.search(pattern, response.text, re.I)
                if match:
                    plan_data['timeframe'] = match.group(0)
                    break

            # Extract sectors
            sector_keywords = [
                'food security', 'nutrition', 'health', 'water sanitation',
                'shelter', 'protection', 'education', 'logistics',
                'emergency telecommunications', 'coordination'
            ]
            found_sectors = []
            for sector in sector_keywords:
                if re.search(sector, response.text, re.I):
                    found_sectors.append(sector.title())
            plan_data['sectors'] = found_sectors

            # Extract locations (look for Sudan-related locations)
            sudan_locations = [
                'Sudan', 'Khartoum', 'Darfur', 'Blue Nile', 'South Kordofan',
                'Kassala', 'Red Sea', 'Gedaref', 'White Nile', 'Northern State',
                'River Nile', 'Sennar', 'Gezira', 'Central Darfur', 'East Darfur',
                'North Darfur', 'South Darfur', 'West Darfur'
            ]
            found_locations = []
            for location in sudan_locations:
                if re.search(location, response.text, re.I):
                    found_locations.append(location)
            plan_data['locations'] = list(set(found_locations))

            # Extract organizations
            org_patterns = [
                r'(UNICEF|WHO|WFP|UNHCR|IOM|OCHA|UNDP|FAO)',
                r'(Save the Children|Oxfam|Médecins Sans Frontières|MSF)',
                r'(International Committee of the Red Cross|ICRC)',
                r'(Norwegian Refugee Council|NRC)'
            ]
            found_orgs = []
            for pattern in org_patterns:
                matches = re.findall(pattern, response.text, re.I)
                found_orgs.extend(matches)
            plan_data['organizations'] = list(set(found_orgs))

            return plan_data

        except Exception as e:
            logger.error(f"Failed to fetch humanitarian plan {plan_id}: {e}")
            raise ValidationError(f"Failed to fetch plan details: {e}")

    def search_sudan_plans(self,
                          query: str = "sudan",
                          from_date: date = None,
                          to_date: date = None,
                          limit: int = 50) -> List[Dict]:
        """Search for Sudan-related humanitarian plans"""
        try:
            from_date = from_date or self.crisis_start_date
            to_date = to_date or date.today()

            # Since we don't have a direct search API, we'll try common plan patterns
            sudan_plan_ids = [
                "1220",  # The specific plan mentioned
                "1219", "1221", "1222", "1223", "1224", "1225",  # Try adjacent IDs
                "sudan-2023", "sudan-2024", "sudan-crisis-2023"  # Try common patterns
            ]

            plans = []
            for plan_id in sudan_plan_ids:
                try:
                    plan_data = self.get_humanitarian_plan(plan_id)
                    if plan_data and any(loc.lower() in plan_data.get('title', '').lower() +
                                       plan_data.get('description', '').lower()
                                       for loc in ['sudan', 'khartoum', 'darfur']):
                        plans.append(plan_data)
                        if len(plans) >= limit:
                            break
                except:
                    continue  # Skip if plan doesn't exist

            return plans

        except Exception as e:
            logger.error(f"Failed to search Sudan plans: {e}")
            raise ValidationError(f"Failed to search plans: {e}")

    def get_crisis_response_data(self,
                               from_date: date = None,
                               to_date: date = None) -> Dict[str, List[Dict]]:
        """Get comprehensive crisis response data"""
        try:
            from_date = from_date or self.crisis_start_date
            to_date = to_date or date.today()

            data = {
                'humanitarian_plans': [],
                'response_activities': [],
                'funding_appeals': [],
                'operational_updates': []
            }

            # Get Sudan-related plans
            sudan_plans = self.search_sudan_plans(
                from_date=from_date,
                to_date=to_date
            )

            for plan in sudan_plans:
                # Categorize data based on content
                plan_data = {
                    'id': plan.get('id'),
                    'title': plan.get('title'),
                    'description': plan.get('description'),
                    'type': self._determine_plan_type(plan),
                    'date_extracted': date.today().isoformat(),
                    'funding_requirements': plan.get('funding_requirements'),
                    'target_population': plan.get('target_population'),
                    'sectors': plan.get('sectors', []),
                    'locations': plan.get('locations', []),
                    'organizations': plan.get('organizations', []),
                    'url': plan.get('url'),
                    'timeframe': plan.get('timeframe')
                }

                if 'humanitarian response plan' in plan.get('title', '').lower():
                    data['humanitarian_plans'].append(plan_data)
                elif 'appeal' in plan.get('title', '').lower():
                    data['funding_appeals'].append(plan_data)
                elif 'update' in plan.get('title', '').lower():
                    data['operational_updates'].append(plan_data)
                else:
                    data['response_activities'].append(plan_data)

            return data

        except Exception as e:
            logger.error(f"Failed to fetch crisis response data: {e}")
            raise ValidationError(f"Failed to fetch crisis response data: {e}")

    def _determine_plan_type(self, plan: Dict) -> str:
        """Determine the type of humanitarian plan based on content"""
        title = plan.get('title', '').lower()
        description = plan.get('description', '').lower()

        content = f"{title} {description}"

        if any(keyword in content for keyword in ['humanitarian response plan', 'hrp']):
            return 'humanitarian_response_plan'
        elif any(keyword in content for keyword in ['flash appeal', 'emergency appeal']):
            return 'emergency_appeal'
        elif any(keyword in content for keyword in ['regional response', 'regional plan']):
            return 'regional_response'
        elif any(keyword in content for keyword in ['contingency plan', 'preparedness']):
            return 'contingency_plan'
        else:
            return 'general_plan'

    def get_plan_funding_breakdown(self, plan_id: str) -> Dict:
        """Get detailed funding breakdown for a specific plan"""
        try:
            plan_data = self.get_humanitarian_plan(plan_id)

            # Extract more detailed funding information
            funding_breakdown = {
                'total_requirements': plan_data.get('funding_requirements'),
                'funded_amount': None,
                'funding_gap': None,
                'funding_percentage': None,
                'donors': [],
                'sectors_funding': [],
                'last_updated': date.today().isoformat()
            }

            # Parse funding details from the raw HTML if available
            raw_html = plan_data.get('raw_html', '')
            soup = BeautifulSoup(raw_html, 'html.parser')

            # Look for funding tables or sections
            funding_tables = soup.find_all('table')
            for table in funding_tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        cell_text = ' '.join([cell.get_text(strip=True) for cell in cells])

                        # Extract donor information
                        if any(donor in cell_text.lower() for donor in ['donor', 'contributor', 'funding']):
                            funding_breakdown['donors'].append(cell_text)

            return funding_breakdown

        except Exception as e:
            logger.error(f"Failed to get funding breakdown for plan {plan_id}: {e}")
            raise ValidationError(f"Failed to get funding breakdown: {e}")


def get_humanitarian_action_service() -> HumanitarianActionService:
    """Get configured Humanitarian Action service instance"""
    api_key = getattr(settings, 'HUMANITARIAN_ACTION_API_KEY', None)
    return HumanitarianActionService(api_key=api_key)