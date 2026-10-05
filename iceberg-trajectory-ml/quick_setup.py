"""
Quick Setup for Iceberg Prediction
Processes a good sample of data and creates working predictor
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

def quick_data_processing():
    """Quick processing of iceberg data"""
    print("🧊 QUICK DATA PROCESSING")
    print("=" * 40)
    
    from comprehensive_processor import ComprehensiveIcebergProcessor
    
    # Configuration
    data_root_dir = r"C:\Users\Anto\OneDrive\Desktop\CryoNav-AI-Enabled-Antarctic-Sea-Ice-Iceberg-Trajectory-and-Navigation-Decision-Support-System\DATA"
    output_dir = Path(__file__).parent / "data"
    
    processor = ComprehensiveIcebergProcessor(data_root_dir)
    
    # Process current icebergs CSV first (quick)
    print("\n📊 Processing current iceberg positions...")
    current_df = processor.process_current_icebergs_csv()
    
    # Process a sample of historical data (50 files)
    print("\n📊 Processing sample of historical trajectories (50 icebergs)...")
    
    consol_dir = os.path.join(data_root_dir, "consolidated_database_v8.0", "updated7_consol")
    if os.path.exists(consol_dir):
        import glob
        csv_files = glob.glob(os.path.join(consol_dir, "*.csv"))
        
        # Select 50 diverse files
        selected_files = csv_files[::len(csv_files)//50][:50]  # Every Nth file to get diversity
        
        historical_data = []
        successful_count = 0
        
        for i, filepath in enumerate(selected_files):
            print(f"   Processing {i+1}/50: {os.path.basename(filepath)}")
            
            try:
                df = pd.read_csv(filepath)
                iceberg_name = os.path.basename(filepath).replace('.csv', '').upper()
                
                if len(df) >= 10:  # Minimum observations needed
                    processed_df = processor.process_single_iceberg(df, iceberg_name)
                    
                    if not processed_df.empty and len(processed_df) >= 5:
                        historical_data.append(processed_df)
                        successful_count += 1
                        
            except Exception as e:
                continue  # Skip problematic files
        
        # Combine data
        all_datasets = []
        
        if historical_data:
            historical_df = pd.concat(historical_data, ignore_index=True)
            historical_df['data_source'] = 'historical'
            all_datasets.append(historical_df)
            print(f"   ✅ Historical: {len(historical_df)} observations, {historical_df['iceberg_id'].nunique()} icebergs")
        
        if not current_df.empty:
            current_df['data_source'] = 'current'  
            all_datasets.append(current_df)
            print(f"   ✅ Current: {len(current_df)} observations")
        
        # Combine and save
        if all_datasets:
            combined_df = pd.concat(all_datasets, ignore_index=True, sort=False)
            combined_df = combined_df.sort_values(['iceberg_id', 'datetime']).reset_index(drop=True)
            
            # Save data
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "iceberg_dataset_sample.csv"
            combined_df.to_csv(output_path, index=False)
            
            print(f"\n✅ QUICK PROCESSING COMPLETE!")
            print(f"   📊 Total observations: {len(combined_df)}")
            print(f"   🧊 Unique icebergs: {combined_df['iceberg_id'].nunique()}")
            print(f"   📄 Saved to: {output_path}")
            
            return str(output_path)
    
    return None

def create_simple_predictor_demo():
    """Create and demo the simple predictor"""
    print("\n🧊 CREATING PREDICTION SYSTEM")
    print("=" * 40)
    
    from simple_predictor import SimpleIcebergPredictor
    
    # Initialize predictor
    predictor = SimpleIcebergPredictor()
    
    # Try to load processed data
    data_path = Path(__file__).parent / "data" / "iceberg_dataset_sample.csv"
    if data_path.exists():
        predictor.load_historical_patterns(str(data_path))
    else:
        print("⚠️  Using default patterns (no processed data found)")
        predictor.use_default_patterns()
    
    # Test predictions
    print("\n🔮 TESTING PREDICTIONS:")
    
    test_cases = [
        {"name": "Weddell Sea Iceberg", "lat": -70.5, "lon": -25.0},
        {"name": "Ross Sea Iceberg", "lat": -75.2, "lon": 165.8}, 
        {"name": "East Antarctic Iceberg", "lat": -66.1, "lon": 85.3},
        {"name": "Southern Ocean Iceberg", "lat": -58.7, "lon": -35.2}
    ]
    
    for test in test_cases:
        print(f"\n📍 {test['name']} at ({test['lat']}, {test['lon']}):")
        
        try:
            result = predictor.predict_position(test['lat'], test['lon'])
            
            print(f"   🌍 Region: {result['metadata']['region']}")
            print(f"   📅 Season: {result['metadata']['season']}")
            print(f"   🏃 Speed: {result['metadata']['base_speed_km_day']} km/day")
            
            for day_key, pred in result['predictions'].items():
                days = day_key.replace('_day', '')
                print(f"   📈 {days}d ahead: ({pred['predicted_lat']:.2f}, {pred['predicted_lon']:.2f}) - {pred['distance_from_start_km']}km drift")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return True

def create_api_interface():
    """Create simple API-like interface"""
    
    api_code = '''
"""
Simple Iceberg Prediction API
Usage: python iceberg_api.py lat lon
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

def predict(lat, lon, days_ahead=[1, 3, 7]):
    """
    Predict iceberg trajectory
    
    Args:
        lat: Current latitude (-90 to -50)
        lon: Current longitude (-180 to 180) 
        days_ahead: Days to predict ahead
    
    Returns:
        Prediction results
    """
    from simple_predictor import SimpleIcebergPredictor
    
    predictor = SimpleIcebergPredictor()
    
    # Load data if available
    data_path = Path(__file__).parent / "data" / "iceberg_dataset_sample.csv"
    if data_path.exists():
        predictor.load_historical_patterns(str(data_path))
    
    return predictor.predict_position(lat, lon, days_ahead)

def main():
    """Command line interface"""
    if len(sys.argv) != 3:
        print("Usage: python iceberg_api.py <latitude> <longitude>")
        print("Example: python iceberg_api.py -66.5 45.2")
        sys.exit(1)
    
    try:
        lat = float(sys.argv[1])
        lon = float(sys.argv[2])
        
        print(f"🧊 Predicting iceberg trajectory from ({lat}, {lon})")
        
        result = predict(lat, lon)
        
        print(f"\\n📊 RESULTS:")
        print(f"Region: {result['metadata']['region']}")
        print(f"Season: {result['metadata']['season']}")
        print(f"Base Speed: {result['metadata']['base_speed_km_day']} km/day")
        
        print(f"\\n🔮 PREDICTIONS:")
        for day_key, pred in result['predictions'].items():
            days = day_key.replace('_day', '')
            print(f"{days} day(s): ({pred['predicted_lat']}, {pred['predicted_lon']}) - {pred['distance_from_start_km']} km")
            print(f"         Confidence: {pred['confidence']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    api_path = Path(__file__).parent / "iceberg_api.py"
    with open(api_path, 'w') as f:
        f.write(api_code)
    
    print(f"\n✅ API interface created: {api_path}")
    return str(api_path)

def main():
    """Quick setup main"""
    print("🧊 ICEBERG PREDICTION - QUICK SETUP")
    print("=" * 50)
    print("This will create a working iceberg prediction system using a sample of your data")
    
    try:
        # Step 1: Process data sample
        data_path = quick_data_processing()
        
        if data_path:
            # Step 2: Create and test predictor
            create_simple_predictor_demo()
            
            # Step 3: Create API interface  
            api_path = create_api_interface()
            
            print(f"\n🎉 SUCCESS! Iceberg prediction system is ready!")
            print(f"\n📁 FILES CREATED:")
            print(f"   📄 Data: {data_path}")
            print(f"   🔮 API: {api_path}")
            
            print(f"\n🚀 HOW TO USE:")
            print(f"   1. Command line: python iceberg_api.py -66.5 45.2")
            print(f"   2. Interactive: python src/simple_predictor.py")
            print(f"   3. In Python:")
            print(f"      from iceberg_api import predict")
            print(f"      result = predict(-66.5, 45.2)")
            
            print(f"\n📊 PREDICTION EXAMPLE:")
            print(f"   Input: Latitude -66.5, Longitude 45.2")
            print(f"   Output: Future positions at 1, 3, 7 days")
            print(f"   Features: Region detection, seasonal effects, uncertainty bounds")
            
            return True
        else:
            print("❌ Data processing failed")
            return False
            
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()