import { Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';

const icebergIcon = L.divIcon({
  className: 'iceberg-marker-icon',
  html: `<svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true">
    <polygon points="12,2 22,21 2,21" fill="#ef4444" stroke="#ffffff" stroke-width="1.6" />
  </svg>`,
  iconSize: [26, 26],
  iconAnchor: [13, 24],
  popupAnchor: [0, -20],
});

const toLatLng = (iceberg) => {
  if (Array.isArray(iceberg.position)) return iceberg.position;
  if (iceberg.position?.lat != null) return [iceberg.position.lat, iceberg.position.lon];
  return null;
};

const IcebergMarkers = ({ icebergs = [] }) => {
  return (
    <>
      {icebergs.map((iceberg) => {
        const position = toLatLng(iceberg);
        if (!position) return null;
        const length = iceberg.length ?? iceberg.sizeMeters ?? iceberg.size_meters?.length;
        const width = iceberg.width ?? iceberg.size_meters?.width;
        return (
          <Marker key={iceberg.id} position={position} icon={icebergIcon}>
            <Circle
              center={position}
              radius={Math.max(4000, (length || 400) * 8)}
              pathOptions={{ color: '#ef4444', weight: 1, fillOpacity: 0.08 }}
            />
            <Popup>
              <strong>{iceberg.name || iceberg.id}</strong>
              <br />
              Size: {length || '—'}m × {width || '—'}m
              <br />
              Confidence: {iceberg.confidence}%
              <br />
              Drift: {iceberg.driftSpeedKnots ?? '—'} kn @ {iceberg.driftHeading ?? '—'}°
            </Popup>
          </Marker>
        );
      })}
    </>
  );
};

export default IcebergMarkers;
