// Generates PLACEHOLDER demo data: public/demo/scenario.json and public/demo/cache/*.json
// Run: node scripts/gen-placeholder.mjs   (from web/)
// All numbers are invented filler. Replace scenario.json with real scripted data later
// (see docs/demo_scenario_schema.md).
import { mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const outDir = fileURLToPath(new URL('../public/demo/', import.meta.url));
mkdirSync(outDir + 'cache', { recursive: true });

const R = 6371;
const rad = (d) => (d * Math.PI) / 180;
const hav = (a, b) => {
  const dLat = rad(b[0] - a[0]);
  const dLon = rad(b[1] - a[1]);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a[0])) * Math.cos(rad(b[0])) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
};
const pathKm = (pts) => pts.slice(1).reduce((s, p, i) => s + hav(pts[i], p), 0);
const round = (n, d = 0) => Math.round(n * 10 ** d) / 10 ** d;

const CT = [-33.92, 18.43];
const EDGE = [-70.3, 11.7];
const BOUVET = [-54.4, 3.4];

// Full base routes (Cape Town -> approximate ice edge). Lat, lon.
const A = [CT, [-40, 14], [-48, 8.5], [-56, 8], [-63, 8.5], [-67.5, 10], EDGE]; // west corridor
const B = [CT, [-40, 16.5], [-50, 14], [-60, 12.5], [-66, 12], EDGE]; // direct
const C = [CT, [-36.5, 14], [-43, 9], [-50, 12], [-57, 9.5], [-63, 12.5], [-67, 10.5], EDGE]; // S-curve

const COLORS = { a: '#3fb950', b: '#e3b341', c: '#f0883e' };
const SPEED_KMH = { a: 20, b: 24, c: 20 };
const FUEL_FACTOR = { a: 1.0, b: 1.14, c: 0.9 };
const START = Date.parse('2026-01-12T08:00:00Z');

// Sanity: stay well clear of Bouvet Island
for (const [n, r] of Object.entries({ A, B, C })) {
  const d = Math.min(...r.map((p) => hav(p, BOUVET)));
  if (d < 250) throw new Error(`route ${n} passes ${d.toFixed(0)} km from Bouvet`);
}

const remaining = (base, ship) => [ship, ...base.filter((p) => p[0] < ship[0] - 0.5)];

function mkRoute(id, name, pts, startMs, score, reasons, minRaw) {
  const dist = pathKm(pts);
  let cum = 0;
  const waypoints = pts.map((p, i) => {
    if (i > 0) cum += hav(pts[i - 1], p);
    return { lat: p[0], lon: p[1], eta: new Date(startMs + (cum / SPEED_KMH[id]) * 3600e3).toISOString() };
  });
  return {
    id: `route-${id}`,
    name,
    color: COLORS[id],
    waypoints,
    distance_km: round(dist),
    duration_days: round(dist / SPEED_KMH[id] / 24, 1),
    fuel_raw: dist * FUEL_FACTOR[id],
    risk_score: score,
    reasons,
    _minRaw: minRaw,
  };
}

function finishRoutes(routes) {
  const min = Math.min(...routes.map((r) => r.fuel_raw));
  return routes.map((r) => {
    const { fuel_raw, _minRaw, ...rest } = r;
    return { ...rest, fuel_index: Math.round((fuel_raw / min) * 100) };
  });
}

const levelFromScore = (s) => (s < 25 ? 'GREEN' : s < 50 ? 'YELLOW' : s < 75 ? 'ORANGE' : 'RED');

const dp = (arr) => arr.map(([hours, lat, lon, u]) => ({ hours, lat, lon, uncertainty_radius_km: u }));
const TE = 'track extrapolation';
const CB = 'current-based fallback';

const ib = {
  101: (lat, lon, drift) => ({ id: 'ICE-101', lat, lon, size_m: 400, method: TE, drift_path: dp(drift) }),
  102: () => ({
    id: 'ICE-102', lat: -64.5, lon: 3.5, size_m: 250, method: TE,
    drift_path: dp([[24, -64.5, 3.9, 7], [48, -64.5, 4.3, 16], [72, -64.5, 4.7, 26]]),
  }),
  103: () => ({
    id: 'ICE-103', lat: -61, lon: 18.5, size_m: 600, method: CB,
    drift_path: dp([[24, -61, 18.9, 9], [48, -61, 19.3, 20], [72, -61, 19.7, 32]]),
  }),
  104: (lat, lon, drift) => ({ id: 'ICE-104', lat, lon, size_m: 520, method: CB, drift_path: dp(drift) }),
  105: () => ({
    id: 'ICE-105', lat: -65.5, lon: 9.5, size_m: 300, method: TE,
    drift_path: dp([[24, -65.5, 9.9, 8], [48, -65.5, 10.3, 17], [72, -65.5, 10.7, 28]]),
  }),
};

const shipIdx = [0, 1, 2, 3];
const shipPos = shipIdx.map((i) => A[i]);
const dateAt = (i) => {
  const km = pathKm(A.slice(0, i + 1));
  return new Date(START + (km / 20) * 3600e3).toISOString().slice(0, 10);
};

const FAMILY = 'Family contacts (pre-authorized only)';

function whatif(selected, risk, berg, deltas) {
  const base = {
    risk_level: levelFromScore(selected.risk_score),
    risk_score: selected.risk_score,
    distance_km: selected.distance_km,
    duration_days: selected.duration_days,
    fuel_index: selected.fuel_index,
  };
  const mk = (label, dScore, dDays, dFuel, dDist = 0) => {
    const score = Math.max(0, Math.min(100, selected.risk_score + dScore));
    return {
      label,
      before: base,
      after: {
        risk_level: levelFromScore(score),
        risk_score: score,
        distance_km: round(base.distance_km + dDist),
        duration_days: round(base.duration_days + dDays, 1),
        fuel_index: base.fuel_index + dFuel,
      },
    };
  };
  return [
    mk('Delay departure by 12 h', deltas[0], 0.5, 0),
    mk('Wind +20 km/h (headwind)', deltas[1], 0.4, 6),
    mk(`${berg} moves 15 km north`, deltas[2], 0, 0),
  ];
}

function buildStep(i, cfg) {
  const ship = shipPos[i];
  const startMs = Date.parse(dateAt(i) + 'T08:00:00Z');
  const routes = finishRoutes([
    mkRoute('a', cfg.names.a, cfg.pts.a, startMs, cfg.scores[0], cfg.reasons.a),
    mkRoute('b', cfg.names.b, cfg.pts.b, startMs, cfg.scores[1], cfg.reasons.b),
    mkRoute('c', cfg.names.c, cfg.pts.c, startMs, cfg.scores[2], cfg.reasons.c),
  ]);
  const selected = routes[0];
  return {
    title: cfg.title,
    label: cfg.label,
    date: dateAt(i),
    ship: { lat: ship[0], lon: ship[1] },
    icebergs: cfg.icebergs,
    routes,
    selected_route_id: selected.id,
    risk: { level: cfg.level, reasons: cfg.riskReasons },
    explanation_text: cfg.explanation,
    alert: cfg.alert ? { recipients: ['Mission Control', 'Rescue Coordination Centre', FAMILY], simulated: true } : null,
    whatif: whatif(selected, cfg.level, cfg.whatifBerg, cfg.deltas),
  };
}

const NAMES = { a: 'Safest - west corridor', b: 'Fastest - direct', c: 'Fuel-efficient - current bands' };

const steps = [
  buildStep(0, {
    title: 'Baseline - all clear',
    label: 'Baseline',
    level: 'GREEN',
    names: NAMES,
    pts: { a: A, b: B, c: C },
    scores: [12, 22, 18],
    reasons: {
      a: ['No tracked iceberg within 150 km of the route'],
      b: ['Shortest, passes nearest to ICE-103 (about 170 km)'],
      c: ['Longer, uses monthly-average current bands'],
    },
    icebergs: [
      ib[101](-58.5, 2.0, [[24, -58.4, 2.8, 8], [48, -58.3, 3.5, 17], [72, -58.2, 4.3, 28]]),
      ib[102](),
      ib[103](),
    ],
    riskReasons: [
      'No tracked iceberg within 150 km of the selected route (scripted)',
      'Seasonal sea-ice model: open water along the corridor',
    ],
    explanation:
      'Scripted baseline. All three candidate routes keep well clear of the three tracked icebergs. The west corridor (about 8-10 E, clear of Bouvet Island) is selected because it has the lowest model risk score. The direct route is shorter; the current-band route trades distance for a lower fuel index. Placeholder figures.',
    alert: false,
    whatifBerg: 'ICE-101',
    deltas: [0, 2, 1],
  }),
  buildStep(1, {
    title: 'Timing - an iceberg drifts toward the corridor',
    label: 'Timing',
    level: 'YELLOW',
    names: NAMES,
    pts: { a: A.slice(1), b: remaining(B, shipPos[1]), c: remaining(C, shipPos[1]) },
    scores: [30, 36, 33],
    reasons: {
      a: ['ICE-101 drift path comes within about 40 km of the route near 57 S'],
      b: ['Passes east of ICE-101 drift path'],
      c: ['Crosses the ICE-101 drift cone margin near 57 S'],
    },
    icebergs: [
      ib[101](-58.0, 4.3, [[24, -57.9, 5.1, 8], [48, -57.7, 6.0, 18], [72, -57.5, 6.9, 30]]),
      ib[102](),
      ib[103](),
    ],
    riskReasons: [
      'ICE-101 predicted drift (track extrapolation) approaches the route near 57 S',
      'Ship would reach that latitude inside the 72 h window',
      'Margin to the uncertainty circle is about 40 km (scripted)',
    ],
    explanation:
      'Timing matters here. ICE-101 is moving east and its 48-72 h uncertainty circles approach the planned corridor around the time the ship would pass 57 S. The route still has the lowest score, so it stays selected, but the margin is smaller than at baseline. Placeholder figures.',
    alert: false,
    whatifBerg: 'ICE-101',
    deltas: [-8, 4, 12],
  }),
  buildStep(2, {
    title: 'New iceberg - ICE-104 appears near the corridor',
    label: 'New iceberg',
    level: 'ORANGE',
    names: NAMES,
    pts: { a: A.slice(2), b: remaining(B, shipPos[2]), c: remaining(C, shipPos[2]) },
    scores: [52, 60, 55],
    reasons: {
      a: ['ICE-104 drift path crosses the route near 63 S within 48-72 h'],
      b: ['ICE-104 drift path ends about 150 km west of the route'],
      c: ['Close to ICE-104 and ICE-105 drift cones'],
    },
    icebergs: [
      ib[101](-58.3, 5.0, [[24, -58.2, 5.6, 8], [48, -58.1, 6.2, 18], [72, -58.0, 6.8, 30]]),
      ib[102](),
      ib[103](),
      ib[104](-63.5, 6.8, [[24, -63.4, 7.4, 10], [48, -63.3, 8.1, 22], [72, -63.2, 8.9, 35]]),
    ],
    riskReasons: [
      'New iceberg ICE-104 detected; few observations, so the current-based fallback is used',
      'Its drift path crosses the selected route near 63 S within 48-72 h',
      'Uncertainty is large (35 km at 72 h)',
    ],
    explanation:
      'A new iceberg, ICE-104, has been added. With only a short observation history the drift uses the current-based fallback, so its uncertainty circles are wide. Its predicted path crosses the selected route near 63 S. Every route is now moderately risky; reroute options are being weighed. Placeholder figures.',
    alert: false,
    whatifBerg: 'ICE-104',
    deltas: [-10, 5, 18],
  }),
  buildStep(3, {
    title: 'Reroute + alert - corridor blocked',
    label: 'Reroute + alert',
    level: 'RED',
    names: { a: 'Safest - east arc', b: 'Fastest - direct (blocked)', c: 'Fuel-efficient - S-curve' },
    pts: {
      a: [shipPos[3], [-57, 15], [-63, 15.5], [-68, 13], EDGE],
      b: [shipPos[3], [-60, 10.5], [-65, 11], EDGE],
      c: [shipPos[3], [-59, 11], [-63, 12.5], [-66.5, 10.5], EDGE],
    },
    scores: [34, 88, 58],
    reasons: {
      a: ['Keeps about 80 km or more from every drift cone', 'Longest of the three'],
      b: ['Passes within the ICE-104 uncertainty circle'],
      c: ['Close to ICE-105 drift cone'],
    },
    icebergs: [
      ib[101](-58.0, 5.9, [[24, -57.9, 6.5, 8], [48, -57.8, 7.1, 18], [72, -57.7, 7.7, 30]]),
      ib[102](),
      ib[103](),
      ib[104](-63.0, 8.3, [[24, -62.9, 8.8, 9], [48, -62.8, 9.3, 19], [72, -62.7, 9.8, 30]]),
      ib[105](),
    ],
    riskReasons: [
      'Previous plan (west corridor) now lies inside the ICE-104 uncertainty circle: RED',
      'Rerouted plan via the east arc is selected (score 34, residual risk)',
      'Simulated alert prepared for the recipients below',
    ],
    explanation:
      'ICE-104 now sits on the original west corridor and its 24-72 h circles keep covering it, so the previous plan is rated RED. The system recomputed routes from the current ship position. The east arc keeps the most distance from every drift cone at the cost of extra days. The alert is simulated: nothing is sent. Placeholder figures.',
    alert: true,
    whatifBerg: 'ICE-104',
    deltas: [-4, 3, 16],
  }),
];

const scenario = {
  title: 'Cape Town to Maitri - scripted scenario (PLACEHOLDER DATA)',
  placeholder: true,
  note: 'Invented filler data for UI development. Replace with the real scripted scenario.',
  steps,
};
writeFileSync(outDir + 'scenario.json', JSON.stringify(scenario, null, 1));

// Offline snapshot for Live mode (taken from the "New iceberg" step)
const snap = steps[2];
const w = (name, data) => writeFileSync(outDir + 'cache/' + name, JSON.stringify(data, null, 1));
w('icebergs.json', snap.icebergs);
w('routes.json', snap.routes);
w('risk.json', snap.risk);
w('explain.json', { text: snap.explanation_text });
w('alert.json', steps[3].alert);
console.log('wrote scenario.json and cache/*.json');
for (const s of steps) console.log(s.date, s.risk.level, s.routes.map((r) => `${r.id}:${r.distance_km}km/${r.duration_days}d/fuel${r.fuel_index}`).join(' '));
