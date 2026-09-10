// Mock Ice Zone Data (for Guy 2's unfinished ice detector)
export const mockIceData = {
  timestamp: new Date().toISOString(),
  ice_zones: [
    {
      type: 'open_water',
      percentage: 35,
      coordinates: [
        [-65.2, -64.5],
        [-65.1, -64.4],
        [-65.0, -64.5],
        [-65.1, -64.6]
      ]
    },
    {
      type: 'thin_ice',
      percentage: 42,
      coordinates: [
        [-65.3, -64.6],
        [-65.2, -64.5],
        [-65.1, -64.6],
        [-65.2, -64.7]
      ]
    },
    {
      type: 'thick_ice',
      percentage: 23,
      coordinates: [
        [-65.4, -64.7],
        [-65.3, -64.6],
        [-65.2, -64.7],
        [-65.3, -64.8]
      ]
    }
  ],
  average_concentration: 68
};

// Mock Wind Data (for WindArrows component)
export const mockWindData = {
  timestamp: new Date().toISOString(),
  wind_vectors: [
    { lat: -60.0, lon: 20.0, speed_kmh: 35, direction_deg: 45 },
    { lat: -62.0, lon: 18.0, speed_kmh: 42, direction_deg: 50 },
    { lat: -64.0, lon: 16.0, speed_kmh: 38, direction_deg: 40 },
    { lat: -66.0, lon: 14.0, speed_kmh: 45, direction_deg: 55 },
    { lat: -68.0, lon: 12.0, speed_kmh: 52, direction_deg: 60 }
  ]
};

// Mock Routes (fallback for offline mode - keep ONE scenario)
export const mockRoutes = {
  routes: [
    {
      type: 'safest',
      name: 'Eastern Ice-Avoidance Route',
      waypoints: [
        { seq: 1, lat: 13.0827, lon: 80.2707, label: 'Chennai Port - DEPARTURE' },
        { seq: 2, lat: 0.0, lon: 85.0, label: 'Equator Crossing' },
        { seq: 3, lat: -40.0, lon: 75.0, label: 'Roaring Forties' },
        { seq: 4, lat: -60.0, lon: 20.0, label: 'Antarctic Convergence' },
        { seq: 5, lat: -70.7644, lon: 11.7386, label: 'Maitri Station - ARRIVAL' }
      ],
      distance_km: 12200,
      distance_nm: 6587,
      duration_days: 34,
      fuel_liters: 185000,
      risk_score: 12
    }
  ]
};

// Mock Predictions (if Guy 4's predictor not ready)
export const mockPredictions = {
  predictions: [
    {
      iceberg_id: 'ICE-047',
      trajectory: [
        { time: '6h', position: { lat: -65.22, lon: -64.55 }, uncertainty_radius_km: 3 },
        { time: '12h', position: { lat: -65.20, lon: -64.52 }, uncertainty_radius_km: 5 },
        { time: '24h', position: { lat: -65.18, lon: -64.48 }, uncertainty_radius_km: 8 }
      ]
    }
  ]
};
