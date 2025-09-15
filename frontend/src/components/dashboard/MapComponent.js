import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { fetchSites, selectSite } from '../../features/sites/sitesSlice';

// TO MAKE THE MAP WORK, YOU NEED TO ADD YOUR MAPBOX ACCESS TOKEN
// You can get one for free at https://www.mapbox.com/
mapboxgl.accessToken = 'pk.eyJ1IjoiYXppei14eSIsImEiOiJjbWZiaDd6amIxcW84MmxwZm91Z2llb2t4In0.HDp2hdu7HC8jbCS0blNrpQ';

const SUDAN_BOUNDS = [
  [21.8, 8.6], // Southwest coordinates [lng, lat]
  [39.1, 23.2]  // Northeast coordinates [lng, lat]
];

const ZOOM_LEVELS = {
  COUNTRY: 5,
  STATE: 7,
  LOCALITY: 9,
  SITE: 12
};

const MapComponent = ({ onSiteSelect }) => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const markersRef = useRef({});
  const dispatch = useDispatch();
  
  const { sites, loading, selectedState, selectedLocality } = useSelector(state => state.sites);
  const { activeFilters } = useSelector(state => state.filters);
  
  const [viewState, setViewState] = useState({
    lng: 30.2176, // Centered on Sudan
    lat: 12.8628,
    zoom: ZOOM_LEVELS.COUNTRY
  });

  // Initialize map
  useEffect(() => {
    if (map.current) return;
    
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/satellite-streets-v11',
      center: [viewState.lng, viewState.lat],
      zoom: viewState.zoom,
      maxBounds: SUDAN_BOUNDS,
      minZoom: 4,
      maxZoom: 16
    });

    // Add navigation controls
    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
    
    // Add scale control
    map.current.addControl(new mapboxgl.ScaleControl({
      maxWidth: 80,
      unit: 'metric'
    }), 'bottom-left');

    // Track map movements
    map.current.on('move', () => {
      if (map.current) {
        const center = map.current.getCenter();
        const zoom = map.current.getZoom();
        setViewState({
          lng: parseFloat(center.lng.toFixed(4)),
          lat: parseFloat(center.lat.toFixed(4)),
          zoom: parseFloat(zoom.toFixed(2))
        });
      }
    });

    // Load sites when map loads
    map.current.on('load', () => {
      loadBoundaryLayers();
      dispatch(fetchSites());
    });

    return () => {
      if (map.current) {
        map.current.remove();
      }
    };
  }, [dispatch]);

  // Load boundary layers for states and localities
  const loadBoundaryLayers = useCallback(() => {
    if (!map.current) return;

    // Add state boundaries layer (placeholder - will be replaced with HDX data)
    map.current.addSource('states-source', {
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features: []
      }
    });

    map.current.addLayer({
      id: 'states-fill',
      type: 'fill',
      source: 'states-source',
      paint: {
        'fill-color': 'rgba(200, 200, 200, 0.1)',
        'fill-outline-color': '#666'
      },
      filter: ['>=', ['zoom'], ZOOM_LEVELS.STATE - 1]
    });

    map.current.addLayer({
      id: 'states-line',
      type: 'line',
      source: 'states-source',
      paint: {
        'line-color': '#333',
        'line-width': 2
      },
      filter: ['>=', ['zoom'], ZOOM_LEVELS.COUNTRY]
    });

    // Add locality boundaries layer
    map.current.addSource('localities-source', {
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features: []
      }
    });

    map.current.addLayer({
      id: 'localities-fill',
      type: 'fill',
      source: 'localities-source',
      paint: {
        'fill-color': 'rgba(150, 150, 150, 0.1)',
        'fill-outline-color': '#888'
      },
      filter: ['>=', ['zoom'], ZOOM_LEVELS.LOCALITY - 1]
    });

    map.current.addLayer({
      id: 'localities-line',
      type: 'line',
      source: 'localities-source',
      paint: {
        'line-color': '#666',
        'line-width': 1
      },
      filter: ['>=', ['zoom'], ZOOM_LEVELS.STATE]
    });
  }, []);

  // Update site markers
  useEffect(() => {
    if (!map.current || !sites.length) return;

    // Clear existing markers
    Object.values(markersRef.current).forEach(marker => marker.remove());
    markersRef.current = {};

    // Add new markers for each site
    sites.forEach(site => {
      if (!site.coordinates) return;

      const [lng, lat] = site.coordinates;
      
      // Create marker element
      const markerEl = document.createElement('div');
      markerEl.className = `site-marker site-marker-${site.site_type} status-${site.operational_status}`;
      markerEl.innerHTML = getSiteMarkerIcon(site);
      
      // Create marker
      const marker = new mapboxgl.Marker(markerEl)
        .setLngLat([lng, lat])
        .addTo(map.current);

      // Add click handler
      markerEl.addEventListener('click', () => {
        dispatch(selectSite(site));
        if (onSiteSelect) {
          onSiteSelect(site);
        }
        
        // Zoom to site if not already close
        const currentZoom = map.current.getZoom();
        if (currentZoom < ZOOM_LEVELS.SITE) {
          map.current.flyTo({
            center: [lng, lat],
            zoom: ZOOM_LEVELS.SITE,
            speed: 1.2
          });
        }
      });

      // Store marker reference
      markersRef.current[site.id] = marker;
    });
  }, [sites, dispatch, onSiteSelect]);

  // Get marker icon based on site type and status
  const getSiteMarkerIcon = (site) => {
    const siteTypeIcons = {
      gathering: '🏕️',
      camp: '🏠',
      school: '🏫',
      health: '🏥',
      water: '💧',
      other: '📍'
    };

    const icon = siteTypeIcons[site.site_type] || '📍';
    const isActive = site.operational_status === 'active';
    
    return `
      <div class="marker-icon ${!isActive ? 'inactive' : ''}">
        ${icon}
      </div>
    `;
  };

  // Handle zoom level changes for administrative boundaries
  const handleZoomLevelChange = useCallback((newZoom) => {
    if (!map.current) return;

    if (newZoom >= ZOOM_LEVELS.STATE && !selectedState) {
      // Load state boundaries
      // This will be implemented with HDX API
    } else if (newZoom >= ZOOM_LEVELS.LOCALITY && selectedState && !selectedLocality) {
      // Load locality boundaries for selected state
      // This will be implemented with HDX API
    }
  }, [selectedState, selectedLocality]);

  // Watch for zoom changes
  useEffect(() => {
    handleZoomLevelChange(viewState.zoom);
  }, [viewState.zoom, handleZoomLevelChange]);

  // Fly to specific coordinates (used by filters/selection)
  const flyTo = useCallback((coordinates, zoom = ZOOM_LEVELS.SITE) => {
    if (map.current) {
      map.current.flyTo({
        center: coordinates,
        zoom: zoom,
        speed: 1.2
      });
    }
  }, []);

  // Expose flyTo method to parent components
  useEffect(() => {
    if (window.mapFlyTo) {
      window.mapFlyTo = flyTo;
    }
  }, [flyTo]);

  return (
    <div className="map-wrapper">
      <div ref={mapContainer} className="map-container" />
      
      {/* Zoom level indicator */}
      <div className="map-controls">
        <div className="zoom-indicator">
          Zoom: {viewState.zoom} | 
          {viewState.zoom < ZOOM_LEVELS.STATE && ' Country View'}
          {viewState.zoom >= ZOOM_LEVELS.STATE && viewState.zoom < ZOOM_LEVELS.LOCALITY && ' State View'}
          {viewState.zoom >= ZOOM_LEVELS.LOCALITY && viewState.zoom < ZOOM_LEVELS.SITE && ' Locality View'}
          {viewState.zoom >= ZOOM_LEVELS.SITE && ' Site View'}
        </div>
        
        {/* Loading indicator */}
        {loading && (
          <div className="loading-indicator">
            Loading sites...
          </div>
        )}
        
        {/* Site counter */}
        <div className="site-counter">
          {sites.length} sites shown
        </div>
      </div>
    </div>
  );
};

export default MapComponent;
