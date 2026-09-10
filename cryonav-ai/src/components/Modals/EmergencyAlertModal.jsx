import { useEffect, useState } from 'react';
import { DEMO_CONFIG } from '../../config';

const EmergencyAlertModal = ({ show, riskData, onAcknowledge }) => {
  const [transmitting, setTransmitting] = useState(true);

  useEffect(() => {
    if (!show) return;
    setTransmitting(true);

    const beepTimers = [];
    if (DEMO_CONFIG.ENABLE_SOUNDS) {
      [0, 350, 700].forEach((delay) => {
        beepTimers.push(window.setTimeout(() => new Audio('/sounds/alert.mp3').play().catch(() => {}), delay));
      });
    }

    const timer = window.setTimeout(() => setTransmitting(false), 2000);
    return () => {
      window.clearTimeout(timer);
      beepTimers.forEach(window.clearTimeout);
    };
  }, [show]);

  if (!show) return null;

  return (
    <div className="modal-backdrop">
      <div className="emergency-modal-card">
        <div className="emergency-header">
          <div className="emergency-title">EMERGENCY ALERT</div>
          <div className="emergency-subtitle">Ice-shelf calving · channel blocked</div>
        </div>

        <div className="emergency-details-box">
          <div>
            <strong>Nearest iceberg:</strong> {riskData?.metrics?.nearest_iceberg_km ?? '—'} km
          </div>
          <div>
            <strong>Collision probability:</strong> {riskData?.metrics?.collision_risk_percent ?? '—'}%
          </div>
          <div>
            <strong>Ice concentration:</strong> {riskData?.metrics?.ice_concentration ?? '—'}%
          </div>
        </div>

        <div className="emergency-sat-box">
          {transmitting ? 'Transmitting via satellite…' : 'Alerts dispatched: Bridge · MCC · MRCC'}
        </div>

        <div className="emergency-action-box">
          <strong>Recommended action</strong>
          Route A icebreaker escort convoy. Do not attempt Routes B or C.
        </div>

        <button className="btn-acknowledge" onClick={onAcknowledge} disabled={transmitting}>
          {transmitting ? 'TRANSMITTING…' : 'ACKNOWLEDGE ALERT'}
        </button>
      </div>
    </div>
  );
};

export default EmergencyAlertModal;
