"""
Ocean Data Streaming Helpers
Uses Copernicus Marine Service's open_dataset() to stream directly into xarray.
NO files are saved to disk.

For AMA-3: Write full implementation of streaming helpers.
"""

import xarray as xr
from typing import Optional, List
from datetime import datetime


def stream_ocean_currents(
    start_date: str,
    end_date: str,
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
    variables: Optional[List[str]] = None,
    depth_max: float = 1.0
) -> xr.Dataset:
    """
    Stream ocean current data from Copernicus Marine Service.
    
    Args:
        start_date: ISO format date string (e.g., "2020-01-01")
        end_date: ISO format date string (e.g., "2020-12-31")
        lat_min, lat_max: Latitude bounds (degrees)
        lon_min, lon_max: Longitude bounds (degrees)
        variables: List of variables to fetch. Default: ["uo", "vo", "thetao", "so"]
        depth_max: Maximum depth in meters (default: 1.0 for surface layer)
    
    Returns:
        xarray.Dataset with ocean data (NOT loaded to memory yet)
    
    Example:
        >>> ds = stream_ocean_currents(
        ...     start_date="2020-01-01",
        ...     end_date="2020-01-31",
        ...     lat_min=-60, lat_max=-55,
        ...     lon_min=-5, lon_max=5
        ... )
        >>> # Select surface layer and load to memory
        >>> surface = ds.sel(depth=slice(0, 1)).compute()
        >>> ds.close()
    
    Note:
        - Data is streamed, not downloaded to disk
        - Call .compute() to load into memory when ready
        - Always close() the dataset when done
    """
    import copernicusmarine
    
    if variables is None:
        variables = ["uo", "vo", "thetao", "so"]  # u, v currents, temp, salinity
    
    dataset_id = "cmems_mod_glo_phy_my_0.083deg_P1D-m"
    
    ds = copernicusmarine.open_dataset(
        dataset_id=dataset_id,
        minimum_longitude=lon_min,
        maximum_longitude=lon_max,
        minimum_latitude=lat_min,
        maximum_latitude=lat_max,
        start_datetime=start_date,
        end_datetime=end_date,
        variables=variables,
        minimum_depth=0,
        maximum_depth=depth_max
    )
    
    return ds


def stream_ocean_data_by_year(
    year: int,
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
    variables: Optional[List[str]] = None
) -> xr.Dataset:
    """
    Stream ocean data for a single year.
    Wrapper around stream_ocean_currents for yearly chunking.
    
    Args:
        year: Year to fetch (e.g., 2020)
        lat_min, lat_max: Latitude bounds
        lon_min, lon_max: Longitude bounds
        variables: List of variables (default: currents + temp + salinity)
    
    Returns:
        xarray.Dataset for the specified year
    
    Example:
        >>> ds = stream_ocean_data_by_year(
        ...     year=2020,
        ...     lat_min=-60, lat_max=-55,
        ...     lon_min=-5, lon_max=5
        ... )
        >>> data = ds.compute()
        >>> ds.close()
    """
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    return stream_ocean_currents(
        start_date=start_date,
        end_date=end_date,
        lat_min=lat_min,
        lat_max=lat_max,
        lon_min=lon_min,
        lon_max=lon_max,
        variables=variables
    )


# TODO (AMA-3): Implement additional helpers
# - stream_sea_ice_concentration()
# - stream_sea_surface_height()
# - get_iceberg_bounding_box() - compute bbox from trajectory
# - buffer_bbox() - add buffer for interpolation
