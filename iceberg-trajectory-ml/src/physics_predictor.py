"""
Physics-based Iceberg Drift Predictor
Uses ocean currents from regional monthly data
Monte Carlo approach with uncertainty quantification
"""
import json
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from math import radians, degrees, sin, cos, sqrt, atan2

class PhysicsPredictor:
    def __init__(self):
        """Initialize predictor and load ocean current data"""
        self.ocean_data = {}
        self._load_ocean_currents()
        
    def _load_ocean_currents(self):
        """Load all regional ocean current data into memory"""
        data_dir = Path(__file__).parent.parent / "data" / "ocean_currents_yearly"
        
        if not data_dir.exists():
            print(f"Warning: Ocean current data not found at {data_dir}")
            return
        
        regions = ['weddell_sea', 'east_antarctic', 'ross_sea', 'southern_ocean']
        
        for region in regions:
            json_path = data_dir / f"ocean_currents_{region}_2025.json"
            if json_path.exists():
                with open(json_path, 'r') as f:
                    data = json.load(f)
                    self.ocean_data[region] = data
                    print(f"[OK] Loaded {region}: {len(data.get('data', []))} time steps")
    
    def _find_region(self, lat: float, lon: float) -> Optional[str]:
        """Determine which regional dataset covers this position"""
        # Antarctic region boundaries (approximate)
        if -45 <= lon <= 20 and -80 <= lat <= -50:
            return 'weddell_sea'
        elif 20 <= lon <= 90 and -80 <= lat <= -50:
            return 'east_antarctic'
        elif -180 <= lon <= -135 and -80 <= lat <= -50:
            return 'ross_sea'
        else:
            return 'southern_ocean'
    
    def _get_ocean_current(self, lat: float, lon: float, date: datetime) -> Tuple[float, float]:
        """
        Get ocean current (u, v) for given position and date
        Returns: (u_ms, v_ms) in m/s
        """
        region = self._find_region(lat, lon)
        
        if region not in self.ocean_data:
            return (0.0, 0.0)
        
        data = self.ocean_data[region]
        
        # Find nearest month (monthly data from Oct 2025 - Aug 2026)
        month_idx = date.month - 10 if date.year == 2025 else date.month + 2
        month_idx = max(0, min(month_idx, len(data.get('data', [])) - 1))
        
        if month_idx >= len(data.get('data', [])):
            return (0.0, 0.0)
        
        month_data = data['data'][month_idx]
        
        # Find nearest grid point
        currents = month_data.get('currents', [])
        if len(currents) == 0:
            return (0.0, 0.0)
        
        lats = np.array([p['lat'] for p in currents])
        lons = np.array([p['lon'] for p in currents])
        
        # Nearest neighbor lookup
        distances = np.sqrt((lats - lat)**2 + (lons - lon)**2)
        nearest_idx = np.argmin(distances)
        
        point = currents[nearest_idx]
        return (point['u'], point['v'])
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points on Earth in km"""
        R = 6371  # Earth radius in km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def _apply_coriolis(self, u: float, v: float, lat: float) -> Tuple[float, float]:
        """Apply small leftward deflection (Coriolis effect in Southern Hemisphere)"""
        # Small leftward turn: ~3-5 degrees for Southern Hemisphere
        angle = radians(-4)  # Negative = left turn
        u_new = u * cos(angle) - v * sin(angle)
        v_new = u * sin(angle) + v * cos(angle)
        return (u_new, v_new)
    
    def predict_drift(
        self,
        lat: float,
        lon: float,
        date: datetime,
        hours: int = 72,
        wind_speed: Optional[float] = None,
        wind_direction: Optional[float] = None,
        n_monte_carlo: int = 100
    ) -> Dict:
        """
        Predict iceberg drift using physics-based model
        
        Args:
            lat, lon: Starting position
            date: Starting date
            hours: Prediction horizon (default 72h)
            wind_speed: Wind speed in m/s (optional)
            wind_direction: Wind direction in degrees (0=North, 90=East)
            n_monte_carlo: Number of Monte Carlo simulations
            
        Returns:
            Dictionary with mean path, uncertainty radii, and statistics
        """
        time_step_hours = 6  # 6-hour steps
        n_steps = hours // time_step_hours
        
        # Storage for all Monte Carlo runs
        all_paths = []
        
        for run in range(n_monte_carlo):
            path = [(lat, lon)]
            current_lat, current_lon = lat, lon
            current_date = date
            
            for step in range(n_steps):
                # Get ocean current
                u_ocean, v_ocean = self._get_ocean_current(current_lat, current_lon, current_date)
                
                # Add noise (±20%)
                noise_factor = 1.0 + np.random.uniform(-0.2, 0.2)
                u_ocean *= noise_factor
                v_ocean *= noise_factor
                
                # Apply Coriolis effect
                u_ocean, v_ocean = self._apply_coriolis(u_ocean, v_ocean, current_lat)
                
                # Add wind contribution (3% of wind)
                u_total, v_total = u_ocean, v_ocean
                if wind_speed is not None and wind_direction is not None:
                    wind_rad = radians(wind_direction)
                    u_wind = wind_speed * sin(wind_rad) * 0.03
                    v_wind = wind_speed * cos(wind_rad) * 0.03
                    u_total += u_wind
                    v_total += v_wind
                
                # Convert m/s to degrees for time_step_hours
                seconds = time_step_hours * 3600
                dlat = (v_total * seconds) / 111000  # meters to degrees latitude
                dlon = (u_total * seconds) / (111000 * cos(radians(current_lat)))  # account for latitude
                
                # Update position
                current_lat += dlat
                current_lon += dlon
                current_date += timedelta(hours=time_step_hours)
                
                path.append((current_lat, current_lon))
            
            all_paths.append(path)
        
        # Calculate mean path
        all_paths_array = np.array(all_paths)  # shape: (n_monte_carlo, n_steps+1, 2)
        mean_path = np.mean(all_paths_array, axis=0)  # shape: (n_steps+1, 2)
        
        # Calculate uncertainty at specific horizons
        uncertainty = {}
        for horizon_hours in [24, 48, 72]:
            if horizon_hours <= hours:
                step_idx = horizon_hours // time_step_hours
                positions_at_horizon = all_paths_array[:, step_idx, :]
                
                # Calculate distances from mean
                mean_lat, mean_lon = mean_path[step_idx]
                distances = [
                    self._haversine_distance(mean_lat, mean_lon, pos[0], pos[1])
                    for pos in positions_at_horizon
                ]
                
                uncertainty[f"{horizon_hours}h"] = {
                    'radius_km': np.percentile(distances, 95),  # 95th percentile
                    'mean_km': np.mean(distances),
                    'median_km': np.median(distances)
                }
        
        # Convert mean path to list of dicts
        path_points = []
        for i, (lat_i, lon_i) in enumerate(mean_path):
            hours_elapsed = i * time_step_hours
            path_points.append({
                'lat': float(lat_i),
                'lon': float(lon_i),
                'hours': hours_elapsed,
                'timestamp': (date + timedelta(hours=hours_elapsed)).isoformat()
            })
        
        return {
            'mean_path': path_points,
            'uncertainty': uncertainty,
            'n_simulations': n_monte_carlo,
            'model': 'physics'
        }


# Simple test
if __name__ == "__main__":
    print("\n🧊 Physics-based Iceberg Drift Predictor Test")
    print("=" * 60)
    
    predictor = PhysicsPredictor()
    
    # Test prediction
    test_lat, test_lon = -60.0, -50.0
    test_date = datetime(2025, 11, 15)
    
    print(f"\n📍 Test position: {test_lat}°, {test_lon}°")
    print(f"📅 Date: {test_date.strftime('%Y-%m-%d')}")
    
    result = predictor.predict_drift(
        lat=test_lat,
        lon=test_lon,
        date=test_date,
        hours=72,
        wind_speed=10.0,
        wind_direction=45.0
    )
    
    print(f"\n✅ Predicted path: {len(result['mean_path'])} points")
    print(f"\n📊 Uncertainty (95th percentile):")
    for horizon, stats in result['uncertainty'].items():
        print(f"   {horizon}: {stats['radius_km']:.2f} km (mean: {stats['mean_km']:.2f} km)")
    
    print(f"\n🎯 Final position after 72h:")
    final = result['mean_path'][-1]
    print(f"   {final['lat']:.4f}°, {final['lon']:.4f}°")
    
    initial_pos = result['mean_path'][0]
    distance = predictor._haversine_distance(
        initial_pos['lat'], initial_pos['lon'],
        final['lat'], final['lon']
    )
    print(f"   Distance traveled: {distance:.2f} km")
