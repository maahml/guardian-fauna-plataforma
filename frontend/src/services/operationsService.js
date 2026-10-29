import api from './api';

export const operationsService = {
  list: async () => (await api.get('/operacoes')).data,
  create: async (data) => (await api.post('/operacoes', data)).data,
};
