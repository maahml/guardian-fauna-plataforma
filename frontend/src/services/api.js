import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Inclui o token da sessão nas chamadas que exigem autenticação.
api.interceptors.request.use(
  (config) => {
    const token = sessionStorage.getItem('guardian_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && sessionStorage.getItem('guardian_token')) {
      sessionStorage.removeItem('guardian_token');
      sessionStorage.removeItem('guardian_user');
      window.dispatchEvent(new Event('guardian:unauthorized'));
    }
    return Promise.reject(error);
  }
);

export default api;
