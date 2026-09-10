"""
Model Loader for YOLOv5 Iceberg Detection
Handles loading, caching, and management of the trained YOLO model
"""

import logging
from pathlib import Path
from typing import Optional
import torch

logger = logging.getLogger(__name__)

# Global model cache
_MODEL_CACHE = {
    'model': None,
    'loaded': False,
    'error': None
}

# Model configuration
MODEL_PATH = Path(__file__).parent / "weights" / "best.pt"
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'


def load_model(force_reload: bool = False):
    """
    Load the YOLOv5 iceberg detection model.
    
    Model is cached in memory after first load for performance.
    
    Args:
        force_reload (bool): Force reload model even if cached
        
    Returns:
        Loaded YOLO model or None if loading fails
        
    Raises:
        FileNotFoundError: If model weights file doesn't exist
        RuntimeError: If model loading fails
    """
    global _MODEL_CACHE
    
    # Return cached model if available and not forcing reload
    if _MODEL_CACHE['loaded'] and _MODEL_CACHE['model'] is not None and not force_reload:
        logger.info("Using cached YOLO model")
        return _MODEL_CACHE['model']
    
    try:
        logger.info(f"Loading YOLO model from {MODEL_PATH}")
        
        # Check if model file exists
        if not MODEL_PATH.exists():
            error_msg = f"Model weights not found at {MODEL_PATH}"
            logger.error(error_msg)
            _MODEL_CACHE['error'] = error_msg
            _MODEL_CACHE['loaded'] = False
            raise FileNotFoundError(error_msg)
        
        # Load model using torch.hub (YOLOv5 standard approach)
        try:
            from ultralytics import YOLO
            model = YOLO(str(MODEL_PATH))
            logger.info(f"Loaded model using Ultralytics (YOLOv8 API)")
        except (ImportError, TypeError) as e:
            # Fallback to torch.hub for YOLOv5 format models
            if "references types outside" in str(e) or isinstance(e, ImportError):
                logger.info("Trying torch.hub for YOLOv5 format model...")
                model = torch.hub.load('ultralytics/yolov5', 'custom', path=str(MODEL_PATH))
                logger.info("Loaded YOLOv5 model via torch.hub")
            else:
                raise
        
        # Move model to appropriate device
        if hasattr(model, 'to'):
            model.to(DEVICE)
        
        # Set to evaluation mode
        if hasattr(model, 'eval'):
            model.eval()
        
        # Cache the model
        _MODEL_CACHE['model'] = model
        _MODEL_CACHE['loaded'] = True
        _MODEL_CACHE['error'] = None
        
        logger.info(f"Model loaded successfully on device: {DEVICE}")
        return model
        
    except FileNotFoundError:
        raise
    except Exception as e:
        error_msg = f"Failed to load model: {str(e)}"
        logger.error(error_msg, exc_info=True)
        _MODEL_CACHE['error'] = error_msg
        _MODEL_CACHE['loaded'] = False
        raise RuntimeError(error_msg) from e


def is_model_loaded() -> bool:
    """
    Check if the model is currently loaded in memory.
    
    Returns:
        bool: True if model is loaded, False otherwise
    """
    return _MODEL_CACHE['loaded'] and _MODEL_CACHE['model'] is not None


def get_model_info() -> dict:
    """
    Get information about the current model status.
    
    Returns:
        dict: Model status information including:
            - loaded: bool
            - device: str
            - model_path: str
            - error: str or None
    """
    return {
        'loaded': _MODEL_CACHE['loaded'],
        'device': DEVICE,
        'model_path': str(MODEL_PATH),
        'model_exists': MODEL_PATH.exists(),
        'error': _MODEL_CACHE['error'],
        'cuda_available': torch.cuda.is_available()
    }


def unload_model():
    """
    Unload the model from memory.
    Useful for freeing up memory when model is not needed.
    """
    global _MODEL_CACHE
    
    if _MODEL_CACHE['model'] is not None:
        del _MODEL_CACHE['model']
        _MODEL_CACHE['model'] = None
        _MODEL_CACHE['loaded'] = False
        logger.info("Model unloaded from memory")
        
        # Clear CUDA cache if using GPU
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    else:
        logger.info("No model to unload")


def warmup_model(img_size: tuple = (640, 640)) -> bool:
    """
    Warm up the model with a dummy inference.
    This can improve performance for the first real inference.
    
    Args:
        img_size (tuple): Image size for warmup (height, width)
        
    Returns:
        bool: True if warmup successful, False otherwise
    """
    try:
        import numpy as np
        
        model = load_model()
        if model is None:
            return False
        
        logger.info("Warming up model...")
        
        # Create dummy image
        dummy_img = np.random.randint(0, 255, (*img_size, 3), dtype=np.uint8)
        
        # Run inference
        _ = model(dummy_img)
        
        logger.info("Model warmup complete")
        return True
        
    except Exception as e:
        logger.warning(f"Model warmup failed: {e}")
        return False
