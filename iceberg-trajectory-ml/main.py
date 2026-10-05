"""
Main Pipeline for Iceberg Trajectory Prediction
Runs the complete workflow: data processing -> training -> prediction
"""

import os
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from data_processor import IcebergDataProcessor, main as process_data
from trainer import main as train_model
from predictor import main as make_predictions

def main():
    """
    Run the complete iceberg trajectory prediction pipeline
    """
    print("🧊 ICEBERG TRAJECTORY PREDICTION - COMPLETE PIPELINE 🧊")
    print("=" * 60)
    
    # Configuration
    base_dir = Path(__file__).parent
    data_dir = r"C:\Users\Anto\OneDrive\Desktop\CryoNav-AI-Enabled-Antarctic-Sea-Ice-Iceberg-Trajectory-and-Navigation-Decision-Support-System\DATA\consolidated_database_v8.0\updated7_consol"
    
    print(f"Project directory: {base_dir}")
    print(f"Raw data directory: {data_dir}")
    
    # Check if raw data exists
    if not Path(data_dir).exists():
        print("❌ Raw data directory not found!")
        print("Please ensure the consolidated iceberg database is available.")
        return False
    
    try:
        print("\n" + "="*60)
        print("STEP 1: DATA PROCESSING")
        print("="*60)
        print("Processing raw iceberg CSV files...")
        print("This will:")
        print("- Load all iceberg tracking files")
        print("- Fuse multiple sensor readings")
        print("- Engineer velocity, acceleration, and trajectory features")
        print("- Clean and prepare data for ML")
        
        # Run data processing
        process_data()
        
        print("\n" + "="*60)
        print("STEP 2: MODEL TRAINING")
        print("="*60)
        print("Training LSTM neural network...")
        print("This will:")
        print("- Create training/test sequences")
        print("- Train LSTM model for trajectory prediction")
        print("- Evaluate model performance")
        print("- Save trained model and results")
        
        # Run model training
        train_model()
        
        print("\n" + "="*60)
        print("STEP 3: PREDICTIONS & VISUALIZATION")
        print("="*60)
        print("Making predictions and creating visualizations...")
        print("This will:")
        print("- Load trained model")
        print("- Make trajectory predictions")
        print("- Create interactive visualizations")
        print("- Generate evaluation report")
        
        # Run predictions
        make_predictions()
        
        print("\n" + "="*60)
        print("🎉 PIPELINE COMPLETED SUCCESSFULLY! 🎉")
        print("="*60)
        print("\nResults saved to:")
        print(f"  📊 Training results: {base_dir}/results/")
        print(f"  📈 Visualizations: {base_dir}/visualizations/")
        print(f"  🤖 Trained models: {base_dir}/results/models/")
        print(f"  📋 Processed data: {base_dir}/data/")
        
        print("\nNext steps:")
        print("  1. Review training results in results/training_report.json")
        print("  2. Check model performance in results/models/performance_metrics.json")
        print("  3. View trajectory predictions in visualizations/*.html")
        print("  4. Explore data with notebooks/iceberg_analysis.ipynb")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Check that all requirements are installed: pip install -r requirements.txt")
        print("  2. Verify the raw data path is correct")
        print("  3. Ensure you have sufficient disk space")
        print("  4. Run individual steps manually for debugging")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)