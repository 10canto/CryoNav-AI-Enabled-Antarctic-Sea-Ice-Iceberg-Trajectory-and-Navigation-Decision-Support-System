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

// No mock additional routes — only the 3 scenario routes (A/B/C) are shown
export const MOCK_ADDITIONAL_ROUTES = [];

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
