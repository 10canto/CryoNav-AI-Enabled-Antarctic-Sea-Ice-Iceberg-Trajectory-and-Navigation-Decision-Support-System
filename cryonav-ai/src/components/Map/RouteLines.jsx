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
    // Stays fully in open ocean: Indian Ocean → Southern Ocean → Maitri
    // No waypoint touches land, Madagascar, Africa, or Antarctic Peninsula
    coordinates: [
      [13.0827, 80.2707],  // Chennai Port (departure)
      [7.0,    77.0],      // South of Sri Lanka — open Indian Ocean
      [0.0,    73.0],      // Equator, west of Maldives — deep ocean
      [-10.0,  68.0],      // Southern Indian Ocean, clear of Chagos
      [-20.0,  65.0],      // Open ocean, east of Madagascar
      [-30.0,  60.0],      // Subtropical Indian Ocean
      [-38.0,  52.0],      // Roaring Forties entry — open ocean
      [-44.0,  42.0],      // Prince Edward Islands area — north of them
      [-50.0,  35.0],      // Furious Fifties — open Southern Ocean
      [-56.0,  28.0],      // Sub-Antarctic — no land nearby
      [-61.0,  22.0],      // Antarctic Convergence Zone
      [-65.0,  17.0],      // Southern Ocean approach to Queen Maud Land
      [-68.0,  13.5],      // Near-coastal lead, Princess Astrid Coast
      [-70.7644, 11.7386]  // Maitri Station, Antarctica (arrival)
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
    // Open-ocean balanced path through central Indian Ocean
    coordinates: [
      [13.0827, 80.2707],  // Chennai Port
      [5.0,    78.0],      // Bay of Bengal exit — open water
      [-5.0,   74.0],      // Central Indian Ocean
      [-15.0,  70.0],      // Open ocean, clear of any islands
      [-25.0,  63.0],      // Mid-Indian Ocean
      [-33.0,  55.0],      // Southwest Indian Ocean
      [-42.0,  46.0],      // Roaring Forties — open ocean
      [-50.0,  37.0],      // Furious Fifties approach
      [-56.0,  29.0],      // Deep Southern Ocean
      [-60.0,  23.0],      // Antarctic Convergence
      [-64.0,  18.0],      // Southern Ocean, approaching Queen Maud Land
      [-68.0,  14.0],      // Coastal approach corridor
      [-70.7644, 11.7386]  // Maitri Station (arrival)
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
