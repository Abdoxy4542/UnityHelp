"""
Base MCP Server Framework for UnityAid
Provides standardized data access layer for AI agents
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
from decimal import Decimal

from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import GEOSGeometry
from django.core.paginator import Paginator
from django.db.models import QuerySet, Model
from django.conf import settings
import jwt
from geojson import Feature, FeatureCollection, Point, Polygon

User = get_user_model()
logger = logging.getLogger(__name__)


class MCPAuthenticationError(Exception):
    """Authentication related errors"""
    pass


class MCPDataError(Exception):
    """Data processing related errors"""
    pass


class MCPResponse:
    """Standardized MCP response format"""

    def __init__(self, status: str = "success", data: Any = None, error: str = None,
                 metadata: Dict = None, spatial: Dict = None):
        self.status = status
        self.data = data
        self.error = error
        self.metadata = metadata or {}
        self.spatial = spatial

    def to_dict(self) -> Dict:
        """Convert response to dictionary"""
        response = {
            "status": self.status,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        if self.data is not None:
            response["data"] = self.data

        if self.error:
            response["error"] = self.error

        if self.metadata:
            response["metadata"] = self.metadata

        if self.spatial:
            response["spatial"] = self.spatial

        return response

    def to_json(self) -> str:
        """Convert response to JSON string"""
        return json.dumps(self.to_dict(), cls=UnityAidJSONEncoder, ensure_ascii=False)


class UnityAidJSONEncoder(DjangoJSONEncoder):
    """Custom JSON encoder for UnityAid data types"""

    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, GEOSGeometry):
            return json.loads(obj.geojson)
        return super().default(obj)


class BaseMCPServer(ABC):
    """
    Abstract base class for all MCP servers in UnityAid
    Provides common functionality for authentication, data formatting, and error handling
    """

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"mcp.{name}")

    def authenticate(self, token: str) -> User:
        """
        Authenticate user using JWT token

        Args:
            token: JWT token string

        Returns:
            User instance if authentication successful

        Raises:
            MCPAuthenticationError: If authentication fails
        """
        try:
            if not token:
                raise MCPAuthenticationError("No authentication token provided")

            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]

            # Decode JWT token
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=['HS256']
            )

            user_id = payload.get('user_id')
            if not user_id:
                raise MCPAuthenticationError("Invalid token payload")

            user = User.objects.get(id=user_id)
            if not user.is_active:
                raise MCPAuthenticationError("User account is inactive")

            return user

        except jwt.ExpiredSignatureError:
            raise MCPAuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise MCPAuthenticationError("Invalid token")
        except User.DoesNotExist:
            raise MCPAuthenticationError("User not found")
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            raise MCPAuthenticationError("Authentication failed")

    def check_permissions(self, user: User, action: str, resource: str = None) -> bool:
        """
        Check if user has permissions for specified action

        Args:
            user: Django User instance
            action: Action being performed (read, write, admin)
            resource: Specific resource being accessed

        Returns:
            True if user has permission, False otherwise
        """
        # Basic permission checks based on user role
        if action == 'read':
            # All authenticated users can read data
            return True
        elif action == 'write':
            # Only staff and GSO users can write data
            return user.is_staff or hasattr(user, 'role')
        elif action == 'admin':
            # Only staff users can perform admin actions
            return user.is_staff

        return False

    def paginate_queryset(self, queryset: QuerySet, page: int = 1,
                         per_page: int = 50) -> Dict:
        """
        Paginate Django queryset

        Args:
            queryset: Django QuerySet to paginate
            page: Page number (1-based)
            per_page: Items per page

        Returns:
            Dictionary with paginated data and metadata
        """
        max_per_page = getattr(settings, 'MCP_MAX_PAGE_SIZE', 500)
        per_page = min(per_page, max_per_page)

        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page)

        return {
            'results': list(page_obj.object_list),
            'metadata': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'per_page': per_page,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
                'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None
            }
        }

    def serialize_model_instance(self, instance: Model, fields: List[str] = None,
                                exclude: List[str] = None) -> Dict:
        """
        Serialize Django model instance to dictionary

        Args:
            instance: Django model instance
            fields: List of fields to include (None for all)
            exclude: List of fields to exclude

        Returns:
            Dictionary representation of model instance
        """
        exclude = exclude or []
        data = {}

        for field in instance._meta.fields:
            field_name = field.name

            # Skip excluded fields
            if exclude and field_name in exclude:
                continue

            # Include only specified fields if provided
            if fields and field_name not in fields:
                continue

            value = getattr(instance, field_name)

            # Handle different field types
            if hasattr(field, 'geom_type'):  # PostGIS field
                if value:
                    data[field_name] = json.loads(value.geojson)
                else:
                    data[field_name] = None
            elif isinstance(value, (datetime, date)):
                data[field_name] = value.isoformat() if value else None
            elif isinstance(value, Decimal):
                data[field_name] = float(value)
            elif hasattr(value, 'pk'):  # Related model
                data[field_name] = {
                    'id': value.pk,
                    'name': str(value)
                }
            else:
                data[field_name] = value

        # Add computed fields
        data['id'] = instance.pk
        data['model'] = instance._meta.label_lower

        return data

    def serialize_queryset(self, queryset: QuerySet, fields: List[str] = None,
                          exclude: List[str] = None) -> List[Dict]:
        """
        Serialize Django QuerySet to list of dictionaries

        Args:
            queryset: Django QuerySet
            fields: List of fields to include
            exclude: List of fields to exclude

        Returns:
            List of serialized model instances
        """
        return [
            self.serialize_model_instance(instance, fields, exclude)
            for instance in queryset
        ]

    def create_geojson_feature_collection(self, queryset: QuerySet,
                                        geometry_field: str = 'location',
                                        properties_fields: List[str] = None) -> Dict:
        """
        Create GeoJSON FeatureCollection from QuerySet with spatial data

        Args:
            queryset: Django QuerySet with spatial data
            geometry_field: Name of geometry field
            properties_fields: Fields to include as properties

        Returns:
            GeoJSON FeatureCollection dictionary
        """
        features = []

        for instance in queryset:
            geometry = getattr(instance, geometry_field, None)
            if geometry:
                # Create properties
                properties = {}
                if properties_fields:
                    for field_name in properties_fields:
                        if hasattr(instance, field_name):
                            value = getattr(instance, field_name)
                            if isinstance(value, (datetime, date)):
                                properties[field_name] = value.isoformat() if value else None
                            elif isinstance(value, Decimal):
                                properties[field_name] = float(value)
                            else:
                                properties[field_name] = value
                else:
                    # Include all non-geometric fields
                    properties = self.serialize_model_instance(
                        instance,
                        exclude=[geometry_field]
                    )

                # Create GeoJSON feature
                feature = Feature(
                    geometry=json.loads(geometry.geojson),
                    properties=properties
                )
                features.append(feature)

        return FeatureCollection(features)

    def calculate_spatial_bounds(self, queryset: QuerySet,
                               geometry_field: str = 'location') -> Dict:
        """
        Calculate spatial bounds for a QuerySet with geometric data

        Args:
            queryset: Django QuerySet with spatial data
            geometry_field: Name of geometry field

        Returns:
            Dictionary with bounds and center coordinates
        """
        try:
            # Use Django's spatial aggregates if available
            from django.contrib.gis.db.models import Extent, Union

            extent = queryset.aggregate(extent=Extent(geometry_field))['extent']
            if extent:
                minx, miny, maxx, maxy = extent
                center_x = (minx + maxx) / 2
                center_y = (miny + maxy) / 2

                return {
                    'bounds': [minx, miny, maxx, maxy],  # [west, south, east, north]
                    'center': [center_x, center_y],      # [longitude, latitude]
                    'bbox': {
                        'southwest': [minx, miny],
                        'northeast': [maxx, maxy]
                    }
                }
        except Exception as e:
            self.logger.warning(f"Could not calculate spatial bounds: {e}")

        return None

    def success_response(self, data: Any = None, metadata: Dict = None,
                        spatial: Dict = None) -> MCPResponse:
        """Create success response"""
        return MCPResponse(
            status="success",
            data=data,
            metadata=metadata,
            spatial=spatial
        )

    def error_response(self, error: str, data: Any = None) -> MCPResponse:
        """Create error response"""
        return MCPResponse(
            status="error",
            error=error,
            data=data
        )

    def handle_request(self, method: str, params: Dict, token: str = None) -> MCPResponse:
        """
        Main request handler with authentication and error handling

        Args:
            method: MCP method name
            params: Method parameters
            token: Authentication token

        Returns:
            MCPResponse object
        """
        try:
            # Authenticate user if token provided
            user = None
            if token:
                user = self.authenticate(token)

            # Route to appropriate method
            if hasattr(self, f"handle_{method}"):
                handler = getattr(self, f"handle_{method}")
                return handler(params, user)
            else:
                return self.error_response(f"Unknown method: {method}")

        except MCPAuthenticationError as e:
            return self.error_response(f"Authentication failed: {e}")
        except MCPDataError as e:
            return self.error_response(f"Data error: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in {method}: {e}", exc_info=True)
            return self.error_response(f"Internal server error")

    @abstractmethod
    def get_available_methods(self) -> List[str]:
        """Return list of available methods for this server"""
        pass

    @abstractmethod
    def get_method_schema(self, method: str) -> Dict:
        """Return JSON schema for method parameters"""
        pass