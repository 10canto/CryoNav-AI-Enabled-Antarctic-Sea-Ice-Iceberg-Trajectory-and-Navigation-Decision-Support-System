// TrajectoryLines — iceberg drift visualisation v2
import { useMemo } from 'react';
import { Polyline, CircleMarker, Popup, Tooltip } from 'react-leaflet';

// ─── Risk colour / weight helpers ────────────────────────────────────────────

const RISK_COLORS = {
  safe:     '#10b981',
  low:      '#10b981',
  moderate: '#f97316',
  high:     '#ef4444',
};

const RISK_WEIGHTS = {
  safe:     2,
  low:      2,
  moderate: 3,
  high:     4,
};

const getRiskColor  = (risk) => RISK_COLORS[risk]  || '#6b7280';
const getRiskWeight = (risk) => RISK_WEIGHTS[risk] || 2;

// ─── Scenario-index fallback colour (if risk_level absent) ───────────────────
const getScenarioColor = (scenario) => {
  if (scenario <= 1) return '#10b981';
  if (scenario === 2) return '#f97316';
  return '#ef4444';
};

// ─── Normalise each trajectory point ─────────────────────────────────────────
// Handles both current format { time_hours, latitude, longitude }
// and legacy format { time, position: { lat, lon }, uncertainty_radius_km }
const normalisePoint = (pt) => ({
  time_hours:         Number.isFinite(pt.time_hours)
                        ? pt.time_hours
                        : parseInt(pt.time, 10),
  latitude:           pt.latitude  ?? pt.position?.lat  ?? 0,
  longitude:          pt.longitude ?? pt.position?.lon  ?? 0,
  uncertainty_km:     pt.uncertainty_km ?? pt.uncertainty_radius_km ?? 0,
  drift_speed_kmh:    pt.drift_speed_kmh,
  drift_direction_deg: pt.drift_direction_deg,
  timestamp:          pt.timestamp,
});

const TIME_LABELS = { 6: '6h', 12: '12h', 24: '24h', 48: '48h', 72: '72h' };

// ─── Component ────────────────────────────────────────────────────────────────

/**
 * TrajectoryLines
 *
 * Renders iceberg drift trajectory paths on the Leaflet map.
 *
 * Props:
 *   predictions  – Array of prediction objects from predictions.json
 *   scenario     – Current scenario index (0-3) for fallback colour coding
 *   visible      – Boolean: show/hide the layer
 */
const TrajectoryLines = ({ predictions = [], scenario = 0, visible = true }) => {
  const layers = useMemo(() => {
    if (!visible || !predictions?.length) return [];

    return predictions.flatMap((pred) => {
      const raw = pred.trajectory;
      if (!raw?.length) return [];

      const points  = raw.map(normalisePoint)
                         .filter((p) => TIME_LABELS[p.time_hours]);
      if (!points.length) return [];

      const riskLevel = pred.risk_level;
      const color     = riskLevel ? getRiskColor(riskLevel) : getScenarioColor(scenario);
      const weight    = riskLevel ? getRiskWeight(riskLevel) : (scenario === 3 ? 4 : 2);
      const id        = pred.iceberg_id;
      const positions = points.map((p) => [p.latitude, p.longitude]);

      return [
        // Dashed trajectory path
        <Polyline
          key={`traj-line-${id}`}
          positions={positions}
          pathOptions={{
            color,
            weight,
            dashArray: '10, 10',
            opacity: 0.85,
            lineCap: 'round',
            lineJoin: 'round',
          }}
        />,

        // Circle + popup at each time step
        ...points.map((pt) => {
          const pos       = [pt.latitude, pt.longitude];
          const timeLabel = TIME_LABELS[pt.time_hours] ?? `${pt.time_hours}h`;
          // Radius grows proportionally to uncertainty, capped 6–22px
          const radiusPx  = Math.max(6, Math.min(22, pt.uncertainty_km * 0.7));

          return (
            <CircleMarker
              key={`traj-circle-${id}-${pt.time_hours}`}
              center={pos}
              radius={radiusPx}
              pathOptions={{
                color,
                weight: 1,
                fillColor: color,
                fillOpacity: 0.15,
                opacity: 0.7,
              }}
            >
              <Tooltip direction="top" offset={[0, -10]} sticky>
                <span style={{ whiteSpace: 'nowrap' }}>
                  <strong>{id}</strong> &mdash; {timeLabel} prediction
                </span>
              </Tooltip>

              <Popup minWidth={220} maxWidth={280} autoPan>
                <div style={{ fontSize: '13px', lineHeight: 1.6 }}>
                  <div style={{ fontWeight: 700, marginBottom: 6, color }}>
                    {id}
                  </div>
                  <div><strong>Time horizon:</strong> {timeLabel}</div>
                  <div>
                    <strong>Position:</strong>{' '}
                    {pt.latitude.toFixed(4)}&deg;,{' '}
                    {pt.longitude.toFixed(4)}&deg;
                  </div>
                  <div>
                    <strong>Uncertainty:</strong>{' '}
                    &plusmn;{pt.uncertainty_km.toFixed(1)} km
                  </div>
                  <div>
                    <strong>Drift speed:</strong>{' '}
                    {pt.drift_speed_kmh != null
                      ? `${pt.drift_speed_kmh.toFixed(1)} km/h`
                      : 'N/A'}
                  </div>
                  <div>
                    <strong>Direction:</strong>{' '}
                    {pt.drift_direction_deg != null
                      ? `${pt.drift_direction_deg.toFixed(0)}\u00b0`
                      : 'N/A'}
                  </div>

                  <div
                    style={{
                      marginTop: 6,
                      paddingTop: 6,
                      borderTop: '1px solid #e5e7eb',
                    }}
                  >
                    <strong>Risk level:</strong>{' '}
                    <span
                      style={{
                        textTransform: 'capitalize',
                        color,
                        fontWeight: 700,
                      }}
                    >
                      {riskLevel ?? 'unknown'}
                    </span>
                  </div>

                  {pred.notes && (
                    <div
                      style={{
                        marginTop: 6,
                        fontSize: 12,
                        color: '#6b7280',
                        fontStyle: 'italic',
                      }}
                    >
                      {pred.notes}
                    </div>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          );
        }),
      ];
    });
  }, [predictions, visible, scenario]);

  if (!visible || !layers.length) return null;
  return <>{layers}</>;
};

export default TrajectoryLines;
