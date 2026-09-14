import { getPulseAnimationClass } from '../../utils/riskCalculator';

// Maps status strings → display config
const STATUS_CONFIG = {
  GREEN:     { color: '#10b981', bg: 'rgba(16,185,129,0.12)', border: 'rgba(16,185,129,0.35)', dot: '🟢', label: 'GREEN — Safe'        },
  YELLOW:    { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', border: 'rgba(245,158,11,0.35)', dot: '🟡', label: 'YELLOW — Caution'     },
  ORANGE:    { color: '#f97316', bg: 'rgba(249,115,22,0.12)', border: 'rgba(249,115,22,0.35)', dot: '🟠', label: 'ORANGE — Warning'     },
  RED:       { color: '#ef4444', bg: 'rgba(239,68,68,0.12)',  border: 'rgba(239,68,68,0.35)',  dot: '🔴', label: 'RED — Emergency'      },
  // legacy fallbacks
  SAFE:      { color: '#10b981', bg: 'rgba(16,185,129,0.12)', border: 'rgba(16,185,129,0.35)', dot: '🟢', label: 'SAFE'                 },
  CAUTION:   { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', border: 'rgba(245,158,11,0.35)', dot: '🟡', label: 'CAUTION'              },
  WARNING:   { color: '#f97316', bg: 'rgba(249,115,22,0.12)', border: 'rgba(249,115,22,0.35)', dot: '🟠', label: 'WARNING'              },
  EMERGENCY: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)',  border: 'rgba(239,68,68,0.35)',  dot: '🔴', label: 'EMERGENCY'            },
};

// Per-route override messages shown in Scenario 3 instead of the generic RED message
const ROUTE_OVERRIDE = {
  safest: {
    status:  'GREEN',
    message: 'Route A — Eastern Detour active. Iceberg avoided. All crew safe.',
  },
  fuel: {
    status:  'ORANGE',
    message: 'Route C — Holding point active at 62°S. Waiting for ICE-047 to drift clear.',
  },
};

/**
 * RiskStatusPanel
 *
 * Props:
 *   risk          — riskAssessment object from scenario data
 *   selectedRoute — 'safest' | 'fastest' | 'fuel' | …
 *                   Used in Scenario 3 to override the displayed status so that
 *                   Route A never shows RED and Route C shows ORANGE (warning) not RED.
 */
const RiskStatusPanel = ({ risk, selectedRoute }) => {
  if (!risk) {
    return <div className="risk-panel">Loading risk data…</div>;
  }

  const rawStatus = risk.status || 'GREEN';
  const isEmergencyScenario = rawStatus === 'RED' || rawStatus === 'EMERGENCY';

  // Apply per-route override when in Scenario 3 (RED/EMERGENCY base status)
  const override = isEmergencyScenario ? ROUTE_OVERRIDE[selectedRoute] : null;

  const status  = override?.status  ?? rawStatus;
  const message = override?.message ?? risk.message;

  const cfg   = STATUS_CONFIG[status] || STATUS_CONFIG.GREEN;
  const pulse = getPulseAnimationClass(status);

  const ice       = risk.iceConcentration ?? 0;
  // Show 0% collision risk for Route A in Scenario 3 — it successfully avoided the iceberg
  const collision = (isEmergencyScenario && selectedRoute === 'safest')
    ? 0
    : (isEmergencyScenario && selectedRoute === 'fuel')
      ? 18   // Route C waiting strategy — reduced risk while holding
      : (risk.collisionRisk ?? 0);

  return (
    <div className="risk-panel">
      <div className="risk-header">
        <div className="panel-title">Risk status</div>
      </div>

      {/* ── Hero status badge ── */}
      <div
        className={`risk-display-hero ${pulse}`}
        style={{
          background: cfg.bg,
          border: `1px solid ${cfg.border}`,
          borderRadius: 10,
          padding: '10px 12px',
          marginBottom: 10,
          display: 'flex',
          alignItems: 'center',
          gap: 12,
        }}
      >
        <div
          className={`risk-circle ${pulse}`}
          style={{ backgroundColor: cfg.color, flexShrink: 0 }}
        >
          ●
        </div>

        <div className="risk-status-info" style={{ flex: 1, minWidth: 0 }}>
          <div
            className="risk-status-label"
            style={{ color: cfg.color, fontWeight: 800, fontSize: '0.95rem', letterSpacing: '0.04em' }}
          >
            {cfg.dot} {cfg.label}
          </div>

          {message && (
            <div
              style={{
                fontSize: '0.72rem',
                color: cfg.color,
                opacity: 0.85,
                marginTop: 2,
                lineHeight: 1.35,
                fontWeight: 600,
              }}
            >
              {message}
            </div>
          )}

          <div className="risk-status-sub" style={{ fontSize: '0.68rem', marginTop: 3 }}>
            Ice · berg proximity · collision likelihood
          </div>
        </div>
      </div>

      {/* ── Progress bars ── */}
      <div className="metrics-container">
        <div className="progress-metric-block">
          <div className="progress-metric-head">
            <span>Ice concentration</span>
            <span>{ice}%</span>
          </div>
          <div className="progress-bar-bg">
            <div
              className="progress-bar-fill"
              style={{ width: `${ice}%`, backgroundColor: cfg.color }}
            />
          </div>
        </div>

        <div className="progress-metric-block">
          <div className="progress-metric-head">
            <span>Collision risk</span>
            <span>{collision}%</span>
          </div>
          <div className="progress-bar-bg">
            <div
              className="progress-bar-fill"
              style={{
                width: `${collision}%`,
                backgroundColor: collision > 50 ? '#ef4444' : cfg.color,
              }}
            />
          </div>
        </div>
      </div>

      {/* ── Condition pills ── */}
      <div className="conditions-row">
        <div className="condition-pill">
          <span>Nearest berg</span>
          <span className="val">
            {risk.nearestIceberg != null ? `${risk.nearestIceberg} km` : 'None'}
          </span>
        </div>
        <div className="condition-pill">
          <span>Temp / wind</span>
          <span className="val">
            {risk.temperature}°C · {risk.windSpeed} km/h {risk.windDirection}
          </span>
        </div>
        <div className="condition-pill">
          <span>Visibility</span>
          <span className="val">{risk.visibility}</span>
        </div>
      </div>
    </div>
  );
};

export default RiskStatusPanel;
