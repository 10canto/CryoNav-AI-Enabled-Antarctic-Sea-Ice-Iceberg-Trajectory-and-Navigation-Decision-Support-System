import type { Iceberg, LatLon, Route } from './types';

const R_KM = 6371;
const rad = (d: number) => (d * Math.PI) / 180;

export function haversineKm(a: LatLon, b: LatLon): number {
  const dLat = rad(b.lat - a.lat);
  const dLon = rad(b.lon - a.lon);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLon / 2) ** 2;
  return 2 * R_KM * Math.asin(Math.min(1, Math.sqrt(h)));
}

export function pathKm(pts: LatLon[]): number {
  let s = 0;
  for (let i = 1; i < pts.length; i++) s += haversineKm(pts[i - 1], pts[i]);
  return s;
}

/** Distance from point to a polyline in km (local equirectangular approximation, fine at this scale). */
export function distToPolylineKm(p: LatLon, line: LatLon[]): number {
  if (line.length === 0) return Infinity;
  if (line.length === 1) return haversineKm(p, line[0]);
  const kx = 111.2 * Math.cos(rad(p.lat));
  const ky = 111.2;
  let best = Infinity;
  for (let i = 1; i < line.length; i++) {
    const ax = (line[i - 1].lon - p.lon) * kx;
    const ay = (line[i - 1].lat - p.lat) * ky;
    const bx = (line[i].lon - p.lon) * kx;
    const by = (line[i].lat - p.lat) * ky;
    const dx = bx - ax;
    const dy = by - ay;
    const len2 = dx * dx + dy * dy;
    const t = len2 === 0 ? 0 : Math.max(0, Math.min(1, -(ax * dx + ay * dy) / len2));
    best = Math.min(best, Math.hypot(ax + t * dx, ay + t * dy));
  }
  return best;
}

export interface BBox {
  minLat: number;
  maxLat: number;
  minLon: number;
  maxLon: number;
}

export function routeBBox(route: Route, marginDeg: number): BBox | null {
  if (route.waypoints.length === 0) return null;
  const lats = route.waypoints.map((w) => w.lat);
  const lons = route.waypoints.map((w) => w.lon);
  return {
    minLat: Math.min(...lats) - marginDeg,
    maxLat: Math.max(...lats) + marginDeg,
    minLon: Math.min(...lons) - marginDeg,
    maxLon: Math.max(...lons) + marginDeg,
  };
}

/**
 * Only icebergs inside the route bounding box (+ margin), nearest to the route first.
 * `max` caps the marker count so the map stays responsive.
 */
export function filterIcebergsForRoute(all: Iceberg[], route: Route, marginDeg = 3.5, max = 150): Iceberg[] {
  const box = routeBBox(route, marginDeg);
  if (!box) return [];
  return all
    .filter((b) => b.lat >= box.minLat && b.lat <= box.maxLat && b.lon >= box.minLon && b.lon <= box.maxLon)
    .map((b) => ({ b, d: distToPolylineKm(b, route.waypoints) }))
    .sort((x, y) => x.d - y.d)
    .slice(0, max)
    .map((x) => x.b);
}
