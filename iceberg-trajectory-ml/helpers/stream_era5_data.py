"""
ERA5 Data Streaming Helpers
Uses CDS API with tempfiles - downloads to temp, loads to memory, deletes immediately.
NO files are saved to disk permanently.

For AMA-4: Write full implementation of streaming helpers.
"""

import xarray as xr
import tempfile
from pathlib import Path
from typing import List, Optional, Dict
from contextlib import contextmanager


@contextmanager
def stream_era5_data(
    year: int,
    month: Optional[int] = None,
    lat_min: float = -90,
    lat_max: float = 90,
    lon_min: float = -180,
    lon_max: float = 180,
    variables: Optional[List[str]] = None,
    times: Optional[List[str]] = None
):
    """
    Stream ERA5 data via tempfile context manager.
    Downloads to tempfile, yields xarray dataset, then deletes tempfile.
    
    Args:
        year: Year to fetch (e.g., 2020)
        month: Optional month (1-12). If None, fetches all months.
        lat_min, lat_max: Latitude bounds (degrees, -90 to 90)
        lon_min, lon_max: Longitude bounds (degrees, -180 to 180)
        variables: List of ERA5 variable names
                   Default: ["10m_u_component_of_wind", "10m_v_component_of_wind"]
        times: List of times (e.g., ["00:00", "06:00", "12:00", "18:00"])
               Default: all 4 synoptic times
    
    Yields:
        xarray.Dataset loaded in memory
    
    Example:
        >>> with stream_era5_data(year=2020, month=1) as ds:
        ...     wind_u = ds["u10"].values
        ...     wind_v = ds["v10"].values
        ...     # Process data here
        ... # Tempfile automatically deleted when context exits
    
    Note:
        - Uses Python tempfile for automatic cleanup
        - Data is loaded into memory (.load() called automatically)
        - Tempfile is deleted even if an exception occurs
    """
    import cdsapi
    
    if variables is None:
        variables = ["10m_u_component_of_wind", "10m_v_component_of_wind"]
    
    if times is None:
        times = ["00:00", "06:00", "12:00", "18:00"]
    
    # CDS uses [North, West, South, East] format
    area = [lat_max, lon_min, lat_min, lon_max]
    
    # Build request
    request = {
        'product_type': 'reanalysis',
        'variable': variables,
        'year': str(year),
        'time': times,
        'area': area,
        'format': 'netcdf',
    }
    
    # Add month if specified
    if month is not None:
        request['month'] = f"{month:02d}"
        request['day'] = [f"{d:02d}" for d in range(1, 32)]  # All days
    else:
        # All months
        request['month'] = [f"{m:02d}" for m in range(1, 13)]
        request['day'] = [f"{d:02d}" for d in range(1, 32)]
    
    # Create tempfile
    tmp = tempfile.NamedTemporaryFile(suffix='.nc', delete=False)
    tmp_path = Path(tmp.name)
    tmp.close()
    
    try:
        # Download to tempfile
        c = cdsapi.Client()
        c.retrieve('reanalysis-era5-single-levels', request, str(tmp_path))
        
        # Load into memory
        ds = xr.open_dataset(tmp_path)
        data = ds.load()  # Force load to RAM
        ds.close()
        
        # Yield the in-memory dataset
        yield data
        
    finally:
        # Always delete tempfile
        if tmp_path.exists():
            tmp_path.unlink()


def stream_era5_by_year(
    year: int,
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
    variables: Optional[List[str]] = None
) -> xr.Dataset:
    """
    Stream ERA5 data for a full year.
    
    Args:
        year: Year to fetch
        lat_min, lat_max: Latitude bounds
        lon_min, lon_max: Longitude bounds
        variables: ERA5 variables (default: 10m wind components)
    
    Returns:
        xarray.Dataset loaded in memory (tempfile already deleted)
    
    Example:
        >>> ds = stream_era5_by_year(
        ...     year=2020,
        ...     lat_min=-60, lat_max=-55,
        ...     lon_min=-5, lon_max=5
        ... )
        >>> # ds is already in memory, tempfile deleted
        >>> wind_u = ds["u10"].values
    
    Note:
        - Unlike stream_era5_data context manager, this returns the dataset
        - Tempfile is already deleted when this returns
        - Be careful with memory - one year can be 1-2 GB
    """
    with stream_era5_data(
        year=year,
        lat_min=lat_min,
        lat_max=lat_max,
        lon_min=lon_min,
        lon_max=lon_max,
        variables=variables
    ) as ds:
        # ds is already loaded in memory
        # Create a copy to return (original will be closed)
        return ds.copy(deep=True)


# TODO (AMA-4): Implement additional helpers
# - stream_era5_monthly() - for monthly chunks
# - stream_era5_pressure_levels() - for different dataset
# - parallel_stream_era5() - download multiple months in parallel
# - estimate_era5_size() - estimate download size before fetching
