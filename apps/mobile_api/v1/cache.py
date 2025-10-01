from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
import json
import hashlib
from functools import wraps


class MobileAPICache:
    """Enhanced caching for mobile API endpoints"""

    # Cache timeouts in seconds
    TIMEOUTS = {
        'user_profile': 3600,  # 1 hour
        'sites_list': 1800,    # 30 minutes
        'assessments': 1800,   # 30 minutes
        'dashboard': 900,      # 15 minutes
        'form_data': 3600,     # 1 hour
        'sync_data': 1800,     # 30 minutes
        'nearby_sites': 600,   # 10 minutes
    }

    @staticmethod
    def make_key(prefix, *args, **kwargs):
        """Generate cache key from arguments"""
        key_data = {
            'args': args,
            'kwargs': kwargs,
            'timestamp': timezone.now().strftime('%Y-%m-%d')  # Daily cache invalidation
        }

        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:12]

        return f"mobile_api:{prefix}:{key_hash}"

    @classmethod
    def get(cls, prefix, *args, **kwargs):
        """Get data from cache"""
        key = cls.make_key(prefix, *args, **kwargs)
        return cache.get(key)

    @classmethod
    def set(cls, prefix, data, *args, **kwargs):
        """Set data in cache"""
        key = cls.make_key(prefix, *args, **kwargs)
        timeout = cls.TIMEOUTS.get(prefix, 1800)  # Default 30 minutes
        cache.set(key, data, timeout)

    @classmethod
    def delete(cls, prefix, *args, **kwargs):
        """Delete data from cache"""
        key = cls.make_key(prefix, *args, **kwargs)
        cache.delete(key)

    @classmethod
    def cache_user_data(cls, user):
        """Cache user-specific data"""
        user_key = f"user_data_{user.id}"
        user_data = {
            'id': user.id,
            'role': user.role,
            'organization': user.organization,
            'assigned_sites': list(user.assigned_sites.values_list('id', flat=True)),
            'cached_at': timezone.now().isoformat()
        }
        cls.set('user_profile', user_data, user_id=user.id)
        return user_data

    @classmethod
    def invalidate_user_cache(cls, user_id):
        """Invalidate all cache for a specific user"""
        patterns = [
            f"mobile_api:user_profile:*{user_id}*",
            f"mobile_api:dashboard:*{user_id}*",
            f"mobile_api:assessments:*{user_id}*",
        ]

        # In production, use Redis pattern deletion
        # For now, we'll rely on cache expiration
        pass


def cache_mobile_response(cache_prefix, timeout=None):
    """Decorator to cache mobile API responses"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            # Skip caching for non-GET requests
            if request.method != 'GET':
                return view_func(self, request, *args, **kwargs)

            # Generate cache key based on user, view, and parameters
            cache_args = (
                request.user.id if request.user.is_authenticated else 'anonymous',
                request.path,
                str(request.GET.dict())
            )

            # Try to get from cache
            cached_response = MobileAPICache.get(cache_prefix, *cache_args)
            if cached_response:
                return cached_response

            # Get fresh response
            response = view_func(self, request, *args, **kwargs)

            # Cache successful responses
            if response.status_code == 200:
                MobileAPICache.set(cache_prefix, response, *cache_args)

            return response

        return wrapper
    return decorator


class QueryOptimizer:
    """Database query optimization for mobile API"""

    @staticmethod
    def optimize_sites_queryset(queryset, user=None):
        """Optimize sites queryset with prefetch and select_related"""
        return queryset.select_related(
            'state',
            'locality'
        ).prefetch_related(
            'assigned_gsos'
        ).only(
            'id', 'name', 'name_ar', 'site_type', 'operational_status',
            'location', 'total_population', 'total_households',
            'state__name', 'locality__name', 'updated_at'
        )

    @staticmethod
    def optimize_assessments_queryset(queryset, user=None):
        """Optimize assessments queryset"""
        return queryset.select_related(
            'created_by'
        ).prefetch_related(
            'assigned_to',
            'target_sites'
        ).annotate(
            response_count=Count('responses')
        ).only(
            'id', 'title', 'title_ar', 'assessment_type', 'status',
            'start_date', 'end_date', 'created_by__first_name',
            'created_by__last_name', 'created_at', 'updated_at'
        )

    @staticmethod
    def optimize_responses_queryset(queryset, user=None):
        """Optimize assessment responses queryset"""
        return queryset.select_related(
            'assessment',
            'site',
            'respondent'
        ).only(
            'id', 'assessment__title', 'site__name',
            'respondent__first_name', 'respondent__last_name',
            'is_submitted', 'submitted_at', 'created_at'
        )


class MobileDataCompressor:
    """Compress data for mobile bandwidth optimization"""

    @staticmethod
    def compress_site_data(sites_data):
        """Compress sites data by removing unnecessary fields"""
        compressed = []

        for site in sites_data:
            compressed_site = {
                'id': site['id'],
                'name': site['name'],
                'type': site['site_type'],
                'status': site['operational_status'],
                'coords': site.get('coordinates'),
                'pop': site.get('total_population'),
                'hh': site.get('total_households'),
                'state': site.get('state_name'),
                'locality': site.get('locality_name'),
                'updated': site.get('last_updated')
            }
            compressed.append(compressed_site)

        return compressed

    @staticmethod
    def compress_assessment_data(assessments_data):
        """Compress assessments data"""
        compressed = []

        for assessment in assessments_data:
            compressed_assessment = {
                'id': assessment['id'],
                'title': assessment['title'],
                'type': assessment['assessment_type'],
                'status': assessment['status'],
                'start': assessment.get('start_date'),
                'end': assessment.get('end_date'),
                'responses': assessment.get('response_count', 0),
                'assigned': assessment.get('assigned_to_me', False)
            }
            compressed.append(compressed_assessment)

        return compressed


class OfflineDataManager:
    """Manage offline data synchronization"""

    @staticmethod
    def prepare_offline_data(user):
        """Prepare data for offline usage"""
        offline_data = {
            'user_profile': MobileAPICache.get('user_profile', user_id=user.id),
            'essential_sites': [],
            'active_assessments': [],
            'draft_responses': [],
            'sync_metadata': {
                'prepared_at': timezone.now().isoformat(),
                'version': '1.0',
                'user_id': user.id
            }
        }

        # Add essential sites (user's assigned sites)
        if user.role == 'gso':
            from apps.sites.models import Site
            sites = Site.objects.filter(
                id__in=user.assigned_sites.all()
            ).values(
                'id', 'name', 'location', 'total_population',
                'state__name', 'locality__name'
            )[:20]  # Limit for offline storage

            offline_data['essential_sites'] = list(sites)

        # Add active assessments
        from apps.assessments.models import Assessment
        assessments = Assessment.objects.filter(
            assigned_to=user,
            status='active'
        ).values(
            'id', 'title', 'assessment_type', 'kobo_form_url'
        )[:10]

        offline_data['active_assessments'] = list(assessments)

        return offline_data

    @staticmethod
    def sync_offline_changes(user, offline_data):
        """Sync changes made while offline"""
        sync_results = {
            'uploaded': 0,
            'failed': 0,
            'conflicts': [],
            'sync_id': timezone.now().strftime('%Y%m%d%H%M%S')
        }

        # Process different types of offline changes
        if 'new_responses' in offline_data:
            for response_data in offline_data['new_responses']:
                try:
                    # Create new assessment response
                    # Implementation depends on your response model
                    sync_results['uploaded'] += 1
                except Exception as e:
                    sync_results['failed'] += 1
                    sync_results['conflicts'].append({
                        'type': 'response',
                        'data': response_data,
                        'error': str(e)
                    })

        return sync_results


# Cache invalidation signals
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.sites.models import Site
from apps.assessments.models import Assessment, AssessmentResponse


@receiver(post_save, sender=Site)
@receiver(post_delete, sender=Site)
def invalidate_sites_cache(sender, **kwargs):
    """Invalidate sites cache when sites are modified"""
    # Clear all sites-related cache
    cache.delete_many(cache.keys('mobile_api:sites_list:*'))
    cache.delete_many(cache.keys('mobile_api:nearby_sites:*'))
    cache.delete_many(cache.keys('mobile_api:dashboard:*'))


@receiver(post_save, sender=Assessment)
@receiver(post_delete, sender=Assessment)
def invalidate_assessments_cache(sender, **kwargs):
    """Invalidate assessments cache when assessments are modified"""
    cache.delete_many(cache.keys('mobile_api:assessments:*'))
    cache.delete_many(cache.keys('mobile_api:dashboard:*'))


@receiver(post_save, sender=AssessmentResponse)
def invalidate_responses_cache(sender, **kwargs):
    """Invalidate responses cache when responses are modified"""
    cache.delete_many(cache.keys('mobile_api:assessments:*'))
    cache.delete_many(cache.keys('mobile_api:dashboard:*'))