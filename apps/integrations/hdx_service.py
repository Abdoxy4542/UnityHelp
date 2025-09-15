import requests
import json
from datetime import datetime, date
from django.conf import settings
from django.core.exceptions import ValidationError
from typing import Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class HDXAPIService:
    """Service for interacting with HDX (Humanitarian Data Exchange) API"""

    def __init__(self, api_key: str = None):
        self.base_url = "https://data.humdata.org/api/3"
        self.hapi_url = "https://hapi.humdata.org/api/v1"
        self.api_key = api_key
        self.sudan_country_code = "SDN"
        self.crisis_start_date = date(2023, 4, 15)

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'UnityAid-Platform/1.0'
        }
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers

    def test_connection(self) -> bool:
        """Test connection to HDX API"""
        try:
            response = requests.get(
                f"{self.base_url}/action/package_list",
                headers=self._get_headers(),
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"HDX connection test failed: {e}")
            return False

    def search_sudan_datasets(self,
                            query: str = "sudan",
                            from_date: date = None,
                            to_date: date = None,
                            limit: int = 100) -> List[Dict]:
        """Search for Sudan-related datasets"""
        try:
            from_date = from_date or self.crisis_start_date
            to_date = to_date or date.today()

            params = {
                'q': f'{query} location:"{self.sudan_country_code}"',
                'rows': limit,
                'start': 0,
                'fq': f'metadata_modified:[{from_date.strftime("%Y-%m-%d")}T00:00:00.000Z TO {to_date.strftime("%Y-%m-%d")}T23:59:59.999Z]'
            }

            response = requests.get(
                f"{self.base_url}/action/package_search",
                params=params,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            if data.get('success'):
                return data.get('result', {}).get('results', [])
            else:
                raise ValidationError(f"HDX API error: {data.get('error', {})}")

        except Exception as e:
            logger.error(f"Failed to search Sudan datasets: {e}")
            raise ValidationError(f"Failed to search datasets: {e}")

    def get_dataset_details(self, dataset_id: str) -> Dict:
        """Get detailed information about a specific dataset"""
        try:
            response = requests.get(
                f"{self.base_url}/action/package_show",
                params={'id': dataset_id},
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            if data.get('success'):
                return data.get('result', {})
            else:
                raise ValidationError(f"Dataset not found: {dataset_id}")

        except Exception as e:
            logger.error(f"Failed to fetch dataset {dataset_id}: {e}")
            raise ValidationError(f"Failed to fetch dataset details: {e}")

    def get_dataset_resources(self, dataset_id: str) -> List[Dict]:
        """Get resources (files) for a specific dataset"""
        try:
            dataset = self.get_dataset_details(dataset_id)
            return dataset.get('resources', [])
        except Exception as e:
            logger.error(f"Failed to fetch resources for {dataset_id}: {e}")
            raise ValidationError(f"Failed to fetch dataset resources: {e}")

    def download_resource_data(self, resource_url: str, format_type: str = 'json') -> Union[Dict, List, str]:
        """Download data from a resource URL"""
        try:
            response = requests.get(
                resource_url,
                headers=self._get_headers(),
                timeout=60
            )
            response.raise_for_status()

            if format_type.lower() == 'json':
                return response.json()
            elif format_type.lower() == 'csv':
                return response.text
            else:
                return response.content

        except Exception as e:
            logger.error(f"Failed to download resource {resource_url}: {e}")
            raise ValidationError(f"Failed to download resource: {e}")


class HDXHAPIService:
    """Service for HDX HAPI (Humanitarian API) - specialized for humanitarian data"""

    def __init__(self, api_key: str = None):
        self.base_url = "https://hapi.humdata.org/api/v1"
        self.api_key = api_key
        self.sudan_iso3 = "SDN"
        self.crisis_start_date = date(2023, 4, 15)

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for HAPI requests"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'UnityAid-Platform/1.0'
        }
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        return headers

    def test_connection(self) -> bool:
        """Test connection to HDX HAPI"""
        try:
            response = requests.get(
                f"{self.base_url}/metadata",
                headers=self._get_headers(),
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"HDX HAPI connection test failed: {e}")
            return False

    def get_population_data(self,
                          admin_level: int = 1,
                          from_date: date = None,
                          to_date: date = None) -> List[Dict]:
        """Get population data for Sudan"""
        try:
            from_date = from_date or self.crisis_start_date
            to_date = to_date or date.today()

            params = {
                'location_code': self.sudan_iso3,
                'admin_level': admin_level,
                'reference_period_start': from_date.strftime("%Y-%m-%d"),
                'reference_period_end': to_date.strftime("%Y-%m-%d"),
                'output_format': 'json'
            }

            response = requests.get(
                f"{self.base_url}/coordination-context/population",
                params=params,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()

            return response.json().get('data', [])

        except Exception as e:
            logger.error(f"Failed to fetch population data: {e}")
            raise ValidationError(f"Failed to fetch population data: {e}")

    def get_funding_data(self,
                        from_date: date = None,
                        to_date: date = None) -> List[Dict]:
        """Get humanitarian funding data for Sudan"""
        try:
            from_date = from_date or self.crisis_start_date
            to_date = to_date or date.today()

            params = {
                'location_code': self.sudan_iso3,
                'appeal_start_date_min': from_date.strftime("%Y-%m-%d"),
                'appeal_start_date_max': to_date.strftime("%Y-%m-%d"),
                'output_format': 'json'
            }

            response = requests.get(
                f"{self.base_url}/coordination-context/funding",
                params=params,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()

            return response.json().get('data', [])

        except Exception as e:
            logger.error(f"Failed to fetch funding data: {e}")
            raise ValidationError(f"Failed to fetch funding data: {e}")

    def get_humanitarian_needs(self,
                             admin_level: int = 1,
                             from_date: date = None,
                             to_date: date = None) -> List[Dict]:
        """Get humanitarian needs assessment data for Sudan"""
        try:
            from_date = from_date or self.crisis_start_date
            to_date = to_date or date.today()

            params = {
                'location_code': self.sudan_iso3,
                'admin_level': admin_level,
                'reference_period_start': from_date.strftime("%Y-%m-%d"),
                'reference_period_end': to_date.strftime("%Y-%m-%d"),
                'output_format': 'json'
            }

            response = requests.get(
                f"{self.base_url}/coordination-context/humanitarian-needs",
                params=params,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()

            return response.json().get('data', [])

        except Exception as e:
            logger.error(f"Failed to fetch humanitarian needs: {e}")
            raise ValidationError(f"Failed to fetch humanitarian needs: {e}")

    def get_conflict_events(self,
                          admin_level: int = 1,
                          from_date: date = None,
                          to_date: date = None) -> List[Dict]:
        """Get conflict and security events for Sudan"""
        try:
            from_date = from_date or self.crisis_start_date
            to_date = to_date or date.today()

            params = {
                'location_code': self.sudan_iso3,
                'admin_level': admin_level,
                'reference_period_start': from_date.strftime("%Y-%m-%d"),
                'reference_period_end': to_date.strftime("%Y-%m-%d"),
                'output_format': 'json'
            }

            response = requests.get(
                f"{self.base_url}/coordination-context/conflict-event",
                params=params,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()

            return response.json().get('data', [])

        except Exception as e:
            logger.error(f"Failed to fetch conflict events: {e}")
            raise ValidationError(f"Failed to fetch conflict events: {e}")

    def get_food_security_data(self,
                             admin_level: int = 1,
                             from_date: date = None,
                             to_date: date = None) -> List[Dict]:
        """Get food security data for Sudan"""
        try:
            from_date = from_date or self.crisis_start_date
            to_date = to_date or date.today()

            params = {
                'location_code': self.sudan_iso3,
                'admin_level': admin_level,
                'reference_period_start': from_date.strftime("%Y-%m-%d"),
                'reference_period_end': to_date.strftime("%Y-%m-%d"),
                'output_format': 'json'
            }

            response = requests.get(
                f"{self.base_url}/food/food-security",
                params=params,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()

            return response.json().get('data', [])

        except Exception as e:
            logger.error(f"Failed to fetch food security data: {e}")
            raise ValidationError(f"Failed to fetch food security data: {e}")

    def get_all_sudan_crisis_data(self,
                                admin_level: int = 1,
                                from_date: date = None,
                                to_date: date = None) -> Dict[str, List[Dict]]:
        """Get comprehensive Sudan crisis data from all available endpoints"""
        try:
            from_date = from_date or self.crisis_start_date
            to_date = to_date or date.today()

            data = {}

            # Population and displacement
            data['population'] = self.get_population_data(admin_level, from_date, to_date)

            # Humanitarian funding
            data['funding'] = self.get_funding_data(from_date, to_date)

            # Humanitarian needs
            data['needs'] = self.get_humanitarian_needs(admin_level, from_date, to_date)

            # Conflict events
            data['conflict'] = self.get_conflict_events(admin_level, from_date, to_date)

            # Food security
            data['food_security'] = self.get_food_security_data(admin_level, from_date, to_date)

            return data

        except Exception as e:
            logger.error(f"Failed to fetch comprehensive Sudan data: {e}")
            raise ValidationError(f"Failed to fetch comprehensive data: {e}")


def get_hdx_service() -> HDXAPIService:
    """Get configured HDX API service instance"""
    api_key = getattr(settings, 'HDX_API_KEY', None)
    return HDXAPIService(api_key=api_key)


def get_hdx_hapi_service() -> HDXHAPIService:
    """Get configured HDX HAPI service instance"""
    api_key = getattr(settings, 'HDX_HAPI_API_KEY', None)
    return HDXHAPIService(api_key=api_key)