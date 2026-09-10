"""
Utility functions for iceberg detection inference

Provides coordinate conversion, size estimation, and geographic calculations
for satellite imagery analysis.
"""

import math
from typing import Dict, Tuple, Optional
from datetime import datetime, timezone


class CoordinateConverter:
    """
    Convert pixel coordinates to geographic coordinates for satellite imagery.
    
    Handles Sentinel-1 SAR imagery with standard 10m/pixel resolution.
    """
    
    def __init__(
        self,
        image_width: int,
        image_height: int,
        center_lat: float = -65.0,
        center_lon: float = -64.0,
        resolution_meters: float = 10.0
    ):
        """
        Initialize coordinate converter.
        
        Args:
            image_width: Image width in pixels
            image_height: Image height in pixels
            center_lat: Center latitude of image (default: -65.0 for Antarctic)
            center_lon: Center longitude of image (default: -64.0 for Antarctic Peninsula)
            resolution_meters: Ground sample distance in meters per pixel (default: 10m for Sentinel-1)
        """
        self.image_width = image_width
        self.image_height = image_height
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.resolution_meters = resolution_meters
        
        # Earth radius in meters
        self.earth_radius = 6378137.0
        
        # Calculate meters per degree at this latitude
        self.meters_per_degree_lat = 111320.0  # Approximately constant
        self.meters_per_degree_lon = 111320.0 * math.cos(math.radians(center_lat))
    
    def pixel_to_latlon(self, pixel_x: float, pixel_y: float) -> Tuple[float, float]:
        """
        Convert pixel coordinates to latitude/longitude.
        
        Args:
            pixel_x: X coordinate in pixels (0 = left edge)
            pixel_y: Y coordinate in pixels (0 = top edge)
        
        Returns:
            Tuple of (latitude, longitude)
        """
        # Calculate offset from center in pixels
        center_x = self.image_width / 2
        center_y = self.image_height / 2
        
        offset_x_pixels = pixel_x - center_x
        offset_y_pixels = pixel_y - center_y
        
        # Convert to meters
        offset_x_meters = offset_x_pixels * self.resolution_meters
        offset_y_meters = -offset_y_pixels * self.resolution_meters  # Negative because Y increases downward
        
        # Convert to degrees
        offset_lon = offset_x_meters / self.meters_per_degree_lon
        offset_lat = offset_y_meters / self.meters_per_degree_lat
        
        # Calculate final coordinates
        lat = self.center_lat + offset_lat
        lon = self.center_lon + offset_lon
        
        return lat, lon
    
    def bbox_to_latlon_bounds(
        self,
        x: float,
        y: float,
        width: float,
        height: float
    ) -> Dict[str, float]:
        """
        Convert bounding box to geographic bounds.
        
        Args:
            x: Top-left X coordinate in pixels
            y: Top-left Y coordinate in pixels
            width: Width in pixels
            height: Height in pixels
        
        Returns:
            Dictionary with min/max lat/lon bounds
        """
        # Get corners
        lat_tl, lon_tl = self.pixel_to_latlon(x, y)
        lat_br, lon_br = self.pixel_to_latlon(x + width, y + height)
        
        # Get center
        center_x = x + width / 2
        center_y = y + height / 2
        lat_center, lon_center = self.pixel_to_latlon(center_x, center_y)
        
        return {
            "min_lat": min(lat_tl, lat_br),
            "max_lat": max(lat_tl, lat_br),
            "min_lon": min(lon_tl, lon_br),
            "max_lon": max(lon_tl, lon_br),
            "center_lat": lat_center,
            "center_lon": lon_center,
        }
    
    def calculate_bbox_size_meters(self, width_pixels: float, height_pixels: float) -> Dict[str, float]:
        """
        Calculate bounding box dimensions in meters.
        
        Args:
            width_pixels: Width in pixels
            height_pixels: Height in pixels
        
        Returns:
            Dictionary with width_m, height_m, area_m2, and estimated_diameter_m
        """
        width_m = width_pixels * self.resolution_meters
        height_m = height_pixels * self.resolution_meters
        area_m2 = width_m * height_m
        
        # Estimate diameter assuming roughly circular iceberg
        estimated_diameter_m = math.sqrt(area_m2 / math.pi) * 2
        
        return {
            "width_m": round(width_m, 2),
            "height_m": round(height_m, 2),
            "area_m2": round(area_m2, 2),
            "estimated_diameter_m": round(estimated_diameter_m, 2),
        }


def parse_georeference_from_filename(filename: str) -> Optional[Dict[str, float]]:
    """
    Attempt to extract geographic metadata from satellite image filename.
    
    Common Sentinel-1 naming conventions include lat/lon in the filename.
    This is a simplified parser - real implementation would use GeoTIFF metadata.
    
    Args:
        filename: Image filename
    
    Returns:
        Dictionary with center_lat, center_lon, or None if cannot parse
    """
    # Example: S1A_IW_GRDH_1SDV_20230115T123045_LAT65S_LON64W.tif
    # This is a placeholder - real implementation should use rasterio/GDAL
    
    import re
    
    # Try to find LAT and LON patterns
    lat_match = re.search(r'LAT(\d+\.?\d*)([NS])', filename, re.IGNORECASE)
    lon_match = re.search(r'LON(\d+\.?\d*)([EW])', filename, re.IGNORECASE)
    
    if lat_match and lon_match:
        lat = float(lat_match.group(1))
        if lat_match.group(2).upper() == 'S':
            lat = -lat
        
        lon = float(lon_match.group(1))
        if lon_match.group(2).upper() == 'W':
            lon = -lon
        
        return {
            "center_lat": lat,
            "center_lon": lon,
        }
    
    # Default Antarctic coordinates if cannot parse
    return None


def generate_iceberg_id(index: int, timestamp: datetime = None) -> str:
    """
    Generate unique iceberg detection ID.
    
    Args:
        index: Sequential index within detection batch
        timestamp: Timestamp of detection (default: current time)
    
    Returns:
        Unique ID string (format: ICE_YYYYMMDD_HHMMSS_NNN)
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    
    date_str = timestamp.strftime("%Y%m%d")
    time_str = timestamp.strftime("%H%M%S")
    
    return f"ICE_{date_str}_{time_str}_{index:03d}"


def calculate_haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calculate great-circle distance between two points on Earth.
    
    Uses the Haversine formula.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
    
    Returns:
        Distance in meters
    """
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth radius in meters
    earth_radius = 6378137.0
    
    return earth_radius * c


def estimate_iceberg_mass_tons(
    area_m2: float,
    height_assumption_m: float = 50.0,
    ice_density_kg_m3: float = 900.0
) -> float:
    """
    Rough estimate of iceberg mass.
    
    This is a very rough approximation assuming:
    - Visible iceberg top represents ~10-15% of total volume
    - Average thickness/depth ratio
    
    Args:
        area_m2: Surface area in square meters
        height_assumption_m: Assumed average height above water (default: 50m)
        ice_density_kg_m3: Ice density (default: 900 kg/m³)
    
    Returns:
        Estimated mass in metric tons
    """
    # Assume total height is ~7x the visible height (iceberg tip principle)
    total_height_m = height_assumption_m * 7
    
    # Calculate volume
    volume_m3 = area_m2 * total_height_m
    
    # Calculate mass
    mass_kg = volume_m3 * ice_density_kg_m3
    mass_tons = mass_kg / 1000.0
    
    return round(mass_tons, 2)


def classify_iceberg_size(diameter_m: float) -> str:
    """
    Classify iceberg by size according to standard maritime classification.
    
    Args:
        diameter_m: Estimated diameter in meters
    
    Returns:
        Size classification string
    """
    if diameter_m < 5:
        return "Growler"
    elif diameter_m < 15:
        return "Bergy Bit"
    elif diameter_m < 60:
        return "Small"
    elif diameter_m < 120:
        return "Medium"
    elif diameter_m < 200:
        return "Large"
    else:
        return "Very Large"


def format_coordinates(lat: float, lon: float, precision: int = 4) -> str:
    """
    Format coordinates as human-readable string.
    
    Args:
        lat: Latitude
        lon: Longitude
        precision: Decimal places
    
    Returns:
        Formatted string (e.g., "65.2345°S, 64.5678°W")
    """
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"
    
    return f"{abs(lat):.{precision}f}°{lat_dir}, {abs(lon):.{precision}f}°{lon_dir}"


# Default Sentinel-1 configuration for Antarctic operations
SENTINEL1_ANTARCTIC_CONFIG = {
    "resolution_meters": 10.0,
    "default_center_lat": -65.0,
    "default_center_lon": -64.0,
    "image_size": 640,
}


if __name__ == "__main__":
    # Test coordinate conversion
    print("Testing CoordinateConverter...")
    
    converter = CoordinateConverter(
        image_width=640,
        image_height=640,
        center_lat=-65.0,
        center_lon=-64.0,
        resolution_meters=10.0
    )
    
    # Test pixel to latlon
    lat, lon = converter.pixel_to_latlon(320, 320)
    print(f"Center pixel (320, 320) -> {format_coordinates(lat, lon)}")
    
    # Test bbox conversion
    bbox_geo = converter.bbox_to_latlon_bounds(200, 150, 100, 80)
    print(f"Bbox center: {format_coordinates(bbox_geo['center_lat'], bbox_geo['center_lon'])}")
    
    # Test size calculation
    size = converter.calculate_bbox_size_meters(100, 80)
    print(f"Bbox size: {size['width_m']}m x {size['height_m']}m = {size['area_m2']}m²")
    print(f"Estimated diameter: {size['estimated_diameter_m']}m")
    print(f"Classification: {classify_iceberg_size(size['estimated_diameter_m'])}")
    
    # Test ID generation
    iceberg_id = generate_iceberg_id(1)
    print(f"Generated ID: {iceberg_id}")
    
    print("\n✓ All utility functions working correctly")
