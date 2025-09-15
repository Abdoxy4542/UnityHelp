import requests
import json
from datetime import datetime, date
from django.conf import settings
from django.core.exceptions import ValidationError
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class DTMAPIService:
    """Service for interacting with IOM DTM (Displacement Tracking Matrix) API"""

    def __init__(self, api_key: str = None):
        self.base_url = "https://dtm.iom.int/api"
        self.api_key = api_key
        self.sudan_country_code = "SDN"
        self.sudan_country_id = 212  # IOM country ID for Sudan
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
        """Test connection to DTM API"""
        try:
            response = requests.get(
                f"{self.base_url}/idpfigures",
                headers=self._get_headers(),
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"DTM connection test failed: {e}")
            return False

    def get_country_operations(self, country_code: str = None) -> List[Dict]:
        """Get list of DTM operations by country"""
        try:
            country_code = country_code or self.sudan_country_code

            response = requests.get(
                f"{self.base_url}/operations",
                params={'country': country_code},
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Failed to fetch DTM operations: {e}")
            raise ValidationError(f"Failed to fetch DTM operations: {e}")

    def get_displacement_data(self,
                            country_id: int = None,
                            admin_level: int = 1,
                            from_date: date = None,
                            to_date: date = None,
                            limit: int = 1000) -> List[Dict]:
        """Get IDP figures for Sudan from DTM API"""
        try:
            country_id = country_id or self.sudan_country_id
            from_date = from_date or self.crisis_start_date
            to_date = to_date or date.today()

            params = {
                'country': country_id,
                'admin_level': admin_level,
                'date_from': from_date.strftime("%Y-%m-%d"),
                'date_to': to_date.strftime("%Y-%m-%d"),
                'limit': limit,
                'format': 'json'
            }

            response = requests.get(
                f"{self.base_url}/idpfigures",
                params=params,
                headers=self._get_headers(),
                timeout=60
            )
            response.raise_for_status()

            data = response.json()
            return data.get('results', []) if isinstance(data, dict) else data

        except Exception as e:
            logger.error(f"Failed to fetch displacement data: {e}")
            raise ValidationError(f"Failed to fetch displacement data: {e}")

    def get_returnee_data(self,
                         country_id: int = None,
                         admin_level: int = 1,
                         from_date: date = None,
                         to_date: date = None,
                         limit: int = 1000) -> List[Dict]:
        """Get returnee figures for Sudan"""
        try:
            country_id = country_id or self.sudan_country_id
            from_date = from_date or self.crisis_start_date
            to_date = to_date or date.today()

            params = {
                'country': country_id,
                'admin_level': admin_level,
                'date_from': from_date.strftime("%Y-%m-%d"),
                'date_to': to_date.strftime("%Y-%m-%d"),
                'limit': limit,
                'format': 'json'
            }

            response = requests.get(
                f"{self.base_url}/returnees",
                params=params,
                headers=self._get_headers(),
                timeout=60
            )
            response.raise_for_status()

            data = response.json()
            return data.get('results', []) if isinstance(data, dict) else data

        except Exception as e:
            logger.error(f"Failed to fetch returnee data: {e}")
            raise ValidationError(f"Failed to fetch returnee data: {e}")

    def get_site_assessments(self,
                           country_id: int = None,
                           from_date: date = None,
                           to_date: date = None,
                           limit: int = 500) -> List[Dict]:
        """Get site assessment data for Sudan"""
        try:
            country_id = country_id or self.sudan_country_id
            from_date = from_date or self.crisis_start_date
            to_date = to_date or date.today()

            params = {
                'country': country_id,
                'date_from': from_date.strftime("%Y-%m-%d"),
                'date_to': to_date.strftime("%Y-%m-%d"),
                'limit': limit,
                'format': 'json'
            }

            response = requests.get(
                f"{self.base_url}/site_assessments",
                params=params,
                headers=self._get_headers(),
                timeout=60
            )
            response.raise_for_status()

            data = response.json()
            return data.get('results', []) if isinstance(data, dict) else data

        except Exception as e:
            logger.error(f"Failed to fetch site assessments: {e}")
            raise ValidationError(f"Failed to fetch site assessments: {e}")

    def get_mobility_data(self,
                         country_id: int = None,
                         from_date: date = None,
                         to_date: date = None,
                         limit: int = 1000) -> List[Dict]:
        """Get mobility tracking data for Sudan"""
        try:
            country_id = country_id or self.sudan_country_id
            from_date = from_date or self.crisis_start_date
            to_date = to_date or date.today()

            params = {
                'country': country_id,
                'date_from': from_date.strftime("%Y-%m-%d"),
                'date_to': to_date.strftime("%Y-%m-%d"),
                'limit': limit,
                'format': 'json'
            }

            response = requests.get(
                f"{self.base_url}/mobility",
                params=params,
                headers=self._get_headers(),
                timeout=60
            )
            response.raise_for_status()

            data = response.json()
            return data.get('results', []) if isinstance(data, dict) else data

        except Exception as e:
            logger.error(f"Failed to fetch mobility data: {e}")
            raise ValidationError(f"Failed to fetch mobility data: {e}")

    def get_baseline_assessments(self,
                               country_id: int = None,
                               from_date: date = None,
                               to_date: date = None,
                               limit: int = 500) -> List[Dict]:
        """Get baseline assessment data for Sudan"""
        try:
            country_id = country_id or self.sudan_country_id
            from_date = from_date or self.crisis_start_date
            to_date = to_date or date.today()

            params = {
                'country': country_id,
                'date_from': from_date.strftime("%Y-%m-%d"),
                'date_to': to_date.strftime("%Y-%m-%d"),
                'limit': limit,
                'format': 'json'
            }

            response = requests.get(
                f"{self.base_url}/baseline",
                params=params,
                headers=self._get_headers(),
                timeout=60
            )
            response.raise_for_status()

            data = response.json()
            return data.get('results', []) if isinstance(data, dict) else data

        except Exception as e:
            logger.error(f"Failed to fetch baseline assessments: {e}")
            raise ValidationError(f"Failed to fetch baseline assessments: {e}")

    def get_comprehensive_displacement_data(self,
                                          admin_level: int = 1,
                                          from_date: date = None,
                                          to_date: date = None) -> Dict[str, List[Dict]]:
        """Get comprehensive displacement data for Sudan crisis"""
        try:
            from_date = from_date or self.crisis_start_date
            to_date = to_date or date.today()

            data = {}

            # IDP displacement figures
            data['displacement'] = self.get_displacement_data(
                admin_level=admin_level,
                from_date=from_date,
                to_date=to_date
            )

            # Returnee data
            data['returnees'] = self.get_returnee_data(
                admin_level=admin_level,
                from_date=from_date,
                to_date=to_date
            )

            # Site assessments
            data['site_assessments'] = self.get_site_assessments(
                from_date=from_date,
                to_date=to_date
            )

            # Mobility tracking
            data['mobility'] = self.get_mobility_data(
                from_date=from_date,
                to_date=to_date
            )

            # Baseline assessments
            data['baseline'] = self.get_baseline_assessments(
                from_date=from_date,
                to_date=to_date
            )

            return data

        except Exception as e:
            logger.error(f"Failed to fetch comprehensive displacement data: {e}")
            raise ValidationError(f"Failed to fetch comprehensive displacement data: {e}")

    def get_latest_figures_summary(self, admin_level: int = 1) -> Dict:
        """Get latest displacement figures summary for Sudan"""
        try:
            # Get most recent data
            recent_data = self.get_displacement_data(
                admin_level=admin_level,
                from_date=date.today().replace(day=1),  # Current month
                to_date=date.today(),
                limit=100
            )

            if not recent_data:
                # If no recent data, get last 3 months
                from datetime import timedelta
                three_months_ago = date.today() - timedelta(days=90)
                recent_data = self.get_displacement_data(
                    admin_level=admin_level,
                    from_date=three_months_ago,
                    to_date=date.today(),
                    limit=100
                )

            # Calculate summary statistics
            total_idps = 0
            total_families = 0
            locations = set()

            for record in recent_data:
                if record.get('idp_individuals'):
                    total_idps += record.get('idp_individuals', 0)
                if record.get('idp_families'):
                    total_families += record.get('idp_families', 0)
                if record.get('location_name'):
                    locations.add(record.get('location_name'))

            return {
                'total_idp_individuals': total_idps,
                'total_idp_families': total_families,
                'affected_locations': len(locations),
                'locations_list': list(locations),
                'last_updated': recent_data[0].get('assessment_date') if recent_data else None,
                'data_points': len(recent_data)
            }

        except Exception as e:
            logger.error(f"Failed to get latest figures summary: {e}")
            raise ValidationError(f"Failed to get latest figures summary: {e}")


def get_dtm_service() -> DTMAPIService:
    """Get configured DTM API service instance"""
    api_key = getattr(settings, 'DTM_API_KEY', None)
    return DTMAPIService(api_key=api_key)