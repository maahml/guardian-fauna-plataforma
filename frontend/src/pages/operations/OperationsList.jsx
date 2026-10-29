import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Briefcase, PlusCircle, Users, Calendar } from 'lucide-react';
import styles from '../../styles/pages/operations/Operations.module.css';
import { operationsService } from '../../services/operationsService';

export default function OperationsList() {
  const [operacoes, setOperacoes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    operationsService.list()
      .then(setOperacoes)
      .catch((err) => setErrorMessage(err.response?.data?.message || 'Não foi possível carregar as operações.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Operações Cadastradas</h1>
          <p className={styles.subtitle}>Gerenciamento de missões ativas e controle de membros</p>
        </div>
        <Link to="/operacoes/nova" className={styles.linkButton}>
          <PlusCircle size={18} /> Nova Operação
        </Link>
      </div>

      {errorMessage && <p role="alert" style={{ color: '#fca5a5' }}>{errorMessage}</p>}
      {loading && <p className={styles.subtitle}>Carregando operações...</p>}
      {!loading && operacoes.length === 0 && !errorMessage && (
        <div className={styles.card}><p>Nenhuma operação cadastrada ainda.</p></div>
      )}
      <div className={styles.grid}>
        {operacoes.map((op) => (
          <div key={op.id} className={styles.card}>
            <div className={styles.cardTop}>
              <span style={{ fontSize: '0.8rem', color: '#38bdf8', fontWeight: 600 }}>{op.codigo}</span>
              <span className={styles.statusActive}>{op.status}</span>
            </div>
            <h3 className={styles.opName}>{op.nome}</h3>
            <div className={styles.membersArea}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                <Calendar size={14} /> Início: {new Date(`${op.inicio}T00:00:00`).toLocaleDateString('pt-BR')}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Users size={14} /> Usuários autorizados na organização: {op.membros}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
