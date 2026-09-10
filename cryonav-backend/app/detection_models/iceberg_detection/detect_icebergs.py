"""
Iceberg Detection using YOLOv5
Performs inference on satellite imagery and converts detections to geographic coordinates
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, List, Tuple
import numpy as np
from PIL import Image

from .model_loader import load_model

logger = logging.getLogger(__name__)

# Default configuration for Sentinel-1 SAR imagery
DEFAULT_PIXEL_RESOLUTION = 10.0  # meters per pixel
DEFAULT_IMAGE_CENTER = (-65.0, -64.0)  # (lat, lon) - Antarctic Peninsula


def pixel_to_latlon(
    px: float, 
    py: float, 
    img_width: int, 
    img_height: int,
    center_lat: float = DEFAULT_IMAGE_CENTER[0],
    center_lon: float = DEFAULT_IMAGE_CENTER[1],
    resolution: float = DEFAULT_PIXEL_RESOLUTION
) -> Tuple[float, float]:
    """Convert pixel coordinates to latitude/longitude."""
    dx_pixels = px - (img_width / 2)
    dy_pixels = (img_height / 2) - py
    dx_meters = dx_pixels * resolution
    dy_meters = dy_pixels * resolution
    lat_degrees_per_meter = 1.0 / 111320.0
    lon_degrees_per_meter = 1.0 / (111320.0 * np.cos(np.radians(center_lat)))
    lat = center_lat + (dy_meters * lat_degrees_per_meter)
    lon = center_lon + (dx_meters * lon_degrees_per_meter)
    return lat, lon


def bbox_to_size_meters(bbox_width: float, bbox_height: float, resolution: float = DEFAULT_PIXEL_RESOLUTION) -> Tuple[int, int]:
    """Convert bounding box dimensions from pixels to meters."""
    length = int(bbox_width * resolution)
    width = int(bbox_height * resolution)
    return length, width


def generate_iceberg_id(index: int) -> str:
    """Generate unique iceberg ID."""
    return f"ICE-{index:03d}"


def detect_icebergs(
    image_path: Union[str, Path],
    confidence_threshold: float = 0.7,
    image_center: Optional[Tuple[float, float]] = None,
    pixel_resolution: float = DEFAULT_PIXEL_RESOLUTION,
    iou_threshold: float = 0.45
) -> dict:
    """Detect icebergs in satellite imagery using YOLOv5 model."""
    import time
    start_time = time.time()
    
    if image_center is None:
        image_center = DEFAULT_IMAGE_CENTER
    
    center_lat, center_lon = image_center
    
    try:
        image_path = Path(image_path)
        if not image_path.exists():
            logger.error(f"Image not found: {image_path}")
            return _empty_result(f"Image not found: {image_path}")
        
        logger.info(f"Loading model for detection...")
        try:
            model = load_model()
        except FileNotFoundError as e:
            logger.error(f"Model file not found: {e}")
            return _generate_mock_detections(image_path, confidence_threshold)
        
        if model is None:
            logger.error("Failed to load model")
            return _generate_mock_detections(image_path, confidence_threshold)
        
        logger.info(f"Loading image from {image_path}")
        try:
            img = Image.open(image_path)
            img_array = np.array(img)
            img_height, img_width = img_array.shape[:2]
        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            return _empty_result(f"Failed to load image: {e}")
        
        logger.info(f"Running inference with conf={confidence_threshold}, iou={iou_threshold}")
        results = model(img_array, conf=confidence_threshold, iou=iou_threshold)
        
        detections = _parse_yolo_results(results)
        logger.info(f"Found {len(detections)} icebergs")
        
        icebergs = []
        for idx, detection in enumerate(detections):
            x_center, y_center, width, height, confidence, class_id = detection
            lat, lon = pixel_to_latlon(x_center, y_center, img_width, img_height, center_lat, center_lon, pixel_resolution)
            length_m, width_m = bbox_to_size_meters(width, height, pixel_resolution)
            
            iceberg = {
                "id": generate_iceberg_id(idx + 1),
                "position": {"lat": round(lat, 6), "lon": round(lon, 6)},
                "size_meters": {"length": length_m, "width": width_m},
                "confidence": round(float(confidence), 3),
                "detection_time": datetime.utcnow().isoformat() + "Z",
                "bbox_pixels": {"x": int(x_center), "y": int(y_center), "width": int(width), "height": int(height)}
            }
            icebergs.append(iceberg)
        
        processing_time = (time.time() - start_time) * 1000
        
        response = {
            "icebergs": icebergs,
            "metadata": {
                "total_detections": len(icebergs),
                "confidence_threshold": confidence_threshold,
                "image_path": str(image_path),
                "image_size": {"width": img_width, "height": img_height},
                "processing_time_ms": round(processing_time, 2),
                "pixel_resolution_m": pixel_resolution,
                "image_center": {"lat": center_lat, "lon": center_lon}
            }
        }
        
        logger.info(f"Detection complete: {len(icebergs)} icebergs in {processing_time:.2f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Detection failed: {e}", exc_info=True)
        return _empty_result(f"Detection error: {str(e)}")


def _parse_yolo_results(results) -> List[Tuple]:
    """Parse YOLO results into standardized format."""
    detections = []
    
    try:
        if hasattr(results, '__iter__') and len(results) > 0:
            result = results[0]
            
            if hasattr(result, 'boxes'):
                boxes = result.boxes
                if boxes is not None and len(boxes) > 0:
                    xyxy = boxes.xyxy.cpu().numpy()
                    confs = boxes.conf.cpu().numpy()
                    classes = boxes.cls.cpu().numpy()
                    
                    for i in range(len(xyxy)):
                        x1, y1, x2, y2 = xyxy[i]
                        x_center = (x1 + x2) / 2
                        y_center = (y1 + y2) / 2
                        width = x2 - x1
                        height = y2 - y1
                        detections.append((x_center, y_center, width, height, confs[i], int(classes[i])))
            
            elif hasattr(result, 'xyxy'):
                pred = result.xyxy[0].cpu().numpy()
                for detection in pred:
                    x1, y1, x2, y2, conf, cls = detection
                    x_center = (x1 + x2) / 2
                    y_center = (y1 + y2) / 2
                    width = x2 - x1
                    height = y2 - y1
                    detections.append((x_center, y_center, width, height, conf, int(cls)))
        
    except Exception as e:
        logger.error(f"Error parsing YOLO results: {e}")
    
    return detections


def _empty_result(error_message: str = None) -> dict:
    """Return empty result structure with optional error message."""
    return {
        "icebergs": [],
        "metadata": {
            "total_detections": 0,
            "error": error_message if error_message else "No detections"
        }
    }


def _generate_mock_detections(image_path: Path, confidence_threshold: float) -> dict:
    """
    Generate mock detections when model is not available.
    Useful for testing the pipeline without a trained model.
    """
    import time
    start_time = time.time()
    
    logger.warning("Model not available. Generating mock detections for testing.")
    
    try:
        from PIL import Image
        img = Image.open(image_path)
        img_width, img_height = img.size
    except:
        img_width, img_height = 640, 640
    
    # Generate 2-3 mock icebergs
    import random
    num_detections = random.randint(2, 3)
    
    icebergs = []
    for i in range(num_detections):
        # Random positions
        x = random.randint(img_width // 4, 3 * img_width // 4)
        y = random.randint(img_height // 4, 3 * img_height // 4)
        w = random.randint(50, 150)
        h = random.randint(40, 120)
        conf = random.uniform(confidence_threshold, 0.95)
        
        # Convert to lat/lon
        lat, lon = pixel_to_latlon(x, y, img_width, img_height)
        length_m, width_m = bbox_to_size_meters(w, h)
        
        iceberg = {
            "id": generate_iceberg_id(i + 1),
            "position": {"lat": round(lat, 6), "lon": round(lon, 6)},
            "size_meters": {"length": length_m, "width": width_m},
            "confidence": round(conf, 3),
            "detection_time": datetime.utcnow().isoformat() + "Z",
            "bbox_pixels": {"x": x, "y": y, "width": w, "height": h}
        }
        icebergs.append(iceberg)
    
    processing_time = (time.time() - start_time) * 1000
    
    return {
        "icebergs": icebergs,
        "metadata": {
            "total_detections": len(icebergs),
            "confidence_threshold": confidence_threshold,
            "image_path": str(image_path),
            "image_size": {"width": img_width, "height": img_height},
            "processing_time_ms": round(processing_time, 2),
            "source": "mock_detection",
            "warning": "Model not available. These are mock detections for testing only."
        }
    }


def annotate_image(
    image_path: Union[str, Path],
    detections: dict,
    output_path: Optional[Union[str, Path]] = None,
    show_labels: bool = True
) -> Optional[Path]:
    """Draw bounding boxes on image to visualize detections."""
    try:
        from PIL import ImageDraw, ImageFont
        
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        for iceberg in detections.get("icebergs", []):
            bbox = iceberg["bbox_pixels"]
            x, y = bbox["x"], bbox["y"]
            w, h = bbox["width"], bbox["height"]
            x1, y1 = x - w/2, y - h/2
            x2, y2 = x + w/2, y + h/2
            draw.rectangle([x1, y1, x2, y2], outline="red", width=3)
            
            if show_labels:
                label = f"{iceberg['id']} ({iceberg['confidence']:.2f})"
                draw.text((x1, y1 - 20), label, fill="red", font=font)
        
        if output_path is None:
            image_path = Path(image_path)
            output_path = image_path.parent / f"{image_path.stem}_annotated{image_path.suffix}"
        
        output_path = Path(output_path)
        img.save(output_path)
        logger.info(f"Annotated image saved to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to annotate image: {e}")
        return None
