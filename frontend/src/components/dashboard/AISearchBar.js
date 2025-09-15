import React, { useState } from 'react';

const AISearchBar = () => {
  const [query, setQuery] = useState('');

  const handleSearch = (e) => {
    e.preventDefault();
    // Handle AI search logic here
    console.log('Searching for:', query);
  };

  return (
    <div className="ai-search-container">
      <form onSubmit={handleSearch}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask anything... (e.g., 'What is the Wash situation in Kassala?')"
        />
        <button type="submit">Search</button>
      </form>
    </div>
  );
};

export default AISearchBar;
