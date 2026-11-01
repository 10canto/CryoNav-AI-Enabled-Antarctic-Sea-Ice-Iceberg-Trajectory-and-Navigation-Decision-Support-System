/**
 * TypeScript types for CryoNav AI API responses
 */

export interface Iceberg {
  id?: string;
  Iceberg?: string;
  Lat: number;
  Lon: number;
  Area_km2?: number;
  Length_km?: number;
  Width_km?: number;
  Last_Date?: string;
}

export interface IcebergsResponse {
  icebergs: Iceberg[];
  count: number;
}

export interface PathPoint {
  lat: number;
  lon: number;
  hours: number;
  timestamp: string;
}

export interface UncertaintyStats {
  radius_km: number;
  mean_km: number;
  median_km: number;
}

export interface DriftPrediction {
  mean_path: PathPoint[];
  uncertainty: {
    [key: string]: UncertaintyStats;
  };
  n_simulations: number;
  model: string;
}

export interface OceanCurrent {
  lat: number;
  lon: number;
  u: number;
  v: number;
}

export interface OceanCurrentsResponse {
  region: string;
  date: string;
  currents: OceanCurrent[];
  count: number;
}

export interface Waypoint {
  lat: number;
  lon: number;
}

export interface Route {
  id: string;
  type: 'safest' | 'fastest' | 'fuel_efficient';
  color: string;
  waypoints: Waypoint[];
  distance_km: number;
  time_hours: number;
  fuel_percent_vs_fastest: number;
  risk_score: number;
}

export interface RoutesResponse {
  routes: Route[];
  count: number;
}

export type RiskLevel = 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED';

export interface RiskAssessment {
  level: RiskLevel;
  distance_km: number;
  nearest_iceberg: string;
  reasons: string[];
  timestamp: string;
}

export interface AlertResponse {
  success: boolean;
  alert_id: number;
  recipients: string[];
  timestamp: string;
  note: string;
}

export interface RouteExplanation {
  route_id: string;
  route_type: string;
  summary: string;
  reasons: string[];
  trade_offs: {
    extra_distance_km: number;
    extra_time_hours: number;
    extra_fuel_percent: number;
    risk_reduction_percent: number;
  };
  confidence: string;
  data_sources: string[];
}
