"""
Simple runner for Iceberg Trajectory Prediction
Works with basic Python packages only
"""

import sys
import os
from pathlib import Path

def check_basic_packages():
    """Check if basic packages are available"""
    try:
        import numpy
        import pandas
        import matplotlib
        print("✅ Basic packages (numpy, pandas, matplotlib) are available")
        return True
    except ImportError as e:
        print(f"❌ Missing basic package: {e}")
        print("\nPlease install basic packages first:")
        print("pip install numpy pandas matplotlib")
        return False

def run_data_processing_only():
    """Run just the data processing part"""
    print("🧊 ICEBERG DATA PROCESSING (Basic Version)")
    print("=" * 50)
    
    if not check_basic_packages():
        return False
    
    # Add src to path
    src_path = Path(__file__).parent / "src"
    sys.path.append(str(src_path))
    
    try:
        print("\n📊 Starting data processing...")
        
        # Import and run data processor
        from data_processor import IcebergDataProcessor
        
        # Configuration
        data_dir = r"C:\Users\Anto\OneDrive\Desktop\CryoNav-AI-Enabled-Antarctic-Sea-Ice-Iceberg-Trajectory-and-Navigation-Decision-Support-System\DATA\consolidated_database_v8.0\updated7_consol"
        output_dir = Path(__file__).parent / "data"
        
        print(f"📁 Input directory: {data_dir}")
        print(f"📁 Output directory: {output_dir}")
        
        # Check if input directory exists
        if not Path(data_dir).exists():
            print(f"❌ Input directory not found: {data_dir}")
            return False
        
        # Create processor
        processor = IcebergDataProcessor(data_dir)
        
        # Process data (start with small sample)
        print("\n🔄 Processing iceberg data (sample of 5 icebergs)...")
        df_processed = processor.process_all_icebergs(sample_size=5)
        
        # Save processed data
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "processed_icebergs_sample.csv"
        processor.save_processed_data(df_processed, str(output_path))
        
        # Display results
        print(f"\n📈 PROCESSING RESULTS:")
        print(f"   Total observations: {len(df_processed)}")
        print(f"   Unique icebergs: {df_processed['iceberg_id'].nunique()}")
        print(f"   Features created: {len(df_processed.columns)}")
        print(f"   Date range: {df_processed['datetime'].min()} to {df_processed['datetime'].max()}")
        
        print(f"\n📋 SAMPLE DATA:")
        print(df_processed[['iceberg_id', 'datetime', 'lat', 'lon', 'speed_km_day', 'area_km2']].head(10))
        
        print(f"\n📊 FEATURE STATISTICS:")
        numeric_cols = df_processed.select_dtypes(include=['float64', 'int64']).columns
        print(df_processed[numeric_cols].describe())
        
        print(f"\n✅ Data processing completed successfully!")
        print(f"📄 Processed data saved to: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🧊 Iceberg Trajectory Prediction - Simple Mode")
    print("\nThis version runs basic data processing without ML dependencies.")
    print("Once data is processed, you can install ML packages and run full training.")
    
    success = run_data_processing_only()
    
    if success:
        print("\n🎉 SUCCESS! Next steps:")
        print("1. Install ML packages: python setup.py install")
        print("2. Run full pipeline: python main.py")
        print("3. Or continue with manual analysis using the processed CSV file")
    else:
        print("\n❌ Processing failed. Please check the error messages above.")

if __name__ == "__main__":
    main()