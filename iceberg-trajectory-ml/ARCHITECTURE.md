# CryoNav AI - Data Pipeline Architecture

## Critical Design Decision: Streaming-First, No Persistent NetCDF Files

### Overview

The iceberg trajectory ML pipeline is designed to **stream data directly from sources** without saving intermediate NetCDF files to disk. This approach:
- ✅ Saves disk space (NetCDF files can be 100s of GBs)
- ✅ Avoids data duplication
- ✅ Forces proper data lineage (always fresh from source)
- ✅ Simplifies pipeline (no cache invalidation logic)

---

## Architecture Principles

### 1. Stream-First Data Access

#### Copernicus Marine Service
```python
import copernicusmarine
import xarray as xr

# CORRECT: Stream directly into xarray
ds = copernicusmarine.open_dataset(
    dataset_id="cmems_mod_glo_phy_my_0.083deg_P1D-m",
    minimum_longitude=lon_min,
    maximum_longitude=lon_max,
    minimum_latitude=lat_min,
    maximum_latitude=lat_max,
    start_datetime="2020-01-01",
    end_datetime="2020-12-31",
    variables=["uo", "vo", "thetao"]
)

# Process immediately
data = ds.sel(depth=0).compute()  # Load surface layer only
ds.close()

# WRONG: Do NOT use .subset() to save files
# copernicusmarine.subset(..., output_filename="data.nc")  # ❌ NO!
```

#### CDS (Climate Data Store) / ERA5
```python
import cdsapi
import xarray as xr
import tempfile
from pathlib import Path

# CORRECT: Download to tempfile, load to memory, delete immediately
c = cdsapi.Client()

with tempfile.NamedTemporaryFile(suffix='.nc', delete=False) as tmp:
    tmp_path = tmp.name

try:
    c.retrieve('reanalysis-era5-single-levels', {...}, tmp_path)
    
    # Load into xarray with .load() to force in-memory
    ds = xr.open_dataset(tmp_path)
    data = ds.load()  # Critical: loads to RAM
    ds.close()
    
    # Process data here
    # ...
    
finally:
    # Always clean up tempfile
    Path(tmp_path).unlink()

# WRONG: Do NOT save to permanent locations
# c.retrieve(..., "data/era5/wind_2020.nc")  # ❌ NO!
```

---

### 2. Single Persistent Data File

**The ONLY file that should be saved permanently**:
```
iceberg-trajectory-ml/data/training_table.csv
```

This is the final output of the data pipeline (AMA-5):
- Rows: iceberg positions at hourly or daily intervals
- Columns: interpolated features (currents, wind, SST, SIC, etc.) + target (next position)

Example structure:
```csv
iceberg_id,timestamp,lat,lon,uo,vo,u10,v10,sst,sic,target_lat,target_lon
A68a,2020-01-01T00:00:00,-75.5,10.2,0.12,-0.08,5.3,-2.1,1.5,0.85,-75.48,10.25
A68a,2020-01-01T01:00:00,-75.48,10.25,0.15,-0.07,5.1,-2.3,1.5,0.84,-75.46,10.30
...
```

---

### 3. Process Data in Yearly Chunks

To avoid RAM overflow when processing multi-year datasets:

```python
def process_iceberg_trajectory_streaming(iceberg_id, start_year, end_year):
    """Process iceberg trajectory year by year."""
    all_rows = []
    
    for year in range(start_year, end_year + 1):
        print(f"Processing {iceberg_id} - Year {year}")
        
        # 1. Get iceberg positions for this year
        positions = load_iceberg_positions(iceberg_id, year)
        
        # 2. Stream ocean data for this year's bounding box
        ocean_data = stream_copernicus_data(
            year=year,
            bbox=get_bounding_box(positions)
        )
        
        # 3. Stream atmospheric data for this year
        with stream_cds_data(year=year, bbox=...) as atmos_data:
            # 4. Interpolate all features to iceberg positions
            rows = interpolate_to_positions(positions, ocean_data, atmos_data)
            all_rows.extend(rows)
        
        # 5. Clean up (xarray datasets closed, tempfiles deleted)
        ocean_data.close()
    
    # 6. Save final table only
    df = pd.DataFrame(all_rows)
    df.to_csv("data/training_table.csv", index=False)
```

**Key points**:
- Load only one year at a time
- Close datasets immediately after processing
- Delete tempfiles in `finally` blocks
- Only write the final CSV

---

### 4. Updated Task Definitions

#### AMA-3: Ocean Data Access (REVISED)
**OLD**: Download historical ocean current data  
**NEW**: Verify Copernicus Marine streaming access and write helper functions

**Deliverables**:
1. `helpers/stream_ocean_data.py` - Functions to stream ocean data by year/region
2. Test that streams 1 week of data for a small region
3. Verify memory usage stays reasonable

#### AMA-4: Atmospheric Data Access (REVISED)
**OLD**: Download historical ERA5 data  
**NEW**: Verify CDS streaming access and write helper functions

**Deliverables**:
1. `helpers/stream_era5_data.py` - Functions to stream ERA5 via tempfiles
2. Test that downloads and immediately deletes a 1-week tempfile
3. Context manager for automatic cleanup

#### AMA-5: Feature Engineering (UNCHANGED)
Build the final `training_table.csv` by:
1. Loading iceberg positions from database
2. Streaming environmental data year-by-year
3. Interpolating features to iceberg positions
4. Saving the final CSV

---

## Memory Management Strategy

### Target Memory Budget: < 8 GB RAM

```python
# GOOD: Process in chunks
for year in years:
    data = stream_data(year)  # ~1-2 GB per year
    process(data)
    data.close()  # Release memory

# BAD: Load everything at once
data = stream_data(years)  # 20+ GB for multi-year
process(data)  # OOM!
```

### Spatial Subsetting

```python
# Only load data within iceberg's actual path
bbox = get_iceberg_bounding_box(positions)
# Add buffer for interpolation
bbox_buffered = expand_bbox(bbox, buffer_degrees=2)

ds = copernicusmarine.open_dataset(
    ...,
    minimum_longitude=bbox_buffered.lon_min,
    maximum_longitude=bbox_buffered.lon_max,
    minimum_latitude=bbox_buffered.lat_min,
    maximum_latitude=bbox_buffered.lat_max
)
```

Only load the region where the iceberg actually traveled + small buffer.

### Temporal Subsetting

```python
# Process one year at a time, not the entire lifetime
for year in range(2015, 2024):
    year_positions = positions[positions.year == year]
    if len(year_positions) == 0:
        continue
    
    # Stream only this year's data
    ds = stream_ocean_data(
        start_date=f"{year}-01-01",
        end_date=f"{year}-12-31",
        bbox=...
    )
```

---

## File System Structure

```
iceberg-trajectory-ml/
├── data/
│   ├── training_table.csv          ← ONLY persistent file
│   ├── era5/                        ← Empty (no .nc files saved)
│   └── validation/                  ← Empty (no .nc files saved)
├── scripts/
│   ├── ama1_check_accounts.py      ← Tests streaming access
│   ├── ama3_stream_ocean.py        ← Ocean streaming helpers
│   ├── ama4_stream_era5.py         ← ERA5 streaming helpers
│   └── ama5_build_training_table.py ← Final CSV builder
├── helpers/
│   ├── stream_ocean_data.py
│   ├── stream_era5_data.py
│   └── interpolate.py
└── ARCHITECTURE.md                  ← This file
```

---

## Testing Strategy

### Unit Tests
```python
def test_stream_ocean_data_no_files_saved():
    """Verify no .nc files are created during streaming."""
    data_dir = Path("data/validation")
    initial_files = set(data_dir.glob("*.nc"))
    
    # Stream data
    ds = stream_ocean_data(year=2020, bbox=...)
    data = ds.compute()
    ds.close()
    
    # Verify no new files
    final_files = set(data_dir.glob("*.nc"))
    assert final_files == initial_files, "Streaming created .nc files!"
```

### Integration Tests
```python
def test_full_pipeline_memory_bounded():
    """Verify full pipeline stays under 8 GB."""
    import tracemalloc
    
    tracemalloc.start()
    
    build_training_table(
        iceberg_id="test_iceberg",
        years=[2020, 2021]
    )
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    assert peak < 8 * 1024**3, f"Peak memory {peak} exceeded 8 GB"
```

---

## Benefits of This Architecture

1. **Disk Space**: No 100+ GB of cached NetCDF files
2. **Data Freshness**: Always fetch latest data from sources
3. **Reproducibility**: Clear data lineage (source → streaming → CSV)
4. **Simplicity**: No cache invalidation, no stale data issues
5. **Scalability**: Process decades of data without running out of disk

---

## Migration Notes

If you have existing code that downloads files:

```python
# OLD WAY ❌
copernicusmarine.subset(..., output_filename="ocean.nc")
ds = xr.open_dataset("ocean.nc")

# NEW WAY ✅
ds = copernicusmarine.open_dataset(...)
data = ds.compute()  # Load to memory
ds.close()
```

```python
# OLD WAY ❌
c.retrieve(..., "data/era5/wind.nc")
ds = xr.open_dataset("data/era5/wind.nc")

# NEW WAY ✅
with tempfile.NamedTemporaryFile(suffix='.nc') as tmp:
    c.retrieve(..., tmp.name)
    ds = xr.open_dataset(tmp.name).load()
# Tempfile auto-deleted
```

---

## References

- Copernicus Marine Streaming: https://help.marine.copernicus.eu/en/articles/8283189-how-to-open-a-copernicus-marine-dataset-with-the-python-copernicus-marine-toolbox
- xarray Memory Management: https://docs.xarray.dev/en/stable/user-guide/dask.html
- CDS API: https://cds.climate.copernicus.eu/api-how-to

---

**Last Updated**: 2024-11-05  
**Author**: Data & ML Team (AMA-1)
