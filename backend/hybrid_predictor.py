"""
Hybrid Iceberg Drift Predictor
Primary: Track extrapolation (if >= 2 positions available)
Fallback: Current-based physics predictor
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from math import radians, degrees, sin, cos, sqrt, atan2

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent / "iceberg-trajectory-ml" / "src"))
from physics_predictor import PhysicsPredictor

class HybridPredictor:
    def __init__(self):
        """Initialize hybrid predictor with calibrated uncertainty"""
        self.physics_predictor = PhysicsPredictor()
        
        # Load calibrated uncertainty config
        config_path = Path(__file__).parent / "drift_config.json"
        with open(config_path, 'r') as f:
            self.config = json.load(f)['drift_prediction']
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km"""
        R = 6371
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c
    
    def _calculate_velocity(
        self,
        positions: List[Dict[str, float]]
    ) -> Tuple[float, float, float]:
        """
        Calculate velocity from recent positions
        Returns: (vel_lat, vel_lon, speed_km_h)
        """
        if len(positions) < 2:
            return (0.0, 0.0, 0.0)
        
        # Use last 2 positions for most recent velocity
        pos1 = positions[-2]
        pos2 = positions[-1]
        
        # Calculate time difference
        if 'timestamp' in pos1 and 'timestamp' in pos2:
            try:
                dt1 = datetime.fromisoformat(pos1['timestamp'])
                dt2 = datetime.fromisoformat(pos2['timestamp'])
                hours = (dt2 - dt1).total_seconds() / 3600
            except:
                hours = 24  # Default assumption
        else:
            hours = 24
        
        if hours <= 0:
            return (0.0, 0.0, 0.0)
        
        # Calculate velocity in degrees per hour
        vel_lat = (pos2['lat'] - pos1['lat']) / hours
        vel_lon = (pos2['lon'] - pos1['lon']) / hours
        
        # Calculate speed in km/h
        distance = self._haversine_distance(
            pos1['lat'], pos1['lon'],
            pos2['lat'], pos2['lon']
        )
        speed_km_h = distance / hours
        
        return (vel_lat, vel_lon, speed_km_h)
    
    def predict_drift(
        self,
        lat: float,
        lon: float,
        date: datetime,
        hours: int = 72,
        recent_positions: Optional[List[Dict[str, float]]] = None,
        wind_speed: Optional[float] = None,
        wind_direction: Optional[float] = None
    ) -> Dict:
        """
        Predict iceberg drift using hybrid method
        
        Args:
            lat, lon: Current position
            date: Current date
            hours: Prediction horizon
            recent_positions: List of recent positions [{'lat': ..., 'lon': ..., 'timestamp': ...}]
            wind_speed, wind_direction: Optional wind parameters
            
        Returns:
            Dict with mean_path, uncertainty, method, etc.
        """
        # Determine which method to use
        use_track = (recent_positions is not None and 
                    len(recent_positions) >= self.config['track_extrapolation']['min_positions'])
        
        if use_track:
            return self._predict_track_extrapolation(
                lat, lon, date, hours, recent_positions
            )
        else:
            return self._predict_current_based(
                lat, lon, date, hours, wind_speed, wind_direction
            )
    
    def _predict_track_extrapolation(
        self,
        lat: float,
        lon: float,
        date: datetime,
        hours: int,
        recent_positions: List[Dict[str, float]]
    ) -> Dict:
        """Track extrapolation: constant velocity from recent track"""
        
        # Calculate velocity from track
        vel_lat, vel_lon, speed_km_h = self._calculate_velocity(recent_positions)
        
        # Generate path points
        time_step_hours = 6
        n_steps = hours // time_step_hours
        
        path_points = []
        for step in range(n_steps + 1):
            hours_elapsed = step * time_step_hours
            
            # Extrapolate position
            pred_lat = lat + vel_lat * hours_elapsed
            pred_lon = lon + vel_lon * hours_elapsed
            
            path_points.append({
                'lat': float(pred_lat),
                'lon': float(pred_lon),
                'hours': hours_elapsed,
                'timestamp': (date + timedelta(hours=hours_elapsed)).isoformat()
            })
        
        # Get calibrated uncertainty from config
        uncertainty_config = self.config['track_extrapolation']['uncertainty_km']
        uncertainty = {}
        
        for horizon in [24, 48, 72]:
            if horizon <= hours:
                uncertainty[f"{horizon}h"] = {
                    'radius_km': uncertainty_config[f'{horizon}h'],
                    'percentile': uncertainty_config['percentile'],
                    'method': 'calibrated_from_validation'
                }
        
        return {
            'mean_path': path_points,
            'uncertainty': uncertainty,
            'method': 'track_extrapolation',
            'velocity': {
                'vel_lat_deg_h': vel_lat,
                'vel_lon_deg_h': vel_lon,
                'speed_km_h': speed_km_h
            },
            'positions_used': len(recent_positions),
            'description': 'Constant velocity extrapolation from recent track'
        }
    
    def _predict_current_based(
        self,
        lat: float,
        lon: float,
        date: datetime,
        hours: int,
        wind_speed: Optional[float],
        wind_direction: Optional[float]
    ) -> Dict:
        """Current-based fallback: physics predictor with ocean currents"""
        
        # Run physics predictor
        result = self.physics_predictor.predict_drift(
            lat=lat,
            lon=lon,
            date=date,
            hours=hours,
            wind_speed=wind_speed,
            wind_direction=wind_direction,
            n_monte_carlo=50  # Reduce for speed
        )
        
        # Override uncertainty with calibrated values
        uncertainty_config = self.config['current_based_fallback']['uncertainty_km']
        calibrated_uncertainty = {}
        
        for horizon in [24, 48, 72]:
            if horizon <= hours:
                calibrated_uncertainty[f"{horizon}h"] = {
                    'radius_km': uncertainty_config[f'{horizon}h'],
                    'percentile': uncertainty_config['percentile'],
                    'method': 'calibrated_from_validation'
                }
        
        result['uncertainty'] = calibrated_uncertainty
        result['method'] = 'current_based_fallback'
        result['description'] = 'Physics-based drift with ocean currents (track unavailable)'
        
        return result


# Simple test
if __name__ == "__main__":
    print("\n🧊 Hybrid Predictor Test")
    print("=" * 60)
    
    predictor = HybridPredictor()
    
    # Test 1: Track extrapolation
    print("\n1. Track Extrapolation (with recent positions):")
    recent_positions = [
        {'lat': -60.0, 'lon': -50.0, 'timestamp': '2025-11-10T00:00:00'},
        {'lat': -59.95, 'lon': -49.95, 'timestamp': '2025-11-11T00:00:00'}
    ]
    
    result1 = predictor.predict_drift(
        lat=-59.9,
        lon=-49.9,
        date=datetime(2025, 11, 12),
        hours=72,
        recent_positions=recent_positions
    )
    
    print(f"   Method: {result1['method']}")
    print(f"   Velocity: {result1['velocity']['speed_km_h']:.2f} km/h")
    print(f"   24h uncertainty: {result1['uncertainty']['24h']['radius_km']} km")
    
    # Test 2: Current-based fallback
    print("\n2. Current-Based Fallback (no track):")
    result2 = predictor.predict_drift(
        lat=-60.0,
        lon=-50.0,
        date=datetime(2025, 11, 15),
        hours=72
    )
    
    print(f"   Method: {result2['method']}")
    print(f"   24h uncertainty: {result2['uncertainty']['24h']['radius_km']} km")
    
    print("\n✅ Tests complete")
