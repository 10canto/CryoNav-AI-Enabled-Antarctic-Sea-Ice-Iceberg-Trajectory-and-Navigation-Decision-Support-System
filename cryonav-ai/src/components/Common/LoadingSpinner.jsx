import React from 'react';

/**
 * Reusable Loading Spinner with radar scan effect
 */
export function LoadingSpinner({ message = 'Loading...', size = 'md' }) {
  const sizeMap = {
    sm: { width: 24, height: 24, borderWidth: 2 },
    md: { width: 38, height: 38, borderWidth: 3 },
    lg: { width: 56, height: 56, borderWidth: 4 },
  };

  const currentSize = sizeMap[size] || sizeMap.md;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '8px', padding: '12px' }}>
      <div
        className="spin-loader"
        style={{
          width: `${currentSize.width}px`,
          height: `${currentSize.height}px`,
          border: `${currentSize.borderWidth}px solid rgba(0, 212, 255, 0.2)`,
          borderTop: `${currentSize.borderWidth}px solid #00d4ff`,
          borderRadius: '50%',
        }}
      />
      {message && (
        <span style={{ fontSize: '0.78rem', color: '#94a3b8', letterSpacing: '0.5px', fontWeight: 600 }}>
          {message}
        </span>
      )}
    </div>
  );
}

export default LoadingSpinner;
