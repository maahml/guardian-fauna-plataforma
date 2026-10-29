import React, { useState } from 'react';
import { KeyRound, X, Unlock } from 'lucide-react';
import Input from './Input';
import Button from './Button';
import styles from '../../styles/components/common/DecryptModal.module.css';

export default function DecryptModal({ isOpen, onClose, onConfirm, loading }) {
  const [segredo, setSegredo] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!segredo.trim()) return;
    onConfirm(segredo);
  };

  return (
    <div className={styles.overlay}>
      <div className={styles.modal}>
        <div className={styles.header}>
          <div className={styles.titleArea}>
            <KeyRound size={22} color="#10b981" />
            <h3 className={styles.title}>Decifrar Dados Sigilosos</h3>
          </div>
          <button type="button" onClick={onClose} className={styles.closeBtn}>
            <X size={18} />
          </button>
        </div>

        <p className={styles.description}>
          Informe o segredo da operação para revelar temporariamente os dados protegidos nesta sessão.
        </p>

        <form onSubmit={handleSubmit} className={styles.form}>
          <Input
            label="Segredo da Operação"
            type="password"
            placeholder="Ex: ChaveOperacional123"
            value={segredo}
            onChange={(e) => setSegredo(e.target.value)}
            required
            autoFocus
          />

          <div className={styles.actions}>
            <Button type="submit" loading={loading} icon={Unlock} fullWidth={true}>
              Decifrar
            </Button>
            <Button type="button" variant="secondary" onClick={onClose} fullWidth={true}>
              Cancelar
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
