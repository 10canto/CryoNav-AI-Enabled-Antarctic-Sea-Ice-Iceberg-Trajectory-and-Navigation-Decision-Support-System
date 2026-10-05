"""
Simple Iceberg Position Predictor
Input: Current lat/lon position
Output: Predicted future positions (1, 3, 7 days ahead)
"""

import numpy as np
import pandas as pd
from typing import Tuple, List, Dict
from math import radians, sin, cos, sqrt, atan2, degrees
import warnings
warnings.filterwarnings('ignore')

class SimpleIcebergPredictor:
    """
    Simple predictor that takes current position and predicts future positions
    """
    
    def __init__(self, model_path: str = None):
        """
        Initialize predictor
        
        Args:
            model_path: Path to trained model (if available)
        """
        self.model_path = model_path
        self.is_trained = False
        
        # Load historical patterns for statistical prediction
        self.regional_patterns = None
        self.seasonal_patterns = None
        
    def load_historical_patterns(self, data_path: str):
        """
        Load historical iceberg movement patterns for prediction
        """
        try:
            df = pd.read_csv(data_path)
            print(f"📊 Loading historical patterns from {len(df)} observations...")
            
            # Calculate regional movement patterns
            self.regional_patterns = self.calculate_regional_patterns(df)
            self.seasonal_patterns = self.calculate_seasonal_patterns(df)
            
            print("✅ Historical patterns loaded successfully")
            
        except Exception as e:
            print(f"⚠️  Could not load historical patterns: {e}")
            print("Using default Antarctic drift patterns...")
            self.use_default_patterns()
    
    def calculate_regional_patterns(self, df: pd.DataFrame) -> Dict:
        """
        Calculate average movement patterns by Antarctic region
        """
        patterns = {}
        
        # Define Antarctic regions
        regions = {
            'Weddell_Sea': {'lat_range': (-80, -60), 'lon_range': (-60, 20)},
            'Ross_Sea': {'lat_range': (-85, -60), 'lon_range': (160, -140)},
            'Amundsen_Sea': {'lat_range': (-80, -65), 'lon_range': (-140, -90)},
            'East_Antarctic': {'lat_range': (-70, -60), 'lon_range': (20, 160)},
            'General_Southern': {'lat_range': (-60, -50), 'lon_range': (-180, 180)}
        }
        
        for region_name, bounds in regions.items():
            lat_min, lat_max = bounds['lat_range']
            lon_min, lon_max = bounds['lon_range']
            
            # Handle longitude wrapping
            if lon_max < lon_min:  # Crosses 180° meridian
                mask = ((df['lat'] >= lat_min) & (df['lat'] <= lat_max) & 
                       ((df['lon'] >= lon_min) | (df['lon'] <= lon_max)))
            else:
                mask = ((df['lat'] >= lat_min) & (df['lat'] <= lat_max) & 
                       (df['lon'] >= lon_min) & (df['lon'] <= lon_max))
            
            regional_data = df[mask]
            
            if len(regional_data) > 10 and 'speed_km_day' in regional_data.columns:
                patterns[region_name] = {
                    'avg_speed_km_day': regional_data['speed_km_day'].mean(),
                    'avg_direction_deg': regional_data['direction_deg'].mean() if 'direction_deg' in regional_data.columns else 45,
                    'speed_std': regional_data['speed_km_day'].std(),
                    'typical_vel_lat': regional_data['vel_lat'].mean() if 'vel_lat' in regional_data.columns else 0.0,
                    'typical_vel_lon': regional_data['vel_lon'].mean() if 'vel_lon' in regional_data.columns else 0.0,
                    'sample_size': len(regional_data)
                }
        
        return patterns
    
    def calculate_seasonal_patterns(self, df: pd.DataFrame) -> Dict:
        """
        Calculate seasonal movement patterns
        """
        patterns = {}
        
        if 'datetime' in df.columns:
            df['month'] = pd.to_datetime(df['datetime']).dt.month
            
            # Antarctic seasons
            seasons = {
                'Summer': [12, 1, 2],  # Dec-Feb
                'Fall': [3, 4, 5],     # Mar-May
                'Winter': [6, 7, 8],   # Jun-Aug
                'Spring': [9, 10, 11]  # Sep-Nov
            }
            
            for season_name, months in seasons.items():
                seasonal_data = df[df['month'].isin(months)]
                
                if len(seasonal_data) > 10:
                    patterns[season_name] = {
                        'avg_speed_km_day': seasonal_data['speed_km_day'].mean() if 'speed_km_day' in seasonal_data.columns else 5.0,
                        'speed_multiplier': seasonal_data['speed_km_day'].mean() / df['speed_km_day'].mean() if 'speed_km_day' in seasonal_data.columns else 1.0
                    }
        
        return patterns
    
    def use_default_patterns(self):
        """
        Use default Antarctic iceberg drift patterns based on literature
        """
        self.regional_patterns = {
            'Weddell_Sea': {
                'avg_speed_km_day': 8.5,
                'avg_direction_deg': 45,  # Northeast
                'typical_vel_lat': 0.02,  # Northward
                'typical_vel_lon': 0.02   # Eastward
            },
            'Ross_Sea': {
                'avg_speed_km_day': 6.2,
                'avg_direction_deg': 315,  # Northwest  
                'typical_vel_lat': 0.015,
                'typical_vel_lon': -0.015
            },
            'East_Antarctic': {
                'avg_speed_km_day': 7.8,
                'avg_direction_deg': 90,   # Eastward
                'typical_vel_lat': 0.0,
                'typical_vel_lon': 0.025
            },
            'General_Southern': {
                'avg_speed_km_day': 12.0,
                'avg_direction_deg': 60,   # Northeast
                'typical_vel_lat': 0.03,
                'typical_vel_lon': 0.02
            }
        }
        
        self.seasonal_patterns = {
            'Summer': {'speed_multiplier': 1.4},   # Faster drift in summer
            'Fall': {'speed_multiplier': 1.1},
            'Winter': {'speed_multiplier': 0.7},   # Slower in winter (sea ice)
            'Spring': {'speed_multiplier': 1.0}
        }
    
    def identify_region(self, lat: float, lon: float) -> str:
        """
        Identify which Antarctic region an iceberg is in
        """
        # Weddell Sea
        if -80 <= lat <= -60 and -60 <= lon <= 20:
            return 'Weddell_Sea'
        
        # Ross Sea (crosses 180° meridian)
        if -85 <= lat <= -60 and (lon >= 160 or lon <= -140):
            return 'Ross_Sea'
        
        # Amundsen Sea
        if -80 <= lat <= -65 and -140 <= lon <= -90:
            return 'Amundsen_Sea'
        
        # East Antarctic
        if -70 <= lat <= -60 and 20 <= lon <= 160:
            return 'East_Antarctic'
        
        # Default to General Southern Ocean
        return 'General_Southern'
    
    def get_current_season(self) -> str:
        """
        Get current Antarctic season
        """
        from datetime import datetime
        month = datetime.now().month
        
        if month in [12, 1, 2]:
            return 'Summer'
        elif month in [3, 4, 5]:
            return 'Fall'
        elif month in [6, 7, 8]:
            return 'Winter'
        else:
            return 'Spring'
    
    def predict_position(self, current_lat: float, current_lon: float, 
                        days_ahead: List[int] = [1, 3, 7]) -> Dict:
        """
        Predict future iceberg positions
        
        Args:
            current_lat: Current latitude
            current_lon: Current longitude  
            days_ahead: List of days to predict (e.g., [1, 3, 7])
        
        Returns:
            Dictionary with predictions for each day
        """
        # Input validation
        if not (-90 <= current_lat <= -50):
            raise ValueError(f"Latitude {current_lat} is outside Antarctic range (-90 to -50)")
        
        if not (-180 <= current_lon <= 180):
            raise ValueError(f"Longitude {current_lon} is outside valid range (-180 to 180)")
        
        # Identify region and season
        region = self.identify_region(current_lat, current_lon)
        season = self.get_current_season()
        
        print(f"🧊 Predicting for region: {region}, season: {season}")
        
        # Get regional patterns
        if self.regional_patterns and region in self.regional_patterns:
            pattern = self.regional_patterns[region]
        else:
            # Fallback pattern
            pattern = {
                'avg_speed_km_day': 8.0,
                'avg_direction_deg': 45,
                'typical_vel_lat': 0.02,
                'typical_vel_lon': 0.02
            }
        
        # Apply seasonal adjustment
        seasonal_multiplier = 1.0
        if self.seasonal_patterns and season in self.seasonal_patterns:
            seasonal_multiplier = self.seasonal_patterns[season]['speed_multiplier']
        
        # Calculate daily velocity (degrees per day)
        base_vel_lat = pattern['typical_vel_lat'] * seasonal_multiplier
        base_vel_lon = pattern['typical_vel_lon'] * seasonal_multiplier
        
        # Add some randomness for uncertainty
        vel_lat_uncertainty = base_vel_lat * 0.3  # 30% uncertainty
        vel_lon_uncertainty = base_vel_lon * 0.3
        
        predictions = {}
        
        for days in days_ahead:
            # Calculate position change
            delta_lat = base_vel_lat * days
            delta_lon = base_vel_lon * days
            
            # Add uncertainty bounds
            pred_lat = current_lat + delta_lat
            pred_lon = current_lon + delta_lon
            
            # Uncertainty bounds
            lat_min = current_lat + (base_vel_lat - vel_lat_uncertainty) * days
            lat_max = current_lat + (base_vel_lat + vel_lat_uncertainty) * days
            lon_min = current_lon + (base_vel_lon - vel_lon_uncertainty) * days
            lon_max = current_lon + (base_vel_lon + vel_lon_uncertainty) * days
            
            # Handle longitude wrapping
            pred_lon = ((pred_lon + 180) % 360) - 180
            lon_min = ((lon_min + 180) % 360) - 180
            lon_max = ((lon_max + 180) % 360) - 180
            
            # Calculate expected distance traveled
            distance_km = self.haversine_distance(current_lat, current_lon, pred_lat, pred_lon)
            
            predictions[f'{days}_day'] = {\n                'predicted_lat': round(pred_lat, 4),\n                'predicted_lon': round(pred_lon, 4),\n                'uncertainty_bounds': {\n                    'lat_min': round(lat_min, 4),\n                    'lat_max': round(lat_max, 4),\n                    'lon_min': round(lon_min, 4),\n                    'lon_max': round(lon_max, 4)\n                },\n                'distance_from_start_km': round(distance_km, 1),\n                'confidence': 'Medium' if days <= 3 else 'Low',\n                'region': region,\n                'season': season\n            }\n        \n        return {\n            'current_position': {'lat': current_lat, 'lon': current_lon},\n            'predictions': predictions,\n            'metadata': {\n                'model_type': 'Statistical Pattern',\n                'region': region,\n                'season': season,\n                'base_speed_km_day': round(pattern['avg_speed_km_day'] * seasonal_multiplier, 1)\n            }\n        }\n    \n    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:\n        \"\"\"Calculate distance between two points\"\"\"\n        R = 6371  # Earth radius in km\n        \n        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])\n        dlat = lat2 - lat1\n        dlon = lon2 - lon1\n        \n        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2\n        c = 2 * atan2(sqrt(a), sqrt(1-a))\n        \n        return R * c\n    \n    def batch_predict(self, positions: List[Tuple[float, float]], \n                     days_ahead: List[int] = [1, 3, 7]) -> List[Dict]:\n        \"\"\"Predict for multiple positions\"\"\"\n        results = []\n        \n        for lat, lon in positions:\n            try:\n                pred = self.predict_position(lat, lon, days_ahead)\n                results.append(pred)\n            except Exception as e:\n                results.append({'error': str(e), 'input': (lat, lon)})\n        \n        return results\n\n\ndef main():\n    \"\"\"\n    Demo the simple predictor\n    \"\"\"\n    print(\"🧊 SIMPLE ICEBERG POSITION PREDICTOR\")\n    print(\"=\" * 50)\n    \n    # Initialize predictor\n    predictor = SimpleIcebergPredictor()\n    \n    # Try to load historical patterns\n    data_path = r\"C:\\Users\\Anto\\OneDrive\\Desktop\\CryoNav-AI-Enabled-Antarctic-Sea-Ice-Iceberg-Trajectory-and-Navigation-Decision-Support-System\\iceberg-trajectory-ml\\data\\complete_iceberg_dataset.csv\"\n    predictor.load_historical_patterns(data_path)\n    \n    # Example predictions\n    test_positions = [\n        (-66.5, 45.2),    # East Antarctic\n        (-72.1, -25.5),   # Weddell Sea\n        (-68.8, 165.3),   # Ross Sea\n        (-58.2, -35.7)    # Southern Ocean\n    ]\n    \n    print(\"\\n📍 EXAMPLE PREDICTIONS:\")\n    print(\"-\" * 50)\n    \n    for i, (lat, lon) in enumerate(test_positions):\n        print(f\"\\n🔍 Position {i+1}: ({lat}°, {lon}°)\")\n        \n        try:\n            result = predictor.predict_position(lat, lon, [1, 3, 7])\n            \n            print(f\"   Region: {result['metadata']['region']}\")\n            print(f\"   Season: {result['metadata']['season']}\")\n            print(f\"   Base speed: {result['metadata']['base_speed_km_day']} km/day\")\n            \n            for day_key, pred in result['predictions'].items():\n                print(f\"   {day_key.replace('_', ' ')}: ({pred['predicted_lat']}, {pred['predicted_lon']}) - {pred['distance_from_start_km']} km drift\")\n        \n        except Exception as e:\n            print(f\"   ❌ Error: {e}\")\n    \n    # Interactive mode\n    print(\"\\n🎯 INTERACTIVE PREDICTION\")\n    print(\"-\" * 30)\n    print(\"Enter iceberg coordinates to get predictions:\")\n    print(\"(Valid range: Latitude -90 to -50, Longitude -180 to 180)\")\n    \n    while True:\n        try:\n            lat_input = input(\"\\nEnter latitude (or 'quit' to exit): \")\n            if lat_input.lower() == 'quit':\n                break\n                \n            lon_input = input(\"Enter longitude: \")\n            \n            lat = float(lat_input)\n            lon = float(lon_input)\n            \n            result = predictor.predict_position(lat, lon)\n            \n            print(f\"\\n📊 PREDICTION RESULTS for ({lat}, {lon}):\")\n            print(f\"   🌍 Region: {result['metadata']['region']}\")\n            print(f\"   📅 Season: {result['metadata']['season']}\")\n            print(f\"   🏃 Base speed: {result['metadata']['base_speed_km_day']} km/day\")\n            \n            print(\"\\n🔮 FUTURE POSITIONS:\")\n            for day_key, pred in result['predictions'].items():\n                days = day_key.replace('_day', '')\n                print(f\"   {days} day(s): ({pred['predicted_lat']}, {pred['predicted_lon']})\")\n                print(f\"     Distance: {pred['distance_from_start_km']} km\")\n                print(f\"     Confidence: {pred['confidence']}\")\n                \n        except KeyboardInterrupt:\n            print(\"\\nExiting...\")\n            break\n        except Exception as e:\n            print(f\"❌ Error: {e}\")\n            print(\"Please enter valid coordinates.\")\n    \n    print(\"\\n👋 Thanks for using the Iceberg Predictor!\")\n\nif __name__ == \"__main__\":\n    main()"