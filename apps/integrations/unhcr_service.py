import requests
import json
from datetime import datetime, date
from django.conf import settings
from django.core.exceptions import ValidationError
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class UNHCRAPIService:
    """Service for interacting with UNHCR Refugee Data Finder API"""

    def __init__(self, api_key: str = None):
        self.base_url = "https://www.unhcr.org/refugee-statistics-uat/download"
        self.api_url = "https://api.unhcr.org/rsq/v1"
        self.api_key = api_key
        self.sudan_country_code = "SDN"
        self.sudan_country_id = 736  # UNHCR country ID for Sudan
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
        """Test connection to UNHCR API"""
        try:
            response = requests.get(
                f"{self.api_url}/demographics",
                headers=self._get_headers(),
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"UNHCR connection test failed: {e}")
            return False

    def get_population_statistics(self,
                                country_of_asylum: str = None,
                                country_of_origin: str = None,
                                year_from: int = None,
                                year_to: int = None) -> List[Dict]:
        """Get refugee population statistics"""
        try:
            country_of_asylum = country_of_asylum or self.sudan_country_code
            year_from = year_from or 2023
            year_to = year_to or datetime.now().year

            params = {
                'country_of_asylum': country_of_asylum,
                'year_from': year_from,
                'year_to': year_to,
                'format': 'json'
            }

            if country_of_origin:
                params['country_of_origin'] = country_of_origin

            response = requests.get(
                f"{self.api_url}/demographics",
                params=params,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            return data.get('data', []) if isinstance(data, dict) else data

        except Exception as e:
            logger.error(f"Failed to fetch population statistics: {e}")
            raise ValidationError(f"Failed to fetch population statistics: {e}")

    def get_refugees_by_origin(self,
                              country_of_asylum: str = None,
                              year_from: int = None,
                              year_to: int = None) -> List[Dict]:
        """Get refugee statistics by country of origin for Sudan"""
        try:
            country_of_asylum = country_of_asylum or self.sudan_country_code
            year_from = year_from or 2023
            year_to = year_to or datetime.now().year

            params = {
                'country_of_asylum': country_of_asylum,
                'year_from': year_from,
                'year_to': year_to,
                'breakdown': 'country_of_origin',
                'format': 'json'
            }

            response = requests.get(
                f"{self.api_url}/demographics",
                params=params,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            return data.get('data', []) if isinstance(data, dict) else data

        except Exception as e:
            logger.error(f"Failed to fetch refugees by origin: {e}")
            raise ValidationError(f"Failed to fetch refugees by origin: {e}")

    def get_sudanese_refugees_worldwide(self,
                                      year_from: int = None,
                                      year_to: int = None) -> List[Dict]:
        """Get statistics for Sudanese refugees in other countries"""
        try:
            year_from = year_from or 2023
            year_to = year_to or datetime.now().year

            params = {
                'country_of_origin': self.sudan_country_code,
                'year_from': year_from,
                'year_to': year_to,
                'breakdown': 'country_of_asylum',
                'format': 'json'
            }

            response = requests.get(
                f"{self.api_url}/demographics",
                params=params,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            return data.get('data', []) if isinstance(data, dict) else data

        except Exception as e:
            logger.error(f"Failed to fetch Sudanese refugees worldwide: {e}")
            raise ValidationError(f"Failed to fetch Sudanese refugees worldwide: {e}")

    def get_asylum_trends(self,
                         country_of_asylum: str = None,
                         year_from: int = None,
                         year_to: int = None) -> List[Dict]:
        """Get asylum application trends"""
        try:
            country_of_asylum = country_of_asylum or self.sudan_country_code
            year_from = year_from or 2023
            year_to = year_to or datetime.now().year

            params = {
                'country_of_asylum': country_of_asylum,
                'year_from': year_from,
                'year_to': year_to,
                'population_type': 'asylum_seekers',
                'format': 'json'
            }

            response = requests.get(
                f"{self.api_url}/asylum-applications",
                params=params,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            return data.get('data', []) if isinstance(data, dict) else data

        except Exception as e:
            logger.error(f"Failed to fetch asylum trends: {e}")
            raise ValidationError(f"Failed to fetch asylum trends: {e}")

    def get_demographic_breakdown(self,
                                country_of_asylum: str = None,
                                country_of_origin: str = None,
                                year: int = None) -> List[Dict]:
        """Get demographic breakdown by age and gender"""
        try:
            country_of_asylum = country_of_asylum or self.sudan_country_code
            year = year or datetime.now().year

            params = {
                'country_of_asylum': country_of_asylum,
                'year': year,
                'breakdown': 'age_gender',
                'format': 'json'
            }

            if country_of_origin:
                params['country_of_origin'] = country_of_origin

            response = requests.get(
                f"{self.api_url}/demographics",
                params=params,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            return data.get('data', []) if isinstance(data, dict) else data

        except Exception as e:
            logger.error(f"Failed to fetch demographic breakdown: {e}")
            raise ValidationError(f"Failed to fetch demographic breakdown: {e}")

    def get_returnee_data(self,
                         country_of_origin: str = None,
                         year_from: int = None,
                         year_to: int = None) -> List[Dict]:
        """Get returnee data for Sudan"""
        try:
            country_of_origin = country_of_origin or self.sudan_country_code
            year_from = year_from or 2023
            year_to = year_to or datetime.now().year

            params = {
                'country_of_origin': country_of_origin,
                'year_from': year_from,
                'year_to': year_to,
                'population_type': 'returnees',
                'format': 'json'
            }

            response = requests.get(
                f"{self.api_url}/solutions",
                params=params,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            return data.get('data', []) if isinstance(data, dict) else data

        except Exception as e:
            logger.error(f"Failed to fetch returnee data: {e}")
            raise ValidationError(f"Failed to fetch returnee data: {e}")

    def get_comprehensive_sudan_refugee_data(self,
                                           year_from: int = None,
                                           year_to: int = None) -> Dict[str, List[Dict]]:
        """Get comprehensive refugee data related to Sudan crisis"""
        try:
            year_from = year_from or 2023
            year_to = year_to or datetime.now().year

            data = {}

            # Refugees in Sudan by country of origin
            data['refugees_in_sudan'] = self.get_refugees_by_origin(
                country_of_asylum=self.sudan_country_code,
                year_from=year_from,
                year_to=year_to
            )

            # Sudanese refugees in other countries
            data['sudanese_refugees_abroad'] = self.get_sudanese_refugees_worldwide(
                year_from=year_from,
                year_to=year_to
            )

            # Asylum seekers in Sudan
            data['asylum_trends_sudan'] = self.get_asylum_trends(
                country_of_asylum=self.sudan_country_code,
                year_from=year_from,
                year_to=year_to
            )

            # Demographic breakdown for latest year
            data['demographics_current'] = self.get_demographic_breakdown(
                country_of_asylum=self.sudan_country_code,
                year=year_to
            )

            # Returnee data
            data['returnees'] = self.get_returnee_data(
                country_of_origin=self.sudan_country_code,
                year_from=year_from,
                year_to=year_to
            )

            return data

        except Exception as e:
            logger.error(f"Failed to fetch comprehensive refugee data: {e}")
            raise ValidationError(f"Failed to fetch comprehensive refugee data: {e}")

    def get_crisis_impact_summary(self, year: int = None) -> Dict:
        """Get summary of refugee situation since Sudan crisis"""
        try:
            year = year or datetime.now().year

            # Get current refugee populations
            refugees_in_sudan = self.get_population_statistics(
                country_of_asylum=self.sudan_country_code,
                year_from=2023,
                year_to=year
            )

            sudanese_abroad = self.get_sudanese_refugees_worldwide(
                year_from=2023,
                year_to=year
            )

            # Calculate totals
            total_refugees_in_sudan = 0
            total_asylum_seekers_in_sudan = 0
            total_sudanese_refugees_abroad = 0

            for record in refugees_in_sudan:
                total_refugees_in_sudan += record.get('refugees', 0)
                total_asylum_seekers_in_sudan += record.get('asylum_seekers', 0)

            for record in sudanese_abroad:
                total_sudanese_refugees_abroad += record.get('refugees', 0)

            # Get country breakdown
            origin_countries = {}
            for record in refugees_in_sudan:
                country = record.get('country_of_origin_name', 'Unknown')
                if country not in origin_countries:
                    origin_countries[country] = 0
                origin_countries[country] += record.get('refugees', 0)

            host_countries = {}
            for record in sudanese_abroad:
                country = record.get('country_of_asylum_name', 'Unknown')
                if country not in host_countries:
                    host_countries[country] = 0
                host_countries[country] += record.get('refugees', 0)

            return {
                'total_refugees_in_sudan': total_refugees_in_sudan,
                'total_asylum_seekers_in_sudan': total_asylum_seekers_in_sudan,
                'total_sudanese_refugees_abroad': total_sudanese_refugees_abroad,
                'top_origin_countries': dict(sorted(origin_countries.items(),
                                                  key=lambda x: x[1], reverse=True)[:10]),
                'top_host_countries': dict(sorted(host_countries.items(),
                                                key=lambda x: x[1], reverse=True)[:10]),
                'crisis_period': f"2023-{year}",
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get crisis impact summary: {e}")
            raise ValidationError(f"Failed to get crisis impact summary: {e}")


def get_unhcr_service() -> UNHCRAPIService:
    """Get configured UNHCR API service instance"""
    api_key = getattr(settings, 'UNHCR_API_KEY', None)
    return UNHCRAPIService(api_key=api_key)