import { Rectangle, Popup, useMap } from 'react-leaflet';
import { useEffect, useState } from 'react';

// ─── Visual style per ice type ────────────────────────────────────────────────
const ICE_TYPE_STYLE = {
  open_water: { color: '#38bdf8', fillOpacity: 0.18, label: 'Open Water' },
  thin_ice:   { color: '#3b82f6', fillOpacity: 0.40, label: 'Thin Ice (<30 cm)' },
  thick_ice:  { color: '#1d4ed8', fillOpacity: 0.62, label: 'Thick Ice (30–70 cm)' },
  pack_ice:   { color: '#1e1b4b', fillOpacity: 0.78, label: 'Pack Ice (>70 cm)' },
};

// Priority order when multiple polygons overlap the same cell
const TYPE_PRIORITY = ['pack_ice', 'thick_ice', 'thin_ice', 'open_water'];

// ─── Point-in-polygon (ray-casting) ──────────────────────────────────────────
function pointInPolygon(lat, lon, coords) {
  // coords: [[lat,lon], ...]
  let inside = false;
  const n = coords.length;
  for (let i = 0, j = n - 1; i < n; j = i++) {
    const [yi, xi] = coords[i];
    const [yj, xj] = coords[j];
    const intersect =
      yi > lat !== yj > lat &&
      lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
}

// ─── Build grid cells from ice zone polygons ──────────────────────────────────
/**
 * Computes the overall bounding box of all zone polygons, then divides it into
 * GRID_ROWS × GRID_COLS cells.  Each cell gets assigned the ice type whose
 * polygon contains the cell centre; if multiple polygons overlap the centre,
 * the highest-priority type wins.  Cells not inside any polygon are skipped.
 */
function buildGrid(zones, gridRows = 22, gridCols = 22) {
  if (!zones || zones.length === 0) return [];

  // Compute bounding box over all coordinates
  let minLat = Infinity, maxLat = -Infinity;
  let minLon = Infinity, maxLon = -Infinity;

  zones.forEach(({ coordinates }) => {
    coordinates.forEach(([lat, lon]) => {
      if (lat < minLat) minLat = lat;
      if (lat > maxLat) maxLat = lat;
      if (lon < minLon) minLon = lon;
      if (lon > maxLon) maxLon = lon;
    });
  });

  const latStep = (maxLat - minLat) / gridRows;
  const lonStep = (maxLon - minLon) / gridCols;

  const cells = [];

  for (let r = 0; r < gridRows; r++) {
    for (let c = 0; c < gridCols; c++) {
      const cellMinLat = minLat + r * latStep;
      const cellMaxLat = cellMinLat + latStep;
      const cellMinLon = minLon + c * lonStep;
      const cellMaxLon = cellMinLon + lonStep;

      // Sample 5 points per cell: centre + 4 sub-centres for better coverage
      const samplePoints = [
        [(cellMinLat + cellMaxLat) / 2, (cellMinLon + cellMaxLon) / 2],
        [cellMinLat + latStep * 0.25, cellMinLon + lonStep * 0.25],
        [cellMinLat + latStep * 0.25, cellMinLon + lonStep * 0.75],
        [cellMinLat + latStep * 0.75, cellMinLon + lonStep * 0.25],
        [cellMinLat + latStep * 0.75, cellMinLon + lonStep * 0.75],
      ];

      // Count hits per type across sample points
      const hits = {};
      samplePoints.forEach(([sLat, sLon]) => {
        // Check against each zone in priority order so we assign the dominant type
        for (const priority of TYPE_PRIORITY) {
          const zone = zones.find((z) => z.type === priority);
          if (zone && pointInPolygon(sLat, sLon, zone.coordinates)) {
            hits[priority] = (hits[priority] || 0) + 1;
            break; // highest-priority match wins for this sample point
          }
        }
      });

      if (Object.keys(hits).length === 0) continue; // cell not covered

      // Majority type (most sample-point hits)
      const majorityType = Object.entries(hits).sort((a, b) => b[1] - a[1])[0][0];

      cells.push({
        id: `${r}-${c}`,
        bounds: [
          [cellMinLat, cellMinLon],
          [cellMaxLat, cellMaxLon],
        ],
        type: majorityType,
        hitCount: hits[majorityType],
        totalSamples: samplePoints.length,
      });
    }
  }

  return cells;
}

// ─── Normalise zone from backend or legacy format ────────────────────────────
function normalise(zone) {
  if (zone.type) {
    return {
      type: zone.type,
      percentage: zone.percentage,
      coordinates: zone.coordinates || [],
      area_km2: zone.area_km2,
      confidence: zone.confidence,
      description: zone.description,
    };
  }
  // Legacy frontend constant format (name / color / fillOpacity)
  return {
    type: 'open_water',
    percentage: zone.concentration,
    coordinates: zone.coordinates || [],
    area_km2: null,
    confidence: null,
    description: null,
  };
}

// ─── Legend overlay ───────────────────────────────────────────────────────────
function IceGridLegend({ types }) {
  if (!types || types.length === 0) return null;
  return (
    <div
      style={{
        position: 'absolute',
        bottom: 28,
        left: 10,
        zIndex: 1000,
        background: 'rgba(15,23,42,0.82)',
        borderRadius: 8,
        padding: '7px 11px',
        backdropFilter: 'blur(6px)',
        border: '1px solid rgba(255,255,255,0.1)',
        pointerEvents: 'none',
        fontSize: 11,
        color: '#e2e8f0',
        minWidth: 150,
      }}
    >
      <div style={{ fontWeight: 700, marginBottom: 5, letterSpacing: '0.04em', color: '#94d2ff' }}>
        ICE GRID
      </div>
      {types.map((t) => {
        const style = ICE_TYPE_STYLE[t];
        if (!style) return null;
        return (
          <div key={t} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: 2,
                background: style.color,
                opacity: style.fillOpacity + 0.2,
                border: `1px solid ${style.color}`,
                flexShrink: 0,
              }}
            />
            <span>{style.label}</span>
          </div>
        );
      })}
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────
const IceZoneLayer = ({ zones = [], data }) => {
  const map = useMap();
  const [cells, setCells] = useState([]);
  const [presentTypes, setPresentTypes] = useState([]);

  const rawList = data?.ice_zones?.length ? data.ice_zones : zones;

  useEffect(() => {
    const normalised = rawList
      .map(normalise)
      .filter((z) => z.coordinates.length >= 3);

    if (normalised.length === 0) {
      setCells([]);
      setPresentTypes([]);
      return;
    }

    // Derive grid size from map zoom for performance
    const zoom = map.getZoom();
    const gridSize = zoom >= 5 ? 30 : zoom >= 4 ? 22 : 16;

    const built = buildGrid(normalised, gridSize, gridSize);
    setCells(built);

    // Collect unique types present (in priority order for legend)
    const typeSet = new Set(built.map((c) => c.type));
    setPresentTypes(TYPE_PRIORITY.filter((t) => typeSet.has(t)));
  }, [rawList, map]);

  if (cells.length === 0) return null;

  return (
    <>
      {cells.map((cell) => {
        const style = ICE_TYPE_STYLE[cell.type] || { color: '#94a3b8', fillOpacity: 0.25 };
        const label = style.label ?? cell.type;
        const pct = Math.round((cell.hitCount / cell.totalSamples) * 100);

        return (
          <Rectangle
            key={cell.id}
            bounds={cell.bounds}
            pathOptions={{
              color: style.color,
              fillColor: style.color,
              fillOpacity: style.fillOpacity,
              weight: 0.4,
              opacity: 0.5,
            }}
          >
            <Popup>
              <div style={{ minWidth: 160, fontSize: '0.8rem', lineHeight: 1.6 }}>
                <div style={{ fontWeight: 700, marginBottom: 3 }}>{label}</div>
                <div>Grid majority: <strong>{pct}%</strong></div>
              </div>
            </Popup>
          </Rectangle>
        );
      })}

      {/* Legend rendered as a DOM overlay via a portal-like approach */}
      <LegendPortal map={map} types={presentTypes} />
    </>
  );
};

// Renders the legend into the map's container div via a React portal
import { createPortal } from 'react-dom';

function LegendPortal({ map, types }) {
  const [container, setContainer] = useState(null);

  useEffect(() => {
    if (!map) return;
    const mapContainer = map.getContainer();
    const div = document.createElement('div');
    div.style.position = 'absolute';
    div.style.inset = '0';
    div.style.pointerEvents = 'none';
    div.style.zIndex = '1000';
    mapContainer.appendChild(div);
    setContainer(div);
    return () => {
      mapContainer.removeChild(div);
    };
  }, [map]);

  if (!container) return null;
  return createPortal(<IceGridLegend types={types} />, container);
}

export default IceZoneLayer;
