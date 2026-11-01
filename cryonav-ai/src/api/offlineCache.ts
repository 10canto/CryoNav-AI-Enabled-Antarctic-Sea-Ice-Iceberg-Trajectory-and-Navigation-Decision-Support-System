/**
 * Offline Cache - Fallback data when backend is unreachable
 */
import type { Iceberg, Route, RiskAssessment, RouteExplanation, DriftPrediction } from './client';

export interface CachedData {
  icebergs?: Iceberg[];
  routes?: Route[];
  risk?: RiskAssessment;
  explanations?: Record<string, RouteExplanation>;
  predictions?: Record<string, DriftPrediction>;
  timestamp?: string;
}

let cache: CachedData = {};
let cacheLoaded = false;

/**
 * Load offline cache from public/demo/cache/
 */
export async function loadOfflineCache(): Promise<void> {
  if (cacheLoaded) return;
  
  try {
    // Try to load demo cache
    const response = await fetch('/demo/cache/snapshot.json');
    if (response.ok) {
      cache = await response.json();
      console.log('[Offline Cache] Loaded snapshot:', Object.keys(cache));
    }
  } catch (error) {
    console.warn('[Offline Cache] No snapshot available');
  }
  
  cacheLoaded = true;
}

/**
 * Get cached icebergs
 */
export function getCachedIcebergs(): Iceberg[] {
  return cache.icebergs || [];
}

/**
 * Get cached routes
 */
export function getCachedRoutes(): Route[] {
  return cache.routes || [];
}

/**
 * Get cached risk assessment
 */
export function getCachedRisk(): RiskAssessment | null {
  return cache.risk || null;
}

/**
 * Get cached explanation for route
 */
export function getCachedExplanation(routeId: string): RouteExplanation | null {
  if (!cache.explanations) return null;
  return cache.explanations[routeId] || null;
}

/**
 * Get cached prediction for iceberg
 */
export function getCachedPrediction(icebergId: string): DriftPrediction | null {
  if (!cache.predictions) return null;
  return cache.predictions[icebergId] || null;
}

/**
 * Update cache with fresh data (when online)
 */
export function updateCache(key: keyof CachedData, data: any): void {
  cache[key] = data;
  cache.timestamp = new Date().toISOString();
}

/**
 * Check if cache is available
 */
export function hasCachedData(): boolean {
  return Object.keys(cache).length > 0;
}
