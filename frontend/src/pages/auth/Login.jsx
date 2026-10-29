import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ShieldCheck, Mail, Lock, AlertCircle } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import styles from '../../styles/pages/auth/Login.module.css';
import Logo from '../../assets/Logo.svg';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [formData, setFormData] = useState({ email: '', senha: '' });
  const [errorMessage, setErrorMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    if (errorMessage) setErrorMessage('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage('');

    // O painel é aberto apenas quando a API confirma o acesso.
    try {
      await login(formData.email, formData.senha);
      navigate('/dashboard');
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Falha na autenticação. Verifique suas credenciais.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      
      <div className={styles.card}>
        <div className={styles.header}>
         <div>
          <img src={Logo} alt="Guardian Logo" className={styles.logo} />
         </div>
          <p className={styles.subtitle}>Plataforma Segura de Proteção à Fauna Silvestre</p>
        </div>

        {errorMessage && (
          <div className={styles.errorBox}>
            <AlertCircle size={18} />
            <span>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className={styles.form}>
          <Input
            label="E-mail Operacional"
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="agente@guardian.gov.br"
            icon={Mail}
            required
          />

          <Input
            label="Senha"
            type="password"
            name="senha"
            value={formData.senha}
            onChange={handleChange}
            placeholder="••••••••"
            icon={Lock}
            required
          />

          <Button type="submit" loading={loading} icon={ShieldCheck}>
            Acessar Plataforma
          </Button>
        </form>

        <div className={styles.footer}>
          <span>Não possui perfil?</span>
          <Link to="/solicitar-acesso" className={styles.link}>
            Solicitar Acesso
          </Link>
        </div>
      </div>
    </div>
  );
}
