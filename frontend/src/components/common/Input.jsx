import React from 'react';

export default function Input({
  label,
  type = 'text',
  name,
  value,
  onChange,
  placeholder,
  error,
  icon: Icon,
  required = false,
  ...props
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '100%' }}>
      {label && (
        <label style={{ fontSize: '0.875rem', fontWeight: 500, color: '#e2e8f0' }}>
          {label} {required && <span style={{ color: '#ef4444' }}>*</span>}
        </label>
      )}

      <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
        {Icon && (
          <div
            style={{
              position: 'absolute',
              left: '12px',
              display: 'flex',
              alignItems: 'center',
              pointerEvents: 'none',
              color: '#94a3b8',
            }}
          >
            <Icon size={18} />
          </div>
        )}

        <input
          type={type}
          name={name}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          required={required}
          style={{
            width: '100%',
            padding: Icon ? '10px 14px 10px 40px' : '10px 14px',
            backgroundColor: '#1e293b',
            border: `1px solid ${error ? '#ef4444' : '#334155'}`,
            borderRadius: '6px',
            color: '#f8fafc',
            fontSize: '0.95rem',
            outline: 'none',
            boxSizing: 'border-box',
            transition: 'border-color 0.2s',
          }}
          onFocus={(e) => {
            if (!error) e.target.style.borderColor = '#10b981';
          }}
          onBlur={(e) => {
            if (!error) e.target.style.borderColor = '#334155';
          }}
          {...props}
        />
      </div>

      {error && (
        <span style={{ fontSize: '0.8rem', color: '#f87171' }}>{error}</span>
      )}
    </div>
  );
}