import { Polygon, Popup } from 'react-leaflet';

// Color + opacity per ice type matching CNN classifier output
const ICE_TYPE_STYLE = {
  open_water:  { color: '#38bdf8', fillOpacity: 0.10 },
  thin_ice:    { color: '#3b82f6', fillOpacity: 0.28 },
  thick_ice:   { color: '#1d4ed8', fillOpacity: 0.50 },
  pack_ice:    { color: '#1e1b4b', fillOpacity: 0.70 },
};

const ICE_TYPE_LABEL = {
  open_water: 'Open Water',
  thin_ice:   'Thin Ice (<30 cm)',
  thick_ice:  'Thick Ice (30–70 cm)',
  pack_ice:   'Pack Ice (>70 cm)',
};

/**
 * Normalises a zone from either source:
 *   - backend ice_data.json  → { type, percentage, coordinates, area_km2, confidence, description }
 *   - legacy ICE_ZONES_DATA  → { name, color, fillOpacity, coordinates, concentration }
 */
const normalise = (zone) => {
  // Backend format
  if (zone.type) {
    const style = ICE_TYPE_STYLE[zone.type] || { color: '#94a3b8', fillOpacity: 0.25 };
    return {
      key:         zone.type,
      label:       ICE_TYPE_LABEL[zone.type] || zone.type,
      color:       style.color,
      fillOpacity: style.fillOpacity,
      coordinates: zone.coordinates || [],
      concentration: zone.percentage,
      area_km2:    zone.area_km2,
      confidence:  zone.confidence,
      description: zone.description,
    };
  }
  // Legacy frontend constant format
  return {
    key:         zone.name,
    label:       zone.name,
    color:       zone.color,
    fillOpacity: zone.fillOpacity ?? 0.25,
    coordinates: zone.coordinates || [],
    concentration: zone.concentration,
    area_km2:    null,
    confidence:  null,
    description: null,
  };
};

const IceZoneLayer = ({ zones = [], data }) => {
  // Prefer backend data; fall back to legacy zones prop
  const rawList = data?.ice_zones?.length ? data.ice_zones : zones;
  const list = rawList.map(normalise).filter((z) => z.coordinates.length >= 3);

  if (!list.length) return null;

  return (
    <>
      {list.map((zone) => (
        <Polygon
          key={zone.key}
          positions={zone.coordinates}
          pathOptions={{
            color:       zone.color,
            fillColor:   zone.color,
            fillOpacity: zone.fillOpacity,
            weight: 1.2,
          }}
        >
          <Popup>
            <div style={{ minWidth: 180, fontSize: '0.8rem', lineHeight: 1.5 }}>
              <div style={{ fontWeight: 700, marginBottom: 4 }}>{zone.label}</div>
              {zone.concentration != null && (
                <div>Coverage: <strong>{zone.concentration}%</strong></div>
              )}
              {zone.area_km2 != null && (
                <div>Area: <strong>{zone.area_km2.toLocaleString()} km²</strong></div>
              )}
              {zone.confidence != null && (
                <div>CNN confidence: <strong>{(zone.confidence * 100).toFixed(0)}%</strong></div>
              )}
              {zone.description && (
                <div style={{ marginTop: 4, color: '#475569' }}>{zone.description}</div>
              )}
            </div>
          </Popup>
        </Polygon>
      ))}
    </>
  );
};

export default IceZoneLayer;
