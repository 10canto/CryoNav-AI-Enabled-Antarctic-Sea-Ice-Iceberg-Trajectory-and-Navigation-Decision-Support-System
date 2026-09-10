"""
Test Script for Iceberg Detector - Minimal Version

Validates the trained model on test images.
"""

import sys
from pathlib import Path
from detect_icebergs import detect_icebergs

def main():
    """Test detection on test images"""
    
    print("="*60)
    print("  TESTING ICEBERG DETECTOR")
    print("="*60)
    
    # Find test images
    test_dir = Path(__file__).parent / "iceberg-4" / "test" / "images"
    
    if not test_dir.exists():
        print(f"\n✗ Test directory not found: {test_dir}")
        print("  Make sure dataset is in iceberg-4/test/images/")
        sys.exit(1)
    
    test_images = sorted(list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png")))
    
    if not test_images:
        print(f"\n✗ No test images found in {test_dir}")
        sys.exit(1)
    
    print(f"\nFound {len(test_images)} test images")
    
    # Find model weights (look for latest training run)
    runs_dir = Path(__file__).parent / "runs" / "train"
    
    # Try to find the most recent iceberg_detector training
    training_dirs = sorted(runs_dir.glob("iceberg_detector_v*"))
    
    weights_path = None
    for train_dir in reversed(training_dirs):  # Check newest first
        # Check in weights subdirectory
        weight_file = train_dir / "weights" / "best.pt"
        if weight_file.exists():
            weights_path = weight_file
            break
        # Check in root directory
        weight_file = train_dir / "best.pt"
        if weight_file.exists():
            weights_path = weight_file
            break
    
    if not weights_path:
        print(f"\n✗ Model weights not found in {runs_dir}")
        print("  Train the model first: python train_iceberg_detector.py")
        sys.exit(1)
    
    print(f"Using model: {weights_path.name}\n")
    
    # Test on first 5 images
    total_icebergs = 0
    total_time = 0
    
    for i, img_path in enumerate(test_images[:5], 1):
        print(f"[{i}/5] Testing: {img_path.name}")
        
        result = detect_icebergs(
            str(img_path),
            weights_path=str(weights_path),
            confidence_threshold=0.7
        )
        
        if result['success']:
            total_icebergs += result['total_icebergs']
            total_time += result['processing_time_ms']
            print(f"  ✓ Found {result['total_icebergs']} icebergs in {result['processing_time_ms']:.1f}ms")
        else:
            print(f"  ✗ Failed: {result['error']}")
    
    # Summary
    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60)
    print(f"  Total icebergs detected: {total_icebergs}")
    print(f"  Average processing time: {total_time/5:.1f}ms")
    print(f"  Average FPS: {1000/(total_time/5):.1f}")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Test interrupted.")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
