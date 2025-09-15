import requests
import json
from datetime import datetime, date
from django.conf import settings
from django.core.exceptions import ValidationError
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class FTSAPIService:
    """Service for interacting with OCHA FTS (Financial Tracking Service) API"""

    def __init__(self, api_key: str = None):
        self.base_url = "https://api.fts.unocha.org/v1"
        self.public_url = "https://fts.unocha.org/api/v1"
        self.api_key = api_key
        self.sudan_country_code = "SDN"
        self.sudan_country_id = 212
        self.crisis_start_date = date(2023, 4, 15)

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'UnityAid-Platform/1.0',
            'Accept': 'application/json'
        }
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers

    def test_connection(self) -> bool:
        """Test connection to FTS API"""
        try:
            response = requests.get(
                f"{self.public_url}/public/country",
                headers=self._get_headers(),
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"FTS connection test failed: {e}")
            return False

    def get_country_funding(self,
                          country_code: str = None,
                          year_from: int = None,
                          year_to: int = None) -> List[Dict]:
        """Get funding data for a specific country"""
        try:
            country_code = country_code or self.sudan_country_code
            year_from = year_from or 2023
            year_to = year_to or datetime.now().year

            params = {
                'countryISO3': country_code,
                'year': f"{year_from}:{year_to}" if year_from != year_to else str(year_from),
                'format': 'json'
            }

            response = requests.get(
                f"{self.public_url}/public/country/{country_code}",
                params=params,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            return data.get('data', []) if isinstance(data, dict) else data

        except Exception as e:
            logger.error(f"Failed to fetch country funding: {e}")
            raise ValidationError(f"Failed to fetch country funding: {e}")

    def get_funding_flows(self,
                         country_code: str = None,
                         year_from: int = None,
                         year_to: int = None,
                         limit: int = 1000) -> List[Dict]:
        """Get detailed funding flows for Sudan"""
        try:
            country_code = country_code or self.sudan_country_code
            year_from = year_from or 2023
            year_to = year_to or datetime.now().year

            params = {
                'countryISO3': country_code,
                'year': f"{year_from}:{year_to}" if year_from != year_to else str(year_from),
                'limit': limit,
                'format': 'json'
            }

            response = requests.get(
                f"{self.public_url}/public/flow",
                params=params,
                headers=self._get_headers(),
                timeout=60
            )
            response.raise_for_status()

            data = response.json()
            return data.get('data', []) if isinstance(data, dict) else data

        except Exception as e:
            logger.error(f"Failed to fetch funding flows: {e}")
            raise ValidationError(f"Failed to fetch funding flows: {e}")

    def get_appeals_and_plans(self,
                            country_code: str = None,
                            year_from: int = None,
                            year_to: int = None) -> List[Dict]:
        """Get humanitarian response plans and appeals for Sudan"""
        try:
            country_code = country_code or self.sudan_country_code
            year_from = year_from or 2023
            year_to = year_to or datetime.now().year

            params = {
                'countryISO3': country_code,
                'year': f"{year_from}:{year_to}" if year_from != year_to else str(year_from),
                'format': 'json'
            }

            response = requests.get(
                f"{self.public_url}/public/plan",
                params=params,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            return data.get('data', []) if isinstance(data, dict) else data

        except Exception as e:
            logger.error(f"Failed to fetch appeals and plans: {e}")
            raise ValidationError(f"Failed to fetch appeals and plans: {e}")

    def get_sector_funding(self,
                          country_code: str = None,
                          year: int = None) -> List[Dict]:
        """Get funding breakdown by sector"""
        try:
            country_code = country_code or self.sudan_country_code
            year = year or datetime.now().year

            params = {
                'countryISO3': country_code,
                'year': str(year),
                'groupby': 'cluster',
                'format': 'json'
            }

            response = requests.get(
                f"{self.public_url}/public/flow",
                params=params,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            return data.get('data', []) if isinstance(data, dict) else data

        except Exception as e:
            logger.error(f"Failed to fetch sector funding: {e}")
            raise ValidationError(f"Failed to fetch sector funding: {e}")

    def get_donor_contributions(self,
                              country_code: str = None,
                              year: int = None,
                              limit: int = 100) -> List[Dict]:
        """Get top donor contributions for Sudan"""
        try:
            country_code = country_code or self.sudan_country_code
            year = year or datetime.now().year

            params = {
                'countryISO3': country_code,
                'year': str(year),
                'groupby': 'donor',
                'limit': limit,
                'format': 'json'
            }

            response = requests.get(
                f"{self.public_url}/public/flow",
                params=params,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            return data.get('data', []) if isinstance(data, dict) else data

        except Exception as e:
            logger.error(f"Failed to fetch donor contributions: {e}")
            raise ValidationError(f"Failed to fetch donor contributions: {e}")

    def get_recipient_organizations(self,
                                  country_code: str = None,
                                  year: int = None,
                                  limit: int = 100) -> List[Dict]:
        """Get funding recipients for Sudan"""
        try:
            country_code = country_code or self.sudan_country_code
            year = year or datetime.now().year

            params = {
                'countryISO3': country_code,
                'year': str(year),
                'groupby': 'recipient',
                'limit': limit,
                'format': 'json'
            }

            response = requests.get(
                f"{self.public_url}/public/flow",
                params=params,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            return data.get('data', []) if isinstance(data, dict) else data

        except Exception as e:
            logger.error(f"Failed to fetch recipient organizations: {e}")
            raise ValidationError(f"Failed to fetch recipient organizations: {e}")

    def get_funding_gaps(self,
                        country_code: str = None,
                        year: int = None) -> Dict:
        """Calculate funding gaps for Sudan humanitarian response"""
        try:
            country_code = country_code or self.sudan_country_code
            year = year or datetime.now().year

            # Get plans and appeals to find requirements
            plans = self.get_appeals_and_plans(
                country_code=country_code,
                year_from=year,
                year_to=year
            )

            # Get funding flows to find received funding
            flows = self.get_funding_flows(
                country_code=country_code,
                year_from=year,
                year_to=year
            )

            total_requirements = 0
            total_funding = 0

            # Calculate requirements from plans
            for plan in plans:
                if plan.get('revisedRequirements'):
                    total_requirements += plan.get('revisedRequirements', 0)
                elif plan.get('requirements'):
                    total_requirements += plan.get('requirements', 0)

            # Calculate received funding
            for flow in flows:
                total_funding += flow.get('amountUSD', 0)

            funding_gap = total_requirements - total_funding
            coverage_percentage = (total_funding / total_requirements * 100) if total_requirements > 0 else 0

            return {
                'year': year,
                'country': country_code,
                'total_requirements_usd': total_requirements,
                'total_funding_received_usd': total_funding,
                'funding_gap_usd': funding_gap,
                'coverage_percentage': round(coverage_percentage, 2),
                'plans_count': len(plans),
                'funding_flows_count': len(flows)
            }

        except Exception as e:
            logger.error(f"Failed to calculate funding gaps: {e}")
            raise ValidationError(f"Failed to calculate funding gaps: {e}")

    def get_comprehensive_funding_data(self,
                                     year_from: int = None,
                                     year_to: int = None) -> Dict[str, any]:
        """Get comprehensive funding data for Sudan crisis"""
        try:
            year_from = year_from or 2023
            year_to = year_to or datetime.now().year

            data = {}

            # Overall country funding summary
            data['country_funding'] = self.get_country_funding(
                year_from=year_from,
                year_to=year_to
            )

            # Detailed funding flows
            data['funding_flows'] = self.get_funding_flows(
                year_from=year_from,
                year_to=year_to
            )

            # Appeals and response plans
            data['response_plans'] = self.get_appeals_and_plans(
                year_from=year_from,
                year_to=year_to
            )

            # Current year analysis
            current_year = datetime.now().year

            # Sector funding breakdown
            data['sector_funding'] = self.get_sector_funding(year=current_year)

            # Top donors
            data['top_donors'] = self.get_donor_contributions(year=current_year)

            # Top recipients
            data['top_recipients'] = self.get_recipient_organizations(year=current_year)

            # Funding gaps analysis
            data['funding_gaps'] = {}
            for year in range(year_from, year_to + 1):
                data['funding_gaps'][str(year)] = self.get_funding_gaps(year=year)

            return data

        except Exception as e:
            logger.error(f"Failed to fetch comprehensive funding data: {e}")
            raise ValidationError(f"Failed to fetch comprehensive funding data: {e}")

    def get_crisis_funding_timeline(self,
                                  year_from: int = None,
                                  year_to: int = None) -> List[Dict]:
        """Get funding timeline since Sudan crisis began"""
        try:
            year_from = year_from or 2023
            year_to = year_to or datetime.now().year

            timeline = []

            flows = self.get_funding_flows(
                year_from=year_from,
                year_to=year_to
            )

            # Group by month
            monthly_funding = {}
            for flow in flows:
                decision_date = flow.get('decisionDate', '')
                if decision_date:
                    # Extract year-month from date
                    try:
                        dt = datetime.strptime(decision_date[:10], '%Y-%m-%d')
                        month_key = dt.strftime('%Y-%m')

                        if month_key not in monthly_funding:
                            monthly_funding[month_key] = {
                                'month': month_key,
                                'total_amount': 0,
                                'flow_count': 0,
                                'donors': set(),
                                'recipients': set()
                            }

                        monthly_funding[month_key]['total_amount'] += flow.get('amountUSD', 0)
                        monthly_funding[month_key]['flow_count'] += 1

                        if flow.get('sourceOrganization', {}).get('name'):
                            monthly_funding[month_key]['donors'].add(
                                flow['sourceOrganization']['name']
                            )

                        if flow.get('destinationOrganization', {}).get('name'):
                            monthly_funding[month_key]['recipients'].add(
                                flow['destinationOrganization']['name']
                            )

                    except (ValueError, KeyError):
                        continue

            # Convert sets to counts and sort by month
            for month_data in monthly_funding.values():
                month_data['unique_donors'] = len(month_data['donors'])
                month_data['unique_recipients'] = len(month_data['recipients'])
                del month_data['donors']
                del month_data['recipients']
                timeline.append(month_data)

            timeline.sort(key=lambda x: x['month'])
            return timeline

        except Exception as e:
            logger.error(f"Failed to get crisis funding timeline: {e}")
            raise ValidationError(f"Failed to get crisis funding timeline: {e}")


def get_fts_service() -> FTSAPIService:
    """Get configured FTS API service instance"""
    api_key = getattr(settings, 'FTS_API_KEY', None)
    return FTSAPIService(api_key=api_key)