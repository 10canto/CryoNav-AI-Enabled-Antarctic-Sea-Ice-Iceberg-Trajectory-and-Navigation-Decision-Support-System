import React from 'react';
import { getStarRating } from '../../utils/riskCalculator.js';

/**
 * Route Details Modal for in-depth navigational telemetry
 */
export function RouteDetailsModal({ isOpen, onClose, route, onSelectRoute }) {
  if (!isOpen || !route) return null;

  return (
    <div className="modal-backdrop" id="route-details-modal">
      <div
        className="dashboard-card"
        style={{
          maxWidth: '520px',
          width: '100%',
          padding: '22px',
          border: `2px solid ${route.color || '#00d4ff'}`,
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #e2e8f0', pb: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '14px', height: '14px', borderRadius: '50%', background: route.color }}></div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#0f172a' }}>{route.name}</h3>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', fontSize: '1.2rem', cursor: 'pointer', color: '#64748b' }}
          >
            ✕
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', background: '#f8fafc', padding: '12px', borderRadius: '8px' }}>
          <div>
            <span style={{ fontSize: '0.72rem', color: '#64748b' }}>Total Distance:</span>
            <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>{route.distanceKm?.toLocaleString()} km</div>
          </div>
          <div>
            <span style={{ fontSize: '0.72rem', color: '#64748b' }}>Estimated Time:</span>
            <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>
              {route.timeDays !== undefined
                ? route.timeDays === 0
                  ? 'BLOCKED'
                  : `${route.timeDays} days (${route.timeHours} hrs)`
                : `${route.timeHours} hrs`}
            </div>
          </div>
          <div>
            <span style={{ fontSize: '0.72rem', color: '#64748b' }}>Fuel Index (Relative):</span>
            <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>{route.fuelIndex?.toLocaleString()}</div>
          </div>
          <div>
            <span style={{ fontSize: '0.72rem', color: '#64748b' }}>Calculated Risk Level:</span>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: route.color }}>
              {route.riskPercent}% {getStarRating(route.riskPercent)}
            </div>
          </div>
        </div>

        <div>
          <h4 style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '6px', color: '#334155' }}>
            Waypoints ({route.coordinates ? route.coordinates.length : 0})
          </h4>
          <div style={{ maxHeight: '120px', overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '8px', fontSize: '0.76rem', fontFamily: 'monospace' }}>
            {route.coordinates?.map((coord, idx) => (
              <div key={idx} style={{ padding: '2px 0', borderBottom: idx < route.coordinates.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                WP-{idx + 1}: [{coord[0].toFixed(3)}, {coord[1].toFixed(3)}]
              </div>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px', marginTop: '6px' }}>
          <button
            className="btn-xs btn-primary"
            style={{ flex: 1, padding: '10px', fontSize: '0.86rem' }}
            onClick={() => {
              if (onSelectRoute) onSelectRoute(route.id);
              onClose();
            }}
          >
            ✓ Confirm & Select This Route
          </button>
          <button
            className="btn-xs"
            style={{ padding: '10px 16px', fontSize: '0.86rem' }}
            onClick={onClose}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default RouteDetailsModal;
