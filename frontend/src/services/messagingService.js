import api from './api';

export const messagingService = {
  list: async (operacao_id) =>
    (await api.get('/mensagens', { params: { operacao_id } })).data,
  create: async (data) => (await api.post('/mensagens', data)).data,
  decrypt: async (id, segredo_operacao) =>
    (await api.post(`/mensagens/${id}/decifrar`, { segredo_operacao })).data,
};
