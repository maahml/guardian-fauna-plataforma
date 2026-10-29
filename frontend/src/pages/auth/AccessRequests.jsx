import React, { useEffect, useState } from 'react';
import { Check, X } from 'lucide-react';
import { authService } from '../../services/authService';
import styles from '../../styles/pages/auth/AccessRequests.module.css';

export default function AccessRequests() {
  const [items, setItems] = useState([]);
  const [busyRequestId, setBusyRequestId] = useState(null);
  const [busyAction, setBusyAction] = useState('');
  const [error, setError] = useState('');

  const load = () => authService.getPendingRequests()
    .then((requests) => {
      setItems(requests);
      setError('');
    })
    .catch((err) => setError(err.response?.data?.message || 'Falha ao carregar solicitações.'));

  useEffect(() => { load(); }, []);

  const review = async (id, action) => {
    setBusyRequestId(id);
    setBusyAction(action);
    setError('');
    try {
      await authService.reviewRequest(id, action);
      await load();
    } catch (err) {
      setError(err.response?.data?.message || 'Falha ao revisar a solicitação.');
    } finally {
      setBusyRequestId(null);
      setBusyAction('');
    }
  };

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <h1>Solicitações de acesso</h1>
        <p>Revise os pedidos de cadastro antes de autorizar o acesso ao sistema.</p>
      </header>

      {error && <p className={styles.error} role="alert">{error}</p>}

      {!items.length && !error && (
        <div className={styles.emptyState}>Nenhuma solicitação pendente.</div>
      )}

      <section className={styles.requestList} aria-label="Pedidos de acesso pendentes">
        {items.map((item) => {
          const isBusy = busyRequestId === item.id;
          return (
            <article className={styles.requestCard} key={item.id}>
              <div className={styles.cardHeader}>
                <h2>{item.nome}</h2>
                <span className={styles.profileBadge}>{item.perfil}</span>
              </div>

              <p className={styles.metadata}>
                <span>{item.email}</span>
                <span className={styles.separator} aria-hidden="true">·</span>
                <span>{item.orgao}</span>
              </p>

              {item.justificativa && (
                <div className={styles.justification}>
                  <h3>Justificativa</h3>
                  <p>{item.justificativa}</p>
                </div>
              )}

              <div className={styles.actions}>
                <button
                  className={`${styles.actionButton} ${styles.approveButton}`}
                  type="button"
                  disabled={busyRequestId !== null}
                  onClick={() => review(item.id, 'aprovar')}
                >
                  <Check size={17} aria-hidden="true" />
                  {isBusy && busyAction === 'aprovar' ? 'Aprovando…' : 'Aprovar'}
                </button>
                <button
                  className={`${styles.actionButton} ${styles.rejectButton}`}
                  type="button"
                  disabled={busyRequestId !== null}
                  onClick={() => review(item.id, 'rejeitar')}
                >
                  <X size={17} aria-hidden="true" />
                  {isBusy && busyAction === 'rejeitar' ? 'Rejeitando…' : 'Rejeitar'}
                </button>
              </div>
            </article>
          );
        })}
      </section>
    </main>
  );
}
