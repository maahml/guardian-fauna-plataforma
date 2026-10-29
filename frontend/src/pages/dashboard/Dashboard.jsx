import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Briefcase, FileWarning, ShieldAlert, PlusCircle, MessageSquare, Home } from 'lucide-react';
import { dashboardService } from '../../services/dashboardService';
import styles from '../../styles/pages/dashboard/Dashboard.module.css';

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => { dashboardService.summary().then(setSummary).catch((err) => setError(err.response?.data?.message || 'Não foi possível carregar o painel.')); }, []);

  return <div className={styles.container}>
    <div className={styles.titleSection}><h1 className={styles.title}>Painel Operacional</h1><p className={styles.subtitle}>Resumo dos registros da sua organização.</p></div>
    {error && <p role="alert" style={{ color: '#fca5a5' }}>{error}</p>}
    <div className={styles.metricsGrid}>
      {[[Briefcase, 'Operações ativas', summary?.operacoes_ativas], [FileWarning, 'Ocorrências registradas', summary?.ocorrencias_registradas], [ShieldAlert, 'Dados cifrados', `${summary?.dados_cifrados_percentual ?? 0}%`], [Home, 'Abrigos cadastrados', summary?.abrigos_cadastrados]].map(([Icon, label, value]) => <div key={label} className={styles.card}>
        <div className={styles.cardInfo}><span className={styles.cardLabel}>{label}</span><span className={styles.cardValue}>{value ?? '—'}</span></div><div className={styles.cardIcon} style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)', color: '#10b981' }}><Icon size={24} /></div>
      </div>)}
    </div>
    <div className={styles.section}><h2 className={styles.sectionTitle}>Ações rápidas</h2><div className={styles.actionsGrid}>
      <Link to="/ocorrencias/nova" className={styles.actionButton}><PlusCircle size={20} color="#10b981" /><span>Registrar ocorrência</span></Link>
      <Link to="/ocorrencias" className={styles.actionButton}><FileWarning size={20} color="#eab308" /><span>Consultar ocorrências cifradas</span></Link>
      <Link to="/mensageria" className={styles.actionButton}><MessageSquare size={20} color="#38bdf8" /><span>Mensageria da operação</span></Link>
    </div></div>
    <p style={{ color: '#94a3b8', fontSize: '0.8rem' }}>A cifra de Hill tem finalidade didática e não deve proteger dados reais ou de uso operacional.</p>
  </div>;
}
