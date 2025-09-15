import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../services/api';

// Async thunks for API calls
export const fetchStates = createAsyncThunk('sites/fetchStates', async () => {
  const response = await api.get('/sites/states/');
  return response.data.results || response.data;
});

export const fetchLocalities = createAsyncThunk('sites/fetchLocalities', async (stateId) => {
  const params = stateId ? { state: stateId } : {};
  const response = await api.get('/sites/localities/', { params });
  return response.data.results || response.data;
});

export const fetchSites = createAsyncThunk('sites/fetchSites', async (filters = {}) => {
  const response = await api.get('/sites/sites/map_data/', { params: filters });
  return response.data;
});

export const fetchSiteDetails = createAsyncThunk('sites/fetchSiteDetails', async (siteId) => {
  const response = await api.get(`/sites/sites/${siteId}/`);
  return response.data;
});

export const fetchSiteStatistics = createAsyncThunk('sites/fetchSiteStatistics', async (filters = {}) => {
  const response = await api.get('/sites/sites/statistics/', { params: filters });
  return response.data;
});

const sitesSlice = createSlice({
  name: 'sites',
  initialState: {
    // Geographic data
    states: [],
    localities: [],
    sites: [],
    
    // Selected items
    selectedState: null,
    selectedLocality: null,
    selectedSite: null,
    
    // Loading states
    loading: false,
    statesLoading: false,
    localitiesLoading: false,
    siteDetailsLoading: false,
    
    // Statistics
    statistics: null,
    statisticsLoading: false,
    
    // Errors
    error: null,
    statesError: null,
    localitiesError: null,
    siteDetailsError: null,
    
    // Map state
    mapBounds: null,
    currentZoom: 5,
  },
  reducers: {
    selectState: (state, action) => {
      state.selectedState = action.payload;
      state.selectedLocality = null;
      state.selectedSite = null;
      state.localities = [];
    },
    selectLocality: (state, action) => {
      state.selectedLocality = action.payload;
      state.selectedSite = null;
    },
    selectSite: (state, action) => {
      state.selectedSite = action.payload;
    },
    clearSelection: (state) => {
      state.selectedState = null;
      state.selectedLocality = null;
      state.selectedSite = null;
    },
    updateMapBounds: (state, action) => {
      state.mapBounds = action.payload;
    },
    updateMapZoom: (state, action) => {
      state.currentZoom = action.payload;
    },
    clearError: (state) => {
      state.error = null;
      state.statesError = null;
      state.localitiesError = null;
      state.siteDetailsError = null;
    }
  },
  extraReducers: (builder) => {
    builder
      // States
      .addCase(fetchStates.pending, (state) => {
        state.statesLoading = true;
        state.statesError = null;
      })
      .addCase(fetchStates.fulfilled, (state, action) => {
        state.statesLoading = false;
        state.states = action.payload;
      })
      .addCase(fetchStates.rejected, (state, action) => {
        state.statesLoading = false;
        state.statesError = action.error.message;
      })
      
      // Localities
      .addCase(fetchLocalities.pending, (state) => {
        state.localitiesLoading = true;
        state.localitiesError = null;
      })
      .addCase(fetchLocalities.fulfilled, (state, action) => {
        state.localitiesLoading = false;
        state.localities = action.payload;
      })
      .addCase(fetchLocalities.rejected, (state, action) => {
        state.localitiesLoading = false;
        state.localitiesError = action.error.message;
      })
      
      // Sites
      .addCase(fetchSites.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSites.fulfilled, (state, action) => {
        state.loading = false;
        state.sites = action.payload;
      })
      .addCase(fetchSites.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      
      // Site details
      .addCase(fetchSiteDetails.pending, (state) => {
        state.siteDetailsLoading = true;
        state.siteDetailsError = null;
      })
      .addCase(fetchSiteDetails.fulfilled, (state, action) => {
        state.siteDetailsLoading = false;
        // Update the selected site with detailed information
        if (state.selectedSite && state.selectedSite.id === action.payload.id) {
          state.selectedSite = action.payload;
        }
      })
      .addCase(fetchSiteDetails.rejected, (state, action) => {
        state.siteDetailsLoading = false;
        state.siteDetailsError = action.error.message;
      })
      
      // Statistics
      .addCase(fetchSiteStatistics.pending, (state) => {
        state.statisticsLoading = true;
      })
      .addCase(fetchSiteStatistics.fulfilled, (state, action) => {
        state.statisticsLoading = false;
        state.statistics = action.payload;
      })
      .addCase(fetchSiteStatistics.rejected, (state, action) => {
        state.statisticsLoading = false;
      });
  },
});

export const {
  selectState,
  selectLocality,
  selectSite,
  clearSelection,
  updateMapBounds,
  updateMapZoom,
  clearError
} = sitesSlice.actions;

export default sitesSlice.reducer;
