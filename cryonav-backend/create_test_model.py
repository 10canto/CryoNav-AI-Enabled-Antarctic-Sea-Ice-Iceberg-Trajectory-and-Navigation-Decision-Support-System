"""
Create a Test YOLO Model for Development
This creates a minimal YOLOv5 model for testing the integration without a trained model.
"""

import torch
from pathlib import Path

def create_test_model():
    """Create a minimal test model that can be loaded by the detection system."""
    
    output_path = Path("app/detection_models/iceberg_detection/weights/best.pt")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Creating test model at: {output_path}")
    
    # Download YOLOv8 nano model (natively supported by Ultralytics)
    try:
        from ultralytics import YOLO
        print("Downloading YOLOv8 nano model for testing...")
        model = YOLO('yolov8n.pt')  # Downloads automatically if not present
        
        # Save it to our location
        import shutil
        if Path('yolov8n.pt').exists():
            shutil.copy('yolov8n.pt', output_path)
        else:
            # Model already downloaded to cache, load and save
            model.save(output_path)
            
        print(f"✅ Test model created successfully!")
        print(f"   Location: {output_path}")
        print(f"   Size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create test model: {e}")
        print("\nFallback: The system will use mock detections")
        print("This is fine for testing the integration!")
        return False


if __name__ == "__main__":
    print("="*70)
    print("CryoNav Test Model Creator")
    print("="*70)
    print("\n⚠️  WARNING: This creates a TEST model for development only!")
    print("For production, use your trained iceberg detection model.\n")
    
    success = create_test_model()
    
    if success:
        print("\n" + "="*70)
        print("NEXT STEPS:")
        print("="*70)
        print("1. Test the integration:")
        print("   python test_yolo_integration.py")
        print("\n2. To use your REAL trained model:")
        print("   cp /path/to/your/trained/best.pt app/detection_models/iceberg_detection/weights/")
        print("\n3. Start the server:")
        print("   python -m uvicorn app.main:app --reload")
    else:
        print("\n" + "="*70)
        print("MANUAL SETUP REQUIRED:")
        print("="*70)
        print("Place your trained best.pt file at:")
        print("  app/detection_models/iceberg_detection/weights/best.pt")
