import React from 'react';

export default function Button({
  children,
  type = 'button',
  onClick,
  disabled = false,
  loading = false,
  variant = 'primary',
  icon: Icon,
  fullWidth = true,
}) {
  const isPrimary = variant === 'primary';

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      style={{
        width: fullWidth ? '100%' : 'auto',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
        padding: '11px 16px',
        borderRadius: '6px',
        fontSize: '0.95rem',
        fontWeight: 600,
        cursor: disabled || loading ? 'not-allowed' : 'pointer',
        border: isPrimary ? 'none' : '1px solid #475569',
        backgroundColor: disabled || loading
          ? '#475569'
          : isPrimary
          ? '#059669' // Cor verde usada na ação principal.
          : 'transparent',
        color: '#ffffff',
        transition: 'background-color 0.2s, opacity 0.2s',
        opacity: disabled ? 0.7 : 1,
      }}
      onMouseEnter={(e) => {
        if (!disabled && !loading) {
          e.currentTarget.style.backgroundColor = isPrimary ? '#047857' : '#334155';
        }
      }}
      onMouseLeave={(e) => {
        if (!disabled && !loading) {
          e.currentTarget.style.backgroundColor = isPrimary ? '#059669' : 'transparent';
        }
      }}
    >
      {loading ? (
        <span>Carregando...</span>
      ) : (
        <>
          {Icon && <Icon size={18} />}
          {children}
        </>
      )}
    </button>
  );
}