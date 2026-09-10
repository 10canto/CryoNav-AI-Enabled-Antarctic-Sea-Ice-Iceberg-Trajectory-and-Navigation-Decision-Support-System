import axios from 'axios';
import { API_BASE_URL, API_TIMEOUT, DEMO_CONFIG } from '../config';
import { mockIceData, mockWindData, mockRoutes, mockPredictions } from './mockData';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Global flag for mock data usage (can be toggled dynamically)
let useMockData = DEMO_CONFIG.USE_MOCK_DATA;

export const setUseMockData = (value) => {
  useMockData = value;
};

export const isUsingMockData = () => useMockData;

// Helper function for error handling
const handleApiError = (error, mockFallback, endpointName) => {
  console.error(`API Error [${endpointName}]:`, error.message);
  if (mockFallback) {
    console.warn(`Falling back to mock data for ${endpointName}`);
    return mockFallback;
  }
  return null;
};

// API Functions

export const getHealth = async () => {
  if (useMockData) return { status: 'Mock Mode', timestamp: new Date().toISOString() };
  try {
    const response = await api.get('/api/health');
    return response.data;
  } catch (error) {
    return handleApiError(error, { status: 'Offline', timestamp: new Date().toISOString() }, 'health');
  }
};

export const getIceAnalysis = async () => {
  if (useMockData) return mockIceData;
  try {
    const response = await api.get('/api/ice-analysis');
    return response.data;
  } catch (error) {
    return handleApiError(error, mockIceData, 'ice-analysis');
  }
};

export const getIcebergs = async () => {
  if (useMockData) return { icebergs: [] };
  try {
    const response = await api.get('/api/icebergs');
    return response.data;
  } catch (error) {
    return handleApiError(error, { icebergs: [] }, 'icebergs');
  }
};

export const getPredictions = async (icebergId = null) => {
  if (useMockData) return mockPredictions;
  try {
    const url = icebergId ? `/api/predict-drift?iceberg_id=${icebergId}` : '/api/predict-drift';
    const response = await api.get(url);
    return response.data;
  } catch (error) {
    return handleApiError(error, mockPredictions, 'predict-drift');
  }
};

export const getRoutes = async () => {
  if (useMockData) return mockRoutes;
  try {
    const response = await api.get('/api/routes');
    return response.data;
  } catch (error) {
    return handleApiError(error, mockRoutes, 'routes');
  }
};

export const getRiskAssessment = async () => {
  if (useMockData) {
    return {
      level: 'GREEN',
      message: 'Safe conditions (Mock Data)',
      metrics: {
        ice_concentration: 68,
        nearest_iceberg_km: null,
        collision_risk_percent: 0,
        temperature_celsius: -12,
        wind_speed_kmh: 35,
        wind_direction: 'NE',
        visibility: 'Good',
        wave_height_meters: 2.1
      }
    };
  }
  try {
    const response = await api.get('/api/risk-assessment');
    return response.data;
  } catch (error) {
    return handleApiError(error, {
      level: 'GREEN',
      message: 'Offline - using fallback',
      metrics: { ice_concentration: 68, nearest_iceberg_km: null, collision_risk_percent: 0 }
    }, 'risk-assessment');
  }
};

export const getExplanation = async () => {
  if (useMockData) {
    return { explanation: 'All systems normal. Safe to proceed on current route. (Mock Data)' };
  }
  try {
    const response = await api.get('/api/explanation');
    return response.data;
  } catch (error) {
    return handleApiError(error, { explanation: 'Explanation unavailable (offline)' }, 'explanation');
  }
};

export const advanceTime = async () => {
  if (useMockData) {
    console.log('Mock mode: Scenario advancement simulated locally');
    return { scenario: 0, message: 'Mock advancement' };
  }
  try {
    const response = await api.post('/api/advance-time');
    return response.data;
  } catch (error) {
    return handleApiError(error, { scenario: 0, message: 'Offline' }, 'advance-time');
  }
};

export const resetDemo = async () => {
  if (useMockData) {
    console.log('Mock mode: Demo reset simulated locally');
    return { scenario: 0, message: 'Mock reset' };
  }
  try {
    const response = await api.post('/api/reset-demo');
    return response.data;
  } catch (error) {
    return handleApiError(error, { scenario: 0, message: 'Offline' }, 'reset-demo');
  }
};

export const getWindData = async () => {
  // Wind data not provided by backend yet - always use mock
  return mockWindData;
};
