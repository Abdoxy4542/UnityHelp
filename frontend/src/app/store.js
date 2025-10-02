import { configureStore } from '@reduxjs/toolkit';
import sitesReducer from '../features/sites/sitesSlice';
import alertsReducer from '../features/alerts/alertsSlice';
import filtersReducer from '../features/filters/filtersSlice';
import chatReducer from '../features/chat/chatSlice';

export const store = configureStore({
  reducer: {
    sites: sitesReducer,
    alerts: alertsReducer,
    filters: filtersReducer,
    chat: chatReducer,
  },
});
