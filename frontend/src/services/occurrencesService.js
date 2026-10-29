import api from './api';

export const occurrencesService = {
  list: async () => (await api.get('/ocorrencias')).data,
  // Envia os dados da nova ocorrência para a API.
  create: async ({ operacao_id, segredo_agente, dados_sensiveis }) => {
    const response = await api.post('/ocorrencias', {
      operacao_id,
      segredo_agente,
      dados_sensiveis,
    });
    return response.data;
  },

  // Consulta uma ocorrência pelo identificador.
  getById: async (id) => {
    const response = await api.get(`/ocorrencias/${id}`);
    return response.data;
  },

  // Solicita à API a decifragem da ocorrência.
  decrypt: async (id, segredo_operacao) => {
    const response = await api.post(`/ocorrencias/${id}/decifrar`, {
      segredo_operacao,
    });
    // Os dados decifrados permanecem somente no estado da interface.
    return response.data;
  },
};
