import React from 'react';
import Header from '../components/layout/Header';
import MapComponent from '../components/dashboard/MapComponent';
import FiltersComponent from '../components/dashboard/FiltersComponent';
import SiteProfileComponent from '../components/dashboard/SiteProfileComponent';
import AlertsPanelComponent from '../components/dashboard/AlertsPanelComponent';
import AISearchBar from '../components/dashboard/AISearchBar';
import '../assets/styles/Dashboard.css';

const DashboardPage = () => {
  return (
    <div className="dashboard-container">
      <Header />
      <div className="main-content">
        <div className="left-panel">
          <AlertsPanelComponent />
        </div>
        <div className="center-panel">
          <AISearchBar />
          <MapComponent />
        </div>
        <div className="right-panel">
          <FiltersComponent />
          <SiteProfileComponent />
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
