import api from './api';

export const sheltersService = {
  list: async () => (await api.get('/abrigos')).data,
  create: async (data) => (await api.post('/abrigos', data)).data,
  decrypt: async (id, segredo_operacional) =>
    (await api.post(`/abrigos/${id}/decifrar`, { segredo_operacional })).data,
};
