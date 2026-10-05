"""
Complete Iceberg Trajectory Prediction Pipeline
Processes ALL data and creates accurate prediction model
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

def check_packages():
    """Check available packages"""
    available = {}
    
    try:
        import numpy
        available['numpy'] = True
    except ImportError:
        available['numpy'] = False
    
    try:
        import pandas  
        available['pandas'] = True
    except ImportError:
        available['pandas'] = False
    
    try:
        import matplotlib
        available['matplotlib'] = True
    except ImportError:
        available['matplotlib'] = False
    
    try:
        import sklearn
        available['sklearn'] = True
    except ImportError:
        available['sklearn'] = False
    
    try:
        import tensorflow
        available['tensorflow'] = True
    except ImportError:
        available['tensorflow'] = False
    
    return available

def run_comprehensive_processing():
    """Process ALL iceberg data"""
    print("🧊 STEP 1: COMPREHENSIVE DATA PROCESSING")
    print("=" * 60)
    
    try:
        from comprehensive_processor import main as process_all_data
        process_all_data()
        return True
    except Exception as e:
        print(f"❌ Data processing failed: {e}")
        return False

def run_simple_prediction():
    """Run simple statistical prediction"""
    print("\n🧊 STEP 2: SIMPLE PREDICTION (Statistical Model)")
    print("=" * 60)
    
    try:
        from simple_predictor import main as run_predictor
        run_predictor()
        return True
    except Exception as e:
        print(f"❌ Simple prediction failed: {e}")
        return False

def run_lstm_training():
    """Train LSTM model if TensorFlow is available"""
    print("\n🧊 STEP 3: LSTM TRAINING (Deep Learning)")
    print("=" * 60)
    
    packages = check_packages()
    
    if not packages['tensorflow']:
        print("⚠️  TensorFlow not available. Skipping LSTM training.")
        print("Install TensorFlow to enable deep learning predictions:")
        print("   pip install tensorflow")
        return False
    
    try:
        # Import and modify trainer for comprehensive data
        from trainer import IcebergTrajectoryTrainer
        
        # Configuration for complete dataset
        data_path = Path(__file__).parent / "data" / "complete_iceberg_dataset.csv"
        output_dir = Path(__file__).parent / "results"
        
        if not data_path.exists():
            print(f"❌ Complete dataset not found: {data_path}")
            print("Please run comprehensive data processing first.")
            return False
        
        # Initialize trainer
        trainer = IcebergTrajectoryTrainer(
            data_path=str(data_path),
            output_dir=str(output_dir),
            sequence_length=30,  # 30 days of history
            prediction_horizon=7  # Predict 7 days ahead
        )
        
        # Load and train
        df = trainer.load_data()
        training_history = trainer.train_model(df)
        trainer.plot_training_history()
        metrics = trainer.evaluate_model()
        trainer.save_training_report()
        
        print("✅ LSTM training completed!")
        return True
        
    except Exception as e:
        print(f"❌ LSTM training failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_prediction_interface():
    """Create easy-to-use prediction interface"""
    interface_code = '''
"""
ICEBERG POSITION PREDICTOR
Simple interface for iceberg trajectory prediction
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from simple_predictor import SimpleIcebergPredictor

def predict_iceberg_position(lat, lon, days=[1, 3, 7]):
    """
    Predict iceberg position given current coordinates
    
    Args:
        lat: Current latitude (-90 to -50)
        lon: Current longitude (-180 to 180)
        days: List of days ahead to predict
    
    Returns:
        Dictionary with predictions
    """
    predictor = SimpleIcebergPredictor()
    
    # Try to load historical data
    data_path = Path(__file__).parent / "data" / "complete_iceberg_dataset.csv"
    if data_path.exists():
        predictor.load_historical_patterns(str(data_path))
    
    return predictor.predict_position(lat, lon, days)

# Example usage
if __name__ == "__main__":
    # Example: Iceberg near Antarctica
    result = predict_iceberg_position(-66.5, 45.2)
    
    print("🧊 ICEBERG PREDICTION EXAMPLE")
    print(f"Current position: {result['current_position']}")
    print(f"Region: {result['metadata']['region']}")
    
    for day_key, pred in result['predictions'].items():
        print(f"{day_key}: ({pred['predicted_lat']}, {pred['predicted_lon']}) - {pred['distance_from_start_km']} km")
'''
    
    interface_path = Path(__file__).parent / "predict_iceberg.py"
    with open(interface_path, 'w') as f:
        f.write(interface_code)
    
    print(f"✅ Prediction interface created: {interface_path}")

def main():
    """
    Run complete pipeline
    """
    print("🧊 COMPLETE ICEBERG TRAJECTORY PREDICTION PIPELINE")
    print("=" * 70)
    print("This will process ALL your iceberg data and create prediction models")
    
    # Check available packages
    packages = check_packages()
    
    print(f"\n📦 PACKAGE STATUS:")
    for pkg, available in packages.items():
        status = "✅" if available else "❌"
        print(f"   {status} {pkg}")
    
    if not (packages['numpy'] and packages['pandas']):
        print("❌ Essential packages missing! Please install:")
        print("   pip install numpy pandas matplotlib")
        return False
    
    success_count = 0
    
    # Step 1: Process all data
    if run_comprehensive_processing():
        success_count += 1
        
        # Step 2: Simple prediction
        if run_simple_prediction():
            success_count += 1
        
        # Step 3: LSTM training (if TensorFlow available)
        if packages['tensorflow'] and packages['sklearn']:
            if run_lstm_training():
                success_count += 1
    
    # Step 4: Create easy interface
    create_prediction_interface()
    
    print(f"\n🎉 PIPELINE RESULTS:")
    print(f"   ✅ Steps completed: {success_count}")
    print(f"   📊 Data processing: {'✅' if success_count >= 1 else '❌'}")
    print(f"   🔮 Statistical prediction: {'✅' if success_count >= 2 else '❌'}")
    print(f"   🧠 Deep learning: {'✅' if success_count >= 3 else '⚠️  TensorFlow needed'}")
    
    print(f"\n📁 RESULTS LOCATION:")
    print(f"   📄 Processed data: data/complete_iceberg_dataset.csv")
    print(f"   🔮 Prediction interface: predict_iceberg.py")
    print(f"   🧠 Trained models: results/models/ (if TensorFlow available)")
    
    print(f"\n🚀 QUICK START:")
    print(f"   python predict_iceberg.py  # Simple prediction example")
    print(f"   python src/simple_predictor.py  # Interactive predictor")
    
    if success_count >= 1:
        print(f"\n✅ SUCCESS! Your iceberg prediction system is ready!")
        return True
    else:
        print(f"\n❌ FAILED! Please check error messages above.")
        return False

if __name__ == "__main__":
    main()