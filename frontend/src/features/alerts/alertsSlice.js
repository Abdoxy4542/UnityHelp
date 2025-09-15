import { createSlice } from '@reduxjs/toolkit';

const alertsSlice = createSlice({
  name: 'alerts',
  initialState: {
    notifications: [],
  },
  reducers: {
    addAlert: (state, action) => {
      state.notifications.unshift(action.payload); // Add new alert to the top
    },
  },
});

export const { addAlert } = alertsSlice.actions;
export default alertsSlice.reducer;
