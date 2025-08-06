import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      console.error('Network Error:', error.request);
    } else {
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// API service methods
export const apiService = {
  // Appointments
  getAppointments: () => {
    // Add cache-busting parameter for real-time updates
    const timestamp = Date.now();
    return api.get(`/appointments?_t=${timestamp}`);
  },
  
  // Personnel
  getPersonnel: () => api.get('/personnel'),
  getPersonnelStatus: () => api.get('/personnel-status'),
  getPersonnelAppointments: () => api.get('/personnel-appointments'),
  
  // Manning
  getManningStatus: () => api.get('/manning'),
  
  // Contacts
  getContacts: () => api.get('/contacts'),
  
  // AI Agent (Vera)
  sendMessage: (message: string, senderId?: string) => 
    api.post('/ai-agent/message', {
      message,
      sender_id: senderId || 'web_user',
    }),
};

export default api;