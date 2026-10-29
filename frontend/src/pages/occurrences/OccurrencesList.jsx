import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Lock, Unlock, PlusCircle, Calendar, ShieldCheck } from 'lucide-react';
import DecryptModal from '../../components/common/DecryptModal';
import Button from '../../components/common/Button';
import { occurrencesService } from '../../services/occurrencesService';
import { formatDate } from '../../utils/formatters';
import styles from '../../styles/pages/occurrences/OccurrencesList.module.css';

export default function OccurrencesList() {
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingList, setLoadingList] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(() => {
    setLoadingList(true);
    occurrencesService.list()
      .then(setItems)
      .catch((err) => setError(err.response?.data?.message || 'Não foi possível carregar o histórico.'))
      .finally(() => setLoadingList(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const decrypt = async (secret) => {
    setLoading(true);
    setError('');
    try {
      // A tela só mostra os dados depois que a API valida o segredo.
      const plaintext = await occurrencesService.decrypt(selected.id, secret);
      setItems((current) => current.map((item) => item.id === selected.id ? { ...item, decifrado: plaintext } : item));
      setModalOpen(false);
    } catch (err) {
      setError(err.response?.data?.message || 'Não foi possível decifrar esta ocorrência.');
    } finally { setLoading(false); }
  };

  return (
    <div className={styles.container}>
      <div className={styles.headerArea}>
        <div>
          <h1 className={styles.title}>Ocorrências Registradas</h1>
          <p className={styles.subtitle}>Histórico de apreensões com dados sensíveis armazenados cifrados.</p>
        </div>
        <Link to="/ocorrencias/nova" className={styles.newButton}><PlusCircle size={18} /><span>Nova Ocorrência</span></Link>
      </div>
      {error && <p role="alert" style={{ color: '#fca5a5' }}>{error}</p>}
      {loadingList && <p className={styles.subtitle}>Carregando histórico...</p>}
      {!loadingList && items.length === 0 && !error && <div className={styles.card}><p>Nenhuma ocorrência registrada.</p></div>}
      <div className={styles.list}>
        {items.map((item) => (
          <div key={item.id} className={styles.card}>
            <div className={styles.cardTop}>
              <span className={styles.opTag}>{item.operacao_id}</span>
              <div className={styles.date}><Calendar size={14} /><span>{formatDate(item.timestamp)}</span></div>
            </div>
            <div className={styles.cipherBlock}>
              <span className={styles.cipherLabel}><Lock size={14} /> Bloco cifrado</span>
              <div className={styles.cipherHex}>{item.bloco_cifrado}</div>
            </div>
            {item.decifrado && (
              <div className={styles.decryptedBlock}>
                <span className={styles.decryptedTitle}><ShieldCheck size={16} /> Dados decifrados nesta sessão</span>
                <div className={styles.decryptedInfo}>
                  <div><strong>Localização:</strong> {item.decifrado.localizacao}</div>
                  <div><strong>Coordenadas:</strong> {item.decifrado.coordenadas}</div>
                  <div><strong>Responsável:</strong> {item.decifrado.agente_responsavel}</div>
                  {item.decifrado.detalhes && <div><strong>Detalhes:</strong> {item.decifrado.detalhes}</div>}
                </div>
              </div>
            )}
            <div className={styles.actionArea}>
              {!item.decifrado
                ? <Button onClick={() => { setSelected(item); setModalOpen(true); }} icon={Unlock} fullWidth={false}>Decifrar com chave</Button>
                : <span style={{ fontSize: '0.8rem', color: '#34d399', fontWeight: 600 }}>✓ Decifrada nesta sessão</span>}
            </div>
          </div>
        ))}
      </div>
      <DecryptModal isOpen={modalOpen} onClose={() => setModalOpen(false)} onConfirm={decrypt} loading={loading} />
    </div>
  );
}
