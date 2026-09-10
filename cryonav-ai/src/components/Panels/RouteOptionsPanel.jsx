import { getStarRating } from '../../utils/riskCalculator';

const RouteOptionsPanel = ({ routes = [], selectedRoute, onRouteSelect, onShowDetails }) => {
  return (
    <div className="route-panel">
      <div className="panel-title">Route options</div>
      <div className="route-cards-list">
        {routes.map((route) => {
          const blocked = route.timeDays === 0 || route.riskPercent >= 90;
          return (
            <div
              key={route.id || route.type}
              className={`route-card ${selectedRoute === route.id || selectedRoute === route.type ? 'selected' : ''} ${blocked ? 'blocked' : ''}`}
              onClick={() => !blocked && onRouteSelect && onRouteSelect(route.id || route.type)}
            >
              <div className="route-card-header">
                <div className="route-title-badge">
                  <span className="route-indicator-dot" style={{ background: route.color || '#64748b' }} />
                  {route.name || route.type}
                </div>
                {route.isSafest && <span className="feature-tag">Safest</span>}
                {route.isFastest && !blocked && <span className="feature-tag">Fastest</span>}
                {route.isCheapest && !blocked && <span className="feature-tag">Fuel</span>}
                {blocked && <span className="feature-tag">UNAVAILABLE</span>}
              </div>

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
                  <span className="value" style={{ color: route.color }}>
                    {route.riskPercent}%
                  </span>
                </div>
              </div>

              <div className="route-actions">
                <span className="stars-rating">{getStarRating(route.riskPercent)}</span>
                <div className="btn-group">
                  <button
                    type="button"
                    className="btn-xs"
                    onClick={(e) => {
                      e.stopPropagation();
                      onShowDetails && onShowDetails(route);
                    }}
                  >
                    Details
                  </button>
                  <button
                    type="button"
                    className={`btn-xs ${selectedRoute === (route.id || route.type) ? 'btn-primary' : ''}`}
                    disabled={blocked}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (!blocked) onRouteSelect && onRouteSelect(route.id || route.type);
                    }}
                  >
                    {selectedRoute === (route.id || route.type) ? 'Selected' : 'Select'}
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
