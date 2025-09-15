import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { setStateFilter, setLocalityFilter, setSectorFilter } from '../../features/filters/filtersSlice';

const FiltersComponent = () => {
  const dispatch = useDispatch();
  const { selectedState, selectedLocality, selectedSector } = useSelector((state) => state.filters);

  // Mock data - replace with data from your API
  const states = ['Kassala', 'Khartoum', 'North Darfur'];
  const localities = {
    Kassala: ['Kassala Town', 'Rural Kassala'],
    Khartoum: ['Khartoum Bahri', 'Omdurman'],
    'North Darfur': ['El Fasher', 'Kutum'],
  };
  const sectors = ['All', 'Food', 'Wash', 'Health', 'Education', 'INF', 'Protection'];

  const handleStateChange = (e) => {
    dispatch(setStateFilter(e.target.value));
  };

  const handleLocalityChange = (e) => {
    dispatch(setLocalityFilter(e.target.value));
  };

  const handleSectorChange = (e) => {
    dispatch(setSectorFilter(e.target.value));
  };

  return (
    <div className="filters-container">
      <h3>Filters</h3>
      <div className="filter-group">
        <label>State</label>
        <select onChange={handleStateChange} value={selectedState || ''}>
          <option value="">Select State</option>
          {states.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
      <div className="filter-group">
        <label>Locality</label>
        <select onChange={handleLocalityChange} value={selectedLocality || ''} disabled={!selectedState}>
          <option value="">Select Locality</option>
          {selectedState && localities[selectedState] && localities[selectedState].map(l => <option key={l} value={l}>{l}</option>)}
        </select>
      </div>
      <div className="filter-group">
        <label>Sector</label>
        <select onChange={handleSectorChange} value={selectedSector}>
          {sectors.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
    </div>
  );
};

export default FiltersComponent;
