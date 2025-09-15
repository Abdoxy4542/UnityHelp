import React, { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import MapComponent from '../components/dashboard/MapComponent';
import SiteProfileComponent from '../components/dashboard/SiteProfileComponent';
import { fetchStates } from '../features/sites/sitesSlice';
import '../assets/styles/SitesMap.css';

const SitesDashboard = () => {
  const dispatch = useDispatch();
  const [isProfileCollapsed, setIsProfileCollapsed] = useState(false);

  useEffect(() => {
    // Load initial data
    dispatch(fetchStates());
  }, [dispatch]);

  const handleSiteSelect = (site) => {
    // This will be handled by the Redux store
    // The site selection is managed in the MapComponent
    console.log('Site selected:', site);
  };

  const handleToggleProfileCollapse = () => {
    setIsProfileCollapsed(!isProfileCollapsed);
  };

  return (
    <div className="sites-dashboard">
      <div className="map-section">
        <MapComponent onSiteSelect={handleSiteSelect} />
      </div>
      <div className="profile-section">
        <SiteProfileComponent 
          isCollapsed={isProfileCollapsed}
          onToggleCollapse={handleToggleProfileCollapse}
        />
      </div>
    </div>
  );
};

export default SitesDashboard;