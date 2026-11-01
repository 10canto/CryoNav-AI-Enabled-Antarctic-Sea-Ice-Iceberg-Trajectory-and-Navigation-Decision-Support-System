/**
 * CryoNav AI API Client
 * Typed functions for all backend endpoints with loading and error handling
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Iceberg {
  id?: string;
  Iceberg?: string;
  Lat: number;
  Lon: number;
  Area_km2?: number;
  Length_km?: number;
  Width_km?: number;
  Last_Date?: string;
  recent_track?: Array<{ lat: number; lon: number; timestamp: string }>;
}

export interface PathPoint {
  lat: number;
  lon: number;
  hours: number;
  timestamp: string;
}

export interface UncertaintyStats {
  radius_km: number;
  mean_km?: number;
  median_km?: number;
}

export interface DriftPrediction {
  mean_path: PathPoint[];
  uncertainty: Record<string, UncertaintyStats>;
  n_simulations?: number;
  model?: string;
  method?: 'track_extrapolation' | 'current_based_fallback';
  velocity_km_h?: number;
}

export interface OceanCurrent {
  lat: number;
  lon: number;
  u: number;
  v: number;
}

export interface Route {
  id: string;
  type: 'safest' | 'fastest' | 'fuel_efficient';
  color: string;
  coordinates: Array<[number, number]>;
  waypoints?: Array<{ lat: number; lon: number }>;
  distanceKm: number;
  timeDays: number;
  fuelIndex: number;
  riskPercent: number;
  isSafest?: boolean;
  isFastest?: boolean;
  isCheapest?: boolean;
}

export type RiskLevel = 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED';

export interface RiskAssessment {
  level: RiskLevel;
  distance_km: number;
  nearest_iceberg: string;
  reasons: string[];
  timestamp: string;
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

export interface AlertResponse {
  success: boolean;
  alert_id: number;
  recipients: string[];
  timestamp: string;
  note: string;
}

class APIError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'APIError';
  }
}

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      throw new APIError(`HTTP ${response.status}: ${response.statusText}`, response.status);
    }
    return await response.json();
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(error instanceof Error ? error.message : 'Network error');
  }
}

export const apiClient = {
  /**
   * Get current iceberg positions
   */
  async getIcebergs(): Promise<{ icebergs: Iceberg[]; count: number }> {
    return fetchJSON(`${API_BASE}/icebergs`);
  },

  /**
   * Predict iceberg drift trajectory
   */
  async predictDrift(
    icebergId: string,
    hours: number = 72,
    model: string = 'hybrid',
    windSpeed?: number,
    windDir?: number
  ): Promise<DriftPrediction> {
    const params = new URLSearchParams({
      iceberg_id: icebergId,
      hours: hours.toString(),
      model
    });
    if (windSpeed !== undefined) params.append('wind_speed', windSpeed.toString());
    if (windDir !== undefined) params.append('wind_dir', windDir.toString());
    
    return fetchJSON(`${API_BASE}/predict-drift?${params}`);
  },

  /**
   * Get ocean current vectors for a region
   */
  async getOceanCurrents(
    region: string = 'southern_ocean',
    date?: string
  ): Promise<{ region: string; date: string; currents: OceanCurrent[]; count: number }> {
    const params = new URLSearchParams({ region });
    if (date) params.append('date', date);
    
    return fetchJSON(`${API_BASE}/ocean-currents?${params}`);
  },

  /**
   * Calculate safe navigation routes
   */
  async calculateRoutes(data: {
    start: { lat: number; lon: number };
    end: { lat: number; lon: number };
    ship: { speed_knots: number };
    date: string;
    wind?: { speed: number; direction: number };
  }): Promise<{ routes: Route[]; count: number }> {
    return fetchJSON(`${API_BASE}/calculate-routes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  },

  /**
   * Assess navigation risk at current position
   */
  async assessRisk(
    shipLat: number,
    shipLon: number,
    date?: string
  ): Promise<RiskAssessment> {
    const params = new URLSearchParams({
      ship_lat: shipLat.toString(),
      ship_lon: shipLon.toString()
    });
    if (date) params.append('date', date);
    
    return fetchJSON(`${API_BASE}/risk?${params}`);
  },

  /**
   * Send simulated satellite alert
   */
  async sendAlert(data: {
    level: string;
    position: { lat: number; lon: number };
    details: Record<string, any>;
  }): Promise<AlertResponse> {
    return fetchJSON(`${API_BASE}/alert`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  },

  /**
   * Get plain-language explanation of route recommendation
   */
  async explainRoute(routeId: string): Promise<RouteExplanation> {
    const params = new URLSearchParams({ route_id: routeId });
    return fetchJSON(`${API_BASE}/explain?${params}`);
  }
};
