import { Polygon, Popup } from 'react-leaflet';

const IceZoneLayer = ({ zones = [], data }) => {
  const list = zones.length
    ? zones
    : data?.ice_zones?.map((zone) => ({
        name: zone.type,
        color:
          zone.type === 'thick_ice' ? '#1854a0' : zone.type === 'thin_ice' ? '#3284cc' : '#64b4ff',
        fillOpacity: zone.type === 'thick_ice' ? 0.55 : zone.type === 'thin_ice' ? 0.35 : 0.18,
        coordinates: zone.coordinates,
        concentration: zone.percentage,
      })) || [];

  if (!list.length) return null;

  return (
    <>
      {list.map((zone) => (
        <Polygon
          key={zone.name}
          positions={zone.coordinates}
          pathOptions={{
            color: zone.color,
            fillColor: zone.color,
            fillOpacity: zone.fillOpacity ?? 0.25,
            weight: 1,
          }}
        >
          <Popup>
            <strong>{zone.name}</strong>
            {zone.concentration != null && (
              <>
                <br />
                Concentration: {zone.concentration}%
              </>
            )}
          </Popup>
        </Polygon>
      ))}
    </>
  );
};

export default IceZoneLayer;
