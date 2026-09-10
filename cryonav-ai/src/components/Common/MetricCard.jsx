import React from 'react';

/**
 * Reusable MetricCard Component for displaying sensor and route statistics
 */
export function MetricCard({ icon, label, value, unit = '', color, subtitle, id }) {
  return (
    <div
      id={id}
      style={{
        background: '#f8fafc',
        border: '1px solid #e2e8f0',
        borderRadius: '8px',
        padding: '10px 12px',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
      }}
    >
      {icon && (
        <div
          style={{
            fontSize: '1.4rem',
            width: '36px',
            height: '36px',
            borderRadius: '6px',
            background: color ? `${color}15` : 'rgba(0, 212, 255, 0.12)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: color || '#0284c7',
          }}
        >
          {icon}
        </div>
      )}
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <span style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>
          {label}
        </span>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
          <span style={{ fontSize: '1.05rem', fontWeight: 700, color: '#1e293b' }}>
            {value}
          </span>
          {unit && (
            <span style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 500 }}>
              {unit}
            </span>
          )}
        </div>
        {subtitle && (
          <span style={{ fontSize: '0.66rem', color: '#94a3b8', marginTop: '2px' }}>
            {subtitle}
          </span>
        )}
      </div>
    </div>
  );
}

export default MetricCard;
