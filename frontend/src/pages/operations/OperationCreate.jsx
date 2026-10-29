import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Briefcase, KeyRound, Calendar } from 'lucide-react';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import { operationsService } from '../../services/operationsService';
import styles from '../../styles/pages/operations/Operations.module.css';

export default function OperationCreate() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [form, setForm] = useState({
    nome: '',
    codigo: '',
    dataInicio: '',
    segredoBase: '',
  });

  const handleChange = (e) => setForm((p) => ({ ...p, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage('');
    try {
      await operationsService.create(form);
      navigate('/operacoes');
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Não foi possível criar a operação.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card} style={{ maxWidth: '600px' }}>
        <h1 className={styles.title}>Criar Nova Operação</h1>
        <p className={styles.subtitle}>
          A chave não será armazenada. Compartilhe-a apenas com os agentes autorizados desta operação.
        </p>

        {errorMessage && <p role="alert" style={{ color: '#fca5a5' }}>{errorMessage}</p>}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Input
            label="Nome da Operação"
            name="nome"
            placeholder="Ex: Operação Asas Abertas"
            icon={Briefcase}
            value={form.nome}
            onChange={handleChange}
            required
          />
          <Input
            label="Código Operacional"
            name="codigo"
            placeholder="OP-2026-ASA"
            value={form.codigo}
            onChange={handleChange}
            required
          />
          <Input
            label="Data de Início"
            name="dataInicio"
            type="date"
            icon={Calendar}
            value={form.dataInicio}
            onChange={handleChange}
            required
          />
          <Input
            label="Segredo Base da Operação"
            name="segredoBase"
            type="password"
            placeholder="Segredo compartilhado com os agentes da operação"
            icon={KeyRound}
            value={form.segredoBase}
            onChange={handleChange}
            minLength={10}
            autoComplete="new-password"
            required
          />
          <div style={{ marginTop: '10px' }}>
            <Button type="submit" loading={loading}>
              Criar Operação
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
