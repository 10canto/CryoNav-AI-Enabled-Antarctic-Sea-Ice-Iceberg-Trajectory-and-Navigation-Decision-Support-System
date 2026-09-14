import { useEffect, useState } from 'react';

/**
 * WaitingModal — shown when Route C (Fuel-Efficient) is selected in Scenario 3.
 *
 * Tells the story: ship has paused at the 62°S holding point while ICE-047
 * drifts past, then will proceed safely to Maitri Station.
 *
 * Props:
 *   show         — boolean
 *   route        — route object (has waitHours, waitReason from scenarioDataRequirements)
 *   onAcknowledge — callback
 */
const WaitingModal = ({ show, route, onAcknowledge }) => {
  const [phase, setPhase] = useState('waiting'); // 'waiting' → 'clearing' → 'safe'

  useEffect(() => {
    if (!show) { setPhase('waiting'); return; }

    // Animate through phases: waiting 2 s → clearing 2 s → safe (stays)
    setPhase('waiting');
    const t1 = window.setTimeout(() => setPhase('clearing'), 2000);
    const t2 = window.setTimeout(() => setPhase('safe'),     4000);
    return () => { window.clearTimeout(t1); window.clearTimeout(t2); };
  }, [show]);

  if (!show) return null;

  const waitHours  = route?.waitHours  ?? 6;
  const waitReason = route?.waitReason ?? 'Holding position while iceberg drifts past';

  const phaseConfig = {
    waiting: {
      icon:    '⏸',
      title:   'HOLDING POSITION',
      sub:     'Route C — Waiting Protocol Active',
      color:   '#f97316',
      bg:      'linear-gradient(135deg,#431407,#7c2d12)',
      btnText: null,            // button disabled while animating
    },
    clearing: {
      icon:    '🔭',
      title:   'ICEBERG CLEARING…',
      sub:     'ICE-047 drifting past 13°E corridor',
      color:   '#f59e0b',
      bg:      'linear-gradient(135deg,#422006,#92400e)',
      btnText: null,
    },
    safe: {
      icon:    '✅',
      title:   'CORRIDOR CLEAR — RESUMING',
      sub:     'Route C — Proceeding safely to Maitri Station',
      color:   '#10b981',
      bg:      'linear-gradient(135deg,#064e3b,#065f46)',
      btnText: 'RESUME VOYAGE',
    },
  };

  const cfg = phaseConfig[phase];

  return (
    <div className="modal-backdrop">
      <div
        className="emergency-modal-card"
        style={{
          borderColor: cfg.color,
          boxShadow: `0 8px 32px ${cfg.color}44, 0 2px 8px rgba(0,0,0,0.6)`,
        }}
      >
        {/* ── Header ── */}
        <div className="emergency-header" style={{ background: cfg.bg }}>
          <div className="emergency-title" style={{ color: cfg.color, fontSize: '1.1rem' }}>
            {cfg.icon}  {cfg.title}
          </div>
          <div className="emergency-subtitle" style={{ color: '#cbd5e1' }}>
            {cfg.sub}
          </div>
        </div>

        {/* ── Waiting details ── */}
        <div
          className="emergency-details-box"
          style={{ borderColor: cfg.color, background: `${cfg.color}10` }}
        >
          <div>
            <strong style={{ color: cfg.color }}>Strategy:</strong>{' '}
            <span style={{ color: '#f1f5f9' }}>Holding-point wait — no collision risk</span>
          </div>
          <div>
            <strong style={{ color: cfg.color }}>Holding position:</strong>{' '}
            <span style={{ color: '#f1f5f9' }}>62°S — safe distance from ICE-047</span>
          </div>
          <div>
            <strong style={{ color: cfg.color }}>Estimated wait:</strong>{' '}
            <span style={{ color: '#f1f5f9' }}>~{waitHours} hours</span>
          </div>
          <div>
            <strong style={{ color: cfg.color }}>Reason:</strong>{' '}
            <span style={{ color: '#f1f5f9' }}>{waitReason}</span>
          </div>
          {phase === 'safe' && (
            <div style={{ marginTop: 6 }}>
              <strong style={{ color: '#6ee7b7' }}>ICE-047 status:</strong>{' '}
              <span style={{ color: '#f1f5f9' }}>Drifted clear — corridor open ✅</span>
            </div>
          )}
        </div>

        {/* ── Animated status bar ── */}
        <div
          className="emergency-sat-box"
          style={{ borderColor: cfg.color, color: cfg.color, background: `${cfg.color}10` }}
        >
          {phase === 'waiting'  && '⏸  Ship stationary at holding point — monitoring iceberg drift…'}
          {phase === 'clearing' && '🔭  ICE-047 passing through 13°E corridor — clearance in progress…'}
          {phase === 'safe'     && '✅  Corridor clear. CryoNav AI authorising route resumption.'}
        </div>

        {/* ── Progress steps ── */}
        <div
          className="emergency-action-box"
          style={{ borderColor: cfg.color, background: `${cfg.color}08`, color: '#cbd5e1' }}
        >
          <strong style={{ color: cfg.color }}>Route C — Waiting Protocol</strong>
          <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 5 }}>
            {[
              { step: '1', label: 'Slow to 4 knots · approach holding point at 62°S', done: true },
              { step: '2', label: `Hold position · wait ~${waitHours} hrs for ICE-047 to drift past`, done: phase !== 'waiting' },
              { step: '3', label: 'Satellite confirms corridor clear · full speed resumed', done: phase === 'safe' },
              { step: '4', label: 'Proceed to Maitri Station · safe arrival', done: phase === 'safe' },
            ].map(({ step, label, done }) => (
              <div key={step} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', fontSize: '0.75rem' }}>
                <span style={{
                  flexShrink: 0, width: 18, height: 18, borderRadius: '50%',
                  background: done ? cfg.color : '#374151',
                  color: done ? '#fff' : '#6b7280',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontWeight: 700, fontSize: '0.65rem',
                }}>
                  {done ? '✓' : step}
                </span>
                <span style={{ color: done ? '#e2e8f0' : '#6b7280' }}>{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── Action button ── */}
        <button
          className="btn-acknowledge"
          style={{
            background: phase === 'safe' ? cfg.color : '#374151',
            cursor: phase === 'safe' ? 'pointer' : 'not-allowed',
            color: phase === 'safe' ? '#fff' : '#6b7280',
          }}
          onClick={phase === 'safe' ? onAcknowledge : undefined}
          disabled={phase !== 'safe'}
        >
          {phase === 'safe' ? cfg.btnText : 'WAITING FOR ICEBERG TO CLEAR…'}
        </button>
      </div>
    </div>
  );
};

export default WaitingModal;
