import { useMemo } from 'react';
import { CircleMarker, Polyline, Popup, Tooltip } from 'react-leaflet';

const TRACK_COLOR = '#f59e0b';

const HistoricalTrajectoryLines = ({ tracks = [], visible = true }) => {
  const layers = useMemo(() => {
    if (!visible || !tracks.length) return [];

    return tracks.flatMap((track) => {
      const points = track.points || [];
      if (points.length < 2) return [];

      const positions = points.map((point) => [point.latitude, point.longitude]);
      const start = positions[0];
      const end = positions[positions.length - 1];
      const latestPoint = points[points.length - 1];

      return [
        <Polyline
          key={`history-line-${track.id}`}
          positions={positions}
          pathOptions={{
            color: TRACK_COLOR,
            weight: 2,
            opacity: 0.78,
            dashArray: '6, 8',
            lineCap: 'round',
            lineJoin: 'round',
          }}
        >
          <Tooltip sticky>
            {track.id} historical track ({points.length} observations)
          </Tooltip>
          <Popup>
            <strong>{track.id} historical track</strong>
            <div>Observations: {points.length}</div>
            <div>From: {points[0].date}</div>
            <div>To: {latestPoint.date}</div>
          </Popup>
        </Polyline>,
        <CircleMarker
          key={`history-start-${track.id}`}
          center={start}
          radius={4}
          pathOptions={{ color: '#ffffff', weight: 1, fillColor: TRACK_COLOR, fillOpacity: 1 }}
        >
          <Tooltip>{track.id} first recorded position</Tooltip>
        </CircleMarker>,
        <CircleMarker
          key={`history-end-${track.id}`}
          center={end}
          radius={6}
          pathOptions={{ color: '#ffffff', weight: 1.5, fillColor: TRACK_COLOR, fillOpacity: 1 }}
        >
          <Tooltip>{track.id} latest recorded position</Tooltip>
        </CircleMarker>,
      ];
    });
  }, [tracks, visible]);

  return layers.length ? <>{layers}</> : null;
};

export default HistoricalTrajectoryLines;
