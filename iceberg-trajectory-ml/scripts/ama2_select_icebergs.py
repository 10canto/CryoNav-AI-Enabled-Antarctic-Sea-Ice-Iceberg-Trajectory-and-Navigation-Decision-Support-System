#!/usr/bin/env python3
# AMA-2: Select Validation Icebergs
"""
Selects icebergs that pass through the Cape Town-Maitri shipping corridor.
Filters by bounding box, date range, and minimum position count.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import glob
import sys

# Color codes
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


def print_header(text):
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")


def print_step(step_num, text):
    print(f"\n{YELLOW}Step {step_num}:{RESET} {text}")


def print_stat(label, value):
    print(f"  {label:40s} {GREEN}{value}{RESET}")


def detect_column(df, keywords):
    """Auto-detect column name by matching keywords (case-insensitive)."""
    cols_lower = {col.lower(): col for col in df.columns}
    for keyword in keywords:
        for col_lower, col_original in cols_lower.items():
            if keyword.lower() in col_lower:
                return col_original
    return None


def parse_date_column(date_val):
    """
    Parse date from various formats:
    - YYYYDDD (year + day of year, e.g., 2016031)
    - YYYY-MM-DD
    - other standard formats
    """
    if pd.isna(date_val):
        return None
    
    date_str = str(date_val).strip()
    
    # Try YYYYDDD format (most common in the data)
    if len(date_str) == 7 and date_str.isdigit():
        try:
            year = int(date_str[:4])
            day_of_year = int(date_str[4:])
            return pd.Timestamp(year=year, month=1, day=1) + pd.Timedelta(days=day_of_year - 1)
        except:
            pass
    
    # Try standard pandas parsing
    try:
        return pd.to_datetime(date_str)
    except:
        return None


def load_master_csv(master_path):
    """Try to load the master CSV if it has trajectory data."""
    print_step("1a", "Checking master CSV for trajectory data")
    
    try:
        df = pd.read_csv(master_path)
        print_stat("Loaded master CSV", f"{len(df)} rows")
        print_stat("Columns", f"{', '.join(df.columns[:5])}...")
        
        # Detect columns
        id_col = detect_column(df, ["id", "name", "iceberg"])
        lat_col = detect_column(df, ["lat", "latitude"])
        lon_col = detect_column(df, ["lon", "long", "longitude"])
        date_col = detect_column(df, ["date", "time", "timestamp", "update"])
        
        print(f"\n  {YELLOW}Detected columns:{RESET}")
        print(f"    ID:        {id_col}")
        print(f"    Latitude:  {lat_col}")
        print(f"    Longitude: {lon_col}")
        print(f"    Date:      {date_col}")
        
        # Check if this is trajectory data vs just a current snapshot
        # Master CSV has dates like "09/24/2026" which are outside our range
        # AND only has 1 row per iceberg - this is just a snapshot index
        if date_col and date_col in df.columns:
            # Try to parse a sample date
            sample_date = parse_date_column(df[date_col].iloc[0])
            if sample_date and sample_date.year > 2022:
                print(f"\n  {YELLOW}✗{RESET} Master CSV contains current snapshot data (2026)")
                print(f"  {YELLOW}→{RESET} Will load individual trajectory files for historical data")
                return None, None, None, None, None
        
        # Check if this has trajectory data (multiple rows per iceberg)
        if id_col and lat_col and lon_col:
            if id_col in df.columns:
                id_counts = df[id_col].value_counts()
                if id_counts.max() > 1:
                    print(f"\n  {GREEN}✓{RESET} Master CSV contains trajectory data!")
                    return df, id_col, lat_col, lon_col, date_col
        
        print(f"\n  {YELLOW}✗{RESET} Master CSV is just an index (1 row per iceberg)")
        print(f"  {YELLOW}→{RESET} Will load individual trajectory files instead")
        return None, None, None, None, None
        
    except Exception as e:
        print(f"  {RED}Error loading master CSV: {e}{RESET}")
        return None, None, None, None, None


def load_individual_files(data_dir):
    """Load all individual iceberg CSV files."""
    print_step("1b", "Loading individual iceberg trajectory files")
    
    csv_pattern = str(data_dir / "consolidated_database_v8.0" / "updated7_consol" / "*.csv")
    files = sorted(glob.glob(csv_pattern))
    
    # Filter out non-data files
    files = [f for f in files if not Path(f).name.startswith(('.', '#', 'README'))]
    
    print_stat("Found trajectory files", len(files))
    
    all_data = []
    failed_files = []
    
    for idx, file_path in enumerate(files, 1):
        # Progress indicator
        if idx % 50 == 0 or idx == len(files):
            print(f"  Loading file {idx}/{len(files)}...", end='\r')
        
        try:
            # Extract iceberg ID from filename
            iceberg_id = Path(file_path).stem.upper()
            
            # Try to load with header
            df = pd.read_csv(file_path)
            
            # Detect columns
            lat_col = detect_column(df, ["lat", "latitude", "nic_1", "ascat_1"])
            lon_col = detect_column(df, ["lon", "long", "longitude", "nic_2", "ascat_2"])
            date_col = detect_column(df, ["date", "time", "timestamp"])
            
            if not (lat_col and lon_col and date_col):
                failed_files.append(file_path)
                continue
            
            # Extract needed columns
            subset = df[[lat_col, lon_col, date_col]].copy()
            subset.columns = ['latitude', 'longitude', 'date']
            subset['iceberg_id'] = iceberg_id
            
            # Parse dates
            subset['date'] = subset['date'].apply(parse_date_column)
            
            # Try to extract size if available
            size_col_1 = detect_column(df, ["size_1", "length", "width"])
            size_col_2 = detect_column(df, ["size_2"])
            
            if size_col_1 and size_col_2:
                # Use max of length/width as representative size
                subset['size_km'] = df[[size_col_1, size_col_2]].max(axis=1)
            else:
                subset['size_km'] = np.nan
            
            all_data.append(subset)
            
        except Exception as e:
            failed_files.append(file_path)
            continue
    
    print(f"\n  {GREEN}✓{RESET} Loaded {len(all_data)} files successfully")
    if failed_files:
        print(f"  {YELLOW}⚠{RESET} Failed to load {len(failed_files)} files")
    
    # Concatenate all data
    df_all = pd.concat(all_data, ignore_index=True)
    print_stat("Total positions loaded", f"{len(df_all):,}")
    
    return df_all


def estimate_size_class(iceberg_id, size_km=None):
    """Estimate size class from size data or iceberg name."""
    if pd.notna(size_km) and size_km > 0:
        if size_km < 10:
            return "Small"
        elif size_km < 50:
            return "Medium"
        elif size_km < 100:
            return "Large"
        else:
            return "Giant"
    
    # Fallback: estimate from name
    # Common patterns: A68 (giant), B15 (giant), smaller numbers often smaller
    id_lower = str(iceberg_id).lower()
    
    # Known giants
    if any(x in id_lower for x in ['a68', 'b15', 'c19', 'd15']):
        return "Giant"
    
    # Extract number if possible
    import re
    match = re.search(r'(\d+)', id_lower)
    if match:
        num = int(match.group(1))
        if num < 20:
            return "Large"
        elif num < 40:
            return "Medium"
        else:
            return "Small"
    
    return "Unknown"


def apply_filters(df):
    """Apply all filters in sequence."""
    print_header("FILTERING DATA")
    
    # Bounding box
    LAT_MIN, LAT_MAX = -72, -30
    LON_MIN, LON_MAX = -20, 60
    DATE_MIN = pd.Timestamp("1993-01-01")
    DATE_MAX = pd.Timestamp("2021-12-31")
    MIN_POSITIONS = 10
    
    print(f"  Bounding Box: {LAT_MIN}° to {LAT_MAX}° lat, {LON_MIN}° to {LON_MAX}° lon")
    print(f"  Date Range:   {DATE_MIN.date()} to {DATE_MAX.date()}")
    print(f"  Min Positions: {MIN_POSITIONS}")
    
    initial_count = len(df)
    initial_icebergs = df['iceberg_id'].nunique()
    
    print(f"\n  {BLUE}Initial:{RESET}")
    print_stat("Total positions", f"{initial_count:,}")
    print_stat("Total icebergs", f"{initial_icebergs}")
    
    # Filter 1: Drop missing lat/lon
    print(f"\n  {YELLOW}Filter 1:{RESET} Drop missing lat/lon")
    df = df.dropna(subset=['latitude', 'longitude'])
    print_stat("Remaining positions", f"{len(df):,} (-{initial_count - len(df):,})")
    
    # Filter 2: Bounding box
    print(f"\n  {YELLOW}Filter 2:{RESET} Keep only positions in bounding box")
    df = df[
        (df['latitude'] >= LAT_MIN) & (df['latitude'] <= LAT_MAX) &
        (df['longitude'] >= LON_MIN) & (df['longitude'] <= LON_MAX)
    ]
    print_stat("Remaining positions", f"{len(df):,}")
    print_stat("Icebergs with any positions in box", df['iceberg_id'].nunique())
    
    # Filter 3: Date range
    print(f"\n  {YELLOW}Filter 3:{RESET} Keep only dates in range")
    df = df[df['date'].notna()]
    df = df[(df['date'] >= DATE_MIN) & (df['date'] <= DATE_MAX)]
    print_stat("Remaining positions", f"{len(df):,}")
    
    # Filter 4: Minimum positions per iceberg
    print(f"\n  {YELLOW}Filter 4:{RESET} Keep icebergs with >= {MIN_POSITIONS} positions")
    position_counts = df.groupby('iceberg_id').size()
    valid_icebergs = position_counts[position_counts >= MIN_POSITIONS].index
    df = df[df['iceberg_id'].isin(valid_icebergs)]
    print_stat("Remaining positions", f"{len(df):,}")
    print_stat("Remaining icebergs", len(valid_icebergs))
    
    # Filter 5: Sort by iceberg and date
    print(f"\n  {YELLOW}Filter 5:{RESET} Sort by iceberg_id, then date")
    df = df.sort_values(['iceberg_id', 'date'])
    print_stat("Final positions", f"{len(df):,}")
    
    return df


def generate_statistics(df):
    """Generate and print statistics."""
    print_header("STATISTICS")
    
    # Check if we have any data
    if len(df) == 0:
        print(f"\n{RED}No icebergs match the filter criteria!{RESET}")
        print(f"\nPossible reasons:")
        print(f"  - Date range filter too restrictive (need data from 1993-2021)")
        print(f"  - Bounding box doesn't match iceberg locations")
        print(f"  - Minimum position count too high")
        print(f"\nThe master CSV contains current data (2026) which is outside the date range.")
        print(f"Individual trajectory files should contain historical data (1993-2021).")
        sys.exit(1)
    
    # Basic stats
    print_step("A", "Basic Statistics")
    print_stat("Total icebergs", df['iceberg_id'].nunique())
    print_stat("Total positions", f"{len(df):,}")
    print_stat("Date range", f"{df['date'].min().date()} to {df['date'].max().date()}")
    
    # Training pairs (consecutive positions)
    total_pairs = 0
    for iceberg_id in df['iceberg_id'].unique():
        iceberg_df = df[df['iceberg_id'] == iceberg_id]
        total_pairs += len(iceberg_df) - 1
    print_stat("Consecutive position pairs (training rows)", f"{total_pairs:,}")
    
    # Count per year
    print_step("B", "Positions per Year")
    df['year'] = df['date'].dt.year
    year_counts = df.groupby('year').size().sort_index()
    
    max_count = year_counts.max()
    for year, count in year_counts.items():
        bar_length = int(40 * count / max_count)
        bar = "█" * bar_length
        print(f"  {year}: {bar} {count:,}")
    
    # Size classes
    print_step("C", "Size Classes")
    df['size_class'] = df.apply(
        lambda row: estimate_size_class(row['iceberg_id'], row.get('size_km', np.nan)), 
        axis=1
    )
    size_counts = df.groupby(['iceberg_id', 'size_class']).size().groupby('size_class').size()
    
    for size_class in ['Giant', 'Large', 'Medium', 'Small', 'Unknown']:
        if size_class in size_counts:
            print_stat(f"{size_class} icebergs", size_counts[size_class])
    
    # Top icebergs by position count
    print_step("D", "Top 10 Icebergs by Position Count")
    position_counts = df.groupby('iceberg_id').size().sort_values(ascending=False).head(10)
    for idx, (iceberg_id, count) in enumerate(position_counts.items(), 1):
        size_class = df[df['iceberg_id'] == iceberg_id]['size_class'].iloc[0]
        print(f"  {idx:2d}. {iceberg_id:10s} {count:5,} positions  ({size_class})")
    
    return df


def save_outputs(df):
    """Save all output files."""
    print_header("SAVING OUTPUTS")
    
    output_dir = Path("iceberg-trajectory-ml/data/validation")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Selected icebergs summary
    print_step("1", "Saving selected_icebergs.csv")
    iceberg_summary = df.groupby('iceberg_id').agg({
        'date': ['min', 'max', 'count'],
        'latitude': 'mean',
        'longitude': 'mean',
        'size_class': 'first'
    }).reset_index()
    
    iceberg_summary.columns = [
        'iceberg_id', 'first_date', 'last_date', 'num_positions',
        'mean_lat', 'mean_lon', 'size_class'
    ]
    
    output_file_1 = output_dir / "selected_icebergs.csv"
    iceberg_summary.to_csv(output_file_1, index=False)
    print_stat("Saved", output_file_1)
    print_stat("Rows", len(iceberg_summary))
    
    # 2. All selected positions
    print_step("2", "Saving selected_positions.csv")
    output_columns = ['iceberg_id', 'date', 'latitude', 'longitude', 'size_class']
    df_output = df[output_columns].copy()
    
    output_file_2 = output_dir / "selected_positions.csv"
    df_output.to_csv(output_file_2, index=False)
    print_stat("Saved", output_file_2)
    print_stat("Rows", f"{len(df_output):,}")
    
    # 3. Summary markdown report
    print_step("3", "Saving ama2_summary.md")
    
    total_pairs = 0
    for iceberg_id in df['iceberg_id'].unique():
        iceberg_df = df[df['iceberg_id'] == iceberg_id]
        total_pairs += len(iceberg_df) - 1
    
    year_counts = df.groupby('year').size().sort_index()
    size_counts = df.groupby(['iceberg_id', 'size_class']).size().groupby('size_class').size()
    position_counts = df.groupby('iceberg_id').size().sort_values(ascending=False).head(10)
    
    md_content = f"""# AMA-2: Iceberg Selection Summary

## Selection Criteria

**Cape Town to Maitri Shipping Corridor**
- **Latitude**: -72° to -30° S
- **Longitude**: -20° to 60° E
- **Date Range**: 1993-01-01 to 2021-12-31
- **Minimum Positions**: 10 per iceberg

## Results

### Overview
- **Total Icebergs Selected**: {df['iceberg_id'].nunique()}
- **Total Positions**: {len(df):,}
- **Date Range**: {df['date'].min().date()} to {df['date'].max().date()}
- **Consecutive Position Pairs** (training rows): {total_pairs:,}

### Positions per Year

| Year | Count |
|------|-------|
"""
    
    for year, count in year_counts.items():
        md_content += f"| {year} | {count:,} |\n"
    
    md_content += f"""
### Size Classes

| Class | Icebergs |
|-------|----------|
"""
    
    for size_class in ['Giant', 'Large', 'Medium', 'Small', 'Unknown']:
        if size_class in size_counts:
            md_content += f"| {size_class} | {size_counts[size_class]} |\n"
    
    md_content += f"""
### Top 10 Icebergs by Position Count

| Rank | Iceberg ID | Positions | Size Class |
|------|------------|-----------|------------|
"""
    
    for idx, (iceberg_id, count) in enumerate(position_counts.items(), 1):
        size_class = df[df['iceberg_id'] == iceberg_id]['size_class'].iloc[0]
        md_content += f"| {idx} | {iceberg_id} | {count:,} | {size_class} |\n"
    
    md_content += f"""
## Files Generated

1. `selected_icebergs.csv` - One row per iceberg with summary stats
2. `selected_positions.csv` - All {len(df):,} positions of selected icebergs
3. `ama2_summary.md` - This file

## Next Steps (AMA-3)

Run `ama2_define_region.py` to:
- Calculate actual bounding box from selected positions
- Add buffer for environmental data download
- Generate `download_config.yaml`

---

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    output_file_3 = output_dir / "ama2_summary.md"
    with open(output_file_3, 'w') as f:
        f.write(md_content)
    print_stat("Saved", output_file_3)


def main():
    print(f"\n{BLUE}╔════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BLUE}║     AMA-2: Select Validation Icebergs                                      ║{RESET}")
    print(f"{BLUE}║     CryoNav AI - Iceberg Trajectory ML                                     ║{RESET}")
    print(f"{BLUE}╚════════════════════════════════════════════════════════════════════════════╝{RESET}")
    
    # Determine data directory (work from repo root)
    data_dir = Path("DATA")
    if not data_dir.exists():
        print(f"\n{RED}ERROR: DATA directory not found!{RESET}")
        print(f"Expected: {data_dir.absolute()}")
        print(f"Make sure you're running from the repo root.")
        sys.exit(1)
    
    print_stat("Data directory", data_dir.absolute())
    
    # Try master CSV first
    master_path = data_dir / "AntarcticIcebergs_20260924.csv"
    df, id_col, lat_col, lon_col, date_col = load_master_csv(master_path)
    
    # If master doesn't have trajectory data, load individual files
    if df is None:
        df = load_individual_files(data_dir)
    else:
        # Standardize column names if using master CSV
        df = df.rename(columns={
            id_col: 'iceberg_id',
            lat_col: 'latitude',
            lon_col: 'longitude',
            date_col: 'date'
        })
        df['date'] = pd.to_datetime(df['date'])
    
    # Apply filters
    df = apply_filters(df)
    
    # Generate statistics
    df = generate_statistics(df)
    
    # Save outputs
    save_outputs(df)
    
    print(f"\n{GREEN}{'=' * 80}{RESET}")
    print(f"{GREEN}✓ AMA-2 COMPLETE{RESET}")
    print(f"{GREEN}{'=' * 80}{RESET}\n")
    print("Next step: Run ama2_define_region.py to generate download_config.yaml\n")


if __name__ == "__main__":
    main()
