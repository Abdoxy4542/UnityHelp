import requests
import json
from django.conf import settings
from django.core.exceptions import ValidationError
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class KoboAPIService:
    """Service for interacting with KoboToolbox API"""
    
    def __init__(self, server_url: str = None, username: str = None, api_token: str = None):
        self.server_url = server_url or 'https://kf.kobotoolbox.org'
        self.username = username
        self.api_token = api_token
        self.base_url = f"{self.server_url}/api/v2"
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        if not self.api_token:
            raise ValidationError("Kobo API token is required")
        
        return {
            'Authorization': f'Token {self.api_token}',
            'Content-Type': 'application/json',
        }
    
    def test_connection(self) -> bool:
        """Test connection to Kobo API"""
        try:
            response = requests.get(
                f"{self.base_url}/assets/",
                headers=self._get_headers(),
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Kobo connection test failed: {e}")
            return False
    
    def get_assets(self) -> List[Dict]:
        """Get list of all assets (forms) from Kobo"""
        try:
            response = requests.get(
                f"{self.base_url}/assets/",
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            return response.json().get('results', [])
        except Exception as e:
            logger.error(f"Failed to fetch Kobo assets: {e}")
            raise ValidationError(f"Failed to fetch forms from Kobo: {e}")
    
    def get_asset_details(self, asset_uid: str) -> Dict:
        """Get detailed information about a specific asset"""
        try:
            response = requests.get(
                f"{self.base_url}/assets/{asset_uid}/",
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch asset {asset_uid}: {e}")
            raise ValidationError(f"Failed to fetch form details: {e}")
    
    def get_form_submissions(self, asset_uid: str, limit: int = 100) -> List[Dict]:
        """Get submissions for a specific form"""
        try:
            response = requests.get(
                f"{self.base_url}/assets/{asset_uid}/data/",
                headers=self._get_headers(),
                params={'limit': limit},
                timeout=60
            )
            response.raise_for_status()
            return response.json().get('results', [])
        except Exception as e:
            logger.error(f"Failed to fetch submissions for {asset_uid}: {e}")
            raise ValidationError(f"Failed to fetch form submissions: {e}")
    
    def get_submission_by_id(self, asset_uid: str, submission_id: str) -> Dict:
        """Get a specific submission by ID"""
        try:
            response = requests.get(
                f"{self.base_url}/assets/{asset_uid}/data/{submission_id}/",
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch submission {submission_id}: {e}")
            raise ValidationError(f"Failed to fetch submission: {e}")
    
    def create_asset(self, name: str, content: Dict) -> Dict:
        """Create a new form asset in Kobo"""
        try:
            data = {
                'name': name,
                'content': json.dumps(content),
                'asset_type': 'survey'
            }
            response = requests.post(
                f"{self.base_url}/assets/",
                headers=self._get_headers(),
                data=json.dumps(data),
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create asset: {e}")
            raise ValidationError(f"Failed to create form: {e}")
    
    def deploy_asset(self, asset_uid: str) -> Dict:
        """Deploy a form asset to make it available for data collection"""
        try:
            response = requests.post(
                f"{self.base_url}/assets/{asset_uid}/deployment/",
                headers=self._get_headers(),
                data=json.dumps({'active': True}),
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to deploy asset {asset_uid}: {e}")
            raise ValidationError(f"Failed to deploy form: {e}")
    
    def get_form_url(self, asset_uid: str) -> str:
        """Get the public URL for a deployed form"""
        try:
            asset_details = self.get_asset_details(asset_uid)
            deployment = asset_details.get('deployment__data_download_links', {})
            
            if 'enketo_url' in deployment:
                return deployment['enketo_url']
            elif asset_details.get('deployment__submission_count', 0) >= 0:
                return f"{self.server_url}/#{asset_uid}"
            else:
                raise ValidationError("Form is not deployed")
                
        except Exception as e:
            logger.error(f"Failed to get form URL for {asset_uid}: {e}")
            raise ValidationError(f"Failed to get form URL: {e}")
    
    def sync_submissions(self, asset_uid: str, last_sync_id: str = None) -> List[Dict]:
        """Sync new submissions since last sync"""
        try:
            params = {'limit': 1000}
            if last_sync_id:
                params['start'] = last_sync_id
                
            response = requests.get(
                f"{self.base_url}/assets/{asset_uid}/data/",
                headers=self._get_headers(),
                params=params,
                timeout=120
            )
            response.raise_for_status()
            
            data = response.json()
            submissions = data.get('results', [])
            
            # Sort by submission time to ensure proper ordering
            submissions.sort(key=lambda x: x.get('_submission_time', ''))
            
            return submissions
            
        except Exception as e:
            logger.error(f"Failed to sync submissions for {asset_uid}: {e}")
            raise ValidationError(f"Failed to sync submissions: {e}")


def get_kobo_service_for_user(user) -> KoboAPIService:
    """Get configured KoboAPIService instance for a user"""
    try:
        from apps.assessments.models import KoboIntegrationSettings
        kobo_settings = KoboIntegrationSettings.objects.get(user=user, is_active=True)
        
        return KoboAPIService(
            server_url=kobo_settings.kobo_server_url,
            username=kobo_settings.kobo_username,
            api_token=kobo_settings.kobo_api_token
        )
    except KoboIntegrationSettings.DoesNotExist:
        raise ValidationError("Kobo integration not configured for this user")