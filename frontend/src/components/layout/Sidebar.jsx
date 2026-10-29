import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  ShieldCheck, 
  LayoutDashboard, 
  Briefcase, 
  FileWarning, 
  Home, 
  MessageSquare,
  UserCheck,
  X
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { ROLES } from '../../utils/constants';
import styles from '../../styles/components/layout/Sidebar.module.css';

export default function Sidebar({ isOpen, onClose }) {
  const { user } = useAuth();
  const perfil = user?.perfil;

  const links = [
    { label: 'Painel Geral', path: '/dashboard', icon: LayoutDashboard, roles: 'ALL' },
    { 
      label: 'Operações', 
      path: '/operacoes', 
      icon: Briefcase, 
      roles: [ROLES.COORDENADOR, ROLES.ADMIN] 
    },
    { label: 'Ocorrências', path: '/ocorrencias', icon: FileWarning, roles: 'ALL' },
    { label: 'Abrigos / Soltura', path: '/abrigos', icon: Home, roles: 'ALL' },
    { 
      label: 'Mensageria', 
      path: '/mensageria', 
      icon: MessageSquare, 
      roles: [ROLES.AGENTE, ROLES.COORDENADOR, ROLES.ADMIN] 
    },
    { label: 'Solicitações de acesso', path: '/admin/solicitacoes', icon: UserCheck, roles: [ROLES.ADMIN] },
  ];

  const itensFiltrados = links.filter((item) => {
    if (item.roles === 'ALL') return true;
    return item.roles.includes(perfil);
  });

  return (
    <>
      {/* Fundo escurecido exibido no celular */}
      <div 
        className={`${styles.backdrop} ${isOpen ? styles.backdropVisible : ''}`} 
        onClick={onClose} 
      />

      {/* Menu principal */}
      <aside className={`${styles.sidebar} ${isOpen ? styles.sidebarOpen : ''}`}>
        <div className={styles.header}>
          <div className={styles.logoArea}>
            <ShieldCheck size={26} color="#10b981" />
            <span className={styles.brand}>GUARDIAN FAUNA</span>
          </div>
          <button 
            type="button" 
            onClick={onClose} 
            className={styles.closeButton}
            aria-label="Fechar Menu"
          >
            <X size={20} />
          </button>
        </div>

        <nav className={styles.nav}>
          {itensFiltrados.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onClose} // Fecha o menu depois que a pessoa escolhe uma opção no celular.
                className={({ isActive }) => 
                  `${styles.navItem} ${isActive ? styles.navItemActive : ''}`
                }
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </aside>
    </>
  );
}
