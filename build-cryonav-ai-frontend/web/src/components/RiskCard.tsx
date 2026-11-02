import { currentStep, useStore } from '../store/useStore';
import type { RiskLevel } from '../domain/types';

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
  
  if (!step) return null;

  const selectedRoute = step.routes.find((r) => r.id === selectedRouteId);
  const originalRoute = step.routes.find((r) => r.id === step.selected_route_id);
  
  // Show original plan risk if it differs from selected
  const showOriginal = originalRoute && selectedRoute && originalRoute.id !== selectedRoute.id;

  return (
    <div className="risk-card">
      <h2>Risk Assessment</h2>
      
      {showOriginal && (
        <div className="risk-row">
          <span className="risk-label">Original plan:</span>
          <div className={`risk-badge ${originalRoute.risk_level}`}>
            <span>{originalRoute.risk_level}</span>
            <SeverityMeter level={originalRoute.risk_level} />
          </div>
        </div>
      )}
      
      <div className="risk-row">
        <span className="risk-label">Selected route:</span>
        <div className={`risk-badge ${selectedRoute?.risk_level || 'GREEN'}`}>
          <span>{selectedRoute?.risk_level || 'GREEN'}</span>
          <SeverityMeter level={selectedRoute?.risk_level || 'GREEN'} />
        </div>
      </div>
    </div>
  );
}
