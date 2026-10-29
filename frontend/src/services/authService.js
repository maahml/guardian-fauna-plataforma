import api from './api';

export const authService = {
  login: async (email, senha) => {
    const response = await api.post('/auth/login', { email, senha });
    const { token, perfil_usuario, nome, id } = response.data;

    sessionStorage.setItem('guardian_token', token);
    sessionStorage.setItem('guardian_user', JSON.stringify({ id, nome, perfil: perfil_usuario }));

    return response.data;
  },

  requestAccess: async (data) => (await api.post('/solicitacoes', data)).data,
  getPendingRequests: async () => (await api.get('/admin/solicitacoes')).data,
  reviewRequest: async (id, acao) => (await api.post(`/admin/solicitacoes/${id}`, { acao })).data,

  logout: () => {
    api.post('/auth/logout').catch(() => {});
    sessionStorage.removeItem('guardian_token');
    sessionStorage.removeItem('guardian_user');
    window.location.href = '/login';
  },

  getCurrentUser: () => {
    const user = sessionStorage.getItem('guardian_user');
    return user ? JSON.parse(user) : null;
  },
};
