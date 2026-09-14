/** Four-step demo data matching the backend current_scenario values (0–3). */
const voyage = [
  [13.0827, 80.2707], [5, 78], [-10, 70], [-28, 60], [-45, 46], [-58, 28], [-66, 16], [-70.7644, 11.7386],
];

// Helper function to get ship position along a route based on scenario progress
const getShipPositionOnRoute = (routeCoordinates, scenario, routeId = '') => {
  if (!routeCoordinates || routeCoordinates.length === 0) return [13.0827, 80.2707];

  // Route A in scenario 3 only: ship has completed the journey — place at Maitri Station endpoint
  if ((routeId === 'safest') && scenario === 3) {
    return routeCoordinates[routeCoordinates.length - 1];
  }

  // All other routes / scenarios: progress-based position
  // 0 = 0%, 1 = 25%, 2 = 60%, 3 = 90%
  const progressMap = { 0: 0, 1: 0.25, 2: 0.6, 3: 0.9 };
  const progress = progressMap[scenario] ?? 0;
  const targetIndex = Math.floor((routeCoordinates.length - 1) * progress);
  return routeCoordinates[targetIndex] || routeCoordinates[0];
};

const route = (id, name, color, options = {}) => ({
  id, name, color, type: id, style: options.style || 'solid', width: options.width || 3,
  distanceKm: options.distanceKm || 12200, timeDays: options.timeDays ?? 34,
  fuelLiters: options.fuelLiters || 185000, riskPercent: options.riskPercent || 0,
  coordinates: options.coordinates || voyage,
  isSafest: id === 'safest', isFastest: id === 'fastest', isCheapest: id === 'fuel',
  // waiting-strategy fields (Route C only, Scenario 3)
  ...(options.waitingStrategy && {
    waitingStrategy: true,
    waitHours: options.waitHours,
    waitPosition: options.waitPosition,
    waitReason: options.waitReason,
  }),
});

const routesFor = (scenario) => {
  // Route A detour coords — used for scenario 2 AND scenario 3 (same safe eastern path)
  const safestDetour = [[13.0827, 80.2707], [5, 78], [-15, 68], [-38, 53], [-55, 28], [-63, 4], [-68, 9], [-70.7644, 11.7386]];

  // Route C holding-point coords — ship pauses at (-62, 18) while iceberg drifts past, then continues
  const fuelWaitCoords = [[13.0827, 80.2707], [5, 76], [-10, 68], [-28, 55], [-45, 40], [-52, 24], [-62, 18], [-66, 14], [-70.7644, 11.7386]];

  if (scenario === 3) return [
    // Route A — safe eastern detour, fully viable, AI recommended
    route('safest', 'Route A — Eastern Detour (AI Recommended)', '#10b981', {
      distanceKm: 12350, timeDays: 34.5, riskPercent: 18,
      coordinates: safestDetour,
    }),
    // Route B — blocked, direct collision with iceberg field
    route('fastest', 'Route B — COLLISION RISK (Blocked)', '#ef4444', {
      style: 'dashed', distanceKm: 10500, timeDays: 0, fuelLiters: 0, riskPercent: 98,
    }),
    // Route C — viable with waiting strategy, warning-level risk
    route('fuel', 'Route C — Holding Point (Wait & Proceed)', '#f97316', {
      style: 'dotted', distanceKm: 11400, timeDays: 33, fuelLiters: 155000, riskPercent: 42,
      coordinates: fuelWaitCoords,
      // flag for UI to show waiting behaviour
      waitingStrategy: true,
      waitHours: 6,
      waitPosition: [-62, 18],
      waitReason: 'Holding at safe position while ICE-047 drifts past the 13°E corridor',
    }),
  ];

  const routeACoords = scenario === 2 ? safestDetour : voyage;
  return [
    route('safest',
      scenario === 2 ? 'Route A — Safest (Modified Detour)' : 'Route A — Safest',
      '#10b981', {
        distanceKm: scenario === 2 ? 12350 : 12200,
        timeDays:   scenario === 2 ? 34.5  : 34,
        riskPercent: scenario === 2 ? 18 : scenario === 1 ? 12 : 8,
        coordinates: routeACoords,
      }),
    route('fastest', 'Route B — Fastest', '#f59e0b', {
      style: 'dashed', distanceKm: 10500, timeDays: 28, fuelLiters: 168000,
      riskPercent: scenario === 2 ? 61 : scenario === 1 ? 52 : 38,
    }),
    route('fuel', 'Route C — Fuel-Efficient', '#f97316', {
      style: 'dotted',
      distanceKm: scenario === 2 ? 11500 : 11200,
      timeDays:   scenario === 2 ? 32    : 31,
      fuelLiters: 152000,
      riskPercent: scenario === 2 ? 35 : 23,
      coordinates: fuelWaitCoords,
    }),
  ];
};

const iceberg = (position, driftSpeedKnots) => ({ id: 'ICE-047', name: 'Iceberg ICE-047', position, sizeMeters: 800, length: 800, width: 600, confidence: 92, driftSpeedKnots, driftHeading: 45 });

// ─── Per-route AI reasoning texts, keyed by scenario → route id ──────────────
export const ROUTE_REASONING = {
  0: {
    safest:  'Current conditions are stable and low-risk. Ice concentration near the Antarctic approach corridor is minimal, and no icebergs are detected along the projected track. For an Indian research expedition carrying critical cargo and scientists, the Eastern Ice-Avoidance Route provides maximum safety margin. It is slightly longer, but it protects mission timelines by reducing the probability of delays due to ice avoidance maneuvers later.',
    fastest: 'The Direct Southern Route minimizes travel time by taking a more direct southern approach. Under current conditions this is feasible, but it provides less buffer against sudden changes in sea-ice and weather systems in the Southern Ocean. Recommended only if there is a strict time window for station resupply and the captain is comfortable with reduced safety margin.',
    fuel:    'The Current-Assisted Western Route balances distance with fuel usage by aligning with favorable current corridors. It remains safe under current conditions and may reduce operational costs for the India–Antarctica voyage. Recommended when fuel economy is a priority. Safety margin is moderate — higher than the fastest route, slightly lower than the safest route.',
  },
  1: {
    safest:  'A new iceberg (ICE-047) has been detected, but proximity to the Eastern Ice-Avoidance Route remains outside the immediate danger threshold. Predicted drift does not indicate near-term intersection. Continuing on Route A is the most reliable option — no immediate course change is required, but hazard tracking is active.',
    fastest: 'The detected iceberg increases risk for the Direct Southern Route because this route passes closer to the hazard corridor. Even with current safe separation, forecast uncertainty grows over time and a small drift deviation could bring ICE-047 into the vessel\'s path. Avoid selecting Route B until the next satellite update confirms drift away from the corridor.',
    fuel:    'The Current-Assisted Western Route is moderately exposed to the iceberg drift zone but still maintains acceptable separation. If fuel savings are required this route can be considered with caution. The vessel\'s holding-point protocol provides an additional safety buffer — if the iceberg approaches, the ship can pause and wait for it to drift clear.',
  },
  2: {
    safest:  'ICE-047 has drifted closer with a 74% probability of intersecting the original Route A corridor within 18 hours. The Eastern Ice-Avoidance Route applies a controlled 150 km detour that restores full safety margin. This is the AI-recommended option — protecting crew, cargo, and scientific objectives is the highest priority. Accept the detour now.',
    fastest: 'Risk on the Direct Southern Route is now high. Drift forecasting shows ICE-047 moving directly toward the Route B corridor. Selecting Route B would require constant reactive maneuvers and could lead to a collision at Scenario 3. Recommendation: do not select Route B.',
    fuel:    'The Current-Assisted Western Route includes a strategic holding-point at 62°S where the ship can pause if the iceberg approaches. This waiting strategy adds approximately 6 hours but avoids the collision risk. Route C remains a viable, intelligent choice — the ship will wait for ICE-047 to drift past the 13°E corridor, then continue safely to Maitri.',
  },
  3: {
    safest:  'Route A (Eastern Ice-Avoidance Detour) is the AI-recommended safe corridor. It creates immediate separation from the ICE-047 hazard zone and bypasses all blocked channels. The ship is navigating around the iceberg field — all crew and cargo are safe. This is the correct decision.',
    fastest: 'ROUTE BLOCKED. ICE-047 is directly on the Route B corridor with 98% collision probability. The Direct Southern Route is impassable — attempting it would result in iceberg collision with no time to escape. This route is rejected by CryoNav AI.',
    fuel:    'Route C has entered its waiting protocol at the 62°S holding point. The ship is pausing safely while ICE-047 drifts past the 13°E navigation corridor. Estimated wait: 6 hours. Once the iceberg clears, the ship will proceed safely to Maitri Station. Final outcome: safe arrival with minor delay.',
  },
};

// ─── One-liner subtitles per scenario → route id ─────────────────────────────
export const ROUTE_SUBTITLES = {
  0: {
    safest:  'Maximum buffer for mission reliability',
    fastest: 'Direct track, lower safety margin',
    fuel:    'Balanced route with current-assisted savings',
  },
  1: {
    safest:  'Hazard detected — safe separation maintained',
    fastest: 'Risk rising — passes near iceberg corridor',
    fuel:    'Moderate exposure — holding-point protocol available',
  },
  2: {
    safest:  'Detour applied — AI recommended, restores full safety',
    fastest: 'High collision probability — avoid',
    fuel:    'Waiting strategy active — ship will pause and proceed safely',
  },
  3: {
    safest:  '✅ Safe corridor — AI recommended',
    fastest: '🚫 Blocked — collision with ICE-047',
    fuel:    '⏸ Holding point active — waiting for iceberg to clear',
  },
};

export const SCENARIO_MOCKS = {
  0: {
    scenario: 0,
    time: 'Departure · 00:00 UTC', shipPosition: [13.0827, 80.2707],
    riskAssessment: {
      status: 'GREEN',
      statusLabel: 'Safe Departure',
      message: 'All systems normal. Safe to proceed.',
      iceConcentration: 15, nearestIceberg: null, collisionRisk: 0,
      temperature: -12, windSpeed: 35, windDirection: 'NE', windDegrees: 45, visibility: 'Good (>10 nm)',
    },
    icebergs: [], routes: routesFor(0),
    explanation: {
      headline: 'ALL SYSTEMS NORMAL',
      text: 'Current conditions are stable and low-risk. Ice concentration near the Antarctic approach corridor is minimal at 15%, and no icebergs are detected within 100 km of the projected track. Weather conditions are favorable. All planned routes are safe for navigation. Continue on the Eastern Ice-Avoidance Route with standard monitoring protocols.',
      confidence: 98,
    },
  },
  1: {
    scenario: 1,
    time: '06:00 UTC · 6 hours elapsed', shipPosition: [8.5, 82],
    riskAssessment: {
      status: 'YELLOW',
      statusLabel: 'Iceberg Detected',
      message: 'Iceberg detected — monitoring situation.',
      iceConcentration: 32, nearestIceberg: 45, collisionRisk: 12,
      temperature: -12, windSpeed: 35, windDirection: 'NE', windDegrees: 45, visibility: 'Good (>10 nm)',
    },
    icebergs: [iceberg([-58.5, 42.0], 1.2)], routes: routesFor(1),
    explanation: {
      headline: 'NEW ICEBERG DETECTED — MONITORING',
      text: 'New iceberg ICE-047 detected at 58.5°S, 42.0°E. Size: 800 m × 600 m. Currently 45 km from Route A (Eastern Ice-Avoidance). Drift: northeast at 1.2 km/day. Route A remains unaffected with safe separation maintained. Route B (Direct Southern) risk has increased to 52% as it passes near the iceberg corridor. No immediate course change required — hazard tracking is active and next satellite pass scheduled in 6 hours.',
      confidence: 92,
    },
  },
  2: {
    scenario: 2,
    time: '18:00 UTC · 18 hours elapsed', shipPosition: [-55, 28],
    riskAssessment: {
      status: 'ORANGE',
      statusLabel: 'Danger Approaching',
      message: 'Warning — hazard approaching. Switch to Route A now.',
      iceConcentration: 58, nearestIceberg: 18, collisionRisk: 34,
      temperature: -12, windSpeed: 42, windDirection: 'NE', windDegrees: 45, visibility: 'Reduced (4 nm)',
    },
    icebergs: [
      iceberg([-60.8, 22.5], 2.1),
      { id: 'ICE-048', name: 'Iceberg ICE-048', position: [-66.2, 13.8], sizeMeters: 450, length: 450, width: 320, confidence: 88, driftSpeedKnots: 0.8, driftHeading: 352 },
    ],
    routes: routesFor(2),
    explanation: {
      headline: 'HAZARD APPROACHING — SWITCH TO ROUTE A',
      text: 'Iceberg ICE-047 is now 18 km away drifting northeast at 2.1 km/day. Drift prediction gives a 74% probability of intersecting the current corridor in approximately 18 hours. Recommendation: accept the Route A eastern detour — trade-off is slightly higher time and fuel cost, but collision probability drops from 34% to near-zero. Route B is now high-risk. Route C will activate its holding-point protocol at 62°S. Course adjustment must be initiated within the next 4 hours.',
      confidence: 94,
      actions: true,
    },
  },
  3: {
    scenario: 3,
    time: '24:00 UTC · Critical', shipPosition: [-66, 16],
    riskAssessment: {
      status: 'RED',
      statusLabel: 'EMERGENCY',
      message: 'EMERGENCY — Immediate collision risk. Route A is the ONLY safe option.',
      iceConcentration: 72, nearestIceberg: 3.2, collisionRisk: 87,
      temperature: -14, windSpeed: 48, windDirection: 'SW', windDegrees: 185, visibility: 'Poor (<1 nm)',
    },
    icebergs: [
      { id: 'ICE-047', name: 'Iceberg ICE-047', position: [-65.96, 15.82], sizeMeters: 800, length: 800, width: 600, confidence: 98, driftSpeedKnots: 0.5, driftHeading: 159 },
      { id: 'ICE-048', name: 'Iceberg ICE-048', position: [-66.5,  14.4],  sizeMeters: 450, length: 450, width: 320, confidence: 91, driftSpeedKnots: 0.6, driftHeading: 348 },
      { id: 'ICE-049', name: 'Iceberg ICE-049', position: [-65.88, 16.14], sizeMeters: 350, length: 350, width: 280, confidence: 85, driftSpeedKnots: 0.4, driftHeading: 162 },
    ],
    routes: routesFor(3),
    explanation: {
      headline: 'RED ALERT — SELECT ROUTE A OR WAIT ON ROUTE C',
      text: 'CRITICAL: Iceberg ICE-047 is 3.2 km ahead on the current corridor. Collision probability 87% in ~14 minutes. Route B is blocked — direct collision hazard. Route A (Eastern Detour) is the safest immediate escape. Route C has activated its holding-point protocol at 62°S — the ship will pause for ~6 hours while ICE-047 drifts clear, then proceed safely. Do NOT stay on Route B.',
      confidence: 99,
    },
  },
};

export const ICE_ZONES_DATA = [
  { name: 'Antarctic pack ice', concentration: 75, color: '#06b6d4', fillOpacity: 0.25, coordinates: [[-64, 5], [-63.5, 25], [-68.5, 26], [-69, 6]] },
  { name: 'Fast ice shelf', concentration: 95, color: '#3b82f6', fillOpacity: 0.35, coordinates: [[-69.5, 8], [-69.2, 16], [-71.2, 18], [-71.5, 10]] },
];

// Export helper for dynamic ship positioning
export { getShipPositionOnRoute };
