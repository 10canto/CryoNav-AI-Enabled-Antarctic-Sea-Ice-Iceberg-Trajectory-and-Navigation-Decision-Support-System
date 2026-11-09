#!/usr/bin/env python3
# AMA-2: Define Region for Environmental Data Download
"""
Reads selected iceberg positions and defines the download region with buffer.
Generates download_config.yaml for streaming environmental data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import yaml
from datetime import datetime
import sys

# Color codes
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"


def print_header(text):
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")


def print_stat(label, value):
    print(f"  {label:40s} {GREEN}{value}{RESET}")


def read_selected_positions(positions_file):
    """Read the selected positions CSV."""
    print_header("READING SELECTED POSITIONS")
    
    if not positions_file.exists():
        print(f"{RED}ERROR: {positions_file} not found!{RESET}")
        print(f"Run ama2_select_icebergs.py first to generate this file.")
        sys.exit(1)
    
    df = pd.read_csv(positions_file, parse_dates=['date'])
    
    print_stat("Total positions", f"{len(df):,}")
    print_stat("Total icebergs", df['iceberg_id'].nunique())
    print_stat("Date range", f"{df['date'].min().date()} to {df['date'].max().date()}")
    
    return df


def calculate_actual_bbox(df, buffer_degrees=2.0):
    """Calculate actual bounding box from data with buffer."""
    print_header("CALCULATING BOUNDING BOX")
    
    # Actual data extent
    lat_min_actual = df['latitude'].min()
    lat_max_actual = df['latitude'].max()
    lon_min_actual = df['longitude'].min()
    lon_max_actual = df['longitude'].max()
    
    print(f"  {CYAN}Actual Data Extent (no buffer):{RESET}")
    print_stat("Latitude range", f"{lat_min_actual:.2f}° to {lat_max_actual:.2f}°")
    print_stat("Longitude range", f"{lon_min_actual:.2f}° to {lon_max_actual:.2f}°")
    print_stat("Span", f"{lat_max_actual - lat_min_actual:.2f}° lat × {lon_max_actual - lon_min_actual:.2f}° lon")
    
    # Add buffer
    lat_min_buffered = lat_min_actual - buffer_degrees
    lat_max_buffered = lat_max_actual + buffer_degrees
    lon_min_buffered = lon_min_actual - buffer_degrees
    lon_max_buffered = lon_max_actual + buffer_degrees
    
    # Clamp to valid ranges
    lat_min_buffered = max(lat_min_buffered, -90)
    lat_max_buffered = min(lat_max_buffered, -30)  # Don't go north of 30°S
    lon_min_buffered = max(lon_min_buffered, -180)
    lon_max_buffered = min(lon_max_buffered, 180)
    
    print(f"\n  {CYAN}With {buffer_degrees}° Buffer:{RESET}")
    print_stat("Latitude range", f"{lat_min_buffered:.2f}° to {lat_max_buffered:.2f}°")
    print_stat("Longitude range", f"{lon_min_buffered:.2f}° to {lon_max_buffered:.2f}°")
    print_stat("Span", f"{lat_max_buffered - lat_min_buffered:.2f}° lat × {lon_max_buffered - lon_min_buffered:.2f}° lon")
    
    return {
        'minimum_latitude': float(lat_min_buffered),
        'maximum_latitude': float(lat_max_buffered),
        'minimum_longitude': float(lon_min_buffered),
        'maximum_longitude': float(lon_max_buffered)
    }


def calculate_date_range(df):
    """Calculate date range from data."""
    start_date = df['date'].min()
    end_date = df['date'].max()
    
    # Round to full days
    start_date = start_date.floor('D')
    end_date = end_date.ceil('D')
    
    return {
        'start': start_date.strftime('%Y-%m-%d'),
        'end': end_date.strftime('%Y-%m-%d')
    }


def estimate_download_size(region, date_range):
    """
    Estimate download size for streaming environmental data.
    
    Formula: ~0.5 MB/day/variable × num_days × num_variables × (area_ratio)
    
    Base assumption: 
    - Reference area: 80° lon × 30° lat = 2400 sq degrees
    - 5 key variables: uo, vo, thetao, u10, v10
    - Daily data
    """
    print_header("ESTIMATING DOWNLOAD SIZE")
    
    # Calculate area
    lat_span = region['maximum_latitude'] - region['minimum_latitude']
    lon_span = region['maximum_longitude'] - region['minimum_longitude']
    area = lat_span * lon_span
    
    # Reference area (80×30)
    reference_area = 80 * 30  # 2400 sq degrees
    area_ratio = area / reference_area
    
    # Calculate number of days
    from datetime import datetime as dt
    start = dt.strptime(date_range['start'], '%Y-%m-%d')
    end = dt.strptime(date_range['end'], '%Y-%m-%d')
    num_days = (end - start).days + 1
    
    # Variables to download
    num_variables = 5  # uo, vo, thetao, u10, v10
    
    # Base size: 0.5 MB per day per variable for reference area
    base_mb_per_day_per_var = 0.5
    
    # Estimated size in MB
    estimated_mb = base_mb_per_day_per_var * num_days * num_variables * area_ratio
    estimated_gb = estimated_mb / 1024
    
    print_stat("Area", f"{area:.0f} sq degrees ({area_ratio:.2%} of reference)")
    print_stat("Time span", f"{num_days:,} days")
    print_stat("Variables", f"{num_variables} (uo, vo, thetao, u10, v10)")
    print(f"\n  {CYAN}Streaming Estimate (in-memory processing):{RESET}")
    print_stat("Per-year memory footprint", f"~{estimated_gb / (num_days / 365):.1f} GB")
    print_stat("Total data to stream", f"~{estimated_gb:.1f} GB over {num_days:,} days")
    print(f"\n  {YELLOW}Note:{RESET} This is streaming data - no persistent files saved")
    print(f"  {YELLOW}→{RESET} Process year-by-year to keep RAM usage < 8 GB")
    
    return round(estimated_gb, 2)


def generate_config(region, date_range, estimated_size_gb):
    """Generate the download configuration YAML."""
    print_header("GENERATING CONFIGURATION")
    
    config = {
        'region': region,
        'date_range': date_range,
        'estimated_size_gb': estimated_size_gb,
        'variables': {
            'ocean': ['uo', 'vo', 'thetao', 'so'],
            'atmosphere': ['10m_u_component_of_wind', '10m_v_component_of_wind']
        },
        'notes': [
            'This configuration is for STREAMING data, not downloading to disk',
            'Use helpers/stream_ocean_data.py and helpers/stream_era5_data.py',
            'Process year-by-year to manage memory (target: < 8 GB RAM)',
            'Only training_table.csv will be saved permanently'
        ],
        'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    output_file = Path("iceberg-trajectory-ml/data/validation/download_config.yaml")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print_stat("Saved", output_file)
    
    # Print the config
    print(f"\n  {CYAN}Configuration:{RESET}")
    print(yaml.dump(config, default_flow_style=False, sort_keys=False, indent=2))
    
    return output_file


def print_next_steps():
    """Print next steps."""
    print(f"\n{GREEN}{'=' * 80}{RESET}")
    print(f"{GREEN}✓ AMA-2 REGION DEFINITION COMPLETE{RESET}")
    print(f"{GREEN}{'=' * 80}{RESET}\n")
    
    print(f"{YELLOW}Next Steps:{RESET}\n")
    print("1. AMA-3: Implement ocean data streaming helpers")
    print("   - Update helpers/stream_ocean_data.py")
    print("   - Test streaming with selected region")
    print()
    print("2. AMA-4: Implement ERA5 data streaming helpers")
    print("   - Update helpers/stream_era5_data.py")
    print("   - Test tempfile download/load/delete cycle")
    print()
    print("3. AMA-5: Build training_table.csv")
    print("   - Load selected_positions.csv")
    print("   - Stream environmental data year-by-year")
    print("   - Interpolate features to iceberg positions")
    print("   - Save final training_table.csv")
    print()


def main():
    print(f"\n{BLUE}╔════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BLUE}║     AMA-2: Define Download Region                                         ║{RESET}")
    print(f"{BLUE}║     CryoNav AI - Iceberg Trajectory ML                                     ║{RESET}")
    print(f"{BLUE}╚════════════════════════════════════════════════════════════════════════════╝{RESET}")
    
    # Read selected positions
    positions_file = Path("iceberg-trajectory-ml/data/validation/selected_positions.csv")
    df = read_selected_positions(positions_file)
    
    # Calculate bounding box with buffer
    region = calculate_actual_bbox(df, buffer_degrees=2.0)
    
    # Calculate date range
    date_range = calculate_date_range(df)
    
    # Estimate download size
    estimated_size_gb = estimate_download_size(region, date_range)
    
    # Generate configuration
    config_file = generate_config(region, date_range, estimated_size_gb)
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main()
