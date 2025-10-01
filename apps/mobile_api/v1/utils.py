import secrets
import logging
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

from ..models import MobileDevice, RefreshToken

logger = logging.getLogger(__name__)


def generate_refresh_token(user, device):
    """Generate a new refresh token for user and device"""
    token = secrets.token_urlsafe(64)
    expires_at = timezone.now() + timedelta(days=30)  # 30 days expiry

    refresh_token = RefreshToken.objects.create(
        user=user,
        device=device,
        token=token,
        expires_at=expires_at
    )

    return refresh_token


def create_or_update_device(user, device_data):
    """Create or update mobile device registration"""
    device_id = device_data['device_id']
    platform = device_data['platform']

    device, created = MobileDevice.objects.get_or_create(
        user=user,
        device_id=device_id,
        defaults={
            'platform': platform,
            'fcm_token': device_data.get('fcm_token', ''),
            'app_version': device_data.get('app_version', ''),
            'os_version': device_data.get('os_version', ''),
            'device_model': device_data.get('device_model', ''),
        }
    )

    if not created:
        # Update existing device
        device.fcm_token = device_data.get('fcm_token', device.fcm_token)
        device.app_version = device_data.get('app_version', device.app_version)
        device.os_version = device_data.get('os_version', device.os_version)
        device.device_model = device_data.get('device_model', device.device_model)
        device.last_seen = timezone.now()
        device.save()

    return device


def send_mobile_notification(user, title, message, data=None):
    """Send push notification to user's mobile devices"""
    devices = MobileDevice.objects.filter(
        user=user,
        is_active=True,
        fcm_token__isnull=False
    ).exclude(fcm_token='')

    for device in devices:
        try:
            # Implement FCM notification sending
            # This would use Firebase Admin SDK or similar service
            logger.info(f"Sending notification to device {device.device_id}: {title}")

            # For now, just log the notification
            # In production, integrate with Firebase Cloud Messaging
            notification_data = {
                'title': title,
                'message': message,
                'data': data or {},
                'device_token': device.fcm_token
            }

            # Store notification in cache for testing
            cache_key = f"notification_{device.id}_{timezone.now().timestamp()}"
            cache.set(cache_key, notification_data, 3600)

        except Exception as e:
            logger.error(f"Failed to send notification to device {device.device_id}: {e}")


def validate_gps_coordinates(latitude, longitude):
    """Validate GPS coordinates"""
    try:
        lat = float(latitude)
        lon = float(longitude)

        if not (-90 <= lat <= 90):
            return False, "Latitude must be between -90 and 90"

        if not (-180 <= lon <= 180):
            return False, "Longitude must be between -180 and 180"

        return True, None

    except (ValueError, TypeError):
        return False, "Invalid coordinate format"


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    import math

    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    # Radius of earth in kilometers
    r = 6371

    return c * r


def get_sites_within_radius(center_lat, center_lon, radius_km):
    """Get sites within specified radius of center point"""
    from apps.sites.models import Site

    sites = []
    all_sites = Site.objects.filter(location__isnull=False)

    for site in all_sites:
        if site.coordinates:
            site_lon, site_lat = site.coordinates
            distance = calculate_distance(center_lat, center_lon, site_lat, site_lon)

            if distance <= radius_km:
                sites.append({
                    'site': site,
                    'distance': round(distance, 2)
                })

    return sorted(sites, key=lambda x: x['distance'])


def compress_response_data(data):
    """Compress response data for mobile bandwidth optimization"""
    import gzip
    import json

    if isinstance(data, dict):
        json_data = json.dumps(data, separators=(',', ':'))
        compressed = gzip.compress(json_data.encode('utf-8'))
        return compressed

    return data


def generate_sync_checksum(data):
    """Generate checksum for sync data integrity"""
    import hashlib
    import json

    if isinstance(data, dict):
        json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.md5(json_str.encode()).hexdigest()

    return None


def log_api_access(user, endpoint, method, status_code, response_time=None):
    """Log API access for monitoring and analytics"""
    log_data = {
        'user_id': user.id if user.is_authenticated else None,
        'username': user.username if user.is_authenticated else 'anonymous',
        'endpoint': endpoint,
        'method': method,
        'status_code': status_code,
        'response_time': response_time,
        'timestamp': timezone.now().isoformat()
    }

    # In production, send to monitoring service or database
    logger.info(f"API Access: {log_data}")


def sanitize_file_upload(file):
    """Sanitize uploaded files for security"""
    import os

    allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx', '.xlsx']
    max_file_size = 10 * 1024 * 1024  # 10MB

    # Check file size
    if file.size > max_file_size:
        return False, "File size exceeds 10MB limit"

    # Check file extension
    file_extension = os.path.splitext(file.name)[1].lower()
    if file_extension not in allowed_extensions:
        return False, f"File type {file_extension} not allowed"

    # Additional security checks can be added here
    # Like virus scanning, content validation, etc.

    return True, None


def format_mobile_error_response(error_message, error_code=None):
    """Format error response for mobile consumption"""
    return {
        'error': True,
        'message': error_message,
        'code': error_code,
        'timestamp': timezone.now().isoformat()
    }


def get_user_sync_data(user, data_types=None, last_sync_date=None):
    """Get synchronized data for user based on their role and permissions"""
    from apps.sites.models import Site
    from apps.assessments.models import Assessment, AssessmentResponse

    sync_data = {}

    if not data_types:
        data_types = ['sites', 'assessments', 'responses']

    # Get sites based on user role
    if 'sites' in data_types:
        if user.role == 'gso':
            sites = Site.objects.filter(
                id__in=user.assigned_sites.all()
            )
        else:
            sites = Site.objects.filter(operational_status='active')

        if last_sync_date:
            sites = sites.filter(updated_at__gt=last_sync_date)

        sync_data['sites'] = sites[:100]  # Limit for mobile

    # Get assessments
    if 'assessments' in data_types:
        assessments = Assessment.objects.filter(
            assigned_to=user,
            status='active'
        )

        if last_sync_date:
            assessments = assessments.filter(updated_at__gt=last_sync_date)

        sync_data['assessments'] = assessments[:50]

    # Get user's responses
    if 'responses' in data_types:
        responses = AssessmentResponse.objects.filter(
            respondent=user
        )

        if last_sync_date:
            responses = responses.filter(updated_at__gt=last_sync_date)

        sync_data['responses'] = responses[:100]

    return sync_data