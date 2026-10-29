import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { UserCheck, Mail, User, Building2, FileText, ArrowLeft, CheckCircle2, AlertCircle, Lock } from 'lucide-react';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import { authService } from '../../services/authService';

export default function RequestAccess() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    orgao: '',
    perfilDesejado: 'Agente',
    justificativa: '',
    senha: '',
    confirmarSenha: '',
  });
  const [loading, setLoading] = useState(false);
  const [sucesso, setSucesso] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleChange = (e) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    if (formData.senha !== formData.confirmarSenha) {
      setErrorMessage('As senhas não coincidem.');
      return;
    }
    setLoading(true);
    try {
      await authService.requestAccess(formData);
      setSucesso(true);
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Não foi possível enviar a solicitação. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#0b1120',
        padding: '20px',
        boxSizing: 'border-box',
        fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '480px',
          backgroundColor: '#111827',
          border: '1px solid #1f2937',
          borderRadius: '12px',
          padding: '36px 32px',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)',
        }}
      >
        <Link
          to="/login"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            color: '#9ca3af',
            textDecoration: 'none',
            fontSize: '0.875rem',
            marginBottom: '20px',
          }}
        >
          <ArrowLeft size={16} /> Voltar ao Login
        </Link>

        <div style={{ marginBottom: '24px' }}>
          <div
            style={{
              display: 'inline-flex',
              padding: '10px',
              borderRadius: '50%',
              backgroundColor: 'rgba(5, 150, 105, 0.15)',
              color: '#10b981',
              marginBottom: '10px',
            }}
          >
            <UserCheck size={32} />
          </div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#f9fafb', margin: '0 0 6px 0' }}>
            Solicitação de Perfil Operacional
          </h2>
          <p style={{ fontSize: '0.85rem', color: '#9ca3af', margin: 0 }}>
            Seu pedido será avaliado pelo Administrador do Órgão antes da liberação de chaves.
          </p>
        </div>

        {sucesso ? (
          <div
            style={{
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid #10b981',
              borderRadius: '8px',
              padding: '24px',
              textAlign: 'center',
            }}
          >
            <CheckCircle2 size={44} style={{ color: '#10b981', margin: '0 auto 12px auto' }} />
            <h3 style={{ color: '#f9fafb', margin: '0 0 8px 0' }}>Solicitação Enviada!</h3>
            <p style={{ color: '#9ca3af', fontSize: '0.9rem', marginBottom: '20px' }}>
              Sua conta será liberada após a aprovação de um administrador. Use a senha informada ao solicitar acesso.
            </p>
            <Button onClick={() => navigate('/login')}>Ir para Login</Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {errorMessage && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#fca5a5', background: 'rgba(127, 29, 29, .2)', padding: 12, borderRadius: 6 }}>
                <AlertCircle size={18} /> <span>{errorMessage}</span>
              </div>
            )}
            <Input
              label="Nome Completo"
              name="nome"
              value={formData.nome}
              onChange={handleChange}
              placeholder="Ex: Agente Carlos Silva"
              icon={User}
              required
            />

            <Input
              label="E-mail Institucional"
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="carlos@ibama.gov.br"
              icon={Mail}
              required
            />

            <Input
              label="Órgão / Instituição"
              name="orgao"
              value={formData.orgao}
              onChange={handleChange}
              placeholder="Ex: IBAMA, Polícia Ambiental, ICMBio"
              icon={Building2}
              required
            />

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '0.875rem', fontWeight: 500, color: '#e2e8f0' }}>
                Perfil Solicitado <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <select
                name="perfilDesejado"
                value={formData.perfilDesejado}
                onChange={handleChange}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '6px',
                  color: '#f8fafc',
                  fontSize: '0.95rem',
                  outline: 'none',
                }}
              >
                <option value="Agente">Agente de Campo (Ocorrências e Apreensões)</option>
                <option value="Coordenador">Coordenador de Operação (Gestão e Segredos)</option>
              </select>
            </div>

            <Input
              label="Senha (mínimo de 10 caracteres)"
              name="senha"
              type="password"
              value={formData.senha}
              onChange={handleChange}
              icon={Lock}
              required
              minLength={10}
              autoComplete="new-password"
            />

            <Input
              label="Confirmar senha"
              name="confirmarSenha"
              type="password"
              value={formData.confirmarSenha}
              onChange={handleChange}
              icon={Lock}
              required
              minLength={10}
              autoComplete="new-password"
            />

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '0.875rem', fontWeight: 500, color: '#e2e8f0' }}>
                Justificativa Operacional <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <textarea
                name="justificativa"
                value={formData.justificativa}
                onChange={handleChange}
                rows={3}
                placeholder="Descreva a necessidade de acesso às operações sigilosas..."
                required
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '6px',
                  color: '#f8fafc',
                  fontSize: '0.95rem',
                  outline: 'none',
                  boxSizing: 'border-box',
                  resize: 'vertical',
                }}
              />
            </div>

            <div style={{ marginTop: '10px' }}>
              <Button type="submit" loading={loading} icon={FileText}>
                Enviar Solicitação
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
