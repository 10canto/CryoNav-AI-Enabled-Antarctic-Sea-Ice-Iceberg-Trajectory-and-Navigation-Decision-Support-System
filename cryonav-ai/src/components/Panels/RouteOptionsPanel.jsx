import { useState } from 'react';
import { getStarRating } from '../../utils/riskCalculator';
import { ROUTE_REASONING, ROUTE_SUBTITLES } from '../../services/scenarioDataRequirements';

// ─── Inline AI reasoning tooltip ─────────────────────────────────────────────
const ReasoningTooltip = ({ text, color }) => {
  const [open, setOpen] = useState(false);

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <button
        type="button"
        title="Show AI reasoning"
        onClick={(e) => { e.stopPropagation(); setOpen((v) => !v); }}
        style={{
          background: 'none',
          border: `1px solid ${color}55`,
          borderRadius: 4,
          color,
          fontSize: '0.65rem',
          fontWeight: 700,
          padding: '1px 6px',
          cursor: 'pointer',
          letterSpacing: '0.03em',
        }}
      >
        AI {open ? '▲' : '▼'}
      </button>

      {open && (
        <div
          onClick={(e) => e.stopPropagation()}
          style={{
            position: 'absolute',
            bottom: 'calc(100% + 6px)',
            left: 0,
            zIndex: 9999,
            background: 'rgba(15,23,42,0.97)',
            border: `1px solid ${color}44`,
            borderRadius: 8,
            padding: '10px 12px',
            width: 290,
            fontSize: '0.72rem',
            lineHeight: 1.55,
            color: '#cbd5e1',
            boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
            backdropFilter: 'blur(8px)',
          }}
        >
          <div style={{ fontWeight: 800, color, marginBottom: 5, fontSize: '0.7rem', letterSpacing: '0.05em' }}>
            🤖 AI REASONING
          </div>
          {text}
        </div>
      )}
    </div>
  );
};

// ─── Main panel ───────────────────────────────────────────────────────────────
const RouteOptionsPanel = ({ routes = [], selectedRoute, onRouteSelect, onShowDetails, scenario = 0 }) => {
  return (
    <div className="route-panel">
      <div className="panel-title">Route options</div>
      <div className="route-cards-list">
        {routes.map((route) => {
          const blocked = route.timeDays === 0 || route.riskPercent >= 90;
          const routeKey = route.id || route.type;

          // Get AI reasoning + subtitle for this route in this scenario
          const reasoning = ROUTE_REASONING[scenario]?.[routeKey];
          const subtitle  = ROUTE_SUBTITLES[scenario]?.[routeKey];

          // Risk badge colour
          const riskColor =
            route.riskPercent >= 75 ? '#ef4444' :
            route.riskPercent >= 40 ? '#f97316' :
            route.riskPercent >= 15 ? '#f59e0b' :
            '#10b981';

          return (
            <div
              key={routeKey}
              className={`route-card ${selectedRoute === routeKey ? 'selected' : ''} ${blocked ? 'blocked' : ''}`}
              onClick={() => !blocked && onRouteSelect && onRouteSelect(routeKey)}
            >
              {/* ── Header ── */}
              <div className="route-card-header">
                <div className="route-title-badge" style={{ flex: 1, minWidth: 0 }}>
                  <span className="route-indicator-dot" style={{ background: route.color || '#64748b', flexShrink: 0 }} />
                  <span style={{ fontWeight: 700, fontSize: '0.78rem' }}>{route.name || route.type}</span>
                </div>
                {route.isSafest           && <span className="feature-tag">Safest</span>}
                {route.isFastest && !blocked && <span className="feature-tag">Fastest</span>}
                {route.isCheapest && !blocked && <span className="feature-tag">Fuel</span>}
                {blocked && <span className="feature-tag" style={{ background: '#ef444422', color: '#ef4444', border: '1px solid #ef444444' }}>BLOCKED</span>}
              </div>

              {/* ── One-liner subtitle ── */}
              {subtitle && (
                <div style={{
                  fontSize: '0.68rem',
                  color: blocked ? '#ef4444' : route.color || '#64748b',
                  fontStyle: 'italic',
                  marginBottom: 5,
                  paddingLeft: 2,
                  opacity: 0.9,
                }}>
                  {subtitle}
                </div>
              )}

              {/* ── Stats grid ── */}
              <div className="route-stats-grid">
                <div className="stat-item">
                  <span className="label">Distance</span>
                  <span className="value">{route.distanceKm?.toLocaleString()} km</span>
                </div>
                <div className="stat-item">
                  <span className="label">Time</span>
                  <span className="value">{blocked ? '—' : `${route.timeDays} d`}</span>
                </div>
                <div className="stat-item">
                  <span className="label">Fuel</span>
                  <span className="value">{blocked ? '—' : `${Math.round((route.fuelLiters || 0) / 1000)}K L`}</span>
                </div>
                <div className="stat-item">
                  <span className="label">Risk</span>
                  <span className="value" style={{ color: riskColor, fontWeight: 700 }}>
                    {route.riskPercent}%
                  </span>
                </div>
              </div>

              {/* ── Actions row ── */}
              <div className="route-actions" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span className="stars-rating">{getStarRating(route.riskPercent)}</span>
                  {reasoning && <ReasoningTooltip text={reasoning} color={route.color || '#64748b'} />}
                </div>

                <div className="btn-group">
                  <button
                    type="button"
                    className="btn-xs"
                    onClick={(e) => { e.stopPropagation(); onShowDetails && onShowDetails(route); }}
                  >
                    Details
                  </button>
                  <button
                    type="button"
                    className={`btn-xs ${selectedRoute === routeKey ? 'btn-primary' : ''}`}
                    disabled={blocked}
                    onClick={(e) => { e.stopPropagation(); if (!blocked) onRouteSelect && onRouteSelect(routeKey); }}
                  >
                    {selectedRoute === routeKey ? 'Selected' : 'Select'}
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default RouteOptionsPanel;
