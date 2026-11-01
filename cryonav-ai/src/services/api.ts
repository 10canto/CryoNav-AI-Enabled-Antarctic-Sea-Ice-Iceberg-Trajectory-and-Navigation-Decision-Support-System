/**
 * API Client for CryoNav AI Backend
 */
import type {
  IcebergsResponse,
  DriftPrediction,
  OceanCurrentsResponse,
  RoutesResponse,
  RiskAssessment,
  AlertResponse,
  RouteExplanation
} from '../types/api';

const API_BASE = 'http://localhost:8000';

export const api = {
  async getIcebergs(): Promise<IcebergsResponse> {
    const response = await fetch(`${API_BASE}/icebergs`);
    if (!response.ok) throw new Error('Failed to fetch icebergs');
    return response.json();
  },

  async predictDrift(
    icebergId: string,
    hours: number = 72,
    windSpeed?: number,
    windDir?: number,
    model: string = 'physics'
  ): Promise<DriftPrediction> {
    const params = new URLSearchParams({
      iceberg_id: icebergId,
      hours: hours.toString(),
      model
    });
    
    if (windSpeed !== undefined) params.append('wind_speed', windSpeed.toString());
    if (windDir !== undefined) params.append('wind_dir', windDir.toString());
    
    const response = await fetch(`${API_BASE}/predict-drift?${params}`);
    if (!response.ok) throw new Error('Failed to predict drift');
    return response.json();
  },

  async getOceanCurrents(region: string, date?: string): Promise<OceanCurrentsResponse> {
    const params = new URLSearchParams({ region });
    if (date) params.append('date', date);
    
    const response = await fetch(`${API_BASE}/ocean-currents?${params}`);
    if (!response.ok) throw new Error('Failed to fetch ocean currents');
    return response.json();
  },

  async calculateRoutes(data: {
    start: { lat: number; lon: number };
    end: { lat: number; lon: number };
    ship: { speed_knots: number };
    date: string;
    wind?: { speed: number; direction: number };
  }): Promise<RoutesResponse> {
    const response = await fetch(`${API_BASE}/calculate-routes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) throw new Error('Failed to calculate routes');
    return response.json();
  },

  async assessRisk(shipLat: number, shipLon: number, date?: string): Promise<RiskAssessment> {
    const params = new URLSearchParams({
      ship_lat: shipLat.toString(),
      ship_lon: shipLon.toString()
    });
    
    if (date) params.append('date', date);
    
    const response = await fetch(`${API_BASE}/risk?${params}`);
    if (!response.ok) throw new Error('Failed to assess risk');
    return response.json();
  },

  async sendAlert(data: {
    level: string;
    position: { lat: number; lon: number };
    details: Record<string, any>;
  }): Promise<AlertResponse> {
    const response = await fetch(`${API_BASE}/alert`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) throw new Error('Failed to send alert');
    return response.json();
  },

  async explainRoute(routeId: string): Promise<RouteExplanation> {
    const params = new URLSearchParams({ route_id: routeId });
    const response = await fetch(`${API_BASE}/explain?${params}`);
    
    if (!response.ok) throw new Error('Failed to get explanation');
    return response.json();
  }
};
