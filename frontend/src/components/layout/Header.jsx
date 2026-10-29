import React from 'react';
import { Menu, LogOut, User } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import styles from '../../styles/components/layout/Header.module.css';

export default function Header({ onToggleSidebar }) {
  const { user, logout } = useAuth();

  return (
    <header className={styles.header}>
      <div className={styles.leftSection}>
        <button
          type="button"
          onClick={onToggleSidebar}
          className={styles.menuButton}
          aria-label="Abrir Menu"
        >
          <Menu size={22} />
        </button>

        <span className={styles.statusBadge}>MODO OPERACIONAL ATIVO</span>
      </div>

      <div className={styles.userSection}>
        <div className={styles.userInfo}>
          <User size={18} color="#94a3b8" />
          <span className={styles.userName}>{user?.nome || 'Agente'}</span>
          <span className={styles.userRole}>{user?.perfil || 'Agente'}</span>
        </div>

        <button
          type="button"
          onClick={logout}
          title="Encerrar Sessão"
          className={styles.logoutButton}
        >
          <LogOut size={16} />
          <span className={styles.logoutText}>Sair</span>
        </button>
      </div>
    </header>
  );
}