import { getPulseAnimationClass, getRiskColor } from '../../utils/riskCalculator';

const RiskStatusPanel = ({ risk }) => {
  if (!risk) {
    return <div className="risk-panel">Loading risk data…</div>;
  }

  const level = risk.status || 'SAFE';
  const color = getRiskColor(level);
  const pulse = getPulseAnimationClass(level);
  const ice = risk.iceConcentration ?? 0;
  const collision = risk.collisionRisk ?? 0;

  return (
    <div className="risk-panel">
      <div className="risk-header">
        <div className="panel-title">Risk status</div>
      </div>

      <div className="risk-display-hero">
        <div className={`risk-circle ${pulse}`} style={{ backgroundColor: color }}>
          ●
        </div>
        <div className="risk-status-info">
          <div className="risk-status-label" style={{ color }}>
            {level}
          </div>
          <div className="risk-status-sub">Ice · berg proximity · collision likelihood</div>
        </div>
      </div>

      <div className="metrics-container">
        <div className="progress-metric-block">
          <div className="progress-metric-head">
            <span>Ice concentration</span>
            <span>{ice}%</span>
          </div>
          <div className="progress-bar-bg">
            <div className="progress-bar-fill" style={{ width: `${ice}%`, backgroundColor: color }} />
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
              style={{ width: `${collision}%`, backgroundColor: collision > 50 ? '#ef4444' : color }}
            />
          </div>
        </div>
      </div>

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
