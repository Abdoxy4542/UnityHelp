import React from 'react';
import { Provider } from 'react-redux';
import { store } from './app/store';
import DashboardPage from './pages/DashboardPage';
import './App.css';

function App() {
  return (
    <Provider store={store}>
      <DashboardPage />
    </Provider>
  );
}

export default App;