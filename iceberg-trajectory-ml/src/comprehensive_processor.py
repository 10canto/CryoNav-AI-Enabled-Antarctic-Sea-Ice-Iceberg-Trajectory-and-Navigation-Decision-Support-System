"""
Comprehensive Iceberg Data Processor
Processes ALL available iceberg data for accurate prediction model
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2, degrees
from typing import List, Tuple, Dict
import warnings
warnings.filterwarnings('ignore')

class ComprehensiveIcebergProcessor:
    def __init__(self, data_root_dir: str):
        """
        Initialize processor for ALL iceberg data
        
        Args:
            data_root_dir: Root DATA directory containing all iceberg files
        """
        self.data_root_dir = data_root_dir
        self.all_data = []
        
    def process_consolidated_database(self) -> pd.DataFrame:
        """
        Process the complete consolidated database (400+ icebergs)
        """
        consol_dir = os.path.join(self.data_root_dir, "consolidated_database_v8.0", "updated7_consol")
        
        if not os.path.exists(consol_dir):
            print(f"❌ Consolidated database not found: {consol_dir}")
            return pd.DataFrame()
        
        csv_files = glob.glob(os.path.join(consol_dir, "*.csv"))
        print(f"📁 Found {len(csv_files)} iceberg files in consolidated database")
        
        all_icebergs = []
        successful_count = 0
        
        for i, filepath in enumerate(csv_files):
            if (i + 1) % 50 == 0:  # Progress update
                print(f"   Processing {i+1}/{len(csv_files)} files...")
            
            try:
                df = pd.read_csv(filepath)
                iceberg_name = os.path.basename(filepath).replace('.csv', '').upper()
                
                # Skip if insufficient data
                if len(df) < 10:
                    continue
                
                # Process this iceberg
                processed_df = self.process_single_iceberg(df, iceberg_name)
                
                if not processed_df.empty and len(processed_df) >= 5:
                    all_icebergs.append(processed_df)
                    successful_count += 1
                
            except Exception as e:
                # Skip problematic files silently
                continue
        
        if all_icebergs:
            combined_df = pd.concat(all_icebergs, ignore_index=True)
            print(f"✅ Successfully processed {successful_count} icebergs")
            return combined_df
        else:
            return pd.DataFrame()
    
    def process_current_icebergs_csv(self) -> pd.DataFrame:
        """
        Process the current icebergs CSV file (AntarcticIcebergs_20260924.csv)
        """
        csv_path = os.path.join(self.data_root_dir, "AntarcticIcebergs_20260924.csv")
        
        if not os.path.exists(csv_path):
            print(f"❌ Current icebergs file not found: {csv_path}")
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(csv_path)
            print(f"📊 Processing current icebergs CSV: {len(df)} records")
            
            # Convert to standard format for processing
            if 'Last_Date' in df.columns:
                df['date'] = pd.to_datetime(df['Last_Date'], errors='coerce')
            
            # Create trajectory data from current positions
            processed_data = []
            
            for _, row in df.iterrows():
                iceberg_data = {
                    'iceberg_id': row.get('Iceberg', 'Unknown'),
                    'lat': row.get('Lat', np.nan),
                    'lon': row.get('Lon', np.nan),
                    'area_km2': row.get('Area_km2', np.nan),
                    'length': row.get('Length_km', np.nan),
                    'width': row.get('Width_km', np.nan),
                    'datetime': row.get('date', pd.NaT),
                    'data_source': 'current_positions'
                }
                
                if not pd.isna(iceberg_data['lat']) and not pd.isna(iceberg_data['lon']):
                    processed_data.append(iceberg_data)
            
            if processed_data:
                current_df = pd.DataFrame(processed_data)
                print(f"✅ Processed {len(current_df)} current iceberg positions")
                return current_df
            
        except Exception as e:
            print(f"❌ Error processing current icebergs: {e}")
        
        return pd.DataFrame()
    
    def process_single_iceberg(self, df: pd.DataFrame, iceberg_name: str) -> pd.DataFrame:
        """
        Process a single iceberg's tracking data
        """
        # Clean and prepare data
        df = df.copy()
        df['iceberg_id'] = iceberg_name
        
        # Parse dates
        if 'date' in df.columns:
            df['year'] = df['date'] // 1000
            df['day_of_year'] = df['date'] % 1000
            df['datetime'] = pd.to_datetime(df['year'].astype(str) + df['day_of_year'].astype(str), format='%Y%j', errors='coerce')
        
        # Sensor fusion for best position
        positions = []
        for _, row in df.iterrows():
            sensors = [
                (row.get('ascat_1', 0), row.get('ascat_2', 0)),
                (row.get('nic_1', 0), row.get('nic_2', 0)),
                (row.get('oscat_1', 0), row.get('oscat_2', 0))
            ]
            
            valid_positions = [(lat, lon) for lat, lon in sensors if lat != 0 and lon != 0 and not pd.isna(lat) and not pd.isna(lon)]
            
            if valid_positions:
                # Average valid positions
                lat = np.mean([pos[0] for pos in valid_positions])
                lon = np.mean([pos[1] for pos in valid_positions])
                positions.append((lat, lon))
            else:
                positions.append((np.nan, np.nan))
        
        df['lat'] = [pos[0] for pos in positions]
        df['lon'] = [pos[1] for pos in positions]
        
        # Remove rows with invalid positions
        df = df.dropna(subset=['lat', 'lon', 'datetime'])
        df = df.sort_values('datetime').reset_index(drop=True)
        
        if len(df) < 2:
            return pd.DataFrame()
        
        # Calculate trajectory features
        df = self.calculate_trajectory_features(df)
        
        return df
    
    def calculate_trajectory_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate velocity, acceleration, and other trajectory features
        """
        # Time differences
        df['time_delta_days'] = df['datetime'].diff().dt.total_seconds() / 86400
        df['time_delta_days'].fillna(1.0, inplace=True)
        
        # Velocity (degrees per day)
        df['vel_lat'] = df['lat'].diff() / df['time_delta_days']
        df['vel_lon'] = df['lon'].diff() / df['time_delta_days']
        
        # Speed and direction
        df['speed_km_day'] = 0.0
        df['direction_deg'] = 0.0
        
        for i in range(1, len(df)):
            if df.iloc[i]['time_delta_days'] > 0:
                lat1, lon1 = df.iloc[i-1]['lat'], df.iloc[i-1]['lon']
                lat2, lon2 = df.iloc[i]['lat'], df.iloc[i]['lon']
                
                # Haversine distance
                distance_km = self.haversine_distance(lat1, lon1, lat2, lon2)
                df.loc[df.index[i], 'speed_km_day'] = distance_km / df.iloc[i]['time_delta_days']
                
                # Bearing
                df.loc[df.index[i], 'direction_deg'] = self.calculate_bearing(lat1, lon1, lat2, lon2)
        
        # Acceleration
        df['acc_lat'] = df['vel_lat'].diff() / df['time_delta_days']
        df['acc_lon'] = df['vel_lon'].diff() / df['time_delta_days']
        
        # Size features
        if 'size_1' in df.columns and 'size_2' in df.columns:
            df['area_km2'] = df['size_1'] * df['size_2'] * (1.852 ** 2)  # Convert from nautical miles
        
        # Temporal features
        df['day_of_year'] = df['datetime'].dt.dayofyear
        df['month'] = df['datetime'].dt.month
        df['year'] = df['datetime'].dt.year
        
        # Distance from start
        if len(df) > 0:
            start_lat, start_lon = df.iloc[0]['lat'], df.iloc[0]['lon']
            df['distance_from_start_km'] = df.apply(
                lambda row: self.haversine_distance(start_lat, start_lon, row['lat'], row['lon']), 
                axis=1
            )
        
        # Rolling averages for smoothing
        for window in [3, 7]:
            if len(df) >= window:
                df[f'speed_avg_{window}d'] = df['speed_km_day'].rolling(window, min_periods=1).mean()
        
        return df
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points on Earth"""
        if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
            return np.nan
            
        R = 6371  # Earth radius in km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate bearing from point 1 to point 2"""
        if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
            return np.nan
            
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlon = lon2 - lon1
        
        x = sin(dlon) * cos(lat2)
        y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
        bearing = atan2(x, y)
        
        return (degrees(bearing) + 360) % 360
    
    def process_all_data(self) -> pd.DataFrame:
        """
        Process ALL available iceberg data
        """
        print("🧊 PROCESSING ALL ICEBERG DATA")
        print("=" * 50)
        
        all_datasets = []
        
        # 1. Process consolidated database (historical trajectories)
        print("\n📊 Processing consolidated database (historical trajectories)...")
        historical_df = self.process_consolidated_database()
        if not historical_df.empty:
            historical_df['data_source'] = 'historical'
            all_datasets.append(historical_df)
            print(f"   ✅ Historical data: {len(historical_df)} observations, {historical_df['iceberg_id'].nunique()} icebergs")
        
        # 2. Process current icebergs
        print("\n📊 Processing current iceberg positions...")
        current_df = self.process_current_icebergs_csv()
        if not current_df.empty:
            current_df['data_source'] = 'current'
            all_datasets.append(current_df)
            print(f"   ✅ Current data: {len(current_df)} observations")
        
        # Combine all data
        if all_datasets:
            combined_df = pd.concat(all_datasets, ignore_index=True, sort=False)
            
            # Clean and standardize
            combined_df = combined_df.sort_values(['iceberg_id', 'datetime']).reset_index(drop=True)
            
            # Remove duplicates
            combined_df = combined_df.drop_duplicates(subset=['iceberg_id', 'datetime'], keep='first')
            
            print(f"\n🎉 PROCESSING COMPLETE!")
            print(f"   📊 Total observations: {len(combined_df)}")
            print(f"   🧊 Unique icebergs: {combined_df['iceberg_id'].nunique()}")
            print(f"   📅 Date range: {combined_df['datetime'].min()} to {combined_df['datetime'].max()}")
            print(f"   📏 Features: {len(combined_df.columns)}")
            
            # Show iceberg statistics
            iceberg_stats = combined_df.groupby('iceberg_id').agg({
                'datetime': ['count', 'min', 'max'],
                'speed_km_day': 'mean'
            }).round(2)
            
            print(f"\n📋 Sample Iceberg Statistics:")
            print(iceberg_stats.head(10))
            
            return combined_df
        else:
            print("❌ No data could be processed!")
            return pd.DataFrame()

def main():
    """
    Process all iceberg data
    """
    print("🧊 COMPREHENSIVE ICEBERG DATA PROCESSING")
    print("=" * 60)
    
    # Configuration
    data_root_dir = r"C:\Users\Anto\OneDrive\Desktop\CryoNav-AI-Enabled-Antarctic-Sea-Ice-Iceberg-Trajectory-and-Navigation-Decision-Support-System\DATA"
    output_dir = r"C:\Users\Anto\OneDrive\Desktop\CryoNav-AI-Enabled-Antarctic-Sea-Ice-Iceberg-Trajectory-and-Navigation-Decision-Support-System\iceberg-trajectory-ml\data"
    
    # Initialize processor
    processor = ComprehensiveIcebergProcessor(data_root_dir)
    
    # Process all data
    df_all = processor.process_all_data()
    
    if not df_all.empty:
        # Save complete dataset
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "complete_iceberg_dataset.csv")
        df_all.to_csv(output_path, index=False)
        
        print(f"\n💾 Complete dataset saved to: {output_path}")
        
        # Show data quality summary
        print(f"\n📊 DATA QUALITY SUMMARY:")
        print(f"   Missing values per column:")
        missing_summary = df_all.isnull().sum()
        for col in ['lat', 'lon', 'speed_km_day', 'direction_deg', 'area_km2']:
            if col in missing_summary:
                missing_pct = (missing_summary[col] / len(df_all)) * 100
                print(f"     {col}: {missing_summary[col]} ({missing_pct:.1f}%)")
        
        # Show recent data
        recent_data = df_all[df_all['datetime'] > '2020-01-01'] if 'datetime' in df_all.columns else df_all
        if not recent_data.empty:
            print(f"\n🔍 RECENT DATA (2020+): {len(recent_data)} observations")
            print(recent_data[['iceberg_id', 'datetime', 'lat', 'lon', 'speed_km_day']].head(10))
        
        print(f"\n✅ READY FOR ML TRAINING!")
        
    else:
        print("❌ No data could be processed. Please check your DATA directory structure.")

if __name__ == "__main__":
    main()