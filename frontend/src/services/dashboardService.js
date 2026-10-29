import api from './api';

export const dashboardService = {
  summary: async () => (await api.get('/dashboard')).data,
};
