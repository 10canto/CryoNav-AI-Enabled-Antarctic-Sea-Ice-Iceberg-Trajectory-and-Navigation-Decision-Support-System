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

// Mock Predictions — matches new iceberg positions in all 4 scenarios
// Scenario 1: ICE-047 at -58.5°S 42°E (Iceberg Alley) drifts NE away from route (safe)
// Scenario 2: ICE-047 at -60.8°S 22.5°E drifts NW crossing Route A; ICE-048 in pack ice
// Scenario 3: ICE-047 & ICE-049 near ship at -66°S 16°E on collision course; ICE-048 in pack ice
export const getMockPredictions = (scenario = 1) => {
  const scenarios = {
    0: { predictions: [] },

    1: {
      predictions: [
        {
          iceberg_id: 'ICE-047',
          current_position: { lat: -58.5, lon: 42.0 },
          risk_level: 'low',
          notes: 'ICE-047 drifting northeast away from route — 45 km clearance maintained. No intervention required.',
          trajectory: [
            { time_hours: 6,  latitude: -58.44, longitude: 42.08, uncertainty_km: 3.2,  timestamp: '2024-01-15T23:30:00Z', drift_speed_kmh: 1.2, drift_direction_deg: 52 },
            { time_hours: 12, latitude: -58.37, longitude: 42.17, uncertainty_km: 5.8,  timestamp: '2024-01-16T05:30:00Z', drift_speed_kmh: 1.2, drift_direction_deg: 52 },
            { time_hours: 24, latitude: -58.24, longitude: 42.34, uncertainty_km: 9.5,  timestamp: '2024-01-16T17:30:00Z', drift_speed_kmh: 1.2, drift_direction_deg: 53 },
            { time_hours: 48, latitude: -57.98, longitude: 42.70, uncertainty_km: 16.8, timestamp: '2024-01-17T17:30:00Z', drift_speed_kmh: 1.2, drift_direction_deg: 54 },
            { time_hours: 72, latitude: -57.72, longitude: 43.06, uncertainty_km: 23.5, timestamp: '2024-01-18T17:30:00Z', drift_speed_kmh: 1.2, drift_direction_deg: 55 },
          ],
        },
      ],
    },

    2: {
      predictions: [
        {
          iceberg_id: 'ICE-047',
          current_position: { lat: -60.8, lon: 22.5 },
          risk_level: 'moderate',
          notes: 'ICE-047 drifting northwest — 74% probability of intersecting Route A in 18 hours. 150 km safety detour recommended.',
          trajectory: [
            { time_hours: 6,  latitude: -60.72, longitude: 22.35, uncertainty_km: 4.2,  timestamp: '2024-01-16T11:45:00Z', drift_speed_kmh: 1.8, drift_direction_deg: 322 },
            { time_hours: 12, latitude: -60.63, longitude: 22.19, uncertainty_km: 7.6,  timestamp: '2024-01-16T17:45:00Z', drift_speed_kmh: 1.8, drift_direction_deg: 322 },
            { time_hours: 24, latitude: -60.47, longitude: 21.88, uncertainty_km: 13.4, timestamp: '2024-01-17T05:45:00Z', drift_speed_kmh: 1.8, drift_direction_deg: 323 },
            { time_hours: 48, latitude: -60.14, longitude: 21.26, uncertainty_km: 24.8, timestamp: '2024-01-18T05:45:00Z', drift_speed_kmh: 1.8, drift_direction_deg: 323 },
            { time_hours: 72, latitude: -59.82, longitude: 20.65, uncertainty_km: 35.1, timestamp: '2024-01-19T05:45:00Z', drift_speed_kmh: 1.8, drift_direction_deg: 324 },
          ],
        },
        {
          iceberg_id: 'ICE-048',
          current_position: { lat: -66.2, lon: 13.8 },
          risk_level: 'moderate',
          notes: 'ICE-048 calved from pack ice — drifting north toward vessel approach corridor at 13°E.',
          trajectory: [
            { time_hours: 6,  latitude: -66.12, longitude: 13.72, uncertainty_km: 2.8,  timestamp: '2024-01-16T11:45:00Z', drift_speed_kmh: 0.52, drift_direction_deg: 352 },
            { time_hours: 12, latitude: -66.04, longitude: 13.65, uncertainty_km: 5.6,  timestamp: '2024-01-16T17:45:00Z', drift_speed_kmh: 0.52, drift_direction_deg: 352 },
            { time_hours: 24, latitude: -65.88, longitude: 13.52, uncertainty_km: 11.2, timestamp: '2024-01-17T05:45:00Z', drift_speed_kmh: 0.52, drift_direction_deg: 351 },
            { time_hours: 48, latitude: -65.55, longitude: 13.28, uncertainty_km: 22.4, timestamp: '2024-01-18T05:45:00Z', drift_speed_kmh: 0.52, drift_direction_deg: 351 },
            { time_hours: 72, latitude: -65.22, longitude: 13.05, uncertainty_km: 33.6, timestamp: '2024-01-19T05:45:00Z', drift_speed_kmh: 0.52, drift_direction_deg: 351 },
          ],
        },
      ],
    },

    3: {
      predictions: [
        {
          iceberg_id: 'ICE-047',
          current_position: { lat: -65.96, lon: 15.82 },
          risk_level: 'high',
          notes: 'CRITICAL: ICE-047 only 3.2 km ahead — collision in ~14 minutes at current speed. Immediate heading change to 185° SW required.',
          trajectory: [
            { time_hours: 6,  latitude: -65.985, longitude: 15.91, uncertainty_km: 1.8,  timestamp: '2024-01-17T00:20:00Z', drift_speed_kmh: 0.62, drift_direction_deg: 159 },
            { time_hours: 12, latitude: -66.01,  longitude: 16.00, uncertainty_km: 3.5,  timestamp: '2024-01-17T06:20:00Z', drift_speed_kmh: 0.62, drift_direction_deg: 159 },
            { time_hours: 24, latitude: -66.06,  longitude: 16.18, uncertainty_km: 6.4,  timestamp: '2024-01-17T18:20:00Z', drift_speed_kmh: 0.62, drift_direction_deg: 160 },
            { time_hours: 48, latitude: -66.16,  longitude: 16.54, uncertainty_km: 11.2, timestamp: '2024-01-18T18:20:00Z', drift_speed_kmh: 0.62, drift_direction_deg: 160 },
            { time_hours: 72, latitude: -66.26,  longitude: 16.90, uncertainty_km: 15.8, timestamp: '2024-01-19T18:20:00Z', drift_speed_kmh: 0.62, drift_direction_deg: 161 },
          ],
        },
        {
          iceberg_id: 'ICE-048',
          current_position: { lat: -66.5, lon: 14.4 },
          risk_level: 'high',
          notes: 'ICE-048 calved from Lazarev Ice Shelf — drifting north toward vessel approach corridor at 14°E.',
          trajectory: [
            { time_hours: 6,  latitude: -66.41, longitude: 14.31, uncertainty_km: 2.45, timestamp: '2024-01-17T00:20:00Z', drift_speed_kmh: 0.68, drift_direction_deg: 348 },
            { time_hours: 12, latitude: -66.32, longitude: 14.22, uncertainty_km: 4.9,  timestamp: '2024-01-17T06:20:00Z', drift_speed_kmh: 0.68, drift_direction_deg: 348 },
            { time_hours: 24, latitude: -66.14, longitude: 14.04, uncertainty_km: 9.8,  timestamp: '2024-01-17T18:20:00Z', drift_speed_kmh: 0.68, drift_direction_deg: 348 },
            { time_hours: 48, latitude: -65.78, longitude: 13.70, uncertainty_km: 19.6, timestamp: '2024-01-18T18:20:00Z', drift_speed_kmh: 0.68, drift_direction_deg: 348 },
            { time_hours: 72, latitude: -65.42, longitude: 13.38, uncertainty_km: 29.4, timestamp: '2024-01-19T18:20:00Z', drift_speed_kmh: 0.68, drift_direction_deg: 348 },
          ],
        },
        {
          iceberg_id: 'ICE-049',
          current_position: { lat: -65.88, lon: 16.14 },
          risk_level: 'high',
          notes: 'CRITICAL: ICE-049 converging on vessel route — blocking escape corridor to the east.',
          trajectory: [
            { time_hours: 6,  latitude: -65.91, longitude: 16.22, uncertainty_km: 2.1,  timestamp: '2024-01-17T00:20:00Z', drift_speed_kmh: 0.58, drift_direction_deg: 162 },
            { time_hours: 12, latitude: -65.94, longitude: 16.30, uncertainty_km: 4.2,  timestamp: '2024-01-17T06:20:00Z', drift_speed_kmh: 0.58, drift_direction_deg: 162 },
            { time_hours: 24, latitude: -66.00, longitude: 16.46, uncertainty_km: 7.8,  timestamp: '2024-01-17T18:20:00Z', drift_speed_kmh: 0.58, drift_direction_deg: 163 },
            { time_hours: 48, latitude: -66.12, longitude: 16.78, uncertainty_km: 13.5, timestamp: '2024-01-18T18:20:00Z', drift_speed_kmh: 0.58, drift_direction_deg: 163 },
            { time_hours: 72, latitude: -66.24, longitude: 17.10, uncertainty_km: 18.9, timestamp: '2024-01-19T18:20:00Z', drift_speed_kmh: 0.58, drift_direction_deg: 164 },
          ],
        },
      ],
    },
  };

  return scenarios[scenario] ?? scenarios[0];
};

// Backward compatibility
export const mockPredictions = getMockPredictions(1);
