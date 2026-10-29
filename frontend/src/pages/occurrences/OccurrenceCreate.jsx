import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, MapPin, KeyRound, User, PlusCircle } from 'lucide-react';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import { occurrencesService } from '../../services/occurrencesService';
import { operationsService } from '../../services/operationsService';
import styles from '../../styles/pages/occurrences/OccurrenceCreate.module.css';

export default function OccurrenceCreate() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    operacao_id: '',
    segredo_agente: '',
    localizacao: '',
    coordenadas: '',
    agente_responsavel: '',
    detalhes: '',
  });
  const [operacoes, setOperacoes] = useState([]);
  const [loadingOperations, setLoadingOperations] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    operationsService.list()
      .then((items) => {
        setOperacoes(items);
        if (items.length) setFormData((prev) => ({ ...prev, operacao_id: items[0].codigo }));
      })
      .catch((err) => setErrorMessage(err.response?.data?.message || 'Não foi possível carregar as operações.'))
      .finally(() => setLoadingOperations(false));
  }, []);

  const handleChange = (e) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage('');

    // O segredo valida a operação; os dados sensíveis seguem separados no envio.
    const payload = {
      operacao_id: formData.operacao_id,
      segredo_agente: formData.segredo_agente,
      dados_sensiveis: {
        localizacao: formData.localizacao,
        coordenadas: formData.coordenadas,
        agente_responsavel: formData.agente_responsavel,
        detalhes: formData.detalhes,
      },
    };

    try {
      await occurrencesService.create(payload);
      navigate('/ocorrencias');
    } catch (err) {
      setErrorMessage(err.response?.data?.message || 'Não foi possível cifrar e registrar a ocorrência.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1 className={styles.title}>Registrar Ocorrência</h1>
        <p className={styles.subtitle}>
          Localização, coordenadas, agente e relatório serão cifrados antes da gravação. A chave não será armazenada.
        </p>

        {errorMessage && <p role="alert" style={{ color: '#fca5a5' }}>{errorMessage}</p>}
        {!loadingOperations && operacoes.length === 0 && !errorMessage && (
          <p role="status" style={{ color: '#fbbf24' }}>Nenhuma operação ativa. Solicite ao coordenador que cadastre uma operação antes do registro.</p>
        )}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.grid}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <label htmlFor="operacao_id" style={{ fontSize: '0.875rem', fontWeight: 500, color: '#e2e8f0' }}>Operação</label>
              <select id="operacao_id" name="operacao_id" value={formData.operacao_id} onChange={handleChange} required disabled={loadingOperations || !operacoes.length} style={{ width: '100%', padding: '10px 14px', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 6, color: '#f8fafc' }}>
                {operacoes.map((operation) => <option key={operation.id} value={operation.codigo}>{operation.codigo} — {operation.nome}</option>)}
              </select>
            </div>
            <Input
              label="Segredo da Operação (Chave de Cifra)"
              name="segredo_agente"
              type="password"
              placeholder="Ex: ChaveOperacional123"
              icon={KeyRound}
              value={formData.segredo_agente}
              onChange={handleChange}
              minLength={10}
              autoComplete="new-password"
              required
            />
          </div>

          <div className={styles.grid}>
            <Input
              label="Local Exato da Apreensão"
              name="localizacao"
              placeholder="Ex: KM 42 Rod. dos Bandeirantes"
              icon={MapPin}
              value={formData.localizacao}
              onChange={handleChange}
              required
            />
            <Input
              label="Coordenadas GPS"
              name="coordenadas"
              placeholder="-23.442, -46.918"
              value={formData.coordenadas}
              onChange={handleChange}
              required
            />
          </div>

          <Input
            label="Agente Responsável"
            name="agente_responsavel"
            placeholder="Nome ou Matrícula do Agente"
            icon={User}
            value={formData.agente_responsavel}
            onChange={handleChange}
            required
          />

          <div className={styles.textareaWrapper}>
            <label className={styles.textareaLabel}>Detalhes dos Animais e Apreensão</label>
            <textarea
              className={styles.textarea}
              rows={3}
              name="detalhes"
              placeholder="Espécies encontradas, quantidade, condições do cativeiro..."
              value={formData.detalhes}
              onChange={handleChange}
              required
            />
          </div>

          <div style={{ marginTop: '8px' }}>
          <Button type="submit" loading={loading} icon={ShieldAlert} disabled={loadingOperations || !operacoes.length}>
              Cifrar e Registrar no Banco
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
