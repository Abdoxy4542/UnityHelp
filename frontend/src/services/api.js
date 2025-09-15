import axios from 'axios';

const api = axios.create({
  baseURL: '/api', // Adjust this to your Django API endpoint
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
