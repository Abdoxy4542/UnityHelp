import time
import logging
import json
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status

logger = logging.getLogger('mobile_api')


class MobileAPILoggingMiddleware(MiddlewareMixin):
    """Middleware for logging mobile API requests and responses"""

    def process_request(self, request):
        # Only log mobile API requests
        if not request.path.startswith('/api/mobile/'):
            return None

        # Store request start time
        request._mobile_api_start_time = time.time()

        # Log request details
        log_data = {
            'event': 'api_request_started',
            'timestamp': timezone.now().isoformat(),
            'path': request.path,
            'method': request.method,
            'user_id': request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'remote_addr': self.get_client_ip(request),
            'query_params': dict(request.GET),
        }

        # Log request body for POST/PUT/PATCH (excluding sensitive data)
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                content_type = request.META.get('CONTENT_TYPE', '')
                if 'application/json' in content_type:
                    body = json.loads(request.body.decode('utf-8'))
                    # Remove sensitive fields
                    sanitized_body = self.sanitize_request_body(body)
                    log_data['request_body'] = sanitized_body
            except (json.JSONDecodeError, UnicodeDecodeError):
                log_data['request_body'] = 'Unable to parse request body'

        logger.info('Mobile API Request', extra={'log_data': log_data})

        return None

    def process_response(self, request, response):
        # Only process mobile API responses
        if not request.path.startswith('/api/mobile/'):
            return response

        # Calculate response time
        if hasattr(request, '_mobile_api_start_time'):
            response_time = time.time() - request._mobile_api_start_time
        else:
            response_time = None

        # Log response details
        log_data = {
            'event': 'api_request_completed',
            'timestamp': timezone.now().isoformat(),
            'path': request.path,
            'method': request.method,
            'status_code': response.status_code,
            'response_time_ms': round(response_time * 1000, 2) if response_time else None,
            'user_id': request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
            'content_length': len(response.content) if hasattr(response, 'content') else None,
        }

        # Log slow requests
        if response_time and response_time > 2.0:  # Requests taking more than 2 seconds
            log_data['slow_request'] = True
            logger.warning('Slow Mobile API Request', extra={'log_data': log_data})
        else:
            logger.info('Mobile API Response', extra={'log_data': log_data})

        # Add performance headers
        if response_time:
            response['X-Response-Time'] = f"{response_time:.3f}s"

        # Track API usage metrics
        self.track_api_metrics(request, response, response_time)

        return response

    def process_exception(self, request, exception):
        # Only process mobile API exceptions
        if not request.path.startswith('/api/mobile/'):
            return None

        # Calculate response time
        if hasattr(request, '_mobile_api_start_time'):
            response_time = time.time() - request._mobile_api_start_time
        else:
            response_time = None

        # Log exception details
        log_data = {
            'event': 'api_request_error',
            'timestamp': timezone.now().isoformat(),
            'path': request.path,
            'method': request.method,
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'response_time_ms': round(response_time * 1000, 2) if response_time else None,
            'user_id': request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
        }

        logger.error('Mobile API Exception', extra={'log_data': log_data}, exc_info=True)

        # Return a mobile-friendly error response
        return JsonResponse({
            'error': True,
            'message': 'An internal error occurred. Please try again.',
            'timestamp': timezone.now().isoformat(),
            'request_id': getattr(request, 'request_id', None)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def sanitize_request_body(self, body):
        """Remove sensitive information from request body"""
        if not isinstance(body, dict):
            return body

        sensitive_fields = ['password', 'password_confirm', 'token', 'refresh_token', 'fcm_token']
        sanitized = body.copy()

        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = '[REDACTED]'

        return sanitized

    def track_api_metrics(self, request, response, response_time):
        """Track API usage metrics in cache"""
        try:
            # Get current date for daily metrics
            date_key = timezone.now().strftime('%Y-%m-%d')

            # Track endpoint usage
            endpoint_key = f"mobile_api_metrics:{date_key}:endpoint:{request.path}"
            cache.set(endpoint_key, cache.get(endpoint_key, 0) + 1, 86400)  # 24 hours

            # Track status codes
            status_key = f"mobile_api_metrics:{date_key}:status:{response.status_code}"
            cache.set(status_key, cache.get(status_key, 0) + 1, 86400)

            # Track response times
            if response_time:
                response_times_key = f"mobile_api_metrics:{date_key}:response_times"
                response_times = cache.get(response_times_key, [])
                response_times.append(response_time)
                # Keep only last 1000 response times
                if len(response_times) > 1000:
                    response_times = response_times[-1000:]
                cache.set(response_times_key, response_times, 86400)

            # Track user activity
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_key = f"mobile_api_metrics:{date_key}:user:{request.user.id}"
                cache.set(user_key, cache.get(user_key, 0) + 1, 86400)

        except Exception as e:
            logger.error(f"Failed to track API metrics: {e}")


class MobileAPISecurityMiddleware(MiddlewareMixin):
    """Security middleware for mobile API"""

    def process_request(self, request):
        # Only process mobile API requests
        if not request.path.startswith('/api/mobile/'):
            return None

        # Rate limiting check
        if self.is_rate_limited(request):
            return JsonResponse({
                'error': True,
                'message': 'Rate limit exceeded. Please try again later.',
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Check for suspicious activity
        if self.is_suspicious_request(request):
            logger.warning(f"Suspicious mobile API request from {self.get_client_ip(request)}")

        return None

    def process_response(self, request, response):
        # Only process mobile API responses
        if not request.path.startswith('/api/mobile/'):
            return response

        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        return response

    def is_rate_limited(self, request):
        """Simple rate limiting implementation"""
        client_ip = self.get_client_ip(request)
        rate_limit_key = f"mobile_api_rate_limit:{client_ip}"

        # Get current request count
        current_count = cache.get(rate_limit_key, 0)

        # Rate limit: 100 requests per minute
        if current_count >= 100:
            return True

        # Increment counter
        cache.set(rate_limit_key, current_count + 1, 60)  # 1 minute expiry

        return False

    def is_suspicious_request(self, request):
        """Detect potentially suspicious requests"""
        # Check for unusual user agents
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        suspicious_agents = ['bot', 'crawler', 'spider', 'scraper']

        if any(agent in user_agent for agent in suspicious_agents):
            return True

        # Check for unusual request patterns
        # This could be expanded with more sophisticated detection logic

        return False

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class MobileAPIMonitoringMiddleware(MiddlewareMixin):
    """Middleware for monitoring mobile API health and performance"""

    def process_request(self, request):
        # Only process mobile API requests
        if not request.path.startswith('/api/mobile/'):
            return None

        # Add request ID for tracing
        request.request_id = self.generate_request_id()

        return None

    def process_response(self, request, response):
        # Only process mobile API responses
        if not request.path.startswith('/api/mobile/'):
            return response

        # Add request ID to response headers
        if hasattr(request, 'request_id'):
            response['X-Request-ID'] = request.request_id

        # Monitor API health
        self.monitor_api_health(request, response)

        return response

    def generate_request_id(self):
        """Generate unique request ID"""
        import uuid
        return str(uuid.uuid4())[:8]

    def monitor_api_health(self, request, response):
        """Monitor API health metrics"""
        try:
            # Track error rates
            if response.status_code >= 400:
                error_key = f"mobile_api_errors:{timezone.now().strftime('%Y-%m-%d-%H')}"
                cache.set(error_key, cache.get(error_key, 0) + 1, 3600)  # 1 hour

            # Track availability
            availability_key = f"mobile_api_availability:{timezone.now().strftime('%Y-%m-%d-%H')}"
            cache.set(availability_key, cache.get(availability_key, 0) + 1, 3600)

            # Check if error rate is too high
            error_count = cache.get(error_key, 0)
            total_count = cache.get(availability_key, 1)
            error_rate = error_count / total_count

            if error_rate > 0.1:  # More than 10% error rate
                logger.critical(f"High error rate detected: {error_rate:.2%}")

        except Exception as e:
            logger.error(f"Failed to monitor API health: {e}")