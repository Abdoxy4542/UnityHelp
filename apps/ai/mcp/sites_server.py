"""
Sites MCP Server for UnityAid
Provides access to displacement sites, demographics, and administrative data
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional
from django.db.models import Q, Count, Sum, Avg
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance

from apps.sites.models import Site, State, Locality
from .base import BaseMCPServer, MCPResponse, MCPDataError
from .formatters import data_formatter, spatial_formatter, humanitarian_formatter
from .schemas import SITES_SERVER_METHODS

logger = logging.getLogger(__name__)


class SitesMCPServer(BaseMCPServer):
    """MCP Server for UnityAid Sites app data access"""

    def __init__(self):
        super().__init__("sites")

    def get_available_methods(self) -> List[str]:
        """Return list of available methods"""
        return list(SITES_SERVER_METHODS.keys())

    def get_method_schema(self, method: str) -> Dict:
        """Return JSON schema for method parameters"""
        return SITES_SERVER_METHODS.get(method, {})

    def handle_get_all_sites(self, params: Dict, user=None) -> MCPResponse:
        """
        Get all displacement sites with filtering and pagination

        Args:
            params: Request parameters
            user: Authenticated user (optional)

        Returns:
            MCPResponse with sites data
        """
        try:
            # Check permissions
            if user and not self.check_permissions(user, 'read', 'sites'):
                return self.error_response("Insufficient permissions to read sites data")

            # Start with base queryset
            queryset = Site.objects.select_related('state', 'locality').all()

            # Apply user-based filtering if needed
            if user:
                from .authentication import permission_checker
                accessible_sites = permission_checker.get_user_accessible_sites(user)
                if accessible_sites is not None:  # None means all sites accessible
                    queryset = queryset.filter(id__in=accessible_sites)

            # Apply filters
            queryset = self._apply_site_filters(queryset, params)

            # Apply spatial filters if provided
            queryset = self._apply_spatial_filters(queryset, params)

            # Apply date range filters
            queryset = self._apply_date_filters(queryset, params)

            # Apply search
            if params.get('search'):
                search_term = params['search']
                queryset = queryset.filter(
                    Q(name__icontains=search_term) |
                    Q(name_ar__icontains=search_term) |
                    Q(description__icontains=search_term) |
                    Q(locality__name__icontains=search_term) |
                    Q(state__name__icontains=search_term)
                )

            # Pagination
            page = params.get('page', 1)
            per_page = params.get('per_page', 50)
            paginated_data = self.paginate_queryset(queryset, page, per_page)

            # Serialize data
            serialized_sites = []
            for site in paginated_data['results']:
                site_data = self._serialize_site(site, include_demographics=True)
                serialized_sites.append(site_data)

            # Calculate spatial bounds
            spatial_bounds = None
            if queryset.exists():
                spatial_bounds = self._calculate_sites_bounds(queryset)

            return self.success_response(
                data=serialized_sites,
                metadata=paginated_data['metadata'],
                spatial=spatial_bounds
            )

        except Exception as e:
            logger.error(f"Error in get_all_sites: {e}", exc_info=True)
            return self.error_response(f"Failed to fetch sites: {str(e)}")

    def handle_get_site_by_id(self, params: Dict, user=None) -> MCPResponse:
        """
        Get detailed information for a specific site

        Args:
            params: Request parameters with site_id
            user: Authenticated user (optional)

        Returns:
            MCPResponse with site data
        """
        try:
            site_id = params.get('site_id')
            if not site_id:
                return self.error_response("site_id parameter is required")

            # Check permissions
            if user and not self.check_permissions(user, 'read', 'sites'):
                return self.error_response("Insufficient permissions to read site data")

            # Get site
            try:
                site = Site.objects.select_related('state', 'locality').get(id=site_id)
            except Site.DoesNotExist:
                return self.error_response(f"Site with ID {site_id} not found")

            # Check user access to specific site
            if user:
                from .authentication import permission_checker
                accessible_sites = permission_checker.get_user_accessible_sites(user)
                if accessible_sites is not None and site.id not in accessible_sites:
                    return self.error_response("Access denied to this site")

            # Serialize site with full details
            include_demographics = params.get('include_demographics', True)
            site_data = self._serialize_site(
                site,
                include_demographics=include_demographics,
                include_calculated_fields=True
            )

            # Add spatial context if location available
            spatial_data = None
            if site.location:
                spatial_data = {
                    'center': site.coordinates,
                    'bounds': None  # Single point doesn't have bounds
                }

            return self.success_response(
                data=site_data,
                spatial=spatial_data
            )

        except Exception as e:
            logger.error(f"Error in get_site_by_id: {e}", exc_info=True)
            return self.error_response(f"Failed to fetch site: {str(e)}")

    def handle_get_sites_geojson(self, params: Dict, user=None) -> MCPResponse:
        """
        Get sites as GeoJSON FeatureCollection for mapping

        Args:
            params: Request parameters
            user: Authenticated user (optional)

        Returns:
            MCPResponse with GeoJSON data
        """
        try:
            # Check permissions
            if user and not self.check_permissions(user, 'read', 'sites'):
                return self.error_response("Insufficient permissions to read sites data")

            # Get sites with location data
            queryset = Site.objects.select_related('state', 'locality')\
                                .filter(location__isnull=False)\
                                .all()

            # Apply user-based filtering
            if user:
                from .authentication import permission_checker
                accessible_sites = permission_checker.get_user_accessible_sites(user)
                if accessible_sites is not None:
                    queryset = queryset.filter(id__in=accessible_sites)

            # Apply filters
            queryset = self._apply_site_filters(queryset, params)
            queryset = self._apply_spatial_filters(queryset, params)
            queryset = self._apply_date_filters(queryset, params)

            # Create GeoJSON FeatureCollection
            features = []
            for site in queryset:
                if site.coordinates:
                    properties = {
                        'id': site.id,
                        'name': site.name,
                        'name_ar': site.name_ar,
                        'site_type': site.site_type,
                        'operational_status': site.operational_status,
                        'total_population': site.total_population,
                        'total_households': site.total_households,
                        'state': site.state.name if site.state else None,
                        'locality': site.locality.name if site.locality else None,
                        'vulnerability_rate': site.vulnerability_rate,
                        'report_date': site.report_date.isoformat() if site.report_date else None
                    }

                    feature = {
                        'type': 'Feature',
                        'geometry': {
                            'type': 'Point',
                            'coordinates': site.coordinates
                        },
                        'properties': properties
                    }
                    features.append(feature)

            geojson = {
                'type': 'FeatureCollection',
                'features': features
            }

            # Calculate bounds
            spatial_bounds = self._calculate_sites_bounds(queryset) if features else None

            return self.success_response(
                data=geojson,
                metadata={'total_features': len(features)},
                spatial=spatial_bounds
            )

        except Exception as e:
            logger.error(f"Error in get_sites_geojson: {e}", exc_info=True)
            return self.error_response(f"Failed to generate GeoJSON: {str(e)}")

    def handle_get_sites_summary(self, params: Dict, user=None) -> MCPResponse:
        """
        Get summary statistics for sites

        Args:
            params: Request parameters
            user: Authenticated user (optional)

        Returns:
            MCPResponse with summary data
        """
        try:
            # Check permissions
            if user and not self.check_permissions(user, 'read', 'sites'):
                return self.error_response("Insufficient permissions to read sites data")

            # Base queryset
            queryset = Site.objects.all()

            # Apply user-based filtering
            if user:
                from .authentication import permission_checker
                accessible_sites = permission_checker.get_user_accessible_sites(user)
                if accessible_sites is not None:
                    queryset = queryset.filter(id__in=accessible_sites)

            # Apply filters
            queryset = self._apply_site_filters(queryset, params)

            # Calculate summary statistics
            summary_stats = queryset.aggregate(
                total_sites=Count('id'),
                total_population=Sum('total_population'),
                total_households=Sum('total_households'),
                avg_population_per_site=Avg('total_population'),
                total_children=Sum('children_under_18'),
                total_adults=Sum('adults_18_59'),
                total_elderly=Sum('elderly_60_plus'),
                total_disabled=Sum('disabled_count'),
                total_pregnant=Sum('pregnant_women'),
                total_chronically_ill=Sum('chronically_ill')
            )

            # Count by status and type
            status_breakdown = dict(queryset.values('operational_status').annotate(count=Count('id')).values_list('operational_status', 'count'))
            type_breakdown = dict(queryset.values('site_type').annotate(count=Count('id')).values_list('site_type', 'count'))

            # Geographic distribution
            state_breakdown = dict(queryset.values('state__name').annotate(count=Count('id')).values_list('state__name', 'count'))

            # Calculate percentages and ratios
            total_pop = summary_stats['total_population'] or 0
            vulnerable_total = (summary_stats['total_disabled'] or 0) + \
                             (summary_stats['total_pregnant'] or 0) + \
                             (summary_stats['total_chronically_ill'] or 0)

            summary_data = {
                'overview': summary_stats,
                'demographics': {
                    'children_percentage': (summary_stats['total_children'] / total_pop * 100) if total_pop else 0,
                    'adults_percentage': (summary_stats['total_adults'] / total_pop * 100) if total_pop else 0,
                    'elderly_percentage': (summary_stats['total_elderly'] / total_pop * 100) if total_pop else 0,
                    'vulnerability_rate': (vulnerable_total / total_pop * 100) if total_pop else 0
                },
                'breakdowns': {
                    'by_status': status_breakdown,
                    'by_type': type_breakdown,
                    'by_state': state_breakdown
                },
                'averages': {
                    'avg_population_per_site': round(summary_stats['avg_population_per_site'] or 0, 2),
                    'avg_households_per_site': round(summary_stats['total_households'] / summary_stats['total_sites']) if summary_stats['total_sites'] else 0
                }
            }

            return self.success_response(data=summary_data)

        except Exception as e:
            logger.error(f"Error in get_sites_summary: {e}", exc_info=True)
            return self.error_response(f"Failed to generate summary: {str(e)}")

    def _apply_site_filters(self, queryset, params: Dict):
        """Apply site-specific filters to queryset"""

        # Filter by operational status
        if params.get('status'):
            queryset = queryset.filter(operational_status=params['status'])

        # Filter by site type
        if params.get('site_type'):
            queryset = queryset.filter(site_type=params['site_type'])

        # Filter by state
        if params.get('state_id'):
            queryset = queryset.filter(state_id=params['state_id'])

        # Filter by locality
        if params.get('locality_id'):
            queryset = queryset.filter(locality_id=params['locality_id'])

        # Filter by population range
        if params.get('min_population'):
            queryset = queryset.filter(total_population__gte=params['min_population'])
        if params.get('max_population'):
            queryset = queryset.filter(total_population__lte=params['max_population'])

        return queryset

    def _apply_spatial_filters(self, queryset, params: Dict):
        """Apply spatial filters to queryset"""

        # Filter by bounding box
        if params.get('bounds'):
            try:
                minx, miny, maxx, maxy = params['bounds']
                # Create polygon from bounds
                bbox = Polygon.from_bbox((minx, miny, maxx, maxy))
                # Filter sites within bounds (using JSON field for now)
                # This is a simplified approach - in production, use proper PostGIS
                bbox_sites = []
                for site in queryset:
                    if site.coordinates:
                        lng, lat = site.coordinates
                        if minx <= lng <= maxx and miny <= lat <= maxy:
                            bbox_sites.append(site.id)
                queryset = queryset.filter(id__in=bbox_sites)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid bounds parameter: {e}")

        # Filter by distance from center point
        if params.get('center') and params.get('radius'):
            try:
                lng, lat = params['center']
                radius_km = params['radius']
                # Similar simplified approach for radius filtering
                center_sites = []
                for site in queryset:
                    if site.coordinates:
                        site_lng, site_lat = site.coordinates
                        # Rough distance calculation (would use PostGIS in production)
                        distance = ((lng - site_lng) ** 2 + (lat - site_lat) ** 2) ** 0.5
                        # Convert to rough kilometers (1 degree ≈ 111 km)
                        distance_km = distance * 111
                        if distance_km <= radius_km:
                            center_sites.append(site.id)
                queryset = queryset.filter(id__in=center_sites)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid center/radius parameters: {e}")

        return queryset

    def _apply_date_filters(self, queryset, params: Dict):
        """Apply date range filters to queryset"""

        if params.get('from_date'):
            try:
                from_date = datetime.strptime(params['from_date'], '%Y-%m-%d').date()
                queryset = queryset.filter(report_date__gte=from_date)
            except ValueError:
                logger.warning("Invalid from_date format")

        if params.get('to_date'):
            try:
                to_date = datetime.strptime(params['to_date'], '%Y-%m-%d').date()
                queryset = queryset.filter(report_date__lte=to_date)
            except ValueError:
                logger.warning("Invalid to_date format")

        return queryset

    def _serialize_site(self, site: Site, include_demographics: bool = True,
                       include_calculated_fields: bool = False) -> Dict:
        """
        Serialize Site model to dictionary

        Args:
            site: Site model instance
            include_demographics: Include demographic data
            include_calculated_fields: Include calculated fields

        Returns:
            Serialized site data
        """
        data = {
            'id': site.id,
            'name': site.name,
            'name_ar': site.name_ar,
            'description': site.description,
            'site_type': site.site_type,
            'site_type_display': site.get_site_type_display(),
            'operational_status': site.operational_status,
            'operational_status_display': site.get_operational_status_display(),
            'location': site.location,
            'coordinates': site.coordinates,
            'longitude': site.longitude,
            'latitude': site.latitude,
            'size_of_location': site.size_of_location,
            'contact_person': site.contact_person,
            'contact_phone': site.contact_phone,
            'contact_email': site.contact_email,
            'report_date': site.report_date.isoformat() if site.report_date else None,
            'reported_by': site.reported_by,
            'created_at': site.created_at.isoformat(),
            'updated_at': site.updated_at.isoformat()
        }

        # Administrative hierarchy
        if site.state:
            data['state'] = {
                'id': site.state.id,
                'name': site.state.name,
                'name_ar': site.state.name_ar
            }

        if site.locality:
            data['locality'] = {
                'id': site.locality.id,
                'name': site.locality.name,
                'name_ar': site.locality.name_ar
            }

        # Demographics
        if include_demographics:
            data['demographics'] = {
                'total_population': site.total_population,
                'total_households': site.total_households,
                'age_breakdown': {
                    'children_under_18': site.children_under_18,
                    'adults_18_59': site.adults_18_59,
                    'elderly_60_plus': site.elderly_60_plus
                },
                'gender_breakdown': {
                    'male_count': site.male_count,
                    'female_count': site.female_count
                },
                'vulnerability': {
                    'disabled_count': site.disabled_count,
                    'pregnant_women': site.pregnant_women,
                    'chronically_ill': site.chronically_ill
                }
            }

        # Calculated fields
        if include_calculated_fields:
            data['calculated_fields'] = {
                'population_by_age_verified': site.population_by_age_verified,
                'population_by_gender_verified': site.population_by_gender_verified,
                'average_household_size': site.average_household_size,
                'vulnerability_rate': site.vulnerability_rate,
                'child_dependency_ratio': site.child_dependency_ratio
            }

        return data

    def _calculate_sites_bounds(self, queryset) -> Optional[Dict]:
        """Calculate spatial bounds for sites queryset"""
        sites_with_coords = []

        for site in queryset:
            if site.coordinates:
                lng, lat = site.coordinates
                sites_with_coords.append((lng, lat))

        if not sites_with_coords:
            return None

        lngs = [coord[0] for coord in sites_with_coords]
        lats = [coord[1] for coord in sites_with_coords]

        minx, maxx = min(lngs), max(lngs)
        miny, maxy = min(lats), max(lats)

        center_x = (minx + maxx) / 2
        center_y = (miny + maxy) / 2

        return {
            'bounds': [minx, miny, maxx, maxy],
            'center': [center_x, center_y],
            'bbox': {
                'southwest': {'lng': minx, 'lat': miny},
                'northeast': {'lng': maxx, 'lat': maxy}
            }
        }


# Create server instance
sites_server = SitesMCPServer()