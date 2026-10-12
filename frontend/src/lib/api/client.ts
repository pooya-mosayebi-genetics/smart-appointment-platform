import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getHealth = async () => {
  let retries = 5;
  
  while (retries > 0) {
    try {
      const response = await apiClient.get('/health/');
      return response.data;
    } catch (error) {
      retries--;
      if (retries === 0) throw error;
      
      // صبر ۱ ثانیه قبل از تلاش مجدد
      console.log(`Backend not ready yet, retrying in 1s... (${retries} left)`);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
};

export default apiClient;