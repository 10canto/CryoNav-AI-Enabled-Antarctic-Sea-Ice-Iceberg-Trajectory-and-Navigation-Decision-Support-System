/** Four-step demo data matching the backend current_scenario values (0–3). */
const voyage = [
  [13.0827, 80.2707], [5, 78], [-10, 70], [-28, 60], [-45, 46], [-58, 28], [-66, 16], [-70.7644, 11.7386],
];

// Helper function to get ship position along a route based on scenario progress
const getShipPositionOnRoute = (routeCoordinates, scenario) => {
  if (!routeCoordinates || routeCoordinates.length === 0) return [13.0827, 80.2707];
  
  // Calculate progress based on scenario (0=0%, 1=25%, 2=60%, 3=90%)
  const progressMap = { 0: 0, 1: 0.25, 2: 0.6, 3: 0.9 };
  const progress = progressMap[scenario] || 0;
  
  // Calculate index along the route
  const targetIndex = Math.floor((routeCoordinates.length - 1) * progress);
  return routeCoordinates[targetIndex] || routeCoordinates[0];
};

const route = (id, name, color, options = {}) => ({
  id, name, color, type: id, style: options.style || 'solid', width: options.width || 3,
  distanceKm: options.distanceKm || 12200, timeDays: options.timeDays ?? 34,
  fuelLiters: options.fuelLiters || 185000, riskPercent: options.riskPercent || 0,
  coordinates: options.coordinates || voyage, isSafest: id === 'safest', isFastest: id === 'fastest', isCheapest: id === 'fuel',
});

const routesFor = (scenario) => {
  if (scenario === 3) return [
    route('safest', 'Route A — Eastern Detour (Only viable)', '#10b981', { distanceKm: 12350, timeDays: 34.5, riskPercent: 18 }),
    route('fastest', 'Route B — BLOCKED', '#ef4444', { style: 'dashed', distanceKm: 10500, timeDays: 0, fuelLiters: 0, riskPercent: 98 }),
    route('fuel', 'Route C — BLOCKED', '#ef4444', { style: 'dotted', distanceKm: 11200, timeDays: 0, fuelLiters: 0, riskPercent: 95 }),
  ];
  const safestDetour = scenario === 2
    ? [[13.0827, 80.2707], [5, 78], [-15, 68], [-38, 53], [-55, 28], [-63, 4], [-68, 9], [-70.7644, 11.7386]]
    : voyage;
  return [
    route('safest', scenario === 2 ? 'Route A — Safest (Modified Detour)' : 'Route A — Safest', '#10b981', { distanceKm: scenario === 2 ? 12350 : 12200, timeDays: scenario === 2 ? 34.5 : 34, riskPercent: scenario === 2 ? 18 : scenario === 1 ? 12 : 8, coordinates: safestDetour }),
    route('fastest', 'Route B — Fastest', '#f59e0b', { style: 'dashed', distanceKm: 10500, timeDays: 28, fuelLiters: 168000, riskPercent: scenario === 2 ? 61 : scenario === 1 ? 52 : 38 }),
    route('fuel', 'Route C — Fuel-Efficient', '#f97316', { style: 'dotted', distanceKm: scenario === 2 ? 11500 : 11200, timeDays: scenario === 2 ? 32 : 31, fuelLiters: 152000, riskPercent: scenario === 2 ? 35 : 23 }),
  ];
};

const iceberg = (position, driftSpeedKnots) => ({ id: 'ICE-047', name: 'Iceberg ICE-047', position, sizeMeters: 800, length: 800, width: 600, confidence: 92, driftSpeedKnots, driftHeading: 45 });

export const SCENARIO_MOCKS = {
  0: {
    scenario: 0,
    time: 'Departure · 00:00 UTC', shipPosition: [13.0827, 80.2707],
    riskAssessment: { status: 'SAFE', iceConcentration: 68, nearestIceberg: null, collisionRisk: 0, temperature: -12, windSpeed: 35, windDirection: 'NE', windDegrees: 45, visibility: 'Good (>10 nm)' },
    icebergs: [], routes: routesFor(0),
    explanation: { headline: 'ALL SYSTEMS NORMAL', text: 'All systems normal. Safe to proceed on the current route. Weather conditions are favorable and no hazards are detected in the projected path.', confidence: 98 },
  },
  1: {
    scenario: 1,
    time: '06:00 UTC · 6 hours elapsed', shipPosition: [8.5, 82],
    riskAssessment: { status: 'CAUTION', iceConcentration: 68, nearestIceberg: 45, collisionRisk: 12, temperature: -12, windSpeed: 35, windDirection: 'NE', windDegrees: 45, visibility: 'Good (>10 nm)' },
    icebergs: [iceberg([-58.5, 42.0], 1.2)], routes: routesFor(1),
    explanation: { headline: 'NEW ICEBERG DETECTED — MONITORING', text: 'New iceberg ICE-047 detected at 58.5°S, 42.0°E. It is 800 m × 600 m and 45 km from the route. It is drifting northeast at 1.2 km/day. Route A remains unaffected; Route B risk has increased to 52%.', confidence: 92 },
  },
  2: {
    scenario: 2,
    // Waypoint on Route A's modified detour; the marker remains on the route.
    time: '18:00 UTC · 18 hours elapsed', shipPosition: [-55, 28],
    riskAssessment: { status: 'WARNING', iceConcentration: 72, nearestIceberg: 18, collisionRisk: 34, temperature: -12, windSpeed: 42, windDirection: 'NE', windDegrees: 45, visibility: 'Reduced (4 nm)' },
    icebergs: [iceberg([-65.20, -64.52], 2.1)], routes: routesFor(2),
    explanation: { headline: 'HAZARD APPROACHING — PREPARE RESPONSE', text: 'ICE-047 is now 18 km away. Drift prediction gives a 74% probability of intersecting Route A in approximately 18 hours. Route A has a 150 km safety detour; Route B risk is 61%. Recommended: accept the Route B northern detour for a safer balanced approach.', confidence: 94, actions: true },
  },
  3: {
    scenario: 3,
    // Route A remains the only viable route in the emergency scenario.
    time: '24:00 UTC · Emergency', shipPosition: [-66, 16],
    riskAssessment: { status: 'EMERGENCY', iceConcentration: 75, nearestIceberg: 3.2, collisionRisk: 87, temperature: -14, windSpeed: 48, windDirection: 'SW', windDegrees: 185, visibility: 'Poor (<1 nm)' },
    icebergs: [iceberg([-65.18, -64.48], 2.1)], routes: routesFor(3),
    explanation: { headline: 'CRITICAL — IMMEDIATE ACTION REQUIRED', text: 'Iceberg ICE-047 is 3.2 km ahead. Collision probability is 87%, with approximately 14 minutes to impact. Immediately change heading to 185° southwest and reduce speed to 8 knots. Routes B and C are blocked; Route A is the only viable route.', confidence: 99 },
  },
};

export const ICE_ZONES_DATA = [
  { name: 'Antarctic pack ice', concentration: 75, color: '#06b6d4', fillOpacity: 0.25, coordinates: [[-64, 5], [-63.5, 25], [-68.5, 26], [-69, 6]] },
  { name: 'Fast ice shelf', concentration: 95, color: '#3b82f6', fillOpacity: 0.35, coordinates: [[-69.5, 8], [-69.2, 16], [-71.2, 18], [-71.5, 10]] },
];

// Export helper for dynamic ship positioning
export { getShipPositionOnRoute };
