// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const API_TIMEOUT = 10000; // 10 seconds

// Map Configuration - INDIA TO ANTARCTICA VOYAGE
export const MAP_CENTER = [13.0827, 80.2707]; // Chennai, India (START POINT)
export const MAP_ZOOM = 3; // Show India to Antarctica region
export const MAP_MAX_ZOOM = 18;
export const MAP_MIN_ZOOM = 2;

// Antarctic destination (for reference)
export const DESTINATION = [-70.7644, 11.7386]; // Maitri Station, Antarctica

// Data Refresh
export const REFRESH_INTERVAL = 10000; // 10 seconds for polling
// Keep the timeline controls locked until the vessel completes its visual transit.
export const SCENARIO_TRANSITION_DELAY = 2800;
export const SHIP_TRANSITION_DURATION = 2600;

// Demo Configuration
export const DEMO_CONFIG = {
  AUTO_ADVANCE_INTERVAL: 30000, // 30 seconds for auto-play
  ANIMATION_SPEED: 1.0, // 1x normal speed
  SHOW_DEBUG_INFO: false, // Hide debug panels for demo
  ENABLE_SOUNDS: true, // Alert sounds on/off
  USE_MOCK_DATA: false, // Set to true for offline demo (will auto-toggle on backend failure)
};

// Risk Thresholds
export const RISK_LEVELS = {
  GREEN: { max: 20, label: 'SAFE', color: '#10b981' },
  YELLOW: { max: 40, label: 'CAUTION', color: '#f59e0b' },
  ORANGE: { max: 70, label: 'WARNING', color: '#f97316' },
  RED: { max: 100, label: 'EMERGENCY', color: '#ef4444' }
};

// Projection Note
// Using Web Mercator (EPSG:3857) for Leaflet compatibility
// Production would use Antarctic Polar Stereographic (EPSG:3031) for accurate polar calculations
export const MAP_PROJECTION = 'EPSG:3857'; // Web Mercator
