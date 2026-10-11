import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api', // چون proxy داریم، نیازی به نوشتن localhost نیست
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getHealth = async () => {
  const response = await apiClient.get('/health/');
  return response.data;
};

export default apiClient;