"""
Iceberg Detection Inference Function

Production-ready inference function for detecting icebergs in satellite imagery.
Returns structured detection results with geographic coordinates and metadata.
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import logging

# Add local modules to path
sys.path.insert(0, str(Path(__file__).parent))

from model_loader import load_iceberg_model, get_model_loader
from utils_iceberg import (
    CoordinateConverter,
    generate_iceberg_id,
    parse_georeference_from_filename,
    classify_iceberg_size,
    format_coordinates,
    SENTINEL1_ANTARCTIC_CONFIG
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def detect_icebergs(
    image_path: str,
    weights_path: str = None,
    confidence_threshold: float = 0.7,
    center_lat: float = None,
    center_lon: float = None,
    resolution_meters: float = 10.0,
    device: str = '',
    include_visualization: bool = False
) -> Dict[str, Any]:
    """
    Detect icebergs in a satellite image using trained YOLOv5 model.
    
    Args:
        image_path: Path to satellite image file (jpg, png, tif)
        weights_path: Path to trained model weights (.pt file). If None, uses default location.
        confidence_threshold: Minimum confidence score to include detection (0.0-1.0)
        center_lat: Center latitude of image (default: -65.0 for Antarctic)
        center_lon: Center longitude of image (default: -64.0 for Antarctic)
        resolution_meters: Ground sample distance in meters/pixel (default: 10m for Sentinel-1)
        device: Device to run inference on ('cpu', 'cuda', '0', etc.)
        include_visualization: If True, returns annotated image as numpy array
    
    Returns:
        Dictionary with detection results:
        {
            "success": bool,
            "icebergs": [
                {
                    "id": "ICE_20240115_123045_001",
                    "bounding_box": {"x": 245, "y": 180, "width": 50, "height": 45},
                    "position": {"lat": -65.234, "lon": -64.567},
                    "bounds": {"min_lat": ..., "max_lat": ..., "min_lon": ..., "max_lon": ...},
                    "size_meters": {
                        "width_m": 500,
                        "height_m": 450,
                        "area_m2": 225000,
                        "estimated_diameter_m": 800
                    },
                    "size_classification": "Medium",
                    "confidence": 0.92
                },
                ...
            ],
            "detection_time": "2024-01-15T12:30:45Z",
            "total_icebergs": 1,
            "image_info": {
                "path": "path/to/image.jpg",
                "width": 640,
                "height": 640,
                "resolution_meters": 10.0
            },
            "processing_time_ms": 75.3,
            "annotated_image": np.array (if include_visualization=True)
        }
        
        On error:
        {
            "success": False,
            "error": "Error message",
            "icebergs": [],
            "total_icebergs": 0
        }
    
    Example:
        >>> result = detect_icebergs('satellite_image.jpg', confidence_threshold=0.7)
        >>> print(f"Found {result['total_icebergs']} icebergs")
        >>> for iceberg in result['icebergs']:
        ...     print(f"  {iceberg['id']}: {iceberg['confidence']:.2f} at {iceberg['position']}")
    """
    
    start_time = time.time()
    detection_timestamp = datetime.now(timezone.utc)
    
    # Validate inputs
    image_path = Path(image_path)
    if not image_path.exists():
        return {
            "success": False,
            "error": f"Image file not found: {image_path}",
            "icebergs": [],
            "total_icebergs": 0,
            "detection_time": detection_timestamp.isoformat()
        }
    
    # Determine weights path
    if weights_path is None:
        # Try to find latest training run
        runs_dir = Path(__file__).parent / "runs" / "train"
        
        if runs_dir.exists():
            # Look for iceberg_detector training runs
            training_dirs = sorted(runs_dir.glob("iceberg_detector_v*"))
            
            for train_dir in reversed(training_dirs):  # Check newest first
                # Check in weights subdirectory
                default_weights = train_dir / "weights" / "best.pt"
                if default_weights.exists():
                    break
                # Check in root directory
                default_weights = train_dir / "best.pt"
                if default_weights.exists():
                    break
            else:
                default_weights = None
        else:
            default_weights = None
        
        if not default_weights or not default_weights.exists():
            return {
                "success": False,
                "error": "Model weights not found. Please specify weights_path or train a model first.",
                "icebergs": [],
                "total_icebergs": 0,
                "detection_time": detection_timestamp.isoformat()
            }
        
        weights_path = default_weights
    else:
        weights_path = Path(weights_path)
        if not weights_path.exists():
            return {
                "success": False,
                "error": f"Model weights not found: {weights_path}",
                "icebergs": [],
                "total_icebergs": 0,
                "detection_time": detection_timestamp.isoformat()
            }
    
    try:
        # Load model (uses cache if already loaded)
        logger.info(f"Loading model from {weights_path.name}")
        model = load_iceberg_model(str(weights_path), device=device)
        
        # Set confidence threshold
        model.conf = confidence_threshold
        
        # Run inference
        logger.info(f"Running inference on {image_path.name}")
        results = model(str(image_path))
        
        # Parse results
        detections = results.pandas().xyxy[0]  # Get detections as pandas DataFrame
        
        # Load image to get dimensions
        try:
            from PIL import Image
            img = Image.open(str(image_path))
            img_width, img_height = img.size
        except:
            # Fallback to default
            img_width = SENTINEL1_ANTARCTIC_CONFIG["image_size"]
            img_height = SENTINEL1_ANTARCTIC_CONFIG["image_size"]
        
        # Try to extract georeference from filename
        geo_info = parse_georeference_from_filename(image_path.name)
        if geo_info:
            center_lat = center_lat or geo_info.get("center_lat")
            center_lon = center_lon or geo_info.get("center_lon")
        
        # Use defaults if not specified
        if center_lat is None:
            center_lat = SENTINEL1_ANTARCTIC_CONFIG["default_center_lat"]
        if center_lon is None:
            center_lon = SENTINEL1_ANTARCTIC_CONFIG["default_center_lon"]
        
        # Initialize coordinate converter
        converter = CoordinateConverter(
            image_width=img_width,
            image_height=img_height,
            center_lat=center_lat,
            center_lon=center_lon,
            resolution_meters=resolution_meters
        )
        
        # Process each detection
        icebergs = []
        for idx, detection in detections.iterrows():
            # Extract bounding box
            x1, y1, x2, y2 = detection['xmin'], detection['ymin'], detection['xmax'], detection['ymax']
            width = x2 - x1
            height = y2 - y1
            
            # Convert to geographic coordinates
            bounds = converter.bbox_to_latlon_bounds(x1, y1, width, height)
            
            # Calculate size in meters
            size_info = converter.calculate_bbox_size_meters(width, height)
            
            # Generate unique ID
            iceberg_id = generate_iceberg_id(idx + 1, detection_timestamp)
            
            # Build detection record
            iceberg = {
                "id": iceberg_id,
                "bounding_box": {
                    "x": float(x1),
                    "y": float(y1),
                    "width": float(width),
                    "height": float(height)
                },
                "position": {
                    "lat": float(bounds["center_lat"]),
                    "lon": float(bounds["center_lon"]),
                    "formatted": format_coordinates(bounds["center_lat"], bounds["center_lon"])
                },
                "bounds": {
                    "min_lat": float(bounds["min_lat"]),
                    "max_lat": float(bounds["max_lat"]),
                    "min_lon": float(bounds["min_lon"]),
                    "max_lon": float(bounds["max_lon"])
                },
                "size_meters": size_info,
                "size_classification": classify_iceberg_size(size_info["estimated_diameter_m"]),
                "confidence": float(detection['confidence'])
            }
            
            icebergs.append(iceberg)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Build response
        response = {
            "success": True,
            "icebergs": icebergs,
            "detection_time": detection_timestamp.isoformat(),
            "total_icebergs": len(icebergs),
            "image_info": {
                "path": str(image_path),
                "filename": image_path.name,
                "width": img_width,
                "height": img_height,
                "resolution_meters": resolution_meters,
                "center_coordinates": {
                    "lat": center_lat,
                    "lon": center_lon,
                    "formatted": format_coordinates(center_lat, center_lon)
                }
            },
            "processing_time_ms": round(processing_time_ms, 2),
            "model_info": {
                "weights": str(weights_path.name),
                "confidence_threshold": confidence_threshold
            }
        }
        
        # Add annotated image if requested
        if include_visualization:
            try:
                # Get rendered results with bounding boxes
                annotated = results.render()[0]  # Returns numpy array
                response["annotated_image"] = annotated
            except Exception as e:
                logger.warning(f"Could not generate visualization: {e}")
        
        logger.info(f"✓ Detection complete: {len(icebergs)} icebergs found in {processing_time_ms:.1f}ms")
        
        return response
        
    except Exception as e:
        logger.error(f"Detection failed: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "icebergs": [],
            "total_icebergs": 0,
            "detection_time": detection_timestamp.isoformat()
        }


def detect_icebergs_batch(
    image_paths: List[str],
    weights_path: str = None,
    confidence_threshold: float = 0.7,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Run detection on multiple images.
    
    Args:
        image_paths: List of image file paths
        weights_path: Path to model weights
        confidence_threshold: Confidence threshold
        **kwargs: Additional arguments passed to detect_icebergs
    
    Returns:
        List of detection result dictionaries
    """
    results = []
    
    # Load model once for all images
    if weights_path:
        load_iceberg_model(weights_path, kwargs.get('device', ''))
    
    for image_path in image_paths:
        result = detect_icebergs(
            image_path,
            weights_path=weights_path,
            confidence_threshold=confidence_threshold,
            **kwargs
        )
        results.append(result)
    
    return results


if __name__ == "__main__":
    """Test detection on sample images"""
    
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Detect icebergs in satellite imagery")
    parser.add_argument("image", nargs="?", help="Path to satellite image")
    parser.add_argument("--weights", default=None, help="Path to model weights")
    parser.add_argument("--conf", type=float, default=0.7, help="Confidence threshold")
    parser.add_argument("--device", default='', help="Device (cpu, cuda, 0, 1, etc.)")
    parser.add_argument("--save-viz", action="store_true", help="Save annotated image")
    parser.add_argument("--output", default="detection_results.json", help="Output JSON file")
    args = parser.parse_args()
    
    if not args.image:
        # Try to find a test image
        test_dir = Path(__file__).parent / "iceberg-4" / "test" / "images"
        if test_dir.exists():
            test_images = list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png"))
            if test_images:
                args.image = str(test_images[0])
                print(f"Using test image: {args.image}")
        
        if not args.image:
            print("✗ No image specified and no test images found")
            print("Usage: python detect_icebergs.py <image_path>")
            sys.exit(1)
    
    print("="*60)
    print("  ICEBERG DETECTION")
    print("="*60)
    print(f"  Image: {args.image}")
    print(f"  Confidence threshold: {args.conf}")
    print("="*60 + "\n")
    
    # Run detection
    result = detect_icebergs(
        args.image,
        weights_path=args.weights,
        confidence_threshold=args.conf,
        device=args.device,
        include_visualization=args.save_viz
    )
    
    # Display results
    if result["success"]:
        print(f"✓ Detection successful")
        print(f"  Processing time: {result['processing_time_ms']:.1f}ms")
        print(f"  Total icebergs: {result['total_icebergs']}")
        
        if result['total_icebergs'] > 0:
            print(f"\n  Detected icebergs:")
            for iceberg in result['icebergs']:
                print(f"    • {iceberg['id']}")
                print(f"      Position: {iceberg['position']['formatted']}")
                print(f"      Size: {iceberg['size_meters']['estimated_diameter_m']:.0f}m ({iceberg['size_classification']})")
                print(f"      Confidence: {iceberg['confidence']:.2%}")
        
        # Save results
        output_path = Path(args.output)
        
        # Remove numpy array before JSON serialization
        if 'annotated_image' in result:
            annotated = result.pop('annotated_image')
            
            # Save visualization
            if args.save_viz:
                viz_path = output_path.with_suffix('.jpg')
                try:
                    from PIL import Image
                    Image.fromarray(annotated).save(viz_path)
                    print(f"\n  Annotated image saved: {viz_path}")
                except Exception as e:
                    print(f"\n  ✗ Could not save visualization: {e}")
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"  Results saved: {output_path}")
        
    else:
        print(f"✗ Detection failed: {result['error']}")
        sys.exit(1)
    
    print("\n" + "="*60 + "\n")
