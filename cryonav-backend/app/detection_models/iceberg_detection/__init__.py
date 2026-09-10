"""
Iceberg Detection Module
YOLOv5-based iceberg detection from satellite imagery
"""

from .detect_icebergs import detect_icebergs, annotate_image
from .model_loader import load_model, is_model_loaded, get_model_info

__all__ = ['detect_icebergs', 'annotate_image', 'load_model', 'is_model_loaded', 'get_model_info']
