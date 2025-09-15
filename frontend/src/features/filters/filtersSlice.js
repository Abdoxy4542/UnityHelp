import { createSlice } from '@reduxjs/toolkit';

const filtersSlice = createSlice({
  name: 'filters',
  initialState: {
    selectedState: null,
    selectedLocality: null,
    selectedSector: 'All',
  },
  reducers: {
    setStateFilter: (state, action) => {
      state.selectedState = action.payload;
      state.selectedLocality = null; // Reset locality when state changes
    },
    setLocalityFilter: (state, action) => {
      state.selectedLocality = action.payload;
    },
    setSectorFilter: (state, action) => {
      state.selectedSector = action.payload;
    },
  },
});

export const { setStateFilter, setLocalityFilter, setSectorFilter } = filtersSlice.actions;
export default filtersSlice.reducer;
