"""
Iceberg Service - Abstraction Layer
Provides unified interface for iceberg detection, handling both:
1. Pre-calculated scenario data (fast demo mode)
2. Real-time YOLO model detection (live AI mode)
"""

import json
import logging
from pathlib import Path
from typing import Optional, Union
import os

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Toggle between demo mode (JSON files) and live detection (YOLO model)
# Set to True to use real model, False for fast demo with pre-calculated data
USE_REAL_MODEL = os.getenv("USE_REAL_MODEL", "false").lower() == "true"

# Paths
DATA_BASE_PATH = Path(__file__).parent.parent.parent / "data" / "scenarios"

logger.info(f"Iceberg Service initialized: USE_REAL_MODEL={USE_REAL_MODEL}")


# ============================================================================
# PUBLIC API
# ============================================================================

def get_icebergs(
    scenario: int = 0,
    image_path: Optional[Union[str, Path]] = None,
    force_real_model: bool = False,
    confidence_threshold: float = 0.7
) -> dict:
    """
    Get iceberg detections - either from scenario JSON or real-time detection.
    
    This is the main entry point for getting iceberg data. It automatically
    chooses between demo mode and live detection based on configuration.
    
    Args:
        scenario (int): Scenario number (0-3) for demo mode
        image_path (Optional[Union[str, Path]]): Path to satellite image for live detection
        force_real_model (bool): Force use of real model even if USE_REAL_MODEL=False
        confidence_threshold (float): Confidence threshold for detections (0.0-1.0)
        
    Returns:
        dict: Iceberg detection results in standard format:
            {
                "icebergs": [...],
                "metadata": {...}
            }
    """
    # Determine which mode to use
    use_model = USE_REAL_MODEL or force_real_model
    
    if use_model and image_path:
        # Live detection mode
        logger.info(f"Using REAL MODEL detection on image: {image_path}")
        return _get_icebergs_from_model(
            image_path, 
            confidence_threshold=confidence_threshold
        )
    
    elif image_path and not use_model:
        # Image provided but model not enabled - warn and use scenario
        logger.warning(
            f"Image provided but USE_REAL_MODEL=False. "
            f"Using scenario {scenario} data instead."
        )
        return _get_icebergs_from_scenario(scenario)
    
    else:
        # Demo mode - use pre-calculated scenario data
        logger.info(f"Using SCENARIO {scenario} data (demo mode)")
        return _get_icebergs_from_scenario(scenario)


def get_icebergs_live(
    image_path: Union[str, Path],
    confidence_threshold: float = 0.7,
    image_center: Optional[tuple] = None,
    pixel_resolution: float = 10.0
) -> dict:
    """
    Force real-time YOLO detection regardless of USE_REAL_MODEL setting.
    
    This endpoint always uses the live model and is useful for:
    - Demonstrating real AI capability to judges
    - Testing with new images
    - Production deployment
    
    Args:
        image_path (Union[str, Path]): Path to satellite image
        confidence_threshold (float): Confidence threshold (0.0-1.0)
        image_center (Optional[tuple]): (lat, lon) of image center
        pixel_resolution (float): Meters per pixel
        
    Returns:
        dict: Detection results from YOLO model
    """
    logger.info(f"LIVE DETECTION forced for image: {image_path}")
    return _get_icebergs_from_model(
        image_path,
        confidence_threshold=confidence_threshold,
        image_center=image_center,
        pixel_resolution=pixel_resolution
    )


def get_service_status() -> dict:
    """
    Get current service configuration and model status.
    
    Returns:
        dict: Service status including:
            - mode: "demo" or "live"
            - use_real_model: bool
            - model_available: bool
            - model_info: dict (if model loaded)
    """
    from app.detection_models.iceberg_detection import is_model_loaded, get_model_info
    
    mode = "live" if USE_REAL_MODEL else "demo"
    model_loaded = is_model_loaded()
    
    status = {
        "mode": mode,
        "use_real_model": USE_REAL_MODEL,
        "model_loaded": model_loaded,
        "data_path": str(DATA_BASE_PATH),
        "scenarios_available": _get_available_scenarios()
    }
    
    # Add model info if loaded
    if model_loaded:
        try:
            status["model_info"] = get_model_info()
        except Exception as e:
            logger.warning(f"Could not get model info: {e}")
    
    return status


def set_mode(use_real_model: bool) -> dict:
    """
    Dynamically change service mode (demo vs live).
    
    Args:
        use_real_model (bool): True for live model, False for demo
        
    Returns:
        dict: New status after mode change
    """
    global USE_REAL_MODEL
    
    old_mode = "live" if USE_REAL_MODEL else "demo"
    USE_REAL_MODEL = use_real_model
    new_mode = "live" if USE_REAL_MODEL else "demo"
    
    logger.info(f"Mode changed: {old_mode} -> {new_mode}")
    
    return {
        "success": True,
        "old_mode": old_mode,
        "new_mode": new_mode,
        "use_real_model": USE_REAL_MODEL
    }


# ============================================================================
# PRIVATE HELPERS
# ============================================================================

def _get_icebergs_from_scenario(scenario: int) -> dict:
    """
    Load iceberg data from pre-calculated scenario JSON file.
    
    Args:
        scenario (int): Scenario number (0-3)
        
    Returns:
        dict: Iceberg data from JSON file
    """
    try:
        scenario_path = DATA_BASE_PATH / f"scenario_{scenario}" / "icebergs.json"
        
        if not scenario_path.exists():
            logger.error(f"Scenario file not found: {scenario_path}")
            return _empty_result(f"Scenario {scenario} not found")
        
        with open(scenario_path, 'r') as f:
            data = json.load(f)
        
        # Add metadata if not present
        if "metadata" not in data:
            data["metadata"] = {
                "source": "scenario_data",
                "scenario": scenario,
                "total_detections": len(data.get("icebergs", []))
            }
        else:
            data["metadata"]["source"] = "scenario_data"
            data["metadata"]["scenario"] = scenario
        
        logger.info(f"Loaded {len(data.get('icebergs', []))} icebergs from scenario {scenario}")
        return data
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in scenario file: {e}")
        return _empty_result(f"Invalid scenario data: {e}")
    
    except Exception as e:
        logger.error(f"Error loading scenario data: {e}", exc_info=True)
        return _empty_result(f"Error loading scenario: {e}")


def _get_icebergs_from_model(
    image_path: Union[str, Path],
    confidence_threshold: float = 0.7,
    image_center: Optional[tuple] = None,
    pixel_resolution: float = 10.0
) -> dict:
    """
    Perform real-time iceberg detection using YOLO model.
    
    Args:
        image_path (Union[str, Path]): Path to satellite image
        confidence_threshold (float): Confidence threshold
        image_center (Optional[tuple]): (lat, lon) of image center
        pixel_resolution (float): Meters per pixel
        
    Returns:
        dict: Detection results from YOLO model
    """
    try:
        from app.detection_models.iceberg_detection import detect_icebergs
        
        # Run detection
        result = detect_icebergs(
            image_path=image_path,
            confidence_threshold=confidence_threshold,
            image_center=image_center,
            pixel_resolution=pixel_resolution
        )
        
        # Add source metadata
        if "metadata" not in result:
            result["metadata"] = {}
        
        result["metadata"]["source"] = "real_time_detection"
        result["metadata"]["model"] = "YOLOv5"
        
        return result
        
    except ImportError as e:
        logger.error(f"YOLO dependencies not installed: {e}")
        return _empty_result(
            "Real-time detection unavailable. "
            "Install dependencies: pip install ultralytics torch opencv-python"
        )
    
    except Exception as e:
        logger.error(f"Model detection failed: {e}", exc_info=True)
        return _empty_result(f"Detection error: {str(e)}")


def _empty_result(error_message: str = None) -> dict:
    """
    Return empty result with error message.
    
    Args:
        error_message (str): Error description
        
    Returns:
        dict: Empty result structure
    """
    return {
        "icebergs": [],
        "metadata": {
            "total_detections": 0,
            "error": error_message if error_message else "No data available"
        }
    }


def _get_available_scenarios() -> list:
    """
    Get list of available scenario numbers.
    
    Returns:
        list: List of scenario numbers that have data
    """
    scenarios = []
    
    try:
        if DATA_BASE_PATH.exists():
            for item in DATA_BASE_PATH.iterdir():
                if item.is_dir() and item.name.startswith("scenario_"):
                    try:
                        scenario_num = int(item.name.split("_")[1])
                        scenarios.append(scenario_num)
                    except (ValueError, IndexError):
                        continue
        
        scenarios.sort()
    except Exception as e:
        logger.warning(f"Could not list scenarios: {e}")
    
    return scenarios


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_image_path(image_path: Union[str, Path]) -> bool:
    """
    Validate that an image path exists and is readable.
    
    Args:
        image_path (Union[str, Path]): Path to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        path = Path(image_path)
        return path.exists() and path.is_file()
    except Exception:
        return False


def get_scenario_info(scenario: int) -> dict:
    """
    Get information about a specific scenario.
    
    Args:
        scenario (int): Scenario number
        
    Returns:
        dict: Scenario information including available files
    """
    scenario_path = DATA_BASE_PATH / f"scenario_{scenario}"
    
    if not scenario_path.exists():
        return {"exists": False, "scenario": scenario}
    
    files = {}
    for file_name in ["icebergs.json", "ice_data.json", "routes.json", 
                      "predictions.json", "explanation.txt"]:
        file_path = scenario_path / file_name
        files[file_name] = file_path.exists()
    
    return {
        "exists": True,
        "scenario": scenario,
        "path": str(scenario_path),
        "files": files
    }


# ============================================================================
# INITIALIZATION
# ============================================================================

def _initialize_service():
    """
    Initialize service on module load.
    Pre-load model if in live mode and AUTO_LOAD is enabled.
    """
    AUTO_LOAD_MODEL = False  # Set to True to pre-load model on startup
    
    if USE_REAL_MODEL and AUTO_LOAD_MODEL:
        try:
            logger.info("Pre-loading YOLO model...")
            from app.detection_models.iceberg_detection import load_model
            load_model()
            logger.info("Model pre-loaded successfully")
        except Exception as e:
            logger.warning(f"Model pre-load failed: {e}. Will load on first use.")


# Run initialization
_initialize_service()
