import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { PlusCircle, Lock, Unlock } from 'lucide-react';
import Button from '../../components/common/Button';
import DecryptModal from '../../components/common/DecryptModal';
import { sheltersService } from '../../services/sheltersService';
import styles from '../../styles/pages/shelters/Shelters.module.css';

export default function SheltersList() {
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(null);
  const [plaintext, setPlaintext] = useState({});
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [loadingList, setLoadingList] = useState(true);

  useEffect(() => {
    sheltersService.list().then(setItems)
      .catch((err) => setError(err.response?.data?.message || 'Não foi possível carregar os abrigos.'))
      .finally(() => setLoadingList(false));
  }, []);

  const decrypt = async (secret) => {
    setLoading(true); setError('');
    try {
      const result = await sheltersService.decrypt(selected.id, secret);
      setPlaintext((current) => ({ ...current, [selected.id]: result })); setModalOpen(false);
    } catch (err) { setError(err.response?.data?.message || 'Chave incorreta ou dados inválidos.'); }
    finally { setLoading(false); }
  };

  return <div className={styles.container}>
    <div className={styles.header}><div><h1 className={styles.title}>Abrigos e CETAS</h1><p className={styles.subtitle}>Endereços e responsáveis técnicos ficam cifrados.</p></div><Link to="/abrigos/novo" className={styles.button}><PlusCircle size={18} /> Cadastrar Abrigo</Link></div>
    {error && <p role="alert" style={{ color: '#fca5a5' }}>{error}</p>}
    {loadingList && <p>Carregando abrigos...</p>}
    {!loadingList && items.length === 0 && !error && <div className={styles.card}><p>Nenhum abrigo cadastrado.</p></div>}
    <div className={styles.list}>{items.map((item) => <div key={item.id} className={styles.card}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}><h3 style={{ margin: 0, fontSize: '1.05rem', color: '#f8fafc' }}>{item.nome_publico}</h3><span style={{ fontSize: '0.75rem', color: '#38bdf8' }}>{item.status}</span></div>
      <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}><strong>Espécies atendidas:</strong> {item.especies}</p>
      <div className={styles.cipherWarning}><div style={{ color: '#eab308', marginBottom: 4 }}><Lock size={14} /> Endereço e responsável cifrados</div><code>{item.bloco_cifrado}</code></div>
      {plaintext[item.id] ? <div><p><strong>Endereço:</strong> {plaintext[item.id].endereco}</p><p><strong>Responsável:</strong> {plaintext[item.id].responsavel_tecnico}</p></div> : <Button icon={Unlock} fullWidth={false} onClick={() => { setSelected(item); setModalOpen(true); }}>Decifrar dados</Button>}
    </div>)}</div>
    <DecryptModal isOpen={modalOpen} onClose={() => setModalOpen(false)} onConfirm={decrypt} loading={loading} />
  </div>;
}
