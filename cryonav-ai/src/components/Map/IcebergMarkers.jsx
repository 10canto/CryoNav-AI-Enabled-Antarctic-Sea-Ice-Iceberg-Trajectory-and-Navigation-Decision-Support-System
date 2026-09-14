/**
 * IcebergMarkers.jsx
 *
 * Renders two layers of iceberg markers:
 *   1. SCENARIO icebergs  — the animated narrative icebergs (ICE-047, 048, 049)
 *      from scenarioDataRequirements.  Red triangle icon + danger circle.
 *
 *   2. DEMO CSV icebergs  — the 7 real named bergs from demoData.js (B15G, A23A…)
 *      shown as smaller blue diamond icons to distinguish from scenario icebergs.
 *
 * Props:
 *   icebergs  — scenario iceberg array (from App state)
 */

import { Circle, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { DEMO_ICEBERGS } from '../../data/demoData';

// ── Scenario iceberg icon (red triangle — danger) ─────────────────────────────
const scenarioIcon = L.divIcon({
  className: 'iceberg-marker-icon',
  html: `<svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true">
    <polygon points="12,2 22,21 2,21" fill="#ef4444" stroke="#ffffff" stroke-width="1.6"/>
  </svg>`,
  iconSize:   [26, 26],
  iconAnchor: [13, 24],
  popupAnchor:[0, -20],
});

// ── Demo/CSV iceberg icon (blue diamond — reference data) ────────────────────
const demoIcon = L.divIcon({
  className: 'iceberg-demo-icon',
  html: `<svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
    <polygon points="12,1 23,12 12,23 1,12" fill="#38bdf8" stroke="#0ea5e9" stroke-width="1.8" opacity="0.9"/>
  </svg>`,
  iconSize:   [20, 20],
  iconAnchor: [10, 10],
  popupAnchor:[0, -12],
});

// ── Helper: normalise position from various formats ───────────────────────────
const toLatLng = (iceberg) => {
  if (Array.isArray(iceberg.position))         return iceberg.position;
  if (iceberg.position?.lat != null)           return [iceberg.position.lat, iceberg.position.lon];
  if (iceberg.lat != null)                     return [iceberg.lat, iceberg.lon];
  return null;
};

// ── Format metres nicely ──────────────────────────────────────────────────────
const fmt = (m) => m >= 1000 ? `${(m / 1000).toFixed(1)} km` : `${m} m`;

const IcebergMarkers = ({ icebergs = [] }) => (
  <>
    {/* ── 1. Scenario icebergs (narrative / animated) ── */}
    {icebergs.map((iceberg) => {
      const pos = toLatLng(iceberg);
      if (!pos) return null;

      const length = iceberg.length ?? iceberg.sizeMeters ?? iceberg.size_meters?.length ?? 400;
      const width  = iceberg.width  ?? iceberg.size_meters?.width ?? 400;

      return (
        <Marker key={iceberg.id} position={pos} icon={scenarioIcon}>
          {/* danger proximity circle */}
          <Circle
            center={pos}
            radius={Math.max(4000, length * 8)}
            pathOptions={{ color: '#ef4444', weight: 1, fillOpacity: 0.07 }}
          />
          <Popup>
            <div style={{ fontSize: '0.8rem', lineHeight: 1.6, minWidth: 160 }}>
              <div style={{ fontWeight: 700, marginBottom: 4 }}>
                ⚠️ {iceberg.name || iceberg.id}
              </div>
              <div>Size: {fmt(length)} × {fmt(width)}</div>
              {iceberg.confidence != null && (
                <div>Confidence: {iceberg.confidence}%</div>
              )}
              {iceberg.driftSpeedKnots != null && (
                <div>Drift: {iceberg.driftSpeedKnots} kn @ {iceberg.driftHeading}°</div>
              )}
            </div>
          </Popup>
        </Marker>
      );
    })}

    {/* ── 2. Demo CSV icebergs (reference layer — always visible) ── */}
    {DEMO_ICEBERGS.map((berg) => {
      const pos = [berg.lat, berg.lon];
      return (
        <Marker key={`demo_${berg.id}`} position={pos} icon={demoIcon}>
          {/* soft size circle */}
          <Circle
            center={pos}
            radius={Math.max(6000, berg.length * 4)}
            pathOptions={{ color: '#0ea5e9', weight: 0.8, fillOpacity: 0.06 }}
          />
          <Popup>
            <div style={{ fontSize: '0.8rem', lineHeight: 1.6, minWidth: 160 }}>
              <div style={{ fontWeight: 700, marginBottom: 4, color: '#0284c7' }}>
                🧊 Iceberg {berg.id}
              </div>
              <div>Size: {fmt(berg.length)} × {fmt(berg.width)}</div>
              <div>Position: {berg.lat.toFixed(3)}°, {berg.lon.toFixed(3)}°</div>
              <div style={{ marginTop: 4, color: '#64748b', fontSize: '0.7rem' }}>
                Source: DEMO / SYNTHETIC
              </div>
            </div>
          </Popup>
        </Marker>
      );
    })}
  </>
);

export default IcebergMarkers;
