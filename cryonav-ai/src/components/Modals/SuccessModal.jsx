import { useEffect, useState } from 'react';
import { DEMO_CONFIG } from '../../config';

/**
 * SuccessModal — shown when the ship reaches Maitri Station safely on Route A.
 */
const SuccessModal = ({ show, routeName = 'Route A', onAcknowledge }) => {
  const [animating, setAnimating] = useState(true);

  useEffect(() => {
    if (!show) return;
    setAnimating(true);
    const t = window.setTimeout(() => setAnimating(false), 2200);
    return () => window.clearTimeout(t);
  }, [show]);

  if (!show) return null;

  return (
    <div className="modal-backdrop">
      <div
        className="emergency-modal-card"
        style={{
          borderColor: '#10b981',
          boxShadow: '0 0 40px rgba(16,185,129,0.35)',
        }}
      >
        {/* Header */}
        <div
          className="emergency-header"
          style={{ background: 'linear-gradient(135deg,#064e3b,#065f46)' }}
        >
          <div
            className="emergency-title"
            style={{ color: '#6ee7b7', fontSize: '1.4rem' }}
          >
            {animating ? '📡 TRANSMITTING…' : '✅ DESTINATION REACHED'}
          </div>
          <div className="emergency-subtitle" style={{ color: '#a7f3d0' }}>
            R/V Bharati Pioneer — Maitri Research Station, Antarctica
          </div>
        </div>

        {/* Stats */}
        <div
          className="emergency-details-box"
          style={{ borderColor: '#10b981', background: 'rgba(16,185,129,0.06)' }}
        >
          <div>
            <strong style={{ color: '#6ee7b7' }}>Route taken:</strong>{' '}
            <span style={{ color: '#f1f5f9' }}>{routeName} — Eastern Ice-Avoidance</span>
          </div>
          <div>
            <strong style={{ color: '#6ee7b7' }}>All icebergs avoided:</strong>{' '}
            <span style={{ color: '#f1f5f9' }}>100% clearance maintained</span>
          </div>
          <div>
            <strong style={{ color: '#6ee7b7' }}>Crew status:</strong>{' '}
            <span style={{ color: '#f1f5f9' }}>All 47 crew safe</span>
          </div>
          <div>
            <strong style={{ color: '#6ee7b7' }}>Cargo integrity:</strong>{' '}
            <span style={{ color: '#f1f5f9' }}>Research equipment intact</span>
          </div>
        </div>

        {/* Satellite confirmation */}
        <div
          className="emergency-sat-box"
          style={{ borderColor: '#10b981', color: '#6ee7b7', background: 'rgba(16,185,129,0.08)' }}
        >
          {animating
            ? 'Transmitting arrival confirmation via satellite…'
            : 'Arrival confirmed: NCPOR Goa · India MCC · Antarctic Treaty Office'}
        </div>

        {/* CryoNav AI note */}
        <div
          className="emergency-action-box"
          style={{ borderColor: '#10b981', background: 'rgba(16,185,129,0.06)', color: '#a7f3d0' }}
        >
          <strong style={{ color: '#6ee7b7' }}>CryoNav AI — Mission Summary</strong>
          <br />
          Route A successfully avoided all iceberg hazards detected during transit.
          AI-guided navigation reduced collision risk from 87% to 0%.
        </div>

        <button
          className="btn-acknowledge"
          style={{
            background: animating ? '#374151' : '#10b981',
            cursor: animating ? 'not-allowed' : 'pointer',
          }}
          onClick={onAcknowledge}
          disabled={animating}
        >
          {animating ? 'CONFIRMING ARRIVAL…' : 'MISSION COMPLETE'}
        </button>
      </div>
    </div>
  );
};

export default SuccessModal;
