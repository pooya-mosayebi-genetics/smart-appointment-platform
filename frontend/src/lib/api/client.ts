import axios from 'axios';

// ایجاد instance اصلی برای APIهای نیازمند احراز هویت
const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: افزودن توکن JWT به هدر
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response Interceptor: مدیریت انقضای توکن
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) throw new Error('No refresh token');

        const res = await axios.post('/api/v1/auth/refresh/', { refresh: refreshToken });
        const newAccessToken = res.data.access;
        
        localStorage.setItem('access_token', newAccessToken);
        
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch (err) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(err);
      }
    }
    return Promise.reject(error);
  }
);

// --- Auth APIs ---
export const login = async (mobile: string, password: string) => {
  const response = await apiClient.post('/auth/login/', { mobile, password });
  localStorage.setItem('access_token', response.data.access);
  localStorage.setItem('refresh_token', response.data.refresh);
  localStorage.setItem('user', JSON.stringify(response.data.user));
  return response.data;
};

export const logout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
};

export const getCurrentUser = () => {
  const userStr = localStorage.getItem('user');
  return userStr ? JSON.parse(userStr) : null;
};

// --- Appointments APIs (Staff/Admin) ---
export const getProviders = async () => {
  const response = await apiClient.get('/appointments/providers/');
  return response.data;
};

export const getSlots = async (params: { provider?: string, date?: string, status?: string }) => {
  const response = await apiClient.get('/appointments/slots/', { params });
  return response.data;
};

export const bookSlot = async (slotId: string, patientData: { patient_mobile: string, patient_name: string }) => {
  const response = await apiClient.patch(`/appointments/slots/${slotId}/book/`, patientData);
  return response.data;
};

// --- Public APIs (For Patients - No Auth Required) ---

// دریافت لیست پزشکان فعال برای عموم
export const getPublicProviders = async () => {
  // استفاده از instance ساده چون نیاز به توکن نیست
  const response = await axios.get('/api/v1/appointments/providers/?status=active');
  return response.data;
};

// دریافت اسلات‌های آزاد برای یک پزشک خاص در یک تاریخ (عمومی)
export const getPublicAvailableSlots = async (providerId: string, date: string) => {
  const response = await axios.get('/api/v1/appointments/slots/', {
    params: {
      provider: providerId,
      date: date,
      status: 'available' // فقط اسلات‌های آزاد
    }
  });
  return response.data;
};

// Health Check
export const getHealth = async () => {
  const response = await axios.get('/api/health/'); 
  return response.data;
};

export default apiClient;