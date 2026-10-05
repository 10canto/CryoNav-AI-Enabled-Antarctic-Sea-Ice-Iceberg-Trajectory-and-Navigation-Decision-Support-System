"""
Working Iceberg Trajectory Predictor
Uses your current iceberg data (2026) and oceanographic patterns
"""

import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2, degrees
from datetime import datetime, timedelta
import json

class WorkingIcebergPredictor:
    """
    Production-ready iceberg trajectory predictor
    """
    
    def __init__(self):
        """Initialize predictor with current iceberg data"""
        self.current_icebergs = None
        self.regional_patterns = self._initialize_regional_patterns()
        self.seasonal_effects = self._initialize_seasonal_effects()
        
        # Load current iceberg data
        self.load_current_icebergs()
    
    def load_current_icebergs(self):
        """Load current iceberg positions from your data"""
        data_path = r"C:\Users\Anto\OneDrive\Desktop\CryoNav-AI-Enabled-Antarctic-Sea-Ice-Iceberg-Trajectory-and-Navigation-Decision-Support-System\DATA\AntarcticIcebergs_20260924.csv"
        
        try:
            df = pd.read_csv(data_path)
            
            # Clean and standardize data
            df_clean = df.copy()
            df_clean['Lat'] = df_clean['Latitude']
            df_clean['Lon'] = df_clean['Longitude'] 
            df_clean['Area_km2'] = df_clean['Area (sqKM)']
            df_clean['Length_km'] = df_clean['Length (NM)'] * 1.852  # Convert to km
            df_clean['Width_km'] = df_clean['Width (NM)'] * 1.852
            
            self.current_icebergs = df_clean
            print(f"✅ Loaded {len(df_clean)} current icebergs from September 2026")
            
            return True
            
        except Exception as e:
            print(f"⚠️  Could not load current icebergs: {e}")
            return False
    
    def _initialize_regional_patterns(self):
        """
        Initialize movement patterns based on Antarctic oceanography
        Based on published research on Antarctic Circumpolar Current and regional patterns
        """
        return {
            'Weddell_Sea': {
                'name': 'Weddell Sea Gyre',
                'bounds': {'lat': (-80, -60), 'lon': (-60, 20)},
                'base_speed_km_day': 8.5,
                'primary_direction': 45,  # Northeast (gyre circulation)
                'vel_lat_per_day': 0.025,  # Degrees latitude per day
                'vel_lon_per_day': 0.030,  # Degrees longitude per day
                'uncertainty_factor': 0.3,
                'description': 'Clockwise gyre circulation, moderate speeds'
            },
            'Ross_Sea': {
                'name': 'Ross Sea Region',
                'bounds': {'lat': (-85, -60), 'lon': (160, -140)},  # Crosses dateline
                'base_speed_km_day': 6.8,
                'primary_direction': 315,  # Northwest
                'vel_lat_per_day': 0.020,
                'vel_lon_per_day': -0.025,
                'uncertainty_factor': 0.35,
                'description': 'Complex currents, ice shelf interactions'
            },
            'Amundsen_Bellingshausen': {
                'name': 'Amundsen-Bellingshausen Seas',
                'bounds': {'lat': (-80, -65), 'lon': (-140, -60)},
                'base_speed_km_day': 9.2,
                'primary_direction': 60,  # Northeast
                'vel_lat_per_day': 0.028,
                'vel_lon_per_day': 0.035,
                'uncertainty_factor': 0.25,
                'description': 'Strong westerly flow, high speeds'
            },
            'East_Antarctic': {
                'name': 'East Antarctic Coast',
                'bounds': {'lat': (-75, -60), 'lon': (20, 160)},
                'base_speed_km_day': 7.5,
                'primary_direction': 90,  # Eastward (ACC flow)
                'vel_lat_per_day': 0.005,  # Mostly eastward
                'vel_lon_per_day': 0.040,
                'uncertainty_factor': 0.28,
                'description': 'Antarctic Circumpolar Current dominates'
            },
            'Southern_Ocean': {
                'name': 'Open Southern Ocean',
                'bounds': {'lat': (-60, -45), 'lon': (-180, 180)},
                'base_speed_km_day': 14.5,
                'primary_direction': 75,  # ENE
                'vel_lat_per_day': 0.045,  # Northward drift
                'vel_lon_per_day': 0.055,
                'uncertainty_factor': 0.4,
                'description': 'High speeds, storm tracks, melting zone'
            }
        }
    
    def _initialize_seasonal_effects(self):
        """
        Initialize seasonal speed and direction modifications
        Based on Antarctic seasonal patterns
        """
        return {
            'Summer': {  # Dec-Feb
                'months': [12, 1, 2],
                'speed_multiplier': 1.6,  # Faster due to reduced sea ice
                'direction_shift': 10,    # More northward (melting zone expansion)
                'uncertainty_increase': 0.15,
                'description': 'High mobility, ice-free conditions'
            },
            'Fall': {    # Mar-May
                'months': [3, 4, 5],
                'speed_multiplier': 1.2,
                'direction_shift': 0,
                'uncertainty_increase': 0.05,
                'description': 'Transition period, moderate speeds'
            },
            'Winter': {  # Jun-Aug
                'months': [6, 7, 8],
                'speed_multiplier': 0.6,  # Much slower due to sea ice
                'direction_shift': -15,   # More confined by ice
                'uncertainty_increase': -0.1,  # More predictable (trapped)
                'description': 'Low mobility, sea ice constraints'
            },
            'Spring': {  # Sep-Nov
                'months': [9, 10, 11],
                'speed_multiplier': 1.0,
                'direction_shift': 5,
                'uncertainty_increase': 0.1,
                'description': 'Gradual ice breakup, increasing mobility'
            }
        }
    
    def identify_region(self, lat, lon):
        """Identify which Antarctic region the position is in"""
        for region_key, pattern in self.regional_patterns.items():
            bounds = pattern['bounds']
            lat_min, lat_max = bounds['lat']
            lon_min, lon_max = bounds['lon']
            
            # Handle longitude wrapping for Ross Sea
            if lon_max < lon_min:  # Crosses 180° meridian
                lon_match = (lon >= lon_min) or (lon <= lon_max)
            else:
                lon_match = (lon_min <= lon <= lon_max)
            
            if (lat_min <= lat <= lat_max) and lon_match:
                return region_key, pattern
        
        # Default to Southern Ocean
        return 'Southern_Ocean', self.regional_patterns['Southern_Ocean']
    
    def get_current_season(self):
        """Get current Antarctic season"""
        month = datetime.now().month
        
        for season, info in self.seasonal_effects.items():
            if month in info['months']:
                return season, info
        
        return 'Spring', self.seasonal_effects['Spring']  # Default
    
    def predict_trajectory(self, lat, lon, days_ahead=[1, 3, 7, 14, 30]):
        """
        Predict iceberg trajectory from current position
        
        Args:
            lat: Current latitude
            lon: Current longitude
            days_ahead: List of prediction horizons
        
        Returns:
            Detailed prediction results
        """
        # Validate inputs
        if not (-90 <= lat <= -40):
            raise ValueError(f"Latitude {lat} outside Antarctic region (-90 to -40)")
        
        if not (-180 <= lon <= 180):
            raise ValueError(f"Longitude {lon} outside valid range")
        
        # Get region and season
        region_key, region_pattern = self.identify_region(lat, lon)
        season_key, season_info = self.get_current_season()
        
        print(f"🧊 Prediction for: Region {region_pattern['name']}, Season {season_key}")
        
        # Calculate base velocities
        base_vel_lat = region_pattern['vel_lat_per_day']
        base_vel_lon = region_pattern['vel_lon_per_day']
        base_speed = region_pattern['base_speed_km_day']
        
        # Apply seasonal effects
        speed_multiplier = season_info['speed_multiplier']
        direction_shift = season_info['direction_shift']
        uncertainty_factor = region_pattern['uncertainty_factor'] + season_info['uncertainty_increase']
        
        # Adjusted velocities
        adj_vel_lat = base_vel_lat * speed_multiplier
        adj_vel_lon = base_vel_lon * speed_multiplier
        adj_speed = base_speed * speed_multiplier
        
        # Calculate predictions
        predictions = {}
        
        for days in days_ahead:
            # Basic trajectory
            pred_lat = lat + (adj_vel_lat * days)
            pred_lon = lon + (adj_vel_lon * days)
            
            # Handle longitude wrapping
            pred_lon = ((pred_lon + 180) % 360) - 180
            
            # Calculate uncertainty bounds
            uncertainty_lat = abs(adj_vel_lat) * uncertainty_factor * days
            uncertainty_lon = abs(adj_vel_lon) * uncertainty_factor * days
            
            lat_min = pred_lat - uncertainty_lat
            lat_max = pred_lat + uncertainty_lat
            lon_min = ((pred_lon - uncertainty_lon + 180) % 360) - 180
            lon_max = ((pred_lon + uncertainty_lon + 180) % 360) - 180
            
            # Calculate total distance
            distance_km = self.haversine_distance(lat, lon, pred_lat, pred_lon)
            
            # Confidence assessment
            if days <= 3:
                confidence = 'High'
            elif days <= 7:
                confidence = 'Medium'  
            elif days <= 14:
                confidence = 'Low'
            else:
                confidence = 'Very Low'
            
            predictions[f'{days}_days'] = {
                'predicted_lat': round(pred_lat, 4),
                'predicted_lon': round(pred_lon, 4),
                'uncertainty_bounds': {
                    'lat_range': [round(lat_min, 4), round(lat_max, 4)],
                    'lon_range': [round(lon_min, 4), round(lon_max, 4)]
                },
                'distance_km': round(distance_km, 1),
                'confidence': confidence,
                'days_ahead': days
            }
        
        return {
            'input_position': {'lat': lat, 'lon': lon},
            'predictions': predictions,
            'metadata': {
                'region': region_pattern['name'],
                'season': season_key,
                'base_speed_km_day': round(adj_speed, 1),
                'primary_direction': region_pattern['primary_direction'] + direction_shift,
                'uncertainty_factor': round(uncertainty_factor, 2),
                'prediction_date': datetime.now().isoformat()
            }
        }
    
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points"""
        R = 6371  # Earth radius in km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def predict_current_icebergs(self):
        """Predict trajectories for all current icebergs"""
        if self.current_icebergs is None:
            print("❌ No current iceberg data loaded")
            return None
        
        results = {}
        
        print(f"🧊 Predicting trajectories for {len(self.current_icebergs)} current icebergs...")
        
        for _, iceberg in self.current_icebergs.iterrows():
            iceberg_id = iceberg['Iceberg']
            lat = iceberg['Lat']
            lon = iceberg['Lon']
            
            try:
                prediction = self.predict_trajectory(lat, lon)
                results[iceberg_id] = prediction
                
                # Print summary
                pred_7d = prediction['predictions']['7_days']
                print(f"   {iceberg_id}: 7-day → ({pred_7d['predicted_lat']}, {pred_7d['predicted_lon']}) - {pred_7d['distance_km']} km")
                
            except Exception as e:
                print(f"   ❌ {iceberg_id}: Error - {e}")
        
        return results
    
    def find_nearest_iceberg(self, lat, lon, max_distance_km=500):
        """Find the nearest current iceberg to a position"""
        if self.current_icebergs is None:
            return None
        
        distances = []
        
        for _, iceberg in self.current_icebergs.iterrows():
            distance = self.haversine_distance(lat, lon, iceberg['Lat'], iceberg['Lon'])
            distances.append({
                'iceberg_id': iceberg['Iceberg'],
                'distance_km': distance,
                'lat': iceberg['Lat'],
                'lon': iceberg['Lon'],
                'area_km2': iceberg['Area_km2']
            })
        
        # Sort by distance
        distances.sort(key=lambda x: x['distance_km'])
        
        # Return nearest if within max distance
        if distances and distances[0]['distance_km'] <= max_distance_km:
            return distances[0]
        
        return None

def main():
    """Demo the working predictor"""
    print("🧊 WORKING ICEBERG TRAJECTORY PREDICTOR")
    print("=" * 50)
    print("Using real Antarctic iceberg data from September 2026")
    
    # Initialize predictor
    predictor = WorkingIcebergPredictor()
    
    if predictor.current_icebergs is None:
        print("❌ Could not load current iceberg data")
        return
    
    print(f"\n📊 CURRENT ICEBERGS LOADED:")
    print(f"   Total icebergs: {len(predictor.current_icebergs)}")
    print(f"   Largest: {predictor.current_icebergs.loc[predictor.current_icebergs['Area_km2'].idxmax(), 'Iceberg']} ({predictor.current_icebergs['Area_km2'].max():.1f} km²)")
    print(f"   Locations: {predictor.current_icebergs['Lat'].min():.1f}° to {predictor.current_icebergs['Lat'].max():.1f}° S")
    
    # Test prediction for a few icebergs
    print(f"\n🔮 SAMPLE PREDICTIONS:")
    sample_icebergs = predictor.current_icebergs.head(3)
    
    for _, iceberg in sample_icebergs.iterrows():
        print(f"\n📍 Iceberg {iceberg['Iceberg']} at ({iceberg['Lat']}, {iceberg['Lon']}):")
        print(f"   Size: {iceberg['Length_km']:.1f} × {iceberg['Width_km']:.1f} km, Area: {iceberg['Area_km2']:.1f} km²")
        
        result = predictor.predict_trajectory(iceberg['Lat'], iceberg['Lon'])
        
        print(f"   Region: {result['metadata']['region']}")
        print(f"   Season: {result['metadata']['season']}")
        print(f"   Speed: {result['metadata']['base_speed_km_day']} km/day")
        
        # Show predictions
        for period in ['1_days', '7_days', '30_days']:
            if period in result['predictions']:
                pred = result['predictions'][period]
                print(f"   {period.replace('_', ' ')}: ({pred['predicted_lat']}, {pred['predicted_lon']}) - {pred['distance_km']} km, {pred['confidence']} confidence")
    
    # Interactive mode
    print(f"\n🎯 INTERACTIVE PREDICTION MODE")
    print(f"Enter coordinates to predict iceberg trajectory:")
    print(f"(Or type 'list' to see all current icebergs)")
    
    while True:
        try:
            user_input = input(f"\nEnter latitude (or 'quit'): ").strip().lower()
            
            if user_input == 'quit':
                break
            elif user_input == 'list':
                print(f"\n📋 CURRENT ICEBERGS:")
                for _, iceberg in predictor.current_icebergs.iterrows():
                    print(f"   {iceberg['Iceberg']}: ({iceberg['Lat']}, {iceberg['Lon']}) - {iceberg['Area_km2']:.1f} km²")
                continue
            
            lat = float(user_input)
            lon = float(input("Enter longitude: "))
            
            # Check for nearby icebergs
            nearest = predictor.find_nearest_iceberg(lat, lon)
            if nearest:
                print(f"   📍 Nearest iceberg: {nearest['iceberg_id']} ({nearest['distance_km']:.1f} km away)")
            
            # Make prediction
            result = predictor.predict_trajectory(lat, lon)
            
            print(f"\n📊 PREDICTION RESULTS:")
            print(f"   🌍 Region: {result['metadata']['region']}")
            print(f"   📅 Season: {result['metadata']['season']}")
            print(f"   🏃 Speed: {result['metadata']['base_speed_km_day']} km/day")
            print(f"   🧭 Direction: {result['metadata']['primary_direction']}°")
            
            print(f"\n🔮 TRAJECTORY FORECAST:")
            for period, pred in result['predictions'].items():
                days = period.replace('_days', '')
                print(f"   {days:>2} days: ({pred['predicted_lat']:>7.3f}, {pred['predicted_lon']:>8.3f}) - {pred['distance_km']:>5.1f} km - {pred['confidence']:>9}")
            
        except KeyboardInterrupt:
            print(f"\nExiting...")
            break
        except ValueError:
            print(f"❌ Please enter valid numbers")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n🎉 Thank you for using the Iceberg Trajectory Predictor!")

if __name__ == "__main__":
    main()