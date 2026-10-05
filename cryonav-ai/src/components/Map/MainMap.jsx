import { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import { MAP_CENTER, MAP_ZOOM, SHIP_TRANSITION_DURATION } from '../../config';
import { getShipPositionOnRoute } from '../../services/scenarioDataRequirements';
import { mockWindData } from '../../services/mockData';
import { calculateBearing } from '../../utils/mapHelpers';
import RouteLines, { MOCK_ADDITIONAL_ROUTES } from './RouteLines';
import IcebergMarkers from './IcebergMarkers';
import IceZoneLayer from './IceZoneLayer';
import ShipMarker from './ShipMarker';
import WindArrows from './WindArrows';
import MapControls from './MapControls';
import VoyageInfoPanel from '../Panels/VoyageInfoPanel';
import TrajectoryLines from './TrajectoryLines';
import HistoricalTrajectoryLines from './HistoricalTrajectoryLines';

function MapSync({ center, zoom, duration = 0.8 }) {
  const map = useMap();
  useEffect(() => {
    map.invalidateSize();
  }, [map]);
  useEffect(() => {
    if (!center) return;
    map.flyTo(center, zoom ?? map.getZoom(), { duration });
  }, [center, zoom, duration, map]);
  return null;
}

function SatelliteBasemapStyle({ enabled }) {
  const map = useMap();
  useEffect(() => {
    map.getContainer().classList.toggle('satellite-basemap', enabled);
  }, [enabled, map]);
  return null;
}

const samePosition = (first, second) =>
  first?.[0] === second?.[0] && first?.[1] === second?.[1];

const easeInOutCubic = (progress) =>
  progress < 0.5 ? 4 * progress ** 3 : 1 - ((-2 * progress + 2) ** 3) / 2;

const distanceSquared = (first, second) =>
  (first[0] - second[0]) ** 2 + (first[1] - second[1]) ** 2;

const closestWaypointIndex = (position, waypoints) => waypoints.reduce(
  (closestIndex, waypoint, index) => (
    distanceSquared(position, waypoint) < distanceSquared(position, waypoints[closestIndex]) ? index : closestIndex
  ),
  0,
);

const pointAlongPath = (path, progress) => {
  const lengths = path.slice(1).map((point, index) => Math.sqrt(distanceSquared(point, path[index])));
  const totalLength = lengths.reduce((total, length) => total + length, 0);
  let remaining = totalLength * progress;

  for (let index = 0; index < lengths.length; index += 1) {
    if (remaining <= lengths[index] || index === lengths.length - 1) {
      const segmentProgress = lengths[index] ? remaining / lengths[index] : 1;
      return [
        path[index][0] + (path[index + 1][0] - path[index][0]) * segmentProgress,
        path[index][1] + (path[index + 1][1] - path[index][1]) * segmentProgress,
      ];
    }
    remaining -= lengths[index];
  }

  return path[path.length - 1];
};

const routeLeg = (start, end, routeCoordinates = []) => {
  if (routeCoordinates.length < 2) return [start, end];
  const startIndex = closestWaypointIndex(start, routeCoordinates);
  const endIndex = closestWaypointIndex(end, routeCoordinates);
  const intermediate = routeCoordinates.slice(Math.min(startIndex, endIndex), Math.max(startIndex, endIndex) + 1);
  const inTravelDirection = startIndex <= endIndex ? intermediate : intermediate.reverse();
  return [start, ...inTravelDirection.filter((point) => !samePosition(point, start) && !samePosition(point, end)), end];
};

function useAnimatedShipPosition(targetPosition, routeCoordinates) {
  const initialPosition = targetPosition || MAP_CENTER;
  const [position, setPosition] = useState(initialPosition);
  const positionRef = useRef(initialPosition);
  const targetRef = useRef(initialPosition);

  useEffect(() => {
    if (!targetPosition || samePosition(targetPosition, targetRef.current)) return undefined;

    const start = positionRef.current;
    const end = targetPosition;
    const path = routeLeg(start, end, routeCoordinates);
    const startedAt = performance.now();
    let animationFrame;

    targetRef.current = end;
    const animate = (now) => {
      const progress = Math.min((now - startedAt) / SHIP_TRANSITION_DURATION, 1);
      const easedProgress = easeInOutCubic(progress);
      const nextPosition = pointAlongPath(path, easedProgress);

      positionRef.current = nextPosition;
      setPosition(nextPosition);

      if (progress < 1) animationFrame = requestAnimationFrame(animate);
    };

    animationFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrame);
  }, [targetPosition?.[0], targetPosition?.[1]]);

  return position;
}

const MainMap = ({ scenario, selectedRoute, onSelectRoute }) => {
  const [layers, setLayers] = useState({
    ice: true,
    routes: true,
    wind: true,
    icebergs: true,
    trajectories: true,
    tracks: true,
    satellite: false,
  });

  // Combine backend routes with mock routes to find the active route
  const allRoutes = [...(scenario?.routes || []), ...MOCK_ADDITIONAL_ROUTES];
  const activeRoute = allRoutes.find((route) => route.id === selectedRoute) || scenario?.routes?.[0];
  
  // Calculate ship position dynamically based on selected route and scenario progress.
  // Route A in scenario 3 → endpoint (Maitri Station). All other routes unchanged.
  const calculateShipPosition = () => {
    if (!activeRoute || !activeRoute.coordinates) {
      return scenario?.shipPosition || MAP_CENTER;
    }
    return getShipPositionOnRoute(activeRoute.coordinates, scenarioIndex, activeRoute.id);
  };
  
  // Calculate scenarioIndex directly for the info panel
  const scenarioIndex = typeof scenario?.scenario === 'number' ? scenario.scenario : 
                        (scenario?.time?.includes('Departure') ? 0 :
                         scenario?.time?.includes('6 hours') ? 1 :
                         scenario?.time?.includes('18 hours') ? 2 : 3);
  
  const predictions = scenario?.predictions || [];
  
  const targetShipPosition = calculateShipPosition();
  
  const shipPosition = useAnimatedShipPosition(targetShipPosition, activeRoute?.coordinates);
  const previousShipPosition = useRef(shipPosition);
  const heading = calculateBearing(previousShipPosition.current, shipPosition) || scenario?.riskAssessment?.windDegrees || 210;

  useEffect(() => {
    previousShipPosition.current = shipPosition;
  }, [shipPosition]);

  const toggleLayer = (key) => {
    setLayers((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <MapContainer
      center={[-32, 48]}
      zoom={MAP_ZOOM}
      style={{ height: '100%', width: '100%', minHeight: 380 }}
      zoomControl={false}
    >
      <SatelliteBasemapStyle enabled={layers.satellite} />
      <TileLayer
        key={layers.satellite ? 'satellite' : 'street'}
        url={layers.satellite
          ? 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
          : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'}
        attribution={layers.satellite
          ? 'Tiles &copy; Esri, Maxar, Earthstar Geographics, and the GIS User Community'
          : '&copy; OpenStreetMap contributors'}
      />
      {layers.satellite && (
        <TileLayer
          url="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
          attribution="Labels &copy; Esri"
        />
      )}
      <MapSync center={targetShipPosition} zoom={4} duration={SHIP_TRANSITION_DURATION / 1000} />
      <MapControls layerVisibility={layers} onToggleLayer={toggleLayer} />

      {layers.ice && (
        <IceZoneLayer />
      )}
      {layers.routes && (
        <RouteLines
          routes={scenario?.routes || []}
          selectedRoute={selectedRoute}
          onSelectRoute={onSelectRoute}
        />
      )}
      {layers.trajectories && <TrajectoryLines predictions={predictions} scenario={scenarioIndex} visible={layers.trajectories} />}
      {layers.tracks && <HistoricalTrajectoryLines tracks={scenario?.historicalTracks} visible={layers.tracks} />}
      {layers.icebergs && <IcebergMarkers icebergs={scenario?.icebergs || []} />}
      <ShipMarker position={shipPosition} heading={heading} />
      {layers.wind && <WindArrows vectors={mockWindData.wind_vectors} />}
      
      <VoyageInfoPanel scenarioId={scenarioIndex} />
    </MapContainer>
  );
};

export default MainMap;