/**
 * IceZoneLayer.jsx
 *
 * Renders Antarctic sea-ice from ICE_GRID (demoData.js) as:
 *   • Pack / thick ice  (sic ≥ 0.70) → dark navy filled Circles
 *   • Thin ice          (sic 0.30–0.69) → cyan semi-transparent Circles
 *
 * Circles are placed on a UNIFORM fine grid over the Antarctic region
 * (every 1.5° lat × 1.5° lon), each circle's type determined by the
 * nearest ICE_GRID cell's sic value.  This guarantees full coverage
 * with no vertical stripes or gaps.
 *
 * Open water (sic < 0.30) → no overlay (ocean tile is the background).
 */

import { createPortal } from 'react-dom';
import { useEffect, useMemo, useState } from 'react';
import { Circle, Popup, useMap } from 'react-leaflet';
import { ICE_GRID } from '../../data/demoData';

// ─── Seeded RNG (mulberry32) ──────────────────────────────────────────────────
function mulberry32(seed) {
  let s = (seed >>> 0) + 1;
  return () => {
    s += 0x6d2b79f5;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t ^= t + Math.imul(t ^ (t >>> 7), 61 | t);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}


// ─── Generate circles on a uniform fine grid ─────────────────────────────────
// For each placement point, find the nearest ICE_GRID entry by Euclidean
// distance (runs once in useMemo — not on every render).
const STEP    = 1.5;
const LAT_MIN = -80;
const LAT_MAX = -55;
const LON_MIN = -180;
const LON_MAX = 180;

function buildCircles() {
  const circles = [];
  let idx = 0;

  for (let lat = LAT_MIN; lat <= LAT_MAX; lat += STEP) {
    for (let lon = LON_MIN; lon <= LON_MAX; lon += STEP) {

      // Find nearest ICE_GRID entry (brute force — runs once)
      let best = null, bestD = Infinity;
      for (const [glat, glon, gsic] of ICE_GRID) {
        const d = (glat - lat) ** 2 + (glon - lon) ** 2;
        if (d < bestD) { bestD = d; best = gsic; }
      }

      if (best == null || best < 0.3) { idx++; continue; } // open water / no data

      const type   = best >= 0.7 ? 'pack' : 'thin';
      const rng    = mulberry32(idx * 7919 + 12345);
      const jLat   = (rng() - 0.5) * STEP * 0.65;
      const jLon   = (rng() - 0.5) * STEP * 0.65;
      const radius = type === 'pack'
        ? 28000 + best * 22000
        : 16000 + best * 16000;

      circles.push({ id: idx, lat: lat + jLat, lon: lon + jLon, sic: best, type, radius });
      idx++;
    }
  }
  return circles;
}

// ─── Styles ───────────────────────────────────────────────────────────────────
const CIRCLE_STYLE = {
  thin: { color: '#7dd3fc', fillColor: '#7dd3fc', fillOpacity: 0.28, weight: 0.4, opacity: 0.4 },
  pack: { color: '#1e3a8a', fillColor: '#1e3a8a', fillOpacity: 0.55, weight: 0.3, opacity: 0.3 },
};

// ─── Legend ───────────────────────────────────────────────────────────────────
function IceLegend() {
  return (
    <div style={{
      position: 'absolute', bottom: 28, left: 10, zIndex: 1000,
      background: 'rgba(15,23,42,0.85)', borderRadius: 8, padding: '8px 12px',
      backdropFilter: 'blur(6px)', border: '1px solid rgba(255,255,255,0.1)',
      pointerEvents: 'none', fontSize: 11, color: '#e2e8f0', minWidth: 160,
    }}>
      <div style={{ fontWeight: 700, marginBottom: 6, letterSpacing: '0.05em', color: '#7dd3fc' }}>
        SEA ICE (DEMO)
      </div>
      {[
        { bg: '#7dd3fc', label: 'Thin Ice (SIC 30–69%)' },
        { bg: '#1e3a8a', label: 'Pack / Thick Ice (SIC ≥ 70%)' },
      ].map(({ bg, label }) => (
        <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 4 }}>
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: bg, flexShrink: 0 }} />
          <span>{label}</span>
        </div>
      ))}
    </div>
  );
}

function LegendPortal({ map }) {
  const [container, setContainer] = useState(null);
  useEffect(() => {
    if (!map) return;
    const host = map.getContainer();
    const div  = document.createElement('div');
    div.style.cssText = 'position:absolute;inset:0;pointer-events:none;z-index:1000';
    host.appendChild(div);
    setContainer(div);
    return () => { try { host.removeChild(div); } catch {} };
  }, [map]);
  if (!container) return null;
  return createPortal(<IceLegend />, container);
}

// ─── Main component ───────────────────────────────────────────────────────────
const IceZoneLayer = () => {
  const map = useMap();

  const circles = useMemo(() => buildCircles(), []);

  return (
    <>
      {circles.map(({ id, lat, lon, sic, type, radius }) => (
        <Circle
          key={id}
          center={[lat, lon]}
          radius={radius}
          pathOptions={CIRCLE_STYLE[type]}
        >
          <Popup>
            <div style={{ fontSize: '0.78rem', lineHeight: 1.5 }}>
              <strong>{type === 'pack' ? 'Pack / Thick Ice' : 'Thin Ice'}</strong><br />
              SIC: {Math.round(sic * 100)}%<br />
              <span style={{ color: '#64748b', fontSize: '0.7rem' }}>DEMO / SYNTHETIC</span>
            </div>
          </Popup>
        </Circle>
      ))}
      <LegendPortal map={map} />
    </>
  );
};

export default IceZoneLayer;
