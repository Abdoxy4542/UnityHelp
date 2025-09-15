import React, { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { fetchSiteDetails, clearSelection } from '../../features/sites/sitesSlice';

const SiteProfileComponent = ({ isCollapsed, onToggleCollapse }) => {
  const dispatch = useDispatch();
  const { selectedSite, siteDetailsLoading, siteDetailsError } = useSelector(state => state.sites);
  const [activeTab, setActiveTab] = useState('overview');

  // Fetch detailed site information when a site is selected
  useEffect(() => {
    if (selectedSite && selectedSite.id) {
      dispatch(fetchSiteDetails(selectedSite.id));
    }
  }, [selectedSite, dispatch]);

  if (!selectedSite) {
    return (
      <div className={`site-profile-container ${isCollapsed ? 'collapsed' : ''}`}>
        <div className="profile-header">
          <h3>Site Profile</h3>
          <button 
            className="collapse-btn"
            onClick={onToggleCollapse}
          >
            {isCollapsed ? '◀' : '▶'}
          </button>
        </div>
        {!isCollapsed && (
          <div className="profile-content">
            <div className="empty-state">
              <div className="empty-icon">🏛️</div>
              <p>Click on a site marker on the map to view detailed information.</p>
            </div>
          </div>
        )}
      </div>
    );
  }

  const getSiteTypeLabel = (type) => {
    const labels = {
      gathering: 'Gathering Site',
      camp: 'IDP Camp',
      school: 'School',
      health: 'Health Facility',
      water: 'Water Point',
      other: 'Other'
    };
    return labels[type] || type;
  };

  const getStatusColor = (status) => {
    const colors = {
      active: '#10B981',
      inactive: '#EF4444',
      planned: '#F59E0B',
      closed: '#6B7280'
    };
    return colors[status] || '#6B7280';
  };

  const formatNumber = (num) => {
    if (!num) return 'N/A';
    return num.toLocaleString();
  };

  const renderOverviewTab = () => (
    <div className="tab-content">
      <div className="info-section">
        <h4>Basic Information</h4>
        <div className="info-grid">
          <div className="info-item">
            <label>Site Type</label>
            <span className="site-type-badge">
              {getSiteTypeLabel(selectedSite.site_type)}
            </span>
          </div>
          <div className="info-item">
            <label>Status</label>
            <span 
              className="status-badge"
              style={{ backgroundColor: getStatusColor(selectedSite.operational_status) }}
            >
              {selectedSite.operational_status}
            </span>
          </div>
          <div className="info-item">
            <label>State</label>
            <span>{selectedSite.state_name}</span>
          </div>
          <div className="info-item">
            <label>Locality</label>
            <span>{selectedSite.locality_name}</span>
          </div>
        </div>
      </div>

      {selectedSite.coordinates && (
        <div className="info-section">
          <h4>Location</h4>
          <div className="coordinates">
            <span>Lat: {selectedSite.coordinates[1]?.toFixed(6)}</span>
            <span>Lng: {selectedSite.coordinates[0]?.toFixed(6)}</span>
          </div>
        </div>
      )}

      {selectedSite.description && (
        <div className="info-section">
          <h4>Description</h4>
          <p className="description">{selectedSite.description}</p>
        </div>
      )}
    </div>
  );

  const renderDemographicsTab = () => (
    <div className="tab-content">
      <div className="demographics-section">
        <h4>Population Statistics</h4>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">👥</div>
            <div className="stat-content">
              <div className="stat-number">{formatNumber(selectedSite.population)}</div>
              <div className="stat-label">Total Population</div>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon">🏠</div>
            <div className="stat-content">
              <div className="stat-number">{formatNumber(selectedSite.families)}</div>
              <div className="stat-label">Families</div>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon">⚠️</div>
            <div className="stat-content">
              <div className="stat-number">{formatNumber(selectedSite.vulnerable_population)}</div>
              <div className="stat-label">Vulnerable</div>
            </div>
          </div>
        </div>

        {selectedSite.population && selectedSite.families && (
          <div className="derived-stats">
            <div className="derived-stat">
              <label>Average Family Size</label>
              <span>{(selectedSite.population / selectedSite.families).toFixed(1)} people</span>
            </div>
            {selectedSite.vulnerable_population && (
              <div className="derived-stat">
                <label>Vulnerable Population Rate</label>
                <span>{((selectedSite.vulnerable_population / selectedSite.population) * 100).toFixed(1)}%</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );

  const renderContactTab = () => (
    <div className="tab-content">
      <div className="info-section">
        <h4>Contact Information</h4>
        {selectedSite.contact_person || selectedSite.contact_phone || selectedSite.contact_email ? (
          <div className="contact-grid">
            {selectedSite.contact_person && (
              <div className="contact-item">
                <label>Contact Person</label>
                <span>{selectedSite.contact_person}</span>
              </div>
            )}
            {selectedSite.contact_phone && (
              <div className="contact-item">
                <label>Phone</label>
                <a href={`tel:${selectedSite.contact_phone}`}>{selectedSite.contact_phone}</a>
              </div>
            )}
            {selectedSite.contact_email && (
              <div className="contact-item">
                <label>Email</label>
                <a href={`mailto:${selectedSite.contact_email}`}>{selectedSite.contact_email}</a>
              </div>
            )}
          </div>
        ) : (
          <p className="no-data">No contact information available</p>
        )}
      </div>

      <div className="info-section">
        <h4>Last Updated</h4>
        <p>{new Date(selectedSite.updated_at).toLocaleDateString()} at {new Date(selectedSite.updated_at).toLocaleTimeString()}</p>
      </div>
    </div>
  );

  return (
    <div className={`site-profile-container ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="profile-header">
        <div className="site-title">
          <h3>{selectedSite.name}</h3>
          {selectedSite.name_ar && (
            <p className="site-name-ar">{selectedSite.name_ar}</p>
          )}
        </div>
        <div className="header-actions">
          <button 
            className="close-btn"
            onClick={() => dispatch(clearSelection())}
            title="Close profile"
          >
            ✕
          </button>
          <button 
            className="collapse-btn"
            onClick={onToggleCollapse}
            title={isCollapsed ? 'Expand' : 'Collapse'}
          >
            {isCollapsed ? '◀' : '▶'}
          </button>
        </div>
      </div>

      {!isCollapsed && (
        <div className="profile-content">
          {siteDetailsLoading && (
            <div className="loading-indicator">
              <div className="loading-spinner"></div>
              <span>Loading site details...</span>
            </div>
          )}

          {siteDetailsError && (
            <div className="error-message">
              Failed to load site details: {siteDetailsError}
            </div>
          )}

          {!siteDetailsLoading && !siteDetailsError && (
            <>
              <div className="tabs">
                <button 
                  className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
                  onClick={() => setActiveTab('overview')}
                >
                  Overview
                </button>
                <button 
                  className={`tab ${activeTab === 'demographics' ? 'active' : ''}`}
                  onClick={() => setActiveTab('demographics')}
                >
                  Demographics
                </button>
                <button 
                  className={`tab ${activeTab === 'contact' ? 'active' : ''}`}
                  onClick={() => setActiveTab('contact')}
                >
                  Contact
                </button>
              </div>

              {activeTab === 'overview' && renderOverviewTab()}
              {activeTab === 'demographics' && renderDemographicsTab()}
              {activeTab === 'contact' && renderContactTab()}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default SiteProfileComponent;
