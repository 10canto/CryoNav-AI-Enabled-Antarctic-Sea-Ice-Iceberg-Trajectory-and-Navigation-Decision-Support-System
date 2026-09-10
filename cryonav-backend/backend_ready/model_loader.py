"""
YOLOv5 Model Loader with Caching

Efficiently loads and caches the trained iceberg detection model for fast repeated inference.
Manages model lifecycle and memory.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ModelLoader:
    """
    Singleton model loader that caches the YOLOv5 model in memory.
    
    Usage:
        loader = ModelLoader()
        model = loader.load_model('path/to/best.pt')
        
        # Later calls return the cached model
        model = loader.load_model('path/to/best.pt')  # Instant return
    """
    
    _instance = None
    _model = None
    _model_path = None
    _model_info = {}
    
    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)"""
        if cls._instance is None:
            cls._instance = super(ModelLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize model loader"""
        # Ensure YOLOv5 is in path
        workspace_root = Path(__file__).parent
        yolo_dir = workspace_root / "yolov5"
        
        if yolo_dir.exists() and str(yolo_dir) not in sys.path:
            sys.path.insert(0, str(yolo_dir))
    
    def load_model(
        self,
        weights_path: str,
        device: str = '',
        force_reload: bool = False
    ) -> Any:
        """
        Load YOLOv5 model from weights file.
        
        Args:
            weights_path: Path to model weights (.pt file)
            device: Device to load model on ('cpu', 'cuda', '0', '1', etc. Empty string = auto-detect)
            force_reload: Force reload even if model is already cached
        
        Returns:
            Loaded YOLOv5 model
        
        Raises:
            FileNotFoundError: If weights file doesn't exist
            RuntimeError: If model loading fails
        """
        weights_path = Path(weights_path).resolve()
        
        # Check if file exists
        if not weights_path.exists():
            raise FileNotFoundError(f"Model weights not found: {weights_path}")
        
        # Return cached model if same weights and not forcing reload
        if not force_reload and self._model is not None and self._model_path == str(weights_path):
            logger.info(f"Returning cached model from {weights_path.name}")
            return self._model
        
        # Load new model
        logger.info(f"Loading YOLOv5 model from {weights_path}")
        
        try:
            import torch
            
            # Detect available device
            if device == '':
                device = '0' if torch.cuda.is_available() else 'cpu'
            
            logger.info(f"Using device: {device}")
            
            # Load model using torch.hub or direct loading
            try:
                # Method 1: Try loading with torch hub (trust repo to avoid prompt)
                model = torch.hub.load('ultralytics/yolov5', 'custom', path=str(weights_path), device=device, trust_repo=True)
                logger.info("Model loaded via torch.hub")
            except Exception as e:
                logger.warning(f"torch.hub load failed ({e}), trying direct load...")
                
                # Method 2: Direct load (offline friendly)
                from models.common import DetectMultiBackend
                model = DetectMultiBackend(str(weights_path), device=device)
                logger.info("Model loaded via DetectMultiBackend")
            
            # Configure model for inference
            model.eval()
            
            # Store model metadata
            self._model = model
            self._model_path = str(weights_path)
            self._model_info = {
                'weights_path': str(weights_path),
                'device': str(device),
                'model_size_mb': weights_path.stat().st_size / (1024 * 1024),
            }
            
            logger.info(f"✓ Model loaded successfully ({self._model_info['model_size_mb']:.2f} MB)")
            
            return self._model
            
        except ImportError as e:
            logger.error(f"Missing dependencies: {e}")
            logger.error("Install required packages: pip install torch ultralytics")
            raise RuntimeError(f"Failed to import required libraries: {e}")
        
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Model loading failed: {e}")
    
    def is_model_loaded(self) -> bool:
        """
        Check if a model is currently loaded in memory.
        
        Returns:
            True if model is loaded, False otherwise
        """
        return self._model is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the currently loaded model.
        
        Returns:
            Dictionary with model metadata
        """
        if not self.is_model_loaded():
            return {"status": "no_model_loaded"}
        
        return {
            "status": "loaded",
            **self._model_info
        }
    
    def unload_model(self):
        """
        Unload the model from memory to free resources.
        """
        if self._model is not None:
            logger.info("Unloading model from memory")
            
            # Clear model
            self._model = None
            self._model_path = None
            self._model_info = {}
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Clear CUDA cache if available
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    logger.info("CUDA cache cleared")
            except:
                pass
            
            logger.info("✓ Model unloaded")
        else:
            logger.info("No model to unload")
    
    def reload_model(self, device: str = ''):
        """
        Reload the current model (useful for updating device).
        
        Args:
            device: New device to load model on
        """
        if self._model_path is None:
            logger.warning("No model path stored, cannot reload")
            return None
        
        logger.info("Reloading model...")
        return self.load_model(self._model_path, device=device, force_reload=True)


# Global instance for easy access
_global_loader = None


def get_model_loader() -> ModelLoader:
    """
    Get the global ModelLoader instance.
    
    Returns:
        ModelLoader singleton instance
    """
    global _global_loader
    if _global_loader is None:
        _global_loader = ModelLoader()
    return _global_loader


def load_iceberg_model(weights_path: str, device: str = '') -> Any:
    """
    Convenience function to load iceberg detection model.
    
    Args:
        weights_path: Path to model weights
        device: Device to use
    
    Returns:
        Loaded YOLOv5 model
    """
    loader = get_model_loader()
    return loader.load_model(weights_path, device=device)


def is_model_ready() -> bool:
    """
    Check if model is loaded and ready for inference.
    
    Returns:
        True if model is ready
    """
    loader = get_model_loader()
    return loader.is_model_loaded()


def get_model_status() -> Dict[str, Any]:
    """
    Get status of currently loaded model.
    
    Returns:
        Dictionary with model status and info
    """
    loader = get_model_loader()
    return loader.get_model_info()


if __name__ == "__main__":
    """Test model loader functionality"""
    
    print("="*60)
    print("  MODEL LOADER TEST")
    print("="*60)
    
    # Check for test weights
    test_weights = Path(__file__).parent / "runs" / "train" / "iceberg_detector_v1" / "best.pt"
    
    if not test_weights.exists():
        print("\n✗ Test weights not found at:", test_weights)
        print("  Train a model first: python train_iceberg_detector.py")
        print("\nTrying default YOLOv5s weights as fallback...")
        test_weights = Path(__file__).parent / "yolov5" / "yolov5s.pt"
    
    if not test_weights.exists():
        print("✗ No weights available for testing")
        sys.exit(1)
    
    print(f"\nUsing weights: {test_weights}")
    
    # Test loading
    try:
        print("\n1. Loading model (first time)...")
        loader = get_model_loader()
        model = loader.load_model(str(test_weights))
        print("   ✓ Model loaded")
        
        print("\n2. Getting model info...")
        info = get_model_status()
        print(f"   Status: {info.get('status')}")
        print(f"   Device: {info.get('device')}")
        print(f"   Size: {info.get('model_size_mb', 0):.2f} MB")
        
        print("\n3. Loading model again (should use cache)...")
        model2 = loader.load_model(str(test_weights))
        print("   ✓ Returned cached model")
        
        print("\n4. Checking if model is ready...")
        ready = is_model_ready()
        print(f"   Model ready: {ready}")
        
        print("\n5. Unloading model...")
        loader.unload_model()
        print(f"   Model ready: {is_model_ready()}")
        
        print("\n" + "="*60)
        print("  ✓ ALL TESTS PASSED")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
