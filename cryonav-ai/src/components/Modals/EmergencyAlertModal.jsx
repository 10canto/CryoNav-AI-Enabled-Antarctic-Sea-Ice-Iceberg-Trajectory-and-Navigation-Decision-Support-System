import { useEffect, useState } from 'react';
import { DEMO_CONFIG } from '../../config';

/**
 * EmergencyAlertModal
 *
 * Props:
 *   show          — boolean
 *   riskData      — { level, metrics: { nearest_iceberg_km, collision_risk_percent, ... } }
 *   selectedRoute — 'safest' | 'fastest' | 'fuel' | 'alternative_1' | 'alternative_2'
 *   onAcknowledge — callback
 */
const EmergencyAlertModal = ({ show, riskData, selectedRoute, onAcknowledge }) => {
  const [transmitting, setTransmitting] = useState(true);

  useEffect(() => {
    if (!show) return;
    setTransmitting(true);

    const beepTimers = [];
    if (DEMO_CONFIG.ENABLE_SOUNDS) {
      [0, 350, 700].forEach((delay) => {
        beepTimers.push(
          window.setTimeout(() => new Audio('/sounds/alert.mp3').play().catch(() => {}), delay),
        );
      });
    }

    const timer = window.setTimeout(() => setTransmitting(false), 2000);
    return () => {
      window.clearTimeout(timer);
      beepTimers.forEach(window.clearTimeout);
    };
  }, [show]);

  if (!show) return null;

  // Route B and C have high iceberg collision chances
  const isRiskyRoute =
    selectedRoute === 'fastest' ||
    selectedRoute === 'fuel' ||
    selectedRoute === 'alternative_1' ||
    selectedRoute === 'alternative_2';

  const routeLabel =
    selectedRoute === 'fastest'      ? 'Route B — Direct Southern'
    : selectedRoute === 'fuel'       ? 'Route C — Fuel-Efficient'
    : selectedRoute === 'alternative_1' ? 'Coastal Hugging Route'
    : selectedRoute === 'alternative_2' ? 'Middle Balance Route'
    : 'Current Route';

  return (
    <div className="modal-backdrop">
      <div className="emergency-modal-card">
        <div className="emergency-header">
          <div className="emergency-title">
            {isRiskyRoute ? '⚠️  ICEBERG COLLISION WARNING' : '🚨  EMERGENCY ALERT'}
          </div>
          <div className="emergency-subtitle">
            {isRiskyRoute
              ? `${routeLabel} passes through active iceberg field`
              : 'Ice-shelf calving · channel blocked'}
          </div>
        </div>

        <div className="emergency-details-box">
          <div>
            <strong>Nearest iceberg:</strong>{' '}
            {riskData?.metrics?.nearest_iceberg_km ?? '—'} km
          </div>
          <div>
            <strong>Collision probability:</strong>{' '}
            {isRiskyRoute
              ? `${riskData?.metrics?.collision_risk_percent ?? 87}%`
              : `${riskData?.metrics?.collision_risk_percent ?? '—'}%`}
          </div>
          <div>
            <strong>Ice concentration:</strong>{' '}
            {riskData?.metrics?.ice_concentration ?? '—'}%
          </div>
          {isRiskyRoute && (
            <div>
              <strong>Route risk level:</strong>{' '}
              <span style={{ color: '#ef4444', fontWeight: 700 }}>CRITICAL</span>
            </div>
          )}
        </div>

        <div className="emergency-sat-box">
          {transmitting ? 'Transmitting via satellite…' : 'Alerts dispatched: Bridge · MCC · MRCC'}
        </div>

        <div className="emergency-action-box">
          <strong>Recommended action</strong>
          <br />
          {isRiskyRoute
            ? `⚠️  Switch to Route A immediately. ${routeLabel} has a ${
                riskData?.metrics?.collision_risk_percent ?? 87
              }% iceberg collision probability. Route A provides a safe eastern detour.`
            : 'Route A icebreaker escort convoy. Do not attempt Routes B or C.'}
        </div>

        <button
          className="btn-acknowledge"
          onClick={onAcknowledge}
          disabled={transmitting}
        >
          {transmitting ? 'TRANSMITTING…' : 'ACKNOWLEDGE ALERT'}
        </button>
      </div>
    </div>
  );
};

export default EmergencyAlertModal;
