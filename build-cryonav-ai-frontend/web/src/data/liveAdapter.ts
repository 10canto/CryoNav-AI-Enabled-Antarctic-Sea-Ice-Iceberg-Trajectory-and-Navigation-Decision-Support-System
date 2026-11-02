/**
 * Maps the backend's response shapes onto the domain types. Tolerant by design:
 * several key spellings are accepted, missing fields become undefined / NaN
 * (NaN = "not provided", the UI shows "-"), and nothing here throws on odd input.
 *
 * Shapes handled (ASSUMED, see README "Assumptions"; adjust ONLY this file if the API differs):
 *   /icebergs        -> [] | { icebergs: [] } | GeoJSON FeatureCollection
 *   /predict-drift   -> { trajectory|drift_path|path|predictions: [{hours,lat,lon,uncertainty_*}], method? }
 *   /calculate-routes-> { routes: [{id,name,waypoints|path|coordinates,distance_km,duration_days,fuel_*,risk_*}] }
 *   /risk            -> { level|risk_level, reasons|factors, score? }
 *   /explain         -> { explanation|text|message } | string
 *   /alert           -> { recipients: [] , ... }
 */
import { pathKm } from '../domain/geo';
import type { Alert, DriftPoint, Iceberg, LatLon, Risk, RiskLevel, Route, Waypoint } from '../domain/types';
import { RISK_LEVELS } from '../domain/types';
import { levelFromScore } from '../utils/risk';

type Obj = Record<string, unknown>;
const isObj = (v: unknown): v is Obj => typeof v === 'object' && v !== null && !Array.isArray(v);

export const num = (v: unknown): number | undefined => {
  const n = typeof v === 'string' ? parseFloat(v) : v;
  return typeof n === 'number' && Number.isFinite(n) ? n : undefined;
};

function pick(o: Obj, ...keys: string[]): unknown {
  for (const k of keys) if (o[k] !== undefined && o[k] !== null) return o[k];
  return undefined;
}

function asArray(raw: unknown, ...keys: string[]): unknown[] {
  if (Array.isArray(raw)) return raw;
  if (isObj(raw)) {
    for (const k of keys) if (Array.isArray(raw[k])) return raw[k] as unknown[];
    for (const k of Object.keys(raw)) if (Array.isArray(raw[k])) return raw[k] as unknown[];
  }
  return [];
}

function asStrings(v: unknown): string[] {
  if (typeof v === 'string') return v ? [v] : [];
  if (!Array.isArray(v)) return [];
  return v
    .map((x) => {
      if (typeof x === 'string') return x;
      if (isObj(x)) {
        const t = pick(x, 'message', 'text', 'reason', 'description', 'name', 'factor');
        return typeof t === 'string' ? t : '';
      }
      return '';
    })
    .filter(Boolean);
}

/** Parses {lat,lon|lng|longitude}, [lat,lon] (assumed), GeoJSON Point / [lon,lat] when marked as GeoJSON. */
export function parsePos(v: unknown, geoJsonOrder = false): LatLon | null {
  if (Array.isArray(v) && v.length >= 2) {
    const a = num(v[0]);
    const b = num(v[1]);
    if (a === undefined || b === undefined) return null;
    if (geoJsonOrder || Math.abs(a) > 90) return { lat: b, lon: a };
    return { lat: a, lon: b };
  }
  if (isObj(v)) {
    if (v.type === 'Point' && Array.isArray(v.coordinates)) return parsePos(v.coordinates, true);
    const lat = num(pick(v, 'lat', 'latitude'));
    const lon = num(pick(v, 'lon', 'lng', 'long', 'longitude'));
    if (lat !== undefined && lon !== undefined) return { lat, lon };
    for (const k of ['position', 'location', 'centroid', 'coordinates', 'geometry']) {
      if (v[k] !== undefined) return parsePos(v[k], k === 'geometry');
    }
  }
  return null;
}

export function normMethod(v: unknown): string | undefined {
  if (typeof v !== 'string' || !v.trim()) return undefined;
  if (/track|extrap/i.test(v)) return 'track extrapolation';
  if (/current|fallback/i.test(v)) return 'current-based fallback';
  return v;
}

// ------------------------------------------------------------------ icebergs

export function adaptIcebergs(raw: unknown): Iceberg[] {
  const out: Iceberg[] = [];
  asArray(raw, 'icebergs', 'features', 'data', 'items', 'results').forEach((item, i) => {
    if (!isObj(item)) return;
    // GeoJSON Feature: merge properties, take geometry as position
    const flat: Obj = item.type === 'Feature' && isObj(item.properties) ? { ...item.properties, geometry: item.geometry } : item;
    const pos = parsePos(flat);
    if (!pos) return;
    const id = String(pick(flat, 'id', 'iceberg_id', 'icebergId', 'name', 'uid') ?? `ICE-${i + 1}`);
    const drift = pick(flat, 'drift_path', 'trajectory');
    out.push({
      id,
      lat: pos.lat,
      lon: pos.lon,
      size_m: num(pick(flat, 'size_m', 'length_m', 'size', 'length', 'width_m')),
      method: normMethod(pick(flat, 'method', 'drift_method', 'prediction_method', 'model')),
      drift_path: drift ? adaptDrift({ drift_path: drift }).drift_path : [],
    });
  });
  return out;
}

export function adaptDrift(raw: unknown): { drift_path: DriftPoint[]; method?: string } {
  const list = asArray(raw, 'drift_path', 'trajectory', 'path', 'predictions', 'forecast', 'points', 'positions');
  const pts: DriftPoint[] = [];
  list.forEach((item, i) => {
    if (!isObj(item)) return;
    const pos = parsePos(item);
    if (!pos) return;
    const hours = num(pick(item, 'hours', 'hour', 't', 'time_h', 'lead_time_h', 'horizon', 'step_hours')) ?? (i + 1) * 24;
    pts.push({
      hours,
      ...pos,
      uncertainty_radius_km:
        num(pick(item, 'uncertainty_radius_km', 'uncertainty_km', 'radius_km', 'error_km', 'sigma_km', 'uncertainty')) ?? 0,
    });
  });
  const method = isObj(raw) ? normMethod(pick(raw, 'method', 'drift_method', 'prediction_method', 'model')) : undefined;
  return { drift_path: pts, method };
}

// ------------------------------------------------------------------ routes

const fin = (x: number) => (Number.isFinite(x) ? x : Infinity);
const ROLE_NAMES = ['Safest', 'Fastest', 'Fuel-efficient'];
const ROLE_COLORS = ['#111111', '#3C4043', '#5F6368']; // Near-black, mid-grey, soft-grey for light theme

function parseWaypoints(v: unknown): Waypoint[] {
  let list: unknown[] = [];
  let geo = false;
  if (Array.isArray(v)) list = v;
  else if (isObj(v) && Array.isArray(v.coordinates)) {
    list = v.coordinates;
    geo = true; // GeoJSON LineString: [lon, lat]
  }
  const out: Waypoint[] = [];
  for (const item of list) {
    const p = parsePos(item, geo);
    if (!p) continue;
    const eta = isObj(item) ? pick(item, 'eta', 'time', 'timestamp') : undefined;
    out.push({ ...p, eta: typeof eta === 'string' ? eta : undefined });
  }
  return out;
}

export function adaptRoutes(raw: unknown): Route[] {
  const items = asArray(raw, 'routes', 'alternatives', 'options', 'results', 'data');
  interface Draft {
    id: string;
    name?: string;
    waypoints: Waypoint[];
    distance: number;
    duration: number;
    fuelRaw?: number;
    fuelIsIndex: boolean;
    score: number;
    reasons: string[];
  }
  const drafts: Draft[] = [];
  items.forEach((item, i) => {
    if (!isObj(item)) return;
    const waypoints = parseWaypoints(pick(item, 'waypoints', 'path', 'coordinates', 'geometry', 'polyline', 'points', 'route'));
    if (waypoints.length < 2) return;
    const nm = num(pick(item, 'distance_nm'));
    const distance = num(pick(item, 'distance_km', 'distance', 'total_distance_km', 'length_km')) ?? (nm !== undefined ? nm * 1.852 : pathKm(waypoints));
    const hours = num(pick(item, 'duration_hours', 'hours'));
    const duration = num(pick(item, 'duration_days', 'days', 'eta_days', 'duration')) ?? (hours !== undefined ? hours / 24 : NaN);
    const fuelIdx = num(pick(item, 'fuel_index'));
    const fuelRaw = fuelIdx ?? num(pick(item, 'fuel_liters', 'fuelLiters', 'fuel_l', 'fuel', 'fuel_consumption'));
    let score = num(pick(item, 'risk_score', 'riskScore', 'risk', 'score')) ?? NaN;
    if (Number.isFinite(score) && score <= 1) score *= 100;
    const nameRaw = pick(item, 'name', 'label', 'type', 'strategy');
    drafts.push({
      id: String(pick(item, 'id', 'route_id', 'routeId') ?? `route-${i + 1}`),
      name: typeof nameRaw === 'string' ? nameRaw : undefined,
      waypoints,
      distance,
      duration,
      fuelRaw,
      fuelIsIndex: fuelIdx !== undefined,
      score,
      reasons: asStrings(pick(item, 'reasons', 'risk_reasons', 'factors', 'warnings')),
    });
  });

  // roles: safest = lowest risk, fastest = shortest duration (of the rest), remaining = fuel-efficient
  const order = drafts.map((_, i) => i);
  const roleOf = new Map<number, number>();
  const bySafe = [...order].sort((a, b) => fin(drafts[a].score) - fin(drafts[b].score));
  if (bySafe.length) roleOf.set(bySafe[0], 0);
  const rest = order.filter((i) => !roleOf.has(i)).sort((a, b) => fin(drafts[a].duration) - fin(drafts[b].duration));
  if (rest.length) roleOf.set(rest[0], 1);
  order.filter((i) => !roleOf.has(i)).forEach((i) => roleOf.set(i, 2));

  const fuelVals = drafts.filter((d) => !d.fuelIsIndex && d.fuelRaw !== undefined && d.fuelRaw > 0).map((d) => d.fuelRaw as number);
  const minFuel = fuelVals.length ? Math.min(...fuelVals) : undefined;

  return drafts.map((d, i) => {
    const role = roleOf.get(i) ?? 2;
    let fuel_index = NaN;
    if (d.fuelRaw !== undefined) {
      // Backend litres (if any) are converted to a RELATIVE index; litres are never displayed.
      fuel_index = d.fuelIsIndex ? d.fuelRaw : minFuel ? Math.round((d.fuelRaw / minFuel) * 100) : NaN;
    }
    return {
      id: d.id,
      name: d.name ? (/safest|fastest|fuel/i.test(d.name) ? d.name : `${ROLE_NAMES[role]}: ${d.name}`) : ROLE_NAMES[role],
      color: ROLE_COLORS[role],
      waypoints: d.waypoints,
      distance_km: d.distance,
      duration_days: d.duration,
      fuel_index,
      risk_score: d.score,
      reasons: d.reasons,
    };
  });
}

// ------------------------------------------------------------------ risk / explain / alert

export function adaptRisk(raw: unknown, fallbackScore?: number): Risk {
  const o: Obj = isObj(raw) ? raw : {};
  const lv = pick(o, 'level', 'risk_level', 'riskLevel', 'category', 'status', 'rating');
  let level: RiskLevel | undefined;
  if (typeof lv === 'string' && (RISK_LEVELS as string[]).includes(lv.toUpperCase())) level = lv.toUpperCase() as RiskLevel;
  if (!level) {
    const sc = num(pick(o, 'risk_score', 'score', 'risk')) ?? fallbackScore;
    level = sc !== undefined && Number.isFinite(sc) ? levelFromScore(sc) : 'YELLOW';
  }
  return { level, reasons: asStrings(pick(o, 'reasons', 'risk_reasons', 'factors', 'warnings', 'details')) };
}

export function adaptExplain(raw: unknown): string {
  if (typeof raw === 'string') return raw;
  if (isObj(raw)) {
    const t = pick(raw, 'explanation', 'explanation_text', 'text', 'message', 'summary', 'response', 'content');
    if (typeof t === 'string') return t;
  }
  return '';
}

export function adaptAlert(raw: unknown, fallbackRecipients: string[]): Alert {
  const o: Obj = isObj(raw) ? raw : {};
  const r = pick(o, 'recipients', 'notified', 'contacts', 'to');
  const recipients = asStrings(r);
  // Alerts are always labelled simulated in this UI, whatever the backend says.
  return { recipients: recipients.length ? recipients : fallbackRecipients, simulated: true };
}
