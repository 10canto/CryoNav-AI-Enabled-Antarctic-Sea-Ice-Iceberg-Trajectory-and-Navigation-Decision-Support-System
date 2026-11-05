#!/usr/bin/env python3
# AMA-3: Verify Ocean Data Chunks
"""
Verifies the ocean forcing files saved by ama3_stream_ocean.py.
Checks for completeness, missing years, and data quality.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

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


def print_error(text):
    print(f"{RED}✗ ERROR:{RESET} {text}")


def print_warning(text):
    print(f"{YELLOW}⚠ WARNING:{RESET} {text}")


def print_success(text):
    print(f"{GREEN}✓{RESET} {text}")


def find_chunk_files(data_dir):
    """Find all ocean forcing files."""
    data_dir = Path(data_dir)
    
    forcing_files = list(data_dir.glob("forcing_ocean_*.csv"))
    # Exclude the combined file from individual year list
    forcing_files = [f for f in forcing_files if f.name != "forcing_ocean_all.csv"]
    
    return sorted(forcing_files)


def extract_year_from_filename(file_path):
    """Extract year from filename like forcing_ocean_2015.csv."""
    try:
        # Remove extension and prefix
        year_str = file_path.stem.replace('forcing_ocean_', '')
        return int(year_str)
    except:
        return None


def read_chunk_metadata(file_path):
    """Read metadata from a forcing file without loading all data."""
    try:
        # Read the CSV
        df = pd.read_csv(file_path, parse_dates=['date'])
        
        # Get date range
        date_min = df['date'].min()
        date_max = df['date'].max()
        
        # Calculate valid percentages for each variable
        variables = ['uo', 'vo', 'siconc', 'usi', 'vsi']
        valid_counts = {}
        for var in variables:
            if var in df.columns:
                valid_counts[var] = df[var].notna().sum()
            else:
                valid_counts[var] = 0
        
        return {
            'rows': len(df),
            'columns': list(df.columns),
            'date_min': date_min,
            'date_max': date_max,
            'valid_counts': valid_counts,
            'icebergs': df['iceberg_id'].nunique() if 'iceberg_id' in df.columns else 0
        }
    
    except Exception as e:
        print_error(f"Failed to read {file_path.name}: {e}")
        return None


def verify_chunks(data_dir):
    """Main verification function."""
    print_header("VERIFYING OCEAN FORCING FILES")
    
    data_dir = Path(data_dir)
    if not data_dir.exists():
        print_error(f"Data directory not found: {data_dir}")
        sys.exit(1)
    
    print_stat("Data directory", data_dir)
    
    # Find all chunk files
    chunk_files = find_chunk_files(data_dir)
    
    if not chunk_files:
        print_error("No ocean forcing files found!")
        print("Expected files like: forcing_ocean_2015.csv")
        sys.exit(1)
    
    print_stat("Found chunks", len(chunk_files))
    
    # Extract years and sort
    years_found = []
    year_files = {}
    
    for file_path in chunk_files:
        year = extract_year_from_filename(file_path)
        if year:
            years_found.append(year)
            year_files[year] = file_path
    
    years_found = sorted(years_found)
    
    print_stat("Years present", f"{years_found[0]}-{years_found[-1]} "
                                f"({len(years_found)} years)")
    
    # Check for missing years in range
    expected_years = set(range(years_found[0], years_found[-1] + 1))
    missing_years = sorted(expected_years - set(years_found))
    
    if missing_years:
        print_warning(f"Missing years: {', '.join(map(str, missing_years))}")
    else:
        print_success("No missing years in range")
    
    # Calculate total disk usage
    total_size_mb = sum(f.stat().st_size for f in chunk_files) / 1024**2
    print_stat("Total disk usage", f"{total_size_mb:.2f} MB ({total_size_mb / 1024:.2f} GB)")
    
    # Check for combined file
    combined_file = data_dir / "forcing_ocean_all.csv"
    if combined_file.exists():
        combined_size_mb = combined_file.stat().st_size / 1024**2
        print_stat("Combined file", f"{combined_file.name} ({combined_size_mb:.2f} MB)")
    
    # Detailed verification
    print_header("CHUNK DETAILS")
    
    total_rows = 0
    total_valid = {'uo': 0, 'vo': 0, 'siconc': 0, 'usi': 0, 'vsi': 0}
    overall_date_min = None
    overall_date_max = None
    
    print(f"\n{'Year':<8} {'Rows':>10} {'Size':>8} {'Date Range':<25} {'Valid uo':<10} {'Valid sic':<10}")
    print(f"{'-' * 90}")
    
    for year in years_found:
        file_path = year_files[year]
        file_size_kb = file_path.stat().st_size / 1024
        
        # Read metadata
        metadata = read_chunk_metadata(file_path)
        
        if metadata:
            total_rows += metadata['rows']
            
            # Track overall date range
            if metadata['date_min']:
                if overall_date_min is None or metadata['date_min'] < overall_date_min:
                    overall_date_min = metadata['date_min']
            
            if metadata['date_max']:
                if overall_date_max is None or metadata['date_max'] > overall_date_max:
                    overall_date_max = metadata['date_max']
            
            # Accumulate valid counts
            for var in ['uo', 'vo', 'siconc', 'usi', 'vsi']:
                total_valid[var] += metadata['valid_counts'].get(var, 0)
            
            # Format date range
            if metadata['date_min'] and metadata['date_max']:
                date_range = f"{metadata['date_min'].date()} to {metadata['date_max'].date()}"
            else:
                date_range = "Unknown"
            
            # Calculate percentages
            pct_uo = 100 * metadata['valid_counts'].get('uo', 0) / metadata['rows'] if metadata['rows'] > 0 else 0
            pct_sic = 100 * metadata['valid_counts'].get('siconc', 0) / metadata['rows'] if metadata['rows'] > 0 else 0
            
            # Print row
            print(f"{year:<8} {metadata['rows']:>10,} {file_size_kb:>7.1f}K  {date_range:<25} "
                  f"{pct_uo:>6.1f}%     {pct_sic:>6.1f}%")
    
    # Summary statistics
    print(f"\n{CYAN}{'─' * 90}{RESET}")
    print_header("SUMMARY")
    
    print_stat("Total positions", f"{total_rows:,}")
    print_stat("Total chunks", len(chunk_files))
    print_stat("Total size", f"{total_size_mb:.2f} MB")
    
    if overall_date_min and overall_date_max:
        print_stat("Date range", f"{overall_date_min.date()} to {overall_date_max.date()}")
        days = (overall_date_max - overall_date_min).days + 1
        print_stat("Days covered", f"{days:,}")
    
    print_stat("Years covered", f"{len(years_found)} years")
    
    if missing_years:
        print_stat("Missing years", f"{len(missing_years)}: {', '.join(map(str, missing_years))}")
    
    # Print valid data percentages
    print("\n  Valid data percentage:")
    for var in ['uo', 'vo', 'siconc', 'usi', 'vsi']:
        pct = 100 * total_valid[var] / total_rows if total_rows > 0 else 0
        status = f"{GREEN}✓{RESET}" if pct > 50 else f"{YELLOW}⚠{RESET}"
        print(f"    {status} {var:10s} {total_valid[var]:>10,} / {total_rows:,} ({pct:>5.1f}%)")
    
    # Final verdict
    print(f"\n{GREEN}{'=' * 90}{RESET}")
    
    if not missing_years and total_rows > 0:
        print(f"{GREEN}✓ VERIFICATION PASSED{RESET}")
        print(f"{GREEN}{'=' * 90}{RESET}\n")
        print("All expected chunks are present and readable.")
        print("\nNext steps:")
        print("  1. AMA-4: Stream atmospheric data (ERA5)")
        print("  2. AMA-5: Combine with atmospheric forcing and iceberg positions")
    else:
        print(f"{YELLOW}⚠ VERIFICATION INCOMPLETE{RESET}")
        print(f"{YELLOW}{'=' * 90}{RESET}\n")
        
        if missing_years:
            print(f"Re-run streaming for missing years:")
            for year in missing_years:
                print(f"  python ama3_stream_ocean.py --year {year}")
        
        if total_rows == 0:
            print("No data was loaded. Check the forcing files.")
    
    print()


def main():
    print(f"\n{BLUE}╔════════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BLUE}║     AMA-3: Verify Ocean Forcing Files                                         ║{RESET}")
    print(f"{BLUE}║     CryoNav AI - Iceberg Trajectory ML                                         ║{RESET}")
    print(f"{BLUE}╚════════════════════════════════════════════════════════════════════════════════╝{RESET}")
    
    data_dir = Path("iceberg-trajectory-ml/data/validation")
    verify_chunks(data_dir)


if __name__ == "__main__":
    main()
