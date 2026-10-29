import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Lock, Unlock, ShieldCheck } from 'lucide-react';
import Button from '../../components/common/Button';
import DecryptModal from '../../components/common/DecryptModal';
import { occurrencesService } from '../../services/occurrencesService';
import { formatDate } from '../../utils/formatters';
import styles from '../../styles/pages/occurrences/OccurrenceDetails.module.css';

export default function OccurrenceDetails() {
  const { id } = useParams();
  const [record, setRecord] = useState(null);
  const [plaintext, setPlaintext] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    occurrencesService.getById(id).then(setRecord)
      .catch((err) => setError(err.response?.data?.message || 'Não foi possível carregar a ocorrência.'));
  }, [id]);

  const decrypt = async (secret) => {
    setLoading(true); setError('');
    try { setPlaintext(await occurrencesService.decrypt(id, secret)); setModalOpen(false); }
    catch (err) { setError(err.response?.data?.message || 'Não foi possível decifrar esta ocorrência.'); }
    finally { setLoading(false); }
  };

  return (
    <div className={styles.container}>
      <Link to="/ocorrencias" className={styles.backBtn}><ArrowLeft size={16} /> Voltar para Ocorrências</Link>
      {error && <p role="alert" style={{ color: '#fca5a5' }}>{error}</p>}
      {!record && !error && <p>Carregando ocorrência...</p>}
      {record && <div className={styles.card}>
        <div className={styles.header}><h1 className={styles.title}>Ocorrência #{record.id}</h1><span className={styles.tag}>Operação {record.operacao_id}</span></div>
        <p>{formatDate(record.timestamp)}</p>
        <div><span style={{ fontSize: '0.8rem', color: '#eab308', fontWeight: 600 }}><Lock size={14} /> Bloco cifrado em repouso</span><div className={styles.block}>{record.bloco_cifrado}</div></div>
        {plaintext ? <div style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)', padding: 16, borderRadius: 6, border: '1px solid #10b981' }}>
          <h3 style={{ color: '#34d399' }}><ShieldCheck size={18} /> Conteúdo decifrado em memória</h3>
          <p><strong>Local:</strong> {plaintext.localizacao}</p><p><strong>GPS:</strong> {plaintext.coordenadas}</p><p><strong>Agente:</strong> {plaintext.agente_responsavel}</p><p><strong>Apreensão:</strong> {plaintext.detalhes}</p>
        </div> : <Button icon={Unlock} onClick={() => setModalOpen(true)} fullWidth={false}>Decifrar ocorrência</Button>}
      </div>}
      <DecryptModal isOpen={modalOpen} onClose={() => setModalOpen(false)} onConfirm={decrypt} loading={loading} />
    </div>
  );
}
