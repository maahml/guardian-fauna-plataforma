import { createContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';

export const AuthContext = createContext({});

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedToken = sessionStorage.getItem('guardian_token');
    const storedUser = authService.getCurrentUser();

    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(storedUser);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    const expireSession = () => {
      setToken(null);
      setUser(null);
    };
    window.addEventListener('guardian:unauthorized', expireSession);
    return () => window.removeEventListener('guardian:unauthorized', expireSession);
  }, []);

  const login = async (email, senha) => {
    // Mantém no contexto a sessão devolvida pela API.
    const data = await authService.login(email, senha);
    setToken(data.token);
    setUser({ id: data.id, nome: data.nome, perfil: data.perfil_usuario });
    return data;
  };

  const logout = () => {
    authService.logout();
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, authenticated: !!token, login, logout, loading }}>
      {!loading && children}
    </AuthContext.Provider>
  );
}
