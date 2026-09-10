import { Polyline, Popup } from 'react-leaflet';

const toPositions = (route) => {
  if (Array.isArray(route.coordinates) && route.coordinates.length) {
    return route.coordinates;
  }
  if (Array.isArray(route.waypoints)) {
    return route.waypoints.map((wp) => [wp.lat, wp.lon]);
  }
  return [];
};

// Mock additional routes for prototype demo - EXPORTED so MainMap can use them
export const MOCK_ADDITIONAL_ROUTES = [
  {
    id: 'alternative_1',
    name: 'Coastal Hugging Route',
    color: '#8b5cf6',
    style: 'solid',
    distanceKm: 11800,
    distance_km: 11800,
    timeDays: 32,
    duration_days: 32,
    riskPercent: 18,
    risk_score: 18,
    coordinates: [
      [13.0827, 80.2707],  // Chennai
      [5.0, 75.0],
      [-8.0, 70.0],
      [-18.0, 62.0],
      [-28.0, 50.0],
      [-38.0, 40.0],
      [-46.0, 32.0],
      [-52.0, 25.0],
      [-58.0, 18.0],
      [-62.0, 15.0],
      [-66.0, 13.0],
      [-69.0, 12.0],
      [-70.7644, 11.7386]  // Maitri
    ]
  },
  {
    id: 'alternative_2',
    name: 'Middle Balance Route',
    color: '#ec4899',
    style: 'dashed',
    distanceKm: 11000,
    distance_km: 11000,
    timeDays: 30,
    duration_days: 30,
    riskPercent: 26,
    risk_score: 26,
    coordinates: [
      [13.0827, 80.2707],  // Chennai
      [3.0, 77.0],
      [-10.0, 72.0],
      [-22.0, 65.0],
      [-32.0, 58.0],
      [-42.0, 48.0],
      [-50.0, 38.0],
      [-56.0, 30.0],
      [-60.0, 24.0],
      [-64.0, 19.0],
      [-68.0, 14.0],
      [-70.7644, 11.7386]  // Maitri
    ]
  }
];

const RouteLines = ({ routes, selectedRoute, onSelectRoute }) => {
  // Combine backend routes with mock routes for prototype
  const allRoutes = [...(routes || []), ...MOCK_ADDITIONAL_ROUTES];
  
  if (!allRoutes || allRoutes.length === 0) return null;

  return (
    <>
      {allRoutes.map((route) => {
        const positions = toPositions(route);
        if (!positions.length) return null;
        const id = route.id || route.type;
        const isSelected = selectedRoute === id;
        const dash =
          route.style === 'dashed' || route.type === 'fastest'
            ? '8, 8'
            : route.style === 'dotted' || route.type === 'fuel' || route.type === 'fuel_efficient'
              ? '2, 8'
              : null;

        return (
          <Polyline
            key={id}
            positions={positions}
            pathOptions={{
              color: route.color || '#64748b',
              weight: isSelected ? 6 : route.width || 3,
              opacity: isSelected ? 1 : 0.75,
              dashArray: dash,
            }}
            eventHandlers={{
              click: () => onSelectRoute && onSelectRoute(id),
            }}
          >
            <Popup>
              <strong>{route.name || id}</strong>
              <br />
              Distance: {route.distanceKm ?? route.distance_km} km
              <br />
              Duration: {route.timeDays ?? route.duration_days} days
              <br />
              Risk: {route.riskPercent ?? route.risk_score}%
            </Popup>
          </Polyline>
        );
      })}
    </>
  );
};

export default RouteLines;
