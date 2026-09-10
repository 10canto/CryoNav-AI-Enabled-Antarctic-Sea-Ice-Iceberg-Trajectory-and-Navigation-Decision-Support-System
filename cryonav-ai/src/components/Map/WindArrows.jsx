import { Marker } from 'react-leaflet';
import { divIcon } from 'leaflet';

const WindArrows = ({ vectors = [] }) => {
  const createArrowIcon = (speed, direction) => {
    const color = speed < 20 ? '#10b981' : speed < 40 ? '#f59e0b' : '#ef4444';
    const size = Math.min(speed / 2 + 10, 40);

    return divIcon({
      html: `<div style="
        width: 0;
        height: 0;
        border-left: ${size / 2}px solid transparent;
        border-right: ${size / 2}px solid transparent;
        border-bottom: ${size}px solid ${color};
        transform: rotate(${direction}deg);
      "></div>`,
      className: 'wind-arrow-icon',
      iconSize: [size, size],
    });
  };

  return (
    <>
      {vectors.map((vector, index) => (
        <Marker
          key={`${vector.lat}-${vector.lon}-${index}`}
          position={[vector.lat, vector.lon]}
          icon={createArrowIcon(vector.speed_kmh, vector.direction_deg)}
        />
      ))}
    </>
  );
};

export default WindArrows;
