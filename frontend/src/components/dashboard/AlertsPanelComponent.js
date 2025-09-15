import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { addAlert } from '../../features/alerts/alertsSlice';

const AlertsPanelComponent = () => {
  const dispatch = useDispatch();
  const alerts = useSelector((state) => state.alerts.notifications);

  // Mock WebSocket connection
  useEffect(() => {
    const interval = setInterval(() => {
      dispatch(addAlert({ id: Date.now(), message: 'New alert: Emergency in El Fasher.' }));
    }, 10000); // Add a new alert every 10 seconds
    return () => clearInterval(interval);
  }, [dispatch]);

  return (
    <div className="alerts-panel-container">
      <h3>Alerts</h3>
      <div className="alerts-list">
        {alerts.map(alert => (
          <div key={alert.id} className="alert-item">
            {alert.message}
          </div>
        ))}
      </div>
    </div>
  );
};

export default AlertsPanelComponent;
