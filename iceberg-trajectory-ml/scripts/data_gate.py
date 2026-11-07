#!/usr/bin/env python3
"""
Data Gate - Prevents training on synthetic data.

This module ensures that only REAL observational data is used for model training.
It blocks any synthetic, fabricated, or interpolated datasets.
"""

import json
import sys
from pathlib import Path


def assert_real_data(report_path="iceberg-trajectory-ml/data/validation/data_report.json"):
    """
    Assert that the training data is real observational data, not synthetic.
    
    Args:
        report_path: Path to data_report.json
    
    Raises:
        SystemExit: If data is missing, synthetic, or invalid
    
    Returns:
        dict: The loaded data report
    """
    report_path = Path(report_path)
    
    # Check if report exists
    if not report_path.exists():
        print("\n" + "=" * 80)
        print("DATA GATE ERROR: Training data report not found")
        print("=" * 80)
        print(f"\nExpected file: {report_path}")
        print("\nThe training table has not been built yet.")
        print("Run this command first:")
        print("  python iceberg-trajectory-ml/scripts/ama5_build_training_table.py")
        print()
        sys.exit(1)
    
    # Load report
    try:
        with open(report_path, 'r') as f:
            report = json.load(f)
    except Exception as e:
        print("\n" + "=" * 80)
        print("DATA GATE ERROR: Failed to read data report")
        print("=" * 80)
        print(f"\nError: {e}")
        print(f"File: {report_path}")
        print()
        sys.exit(1)
    
    # Check 1: Synthetic flag must be False
    synthetic_flag = report.get('synthetic', None)
    if synthetic_flag is None:
        print("\n" + "=" * 80)
        print("DATA GATE ERROR: Missing 'synthetic' flag")
        print("=" * 80)
        print("\nThe data report does not contain a 'synthetic' flag.")
        print("This flag is required to verify data integrity.")
        print()
        sys.exit(1)
    
    if synthetic_flag is True:
        print("\n" + "=" * 80)
        print("DATA GATE ERROR: Synthetic data detected")
        print("=" * 80)
        print("\nThe data report indicates this is SYNTHETIC data.")
        print("Training on fabricated data is NOT permitted.")
        print()
        print("Only real observational data may be used for model development.")
        print()
        sys.exit(1)
    
    # Check 2: Data source must be REAL
    data_source = report.get('data_source', '').upper()
    if data_source != 'REAL':
        print("\n" + "=" * 80)
        print("DATA GATE ERROR: Invalid data source")
        print("=" * 80)
        print(f"\nData source: {data_source}")
        print("Expected: REAL")
        print()
        print("Only real observational data may be used for model development.")
        print()
        sys.exit(1)
    
    # All checks passed
    print("\n" + "=" * 80)
    print("DATA GATE PASSED: REAL data verified")
    print("=" * 80)
    print(f"\n✓ Data source: {report.get('data_source')}")
    print(f"✓ Synthetic flag: {report.get('synthetic')} (confirmed REAL data)")
    print(f"✓ Created: {report.get('created_utc')}")
    print(f"✓ Rows: {report.get('n_rows'):,}")
    print(f"✓ Date range: {report.get('date_min')} to {report.get('date_max')}")
    print()
    
    return report


def main():
    """Run data gate check as standalone script."""
    print("Running data gate check...")
    
    report = assert_real_data()
    
    print("✓ All checks passed")
    print(f"✓ Training may proceed with {report.get('n_rows'):,} rows of real data")
    print()


if __name__ == "__main__":
    main()
