import React, { useEffect, useState } from 'react';
import { Send, Lock, Unlock, KeyRound } from 'lucide-react';
import Button from '../../components/common/Button';
import Input from '../../components/common/Input';
import { operationsService } from '../../services/operationsService';
import { messagingService } from '../../services/messagingService';
import styles from '../../styles/pages/messaging/Messaging.module.css';

export default function Messaging() {
  const [operations, setOperations] = useState([]);
  const [operationCode, setOperationCode] = useState('');
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState('');
  const [secret, setSecret] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    operationsService.list().then((list) => {
      setOperations(list);
      if (list.length) setOperationCode(list[0].codigo);
    }).catch((err) => setError(err.response?.data?.message || 'Não foi possível carregar as operações.'));
  }, []);

  useEffect(() => {
    if (!operationCode) { setMessages([]); return; }
    messagingService.list(operationCode).then(setMessages)
      .catch((err) => setError(err.response?.data?.message || 'Não foi possível carregar as mensagens.'));
  }, [operationCode]);

  const sendMessage = async (event) => {
    event.preventDefault();
    if (!message.trim()) return;
    setLoading(true); setError('');
    try {
      await messagingService.create({ operacao_id: operationCode, texto: message, segredo_operacao: secret });
      setMessage('');
      setMessages(await messagingService.list(operationCode));
    } catch (err) { setError(err.response?.data?.message || 'Não foi possível enviar a mensagem.'); }
    finally { setLoading(false); }
  };

  const decryptMessages = async () => {
    if (!secret) { setError('Informe o segredo da operação para decifrar as mensagens.'); return; }
    setLoading(true); setError('');
    try {
      const decoded = await Promise.all(messages.map(async (item) => {
        try { return { ...item, decifrado: await messagingService.decrypt(item.id, secret) }; }
        catch (err) { if (err.response?.status === 403 || err.response?.status === 422) throw err; return item; }
      }));
      setMessages(decoded);
    } catch (err) { setError(err.response?.data?.message || 'Não foi possível decifrar as mensagens.'); }
    finally { setLoading(false); }
  };

  return <div className={styles.container}>
    <div className={styles.header}>
      <div><h2 style={{ margin: 0, fontSize: '1.05rem', color: '#f8fafc' }}>Mensageria operacional</h2><span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Mensagens cifradas por operação</span></div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Lock size={14} /><select aria-label="Operação" value={operationCode} onChange={(e) => { setOperationCode(e.target.value); setMessages([]); }} style={{ padding: 8, background: '#1e293b', color: '#f8fafc', border: '1px solid #334155', borderRadius: 6 }}>{operations.map((op) => <option key={op.id} value={op.codigo}>{op.codigo}</option>)}</select></div>
    </div>
    {error && <p role="alert" style={{ color: '#fca5a5' }}>{error}</p>}
    {operations.length === 0 && <p>Nenhuma operação disponível para mensageria.</p>}
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(220px, 1fr) 2fr', gap: 12, margin: '12px 0' }}>
      <Input label="Segredo da operação" type="password" icon={KeyRound} value={secret} onChange={(e) => setSecret(e.target.value)} autoComplete="current-password" />
      <div style={{ display: 'flex', alignItems: 'end' }}><Button type="button" icon={Unlock} fullWidth={false} loading={loading} onClick={decryptMessages}>Decifrar mensagens</Button></div>
    </div>
    <div className={styles.messagesList}>
      {messages.length === 0 && <p style={{ color: '#94a3b8' }}>Nenhuma mensagem registrada nesta operação.</p>}
      {messages.map((item) => <div key={item.id} className={`${styles.messageCard} ${item.tipo === 'enviada' ? styles.sent : styles.received}`}>
        <span className={styles.sender}>{item.remetente} · {item.timestamp}</span>
        <span className={styles.cipherText}>{item.decifrado?.texto ?? `[Cifrada] ${item.texto_cifrado}`}</span>
      </div>)}
    </div>
    <form onSubmit={sendMessage} className={styles.inputArea}>
      <input type="text" className={styles.inputField} placeholder="Digite uma mensagem..." value={message} onChange={(e) => setMessage(e.target.value)} disabled={!operationCode || !secret} required />
      <Button type="submit" icon={Send} fullWidth={false} loading={loading} disabled={!operationCode || !secret}>Enviar</Button>
    </form>
  </div>;
}
