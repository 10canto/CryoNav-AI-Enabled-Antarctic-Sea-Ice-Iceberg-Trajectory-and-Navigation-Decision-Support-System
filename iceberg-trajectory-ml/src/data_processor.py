"""
Iceberg Data Processor
Loads, cleans, and engineers features from consolidated iceberg database
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2, degrees
from typing import List, Tuple, Dict
import warnings
warnings.filterwarnings('ignore')

class IcebergDataProcessor:
    def __init__(self, data_dir: str):
        """
        Initialize the data processor
        
        Args:
            data_dir: Path to directory containing CSV files
        """
        self.data_dir = data_dir
        self.processed_data = {}
        
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth
        
        Returns:
            Distance in kilometers
        """
        if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
            return np.nan
            
        R = 6371  # Earth's radius in km
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate bearing (direction) from point 1 to point 2
        
        Returns:
            Bearing in degrees (0-360)
        """
        if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
            return np.nan
            
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        dlon = lon2 - lon1
        x = sin(dlon) * cos(lat2)
        y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
        
        bearing = atan2(x, y)
        return (degrees(bearing) + 360) % 360
    
    def sensor_fusion(self, row: pd.Series) -> Tuple[float, float, float]:
        """
        Combine multiple sensor readings into best position estimate
        
        Returns:
            (latitude, longitude, confidence_score)
        """
        # Extract sensor data
        sensors = {
            'ascat': (row.get('ascat_1', 0), row.get('ascat_2', 0), row.get('ascat_3', 0)),
            'nic': (row.get('nic_1', 0), row.get('nic_2', 0), row.get('nic_3', 0)),
            'oscat': (row.get('oscat_1', 0), row.get('oscat_2', 0), row.get('oscat_3', 0))
        }
        
        valid_positions = []
        total_confidence = 0
        
        for sensor_name, (lat, lon, flag) in sensors.items():
            if lat != 0 and lon != 0 and not pd.isna(lat) and not pd.isna(lon):
                # Weight real observations higher than interpolated
                weight = 1.0 if flag == 1 else 0.5
                valid_positions.append((lat, lon, weight))
                total_confidence += weight
        
        if not valid_positions:
            return np.nan, np.nan, 0.0
        
        # Weighted average
        weighted_lat = sum(lat * weight for lat, lon, weight in valid_positions) / sum(weight for _, _, weight in valid_positions)
        weighted_lon = sum(lon * weight for lat, lon, weight in valid_positions) / sum(weight for _, _, weight in valid_positions)
        
        confidence = min(total_confidence / 3.0, 1.0)  # Normalize to [0, 1]
        
        return weighted_lat, weighted_lon, confidence
    
    def parse_julian_date(self, julian_date: int) -> Tuple[int, int, datetime]:
        """
        Convert Julian date (YYYYDDD) to year, day_of_year, and datetime
        """
        year = julian_date // 1000
        day_of_year = julian_date % 1000
        
        # Handle invalid day numbers
        if day_of_year == 0:
            day_of_year = 1
        elif day_of_year > 365:
            if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):  # Leap year
                day_of_year = min(day_of_year, 366)
            else:
                day_of_year = min(day_of_year, 365)
        
        try:
            date = datetime.strptime(f"{year}-{day_of_year}", "%Y-%j")
        except:
            # Fallback for invalid dates
            date = datetime(year, 1, 1)
        
        return year, day_of_year, date
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create all derived features from raw iceberg data
        """
        print(f"Engineering features for {len(df)} observations...")
        
        # Sort by date
        df = df.sort_values('date').reset_index(drop=True)
        
        # Parse dates
        date_info = df['date'].apply(lambda x: self.parse_julian_date(x))
        df['year'] = [x[0] for x in date_info]
        df['day_of_year'] = [x[1] for x in date_info]
        df['datetime'] = [x[2] for x in date_info]
        
        # Sensor fusion for position
        positions = df.apply(self.sensor_fusion, axis=1)
        df['lat'] = [pos[0] for pos in positions]
        df['lon'] = [pos[1] for pos in positions]
        df['position_confidence'] = [pos[2] for pos in positions]
        
        # Remove rows with no valid position
        valid_mask = ~(pd.isna(df['lat']) | pd.isna(df['lon']))
        df = df[valid_mask].reset_index(drop=True)
        
        if len(df) < 2:
            return df
        
        # Time differences (in days)
        df['time_delta'] = df['datetime'].diff().dt.total_seconds() / 86400  # Convert to days
        df.loc[0, 'time_delta'] = 1.0  # Assume 1 day for first observation
        
        # Basic velocity (degrees per day)
        df['vel_lat'] = df['lat'].diff() / df['time_delta']
        df['vel_lon'] = df['lon'].diff() / df['time_delta']
        
        # Speed and direction
        df['speed_km_day'] = 0.0
        df['direction'] = 0.0
        
        for i in range(1, len(df)):
            if df.loc[i, 'time_delta'] > 0:
                distance = self.haversine_distance(
                    df.loc[i-1, 'lat'], df.loc[i-1, 'lon'],
                    df.loc[i, 'lat'], df.loc[i, 'lon']
                )
                df.loc[i, 'speed_km_day'] = distance / df.loc[i, 'time_delta']
                
                df.loc[i, 'direction'] = self.calculate_bearing(
                    df.loc[i-1, 'lat'], df.loc[i-1, 'lon'],
                    df.loc[i, 'lat'], df.loc[i, 'lon']
                )
        
        # Acceleration (change in velocity)
        df['acc_lat'] = df['vel_lat'].diff() / df['time_delta']
        df['acc_lon'] = df['vel_lon'].diff() / df['time_delta']
        df['acc_magnitude'] = np.sqrt(df['acc_lat']**2 + df['acc_lon']**2)
        
        # Size features
        df['area_km2'] = df['size_1'] * df['size_2'] * (1.852 ** 2)  # Convert nautical miles to km²
        df['size_ratio'] = df['size_1'] / df['size_2'].replace(0, np.nan)
        
        # Size change rate (area loss per day due to melting)
        df['area_change_rate'] = df['area_km2'].diff() / df['time_delta']
        
        # Seasonal features
        df['season'] = df['day_of_year'].apply(self.get_antarctic_season)
        df['month'] = df['datetime'].dt.month
        
        # Time since start (iceberg age)
        df['days_since_start'] = (df['datetime'] - df['datetime'].min()).dt.total_seconds() / 86400
        
        # Rolling window features (smoothed statistics)
        window_sizes = [3, 7, 15, 30]
        for window in window_sizes:
            if len(df) >= window:
                df[f'speed_avg_{window}d'] = df['speed_km_day'].rolling(window, min_periods=1).mean()
                df[f'speed_std_{window}d'] = df['speed_km_day'].rolling(window, min_periods=1).std()
                df[f'direction_avg_{window}d'] = df['direction'].rolling(window, min_periods=1, center=True).mean()
        
        # Trajectory features
        df['cumulative_distance'] = df['speed_km_day'].cumsum()
        
        # Net displacement from start
        df['net_displacement'] = df.apply(lambda row: self.haversine_distance(
            df.iloc[0]['lat'], df.iloc[0]['lon'], row['lat'], row['lon']
        ), axis=1)
        
        # Tortuosity (path efficiency)
        df['tortuosity'] = df['cumulative_distance'] / (df['net_displacement'] + 1e-6)
        
        # Distance from Antarctic coast (approximation)
        df['distance_from_coast'] = df.apply(self.estimate_distance_from_coast, axis=1)
        
        # Latitude zone (different ocean regions)
        df['lat_zone'] = pd.cut(df['lat'], bins=[-90, -75, -70, -65, -60, -50], 
                               labels=['Deep_Antarctic', 'Coastal_Antarctic', 'Subantarctic', 'Southern_Ocean', 'Temperate'])
        
        print(f"Feature engineering completed. Final shape: {df.shape}")
        return df
    
    def get_antarctic_season(self, day_of_year: int) -> str:
        """
        Get Antarctic season from day of year
        """
        if day_of_year >= 335 or day_of_year < 60:  # Dec-Feb
            return 'Summer'
        elif 60 <= day_of_year < 152:  # Mar-May
            return 'Fall'
        elif 152 <= day_of_year < 244:  # Jun-Aug
            return 'Winter'
        else:  # Sep-Nov
            return 'Spring'
    
    def estimate_distance_from_coast(self, row: pd.Series) -> float:
        """
        Rough approximation of distance from Antarctic coast
        """
        lat, lon = row['lat'], row['lon']
        
        # Very rough approximation: closer to -90 latitude = closer to coast
        # This is a simplification - real implementation would use coastline data
        coast_proximity = abs(lat + 70)  # Rough Antarctic shelf edge at -70°
        return coast_proximity * 111  # Convert degrees to km (rough)
    
    def load_iceberg_file(self, filepath: str) -> pd.DataFrame:
        """
        Load and process a single iceberg CSV file
        """
        try:
            df = pd.read_csv(filepath)
            
            # Get iceberg name from filename
            iceberg_name = os.path.basename(filepath).replace('.csv', '').upper()
            df['iceberg_id'] = iceberg_name
            
            # Filter out rows with no valid data
            df = df.replace(0, np.nan)  # Replace 0s with NaN for sensor readings
            
            # Ensure we have minimum required columns
            required_cols = ['date']
            if not all(col in df.columns for col in required_cols):
                print(f"Warning: {filepath} missing required columns")
                return pd.DataFrame()
            
            # Process features
            df_processed = self.engineer_features(df)
            
            return df_processed
            
        except Exception as e:
            print(f"Error processing {filepath}: {str(e)}")
            return pd.DataFrame()
    
    def process_all_icebergs(self, sample_size: int = None) -> pd.DataFrame:
        """
        Load and process all iceberg files in the directory
        
        Args:
            sample_size: If specified, only process this many files (for testing)
        """
        csv_files = glob.glob(os.path.join(self.data_dir, "*.csv"))
        
        if sample_size:
            csv_files = csv_files[:sample_size]
        
        print(f"Found {len(csv_files)} CSV files to process")
        
        all_data = []
        successful_files = 0
        
        for i, filepath in enumerate(csv_files):
            print(f"Processing {i+1}/{len(csv_files)}: {os.path.basename(filepath)}")
            
            df = self.load_iceberg_file(filepath)
            
            if not df.empty and len(df) >= 10:  # Minimum 10 observations for useful predictions
                all_data.append(df)
                successful_files += 1
                print(f"  ✓ Loaded {len(df)} observations")
            else:
                print(f"  ✗ Skipped (insufficient data)")
        
        if not all_data:
            raise ValueError("No valid iceberg data found!")
        
        # Combine all icebergs
        combined_df = pd.concat(all_data, ignore_index=True)
        
        print(f"\n=== PROCESSING SUMMARY ===")
        print(f"Files processed successfully: {successful_files}/{len(csv_files)}")
        print(f"Total observations: {len(combined_df)}")
        print(f"Unique icebergs: {combined_df['iceberg_id'].nunique()}")
        print(f"Date range: {combined_df['datetime'].min()} to {combined_df['datetime'].max()}")
        
        return combined_df
    
    def save_processed_data(self, df: pd.DataFrame, output_path: str):
        """
        Save processed data to file
        """
        df.to_csv(output_path, index=False)
        print(f"Processed data saved to {output_path}")

def main():
    """
    Main processing pipeline
    """
    # Set up paths
    data_dir = r"C:\Users\Anto\OneDrive\Desktop\CryoNav-AI-Enabled-Antarctic-Sea-Ice-Iceberg-Trajectory-and-Navigation-Decision-Support-System\DATA\consolidated_database_v8.0\updated7_consol"
    output_dir = r"C:\Users\Anto\OneDrive\Desktop\CryoNav-AI-Enabled-Antarctic-Sea-Ice-Iceberg-Trajectory-and-Navigation-Decision-Support-System\iceberg-trajectory-ml\data"
    
    # Initialize processor
    processor = IcebergDataProcessor(data_dir)
    
    # Process all icebergs (start with sample for testing)
    print("Starting data processing...")
    df_processed = processor.process_all_icebergs(sample_size=10)  # Start with 10 files
    
    # Save processed data
    output_path = os.path.join(output_dir, "processed_icebergs.csv")
    os.makedirs(output_dir, exist_ok=True)
    processor.save_processed_data(df_processed, output_path)
    
    # Display sample
    print(f"\n=== SAMPLE DATA ===")
    print(df_processed[['iceberg_id', 'datetime', 'lat', 'lon', 'speed_km_day', 'direction', 'area_km2']].head(10))
    
    print(f"\n=== FEATURE SUMMARY ===")
    print(f"Columns: {list(df_processed.columns)}")
    print(f"Data types:\n{df_processed.dtypes}")
    
    print("\nData processing completed! 🎉")

if __name__ == "__main__":
    main()