import { currentStep, useStore } from '../store/useStore';
import type { RiskLevel } from '../domain/types';
import { levelFromScore } from '../utils/risk';

const SeverityMeter = ({ level }: { level: RiskLevel }) => {
  const segments = ['GREEN', 'YELLOW', 'ORANGE', 'RED'];
  const activeCount = segments.indexOf(level) + 1;
  
  return (
    <div className="severity-meter">
      {segments.map((_, i) => (
        <div
          key={i}
          className="severity-segment"
          data-active={i < activeCount}
        />
      ))}
    </div>
  );
};

export function RiskCard() {
  const step = useStore((s) => currentStep(s));
  const selectedRouteId = useStore((s) => s.selectedRouteId);
  const loading = useStore((s) => s.loading);
  const offline = useStore((s) => s.offline);
  const mode = useStore((s) => s.mode);
  
  if (loading) {
    return (
      <div className="risk-card">
        <h2>Risk Assessment</h2>
        <div className="state-msg loading">
          <span className="spinner" />
          Loading...
        </div>
      </div>
    );
  }

  if (!step) {
    return (
      <div className="risk-card">
        <h2>Risk Assessment</h2>
        <div className="state-msg empty">
          No data available.
        </div>
      </div>
    );
  }

  const selectedRoute = step.routes.find((r) => r.id === selectedRouteId);
  const originalRoute = step.routes.find((r) => r.id === step.selected_route_id);
  
  // Show original plan risk if it differs from selected
  const showOriginal = originalRoute && selectedRoute && originalRoute.id !== selectedRoute.id;

  // Compute risk levels from scores
  const selectedLevel = selectedRoute ? levelFromScore(selectedRoute.risk_score) : 'GREEN';
  const originalLevel = originalRoute ? levelFromScore(originalRoute.risk_score) : 'GREEN';

  return (
    <div className="risk-card">
      <h2>Risk Assessment</h2>
      
      {mode === 'live' && offline && (
        <div className="state-msg offline">
          Backend offline. Showing cached snapshot.
        </div>
      )}
      
      {showOriginal && (
        <div className="risk-row">
          <span className="risk-label">Original plan:</span>
          <div className={`risk-badge ${originalLevel}`}>
            <span>{originalLevel}</span>
            <SeverityMeter level={originalLevel} />
          </div>
        </div>
      )}
      
      <div className="risk-row">
        <span className="risk-label">Selected route:</span>
        <div className={`risk-badge ${selectedLevel}`}>
          <span>{selectedLevel}</span>
          <SeverityMeter level={selectedLevel} />
        </div>
      </div>
      
      {selectedRoute && selectedRoute.reasons && selectedRoute.reasons.length > 0 && (
        <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--text-muted)' }}>
          {selectedRoute.reasons.map((reason, i) => (
            <div key={i} style={{ marginBottom: '4px' }}>• {reason}</div>
          ))}
        </div>
      )}
    </div>
  );
}
