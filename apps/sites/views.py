from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from .models import State, Locality, Site
from .serializers import (
    StateSerializer, LocalitySerializer, SiteSerializer, SiteDetailSerializer, SiteMapSerializer,
    SiteProfileSerializer, StateGeoSerializer, LocalityGeoSerializer, SiteGeoSerializer
)


class StateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = State.objects.all()
    serializer_class = StateSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'name_ar']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=False, methods=['get'])
    def geojson(self, request):
        """Get states as GeoJSON features"""
        queryset = self.get_queryset().filter(center_point__isnull=False)
        serializer = StateGeoSerializer(queryset, many=True)
        return Response(serializer.data)


class LocalityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Locality.objects.select_related('state')
    serializer_class = LocalitySerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['state']
    search_fields = ['name', 'name_ar', 'state__name']
    ordering_fields = ['name', 'created_at']
    ordering = ['state__name', 'name']


class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.select_related('state', 'locality')
    serializer_class = SiteSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['state', 'locality', 'site_type', 'operational_status']
    search_fields = ['name', 'name_ar', 'description', 'state__name', 'locality__name']
    ordering_fields = ['name', 'population', 'created_at', 'updated_at']
    ordering = ['state__name', 'locality__name', 'name']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SiteDetailSerializer
        elif self.action == 'map_data':
            return SiteMapSerializer
        elif self.action == 'profile':
            return SiteProfileSerializer
        return SiteSerializer
    
    @action(detail=False, methods=['get'])
    def map_data(self, request):
        """
        Get sites data optimized for map display
        Supports filtering by bounds, state, locality, site_type, and geographic proximity
        """
        queryset = self.get_queryset().filter(
            location__isnull=False,
            operational_status='active'
        )
        
        # Filter by bounding box if provided (GIS-enabled)
        bounds = request.query_params.get('bounds')
        if bounds:
            try:
                # Expected format: "west,south,east,north"
                west, south, east, north = map(float, bounds.split(','))
                # Create bounding box polygon for spatial filtering
                from django.contrib.gis.geos import Polygon
                bbox = Polygon.from_bbox((west, south, east, north))
                queryset = queryset.filter(location__within=bbox)
            except (ValueError, TypeError):
                pass
        
        # Apply other filters
        state = request.query_params.get('state')
        if state:
            queryset = queryset.filter(state_id=state)
            
        locality = request.query_params.get('locality')
        if locality:
            queryset = queryset.filter(locality_id=locality)
            
        site_type = request.query_params.get('site_type')
        if site_type:
            queryset = queryset.filter(site_type=site_type)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def geojson(self, request):
        """Get sites as GeoJSON features"""
        queryset = self.get_queryset().filter(location__isnull=False)
        
        # Apply same filters as map_data
        state = request.query_params.get('state')
        if state:
            queryset = queryset.filter(state_id=state)
            
        locality = request.query_params.get('locality')
        if locality:
            queryset = queryset.filter(locality_id=locality)
            
        site_type = request.query_params.get('site_type')
        if site_type:
            queryset = queryset.filter(site_type=site_type)
        
        serializer = SiteGeoSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Find sites near a given point"""
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = request.query_params.get('radius', '10')  # km
        
        if not lat or not lng:
            return Response({'error': 'lat and lng parameters are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            point = Point(float(lng), float(lat), srid=4326)
            radius_km = float(radius)
            
            queryset = self.get_queryset().filter(
                location__isnull=False,
                location__distance_lt=(point, D(km=radius_km))
            ).annotate(
                distance=Distance('location', point)
            ).order_by('distance')
            
            serializer = SiteMapSerializer(queryset, many=True)
            return Response(serializer.data)
            
        except (ValueError, TypeError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get summary statistics for sites"""
        queryset = self.get_queryset()
        
        # Apply same filters as map_data
        state = request.query_params.get('state')
        if state:
            queryset = queryset.filter(state_id=state)
            
        locality = request.query_params.get('locality')
        if locality:
            queryset = queryset.filter(locality_id=locality)
        
        stats = {
            'total_sites': queryset.count(),
            'active_sites': queryset.filter(operational_status='active').count(),
            'total_population': sum(site.population or 0 for site in queryset),
            'total_families': sum(site.families or 0 for site in queryset),
            'total_vulnerable': sum(site.vulnerable_population or 0 for site in queryset),
            'sites_by_type': {},
            'sites_by_status': {}
        }
        
        # Count by type
        for site_type, _ in Site.SITE_TYPES:
            stats['sites_by_type'][site_type] = queryset.filter(site_type=site_type).count()
        
        # Count by status
        for status_type, _ in Site.OPERATIONAL_STATUS:
            stats['sites_by_status'][status_type] = queryset.filter(operational_status=status_type).count()
        
        return Response(stats)
    
    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        """Get comprehensive site profile with all demographic data"""
        site = self.get_object()
        serializer = SiteProfileSerializer(site)
        return Response(serializer.data)
