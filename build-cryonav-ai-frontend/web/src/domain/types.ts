/**
 * Domain types for CryoNav AI.
 * Everything the UI and the map know about is expressed in these types.
 * Backend response shapes are mapped onto them in src/data/liveAdapter.ts.
 * Coordinates are always decimal degrees (lat, lon). Distances are km.
 */

export type RiskLevel = 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED';

export const RISK_LEVELS: RiskLevel[] = ['GREEN', 'YELLOW', 'ORANGE', 'RED'];

export interface LatLon {
  lat: number;
  lon: number;
}

/** One predicted position of an iceberg `hours` after the snapshot. */
export interface DriftPoint {
  hours: number;
  lat: number;
  lon: number;
  uncertainty_radius_km: number;
}

export interface Iceberg {
  id: string;
  lat: number;
  lon: number;
  /** Approximate length in metres (may be missing). */
  size_m?: number;
  /** "track extrapolation" | "current-based fallback" (free text tolerated). */
  method?: string;
  /** Empty when drift has not been requested yet (live mode loads it on click). */
  drift_path: DriftPoint[];
}

export interface Waypoint {
  lat: number;
  lon: number;
  /** ISO-8601 timestamp, optional. */
  eta?: string;
}

export interface Route {
  id: string;
  name: string;
  /** CSS color for line (ignored by MapController which uses position-based styling) */
  color: string;
  waypoints: Waypoint[];
  distance_km: number;
  duration_days: number;
  /** Relative index, 100 = the route with the lowest fuel use in this set. Not litres. */
  fuel_index: number;
  /** 0-100, higher is riskier. Model-defined, not a probability. */
  risk_score: number;
  reasons: string[];
}

export interface Risk {
  level: RiskLevel;
  reasons: string[];
}

export interface Alert {
  recipients: string[];
  simulated: true;
}

/** Numbers shown on one side of a What-If comparison. */
export interface WhatIfOutcome {
  risk_level: RiskLevel;
  risk_score: number;
  distance_km?: number;
  duration_days?: number;
  fuel_index?: number;
}

export interface WhatIfOption {
  label: string;
  before: WhatIfOutcome;
  after: WhatIfOutcome;
}

export interface Step {
  title: string;
  /** Short timeline label, e.g. "Baseline". Optional. */
  label?: string;
  /** ISO date (YYYY-MM-DD). */
  date: string;
  /** Optional narration caption shown as a plain sentence below the header. */
  narration?: string;
  ship: LatLon;
  icebergs: Iceberg[];
  routes: Route[];
  selected_route_id: string;
  risk: Risk;
  explanation_text: string;
  alert: Alert | null;
  whatif: WhatIfOption[];
}

export interface Scenario {
  title?: string;
  /** true when the file is generated placeholder data. */
  placeholder?: boolean;
  note?: string;
  steps: Step[];
}
