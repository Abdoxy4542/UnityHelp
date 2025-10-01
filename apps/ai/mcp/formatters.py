"""
Data formatting utilities for MCP servers
Handles serialization, spatial data, and standardized response formats
"""

import json
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Any, Optional, Union

from django.contrib.gis.geos import GEOSGeometry, Point, Polygon
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Model, QuerySet
from geojson import Feature, FeatureCollection, Point as GeoJSONPoint, Polygon as GeoJSONPolygon

logger = logging.getLogger(__name__)


class UnityAidDataFormatter:
    """Data formatting utilities for UnityAid MCP servers"""

    def __init__(self):
        pass

    def serialize_datetime(self, dt: Union[datetime, date]) -> str:
        """
        Serialize datetime to ISO format string

        Args:
            dt: datetime or date object

        Returns:
            ISO format string
        """
        if dt is None:
            return None
        return dt.isoformat()

    def serialize_decimal(self, decimal_value: Decimal) -> float:
        """
        Serialize Decimal to float

        Args:
            decimal_value: Decimal object

        Returns:
            Float value
        """
        if decimal_value is None:
            return None
        return float(decimal_value)

    def serialize_geometry(self, geometry: GEOSGeometry) -> Dict:
        """
        Serialize PostGIS geometry to GeoJSON

        Args:
            geometry: PostGIS geometry object

        Returns:
            GeoJSON dictionary
        """
        if geometry is None:
            return None
        return json.loads(geometry.geojson)

    def serialize_model_basic(self, instance: Model,
                             include_fields: List[str] = None,
                             exclude_fields: List[str] = None) -> Dict:
        """
        Basic model serialization with field filtering

        Args:
            instance: Django model instance
            include_fields: Fields to include (None for all)
            exclude_fields: Fields to exclude

        Returns:
            Serialized model dictionary
        """
        if not instance:
            return None

        exclude_fields = exclude_fields or []
        data = {'id': instance.pk}

        for field in instance._meta.fields:
            field_name = field.name

            # Skip excluded fields
            if field_name in exclude_fields:
                continue

            # Include only specified fields if provided
            if include_fields and field_name not in include_fields:
                continue

            try:
                value = getattr(instance, field_name)

                # Handle different field types
                if hasattr(field, 'geom_type'):  # PostGIS field
                    data[field_name] = self.serialize_geometry(value)
                elif isinstance(value, (datetime, date)):
                    data[field_name] = self.serialize_datetime(value)
                elif isinstance(value, Decimal):
                    data[field_name] = self.serialize_decimal(value)
                elif hasattr(value, 'pk'):  # Related model
                    data[field_name] = {
                        'id': value.pk,
                        'display_name': str(value)
                    }
                else:
                    data[field_name] = value

            except Exception as e:
                logger.warning(f"Could not serialize field {field_name}: {e}")
                data[field_name] = None

        return data

    def serialize_queryset_basic(self, queryset: QuerySet,
                                include_fields: List[str] = None,
                                exclude_fields: List[str] = None) -> List[Dict]:
        """
        Serialize QuerySet to list of dictionaries

        Args:
            queryset: Django QuerySet
            include_fields: Fields to include
            exclude_fields: Fields to exclude

        Returns:
            List of serialized model dictionaries
        """
        return [
            self.serialize_model_basic(instance, include_fields, exclude_fields)
            for instance in queryset
        ]


class SpatialDataFormatter:
    """Handles spatial data formatting for MCP servers"""

    def __init__(self):
        pass

    def create_geojson_feature(self, instance: Model,
                              geometry_field: str = 'location',
                              properties_fields: List[str] = None) -> Dict:
        """
        Create GeoJSON Feature from model instance

        Args:
            instance: Django model instance with spatial data
            geometry_field: Name of geometry field
            properties_fields: Fields to include as properties

        Returns:
            GeoJSON Feature dictionary
        """
        geometry = getattr(instance, geometry_field, None)
        if not geometry:
            return None

        # Prepare properties
        properties = {'id': instance.pk}

        if properties_fields:
            formatter = UnityAidDataFormatter()
            for field_name in properties_fields:
                if hasattr(instance, field_name):
                    value = getattr(instance, field_name)
                    if isinstance(value, (datetime, date)):
                        properties[field_name] = formatter.serialize_datetime(value)
                    elif isinstance(value, Decimal):
                        properties[field_name] = formatter.serialize_decimal(value)
                    elif hasattr(value, 'pk'):  # Related model
                        properties[field_name] = {
                            'id': value.pk,
                            'name': str(value)
                        }
                    else:
                        properties[field_name] = value

        return Feature(
            geometry=json.loads(geometry.geojson),
            properties=properties
        )

    def create_geojson_feature_collection(self, queryset: QuerySet,
                                        geometry_field: str = 'location',
                                        properties_fields: List[str] = None) -> Dict:
        """
        Create GeoJSON FeatureCollection from QuerySet

        Args:
            queryset: Django QuerySet with spatial data
            geometry_field: Name of geometry field
            properties_fields: Fields to include as properties

        Returns:
            GeoJSON FeatureCollection dictionary
        """
        features = []

        for instance in queryset:
            feature = self.create_geojson_feature(
                instance, geometry_field, properties_fields
            )
            if feature:
                features.append(feature)

        return FeatureCollection(features)

    def calculate_bounds(self, queryset: QuerySet,
                        geometry_field: str = 'location') -> Optional[Dict]:
        """
        Calculate spatial bounds for QuerySet

        Args:
            queryset: Django QuerySet with spatial data
            geometry_field: Name of geometry field

        Returns:
            Dictionary with bounds and center, or None if no spatial data
        """
        try:
            from django.contrib.gis.db.models import Extent

            extent = queryset.aggregate(extent=Extent(geometry_field))['extent']
            if extent:
                minx, miny, maxx, maxy = extent
                center_x = (minx + maxx) / 2
                center_y = (miny + maxy) / 2

                return {
                    'bounds': [minx, miny, maxx, maxy],  # [west, south, east, north]
                    'center': [center_x, center_y],      # [longitude, latitude]
                    'bbox': {
                        'southwest': {'lng': minx, 'lat': miny},
                        'northeast': {'lng': maxx, 'lat': maxy}
                    }
                }
        except Exception as e:
            logger.warning(f"Could not calculate spatial bounds: {e}")

        return None

    def point_from_coordinates(self, lng: float, lat: float) -> Point:
        """
        Create Point geometry from longitude/latitude

        Args:
            lng: Longitude
            lat: Latitude

        Returns:
            PostGIS Point geometry
        """
        return Point(lng, lat, srid=4326)

    def polygon_from_bounds(self, minx: float, miny: float,
                          maxx: float, maxy: float) -> Polygon:
        """
        Create Polygon geometry from bounds

        Args:
            minx: Minimum longitude (west)
            miny: Minimum latitude (south)
            maxx: Maximum longitude (east)
            maxy: Maximum latitude (north)

        Returns:
            PostGIS Polygon geometry
        """
        coords = [
            (minx, miny),  # Southwest
            (minx, maxy),  # Northwest
            (maxx, maxy),  # Northeast
            (maxx, miny),  # Southeast
            (minx, miny)   # Close the polygon
        ]
        return Polygon(coords, srid=4326)


class HumanitarianDataFormatter:
    """Specialized formatting for humanitarian data types"""

    SECTOR_MAPPING = {
        'wash': 'Water, Sanitation & Hygiene',
        'health': 'Health',
        'food_security': 'Food Security',
        'nutrition': 'Nutrition',
        'protection': 'Protection',
        'education': 'Education',
        'shelter': 'Shelter & Non-Food Items',
        'cccm': 'Camp Coordination & Camp Management',
        'early_recovery': 'Early Recovery',
        'logistics': 'Logistics',
        'emergency_telecommunications': 'Emergency Telecommunications'
    }

    CRISIS_SEVERITY_LEVELS = {
        1: 'Minimal',
        2: 'Stressed',
        3: 'Crisis',
        4: 'Emergency',
        5: 'Catastrophe/Famine'
    }

    def format_sector_name(self, sector_code: str) -> str:
        """
        Format sector code to full name

        Args:
            sector_code: Sector abbreviation

        Returns:
            Full sector name
        """
        return self.SECTOR_MAPPING.get(sector_code.lower(), sector_code.title())

    def format_crisis_severity(self, level: int) -> Dict:
        """
        Format crisis severity level

        Args:
            level: Severity level (1-5)

        Returns:
            Dictionary with level and description
        """
        return {
            'level': level,
            'description': self.CRISIS_SEVERITY_LEVELS.get(level, 'Unknown'),
            'is_critical': level >= 4
        }

    def format_population_data(self, data: Dict) -> Dict:
        """
        Format population/demographic data

        Args:
            data: Raw population data

        Returns:
            Formatted population data
        """
        formatted = data.copy()

        # Add calculated fields
        total_population = data.get('total_population', 0)
        if total_population > 0:
            formatted['demographics_breakdown'] = {
                'children_percentage': (data.get('children', 0) / total_population) * 100,
                'women_percentage': (data.get('women', 0) / total_population) * 100,
                'elderly_percentage': (data.get('elderly', 0) / total_population) * 100,
                'men_percentage': (data.get('men', 0) / total_population) * 100
            }

        return formatted

    def format_displacement_data(self, data: Dict) -> Dict:
        """
        Format displacement data

        Args:
            data: Raw displacement data

        Returns:
            Formatted displacement data
        """
        formatted = data.copy()

        # Add calculated fields
        idp_individuals = data.get('idp_individuals', 0)
        returnee_individuals = data.get('returnee_individuals', 0)

        formatted['displacement_summary'] = {
            'total_displaced': idp_individuals,
            'total_returnees': returnee_individuals,
            'net_displacement': idp_individuals - returnee_individuals,
            'displacement_ratio': (idp_individuals / (idp_individuals + returnee_individuals)) if (idp_individuals + returnee_individuals) > 0 else 0
        }

        return formatted

    def format_funding_data(self, data: Dict) -> Dict:
        """
        Format funding data

        Args:
            data: Raw funding data

        Returns:
            Formatted funding data
        """
        formatted = data.copy()

        requirements = data.get('requirements', 0)
        funding_received = data.get('funding_received', 0)

        if requirements > 0:
            formatted['funding_analysis'] = {
                'coverage_percentage': (funding_received / requirements) * 100,
                'funding_gap': requirements - funding_received,
                'is_underfunded': funding_received < requirements,
                'funding_ratio': funding_received / requirements
            }

        return formatted


# Global formatter instances
data_formatter = UnityAidDataFormatter()
spatial_formatter = SpatialDataFormatter()
humanitarian_formatter = HumanitarianDataFormatter()