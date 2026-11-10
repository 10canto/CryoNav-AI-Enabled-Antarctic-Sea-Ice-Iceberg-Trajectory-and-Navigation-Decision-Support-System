#!/usr/bin/env python3
"""
Export AMA-6 Split Manifest
CryoNav AI - Iceberg Trajectory ML

PURPOSE:
    Generate ama6_split_manifest.json so collaborators can cross-reference
    their iceberg IDs against our AMA-6 train/test split and avoid leakage.

INPUT:
    - iceberg-trajectory-ml/data/validation/training_table.csv

OUTPUT:
    - iceberg-trajectory-ml/data/validation/ama6_split_manifest.json

USAGE:
    This manifest helps external evaluators (e.g., Srilatha) determine:
    1. Which icebergs were in AMA-6 training (temporal or spatial)
    2. Which icebergs are safe for independent evaluation
    3. How to avoid data leakage when comparing models
"""

import json
from pathlib import Path
from datetime import datetime

import pandas as pd


def print_header(title):
    """Print section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def load_training_table(data_dir):
    """Load training table and extract iceberg IDs."""
    print_header("LOADING TRAINING TABLE")
    
    csv_path = data_dir / "validation" / "training_table.csv"
    
    if not csv_path.exists():
        print(f"ERROR: Training table not found: {csv_path}")
        print("\nRun AMA-5 first to build the training table:")
        print("  python iceberg-trajectory-ml/scripts/ama5_build_training_table.py")
        import sys
        sys.exit(1)
    
    df = pd.read_csv(csv_path)
    
    print(f"  Total rows: {len(df):,}")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    
    # Extract unique iceberg IDs
    iceberg_ids = df['iceberg_id'].unique()
    print(f"  Unique icebergs: {len(iceberg_ids)}")
    
    return df, iceberg_ids


def apply_temporal_split(df, temporal_cutoff="2017-12-31"):
    """Apply temporal split logic from AMA-6."""
    print_header("TEMPORAL SPLIT")
    print(f"  Cutoff date: {temporal_cutoff}")
    
    # Convert date column to datetime for comparison
    df['date'] = pd.to_datetime(df['date'])
    cutoff_date = pd.to_datetime(temporal_cutoff)
    
    # Find icebergs in each period
    train_mask = df['date'] <= cutoff_date
    test_mask = df['date'] >= pd.to_datetime("2018-01-01")
    
    train_ids = set(df[train_mask]['iceberg_id'].unique())
    test_ids = set(df[test_mask]['iceberg_id'].unique())
    
    # Categorize icebergs
    train_only_ids = train_ids - test_ids
    test_only_ids = test_ids - train_ids
    both_periods_ids = train_ids & test_ids
    
    print(f"\n  Train period (<=2017):")
    print(f"    Icebergs with data: {len(train_ids)}")
    print(f"    Train-only: {len(train_only_ids)}")
    
    print(f"\n  Test period (2018+):")
    print(f"    Icebergs with data: {len(test_ids)}")
    print(f"    Test-only: {len(test_only_ids)}")
    
    print(f"\n  Both periods:")
    print(f"    Icebergs spanning cutoff: {len(both_periods_ids)}")
    
    return {
        'train_ids': sorted(list(train_ids)),
        'test_ids': sorted(list(test_ids)),
        'train_only_ids': sorted(list(train_only_ids)),
        'test_only_ids': sorted(list(test_only_ids)),
        'both_periods_ids': sorted(list(both_periods_ids))
    }


def apply_spatial_split(iceberg_ids):
    """Apply spatial split logic from AMA-6."""
    print_header("SPATIAL SPLIT")
    
    # Hardcoded 10 held-out IDs from AMA-6
    spatial_held_out = [
        "B15T", "B09G", "C19A", "D15A", "A23A",
        "B15G", "D20A", "B15AB", "C16A", "B09B"
    ]
    
    print(f"  Spatial held-out IDs (from AMA-6): {len(spatial_held_out)}")
    
    # Check which held-out IDs are actually in the data
    iceberg_ids_set = set(iceberg_ids)
    found_ids = [iid for iid in spatial_held_out if iid in iceberg_ids_set]
    not_found_ids = [iid for iid in spatial_held_out if iid not in iceberg_ids_set]
    
    print(f"  Found in training table: {len(found_ids)}")
    if not_found_ids:
        print(f"  Not found in training table: {len(not_found_ids)}")
        print(f"    Missing IDs: {', '.join(not_found_ids)}")
    
    return {
        'held_out_ids': spatial_held_out,
        'not_found_in_data': not_found_ids
    }


def export_split_manifest():
    """Main execution: generate split manifest."""
    print_header("EXPORT AMA-6 SPLIT MANIFEST")
    print("CryoNav AI - Iceberg Trajectory ML")
    print("\nPurpose: Help collaborators avoid data leakage when comparing models")
    
    # Set up paths
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    
    # Load training table
    df, iceberg_ids = load_training_table(data_dir)
    
    # Apply temporal split
    temporal_cutoff = "2017-12-31"
    temporal_split = apply_temporal_split(df, temporal_cutoff)
    
    # Apply spatial split
    spatial_split = apply_spatial_split(iceberg_ids)
    
    # Build manifest
    print_header("BUILDING MANIFEST")
    
    manifest = {
        "purpose": "AMA-6 train/test split manifest for cross-referencing. Use this to avoid data leakage when evaluating models on overlapping iceberg IDs.",
        "temporal_cutoff": temporal_cutoff,
        "total_iceberg_ids": len(iceberg_ids),
        "temporal_split": {
            "train_period": "1995-2017",
            "test_period": "2018-2021",
            "train_iceberg_ids": temporal_split['train_ids'],
            "test_iceberg_ids": temporal_split['test_ids'],
            "train_only_ids": temporal_split['train_only_ids'],
            "test_only_ids": temporal_split['test_only_ids'],
            "both_periods_ids": temporal_split['both_periods_ids']
        },
        "spatial_split": {
            "held_out_ids": spatial_split['held_out_ids'],
            "not_found_in_data": spatial_split['not_found_in_data']
        },
        "leakage_guidance": {
            "safe_to_evaluate": "Icebergs in test_only_ids during 2018-2021 were NOT in AMA-6 training.",
            "leakage_risk": "Icebergs in train_only_ids during <=2017 WERE in AMA-6 training. Do not use these for independent evaluation against AMA-6 predictions.",
            "spatial_safe": "Any iceberg NOT in spatial_held_out was in AMA-6 spatial training. Hold out different IDs for independent spatial evaluation."
        },
        "generated_from": "training_table.csv",
        "generated_at": datetime.utcnow().isoformat() + 'Z'
    }
    
    print(f"  Total iceberg IDs: {manifest['total_iceberg_ids']}")
    print(f"  Train period IDs: {len(temporal_split['train_ids'])}")
    print(f"  Test period IDs: {len(temporal_split['test_ids'])}")
    print(f"  Train-only IDs: {len(temporal_split['train_only_ids'])}")
    print(f"  Test-only IDs: {len(temporal_split['test_only_ids'])}")
    print(f"  Both periods IDs: {len(temporal_split['both_periods_ids'])}")
    print(f"  Spatial held-out IDs: {len(spatial_split['held_out_ids'])}")
    
    # Save manifest
    print_header("SAVING MANIFEST")
    
    output_path = data_dir / "validation" / "ama6_split_manifest.json"
    
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    file_size_kb = output_path.stat().st_size / 1024
    
    print(f"  Manifest saved: {output_path}")
    print(f"  File size: {file_size_kb:.1f} KB")
    
    # Print example usage
    print_header("USAGE EXAMPLE")
    print("""
To check if an iceberg ID was in AMA-6 training:

    import json
    
    with open('ama6_split_manifest.json') as f:
        manifest = json.load(f)
    
    iceberg_id = "B15T"
    
    # Check temporal split
    if iceberg_id in manifest['temporal_split']['train_only_ids']:
        print(f"{iceberg_id} was ONLY in AMA-6 training (<=2017)")
        print("⚠️ LEAKAGE RISK if evaluating on <=2017 data")
    
    elif iceberg_id in manifest['temporal_split']['test_only_ids']:
        print(f"{iceberg_id} was ONLY in AMA-6 test (2018+)")
        print("✓ SAFE for independent evaluation on 2018+ data")
    
    elif iceberg_id in manifest['temporal_split']['both_periods_ids']:
        print(f"{iceberg_id} spans both periods")
        print("Use date-specific logic to avoid leakage")
    
    # Check spatial split
    if iceberg_id in manifest['spatial_split']['held_out_ids']:
        print(f"{iceberg_id} was held out in AMA-6 spatial split")
        print("✓ SAFE for independent spatial evaluation")
    else:
        print(f"{iceberg_id} was in AMA-6 spatial training")
        print("⚠️ LEAKAGE RISK for spatial evaluation")
    """)
    
    print_header("COMPLETE")
    print("  Split manifest exported successfully")
    print(f"  Output: {output_path.name}")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    export_split_manifest()
