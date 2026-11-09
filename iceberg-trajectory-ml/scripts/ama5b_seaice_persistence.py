#!/usr/bin/env python3
"""
AMA-5b: Sea Ice Persistence Baseline Model
CryoNav AI - Iceberg Trajectory ML

This script evaluates a naive persistence forecast for sea ice concentration:
"Tomorrow's sea ice concentration = Today's sea ice concentration"

This is a BASELINE model that any ML approach must beat to be considered useful.
NO ACCURACY CLAIMS are made here — only raw error metrics are reported.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================================
# TERMINAL FORMATTING
# ============================================================================

def print_header(text):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(text.upper())
    print("=" * 80)

def print_stat(label, value):
    """Print a labeled statistic."""
    print(f"  {label:.<50} {value}")

def print_success(text):
    """Print a success message."""
    print(f"✓ {text}")


# ============================================================================
# DATA LOADING
# ============================================================================

def load_training_data(data_dir, test_mode=False):
    """
    Load training table and filter for persistence baseline.
    
    Args:
        data_dir: Path to data directory
        test_mode: If True, use only 2015 data
    
    Returns:
        DataFrame with filtered data
    """
    print_header("LOADING TRAINING DATA")
    
    csv_path = data_dir / "training_table.csv"
    if not csv_path.exists():
        print(f"ERROR: Training table not found at {csv_path}")
        print("Run this command first:")
        print("  python iceberg-trajectory-ml/scripts/ama5_build_training_table.py")
        sys.exit(1)
    
    df = pd.read_csv(csv_path, parse_dates=['date', 'date_next'])
    print_stat("Total rows loaded", f"{len(df):,}")
    
    if test_mode:
        df = df[df['year'] == 2015].copy()
        print_stat("Filtered to 2015 (test mode)", f"{len(df):,}")
    
    # Filter for persistence baseline
    print_header("FILTERING FOR PERSISTENCE BASELINE")
    initial_count = len(df)
    
    # Keep only consecutive-day pairs
    df = df[df['dt_days'] == 1].copy()
    print_stat("After dt_days == 1 filter", f"{len(df):,} ({100*len(df)/initial_count:.1f}%)")
    
    # Keep only rows with valid current siconc
    df = df[df['siconc'].notna()].copy()
    print_stat("After siconc not NaN filter", f"{len(df):,} ({100*len(df)/initial_count:.1f}%)")
    
    # Exclude outliers
    df = df[df['outlier_flag'] == False].copy()
    print_stat("After outlier_flag == False filter", f"{len(df):,} ({100*len(df)/initial_count:.1f}%)")
    
    return df


# ============================================================================
# PERSISTENCE FORECAST
# ============================================================================

def build_persistence_forecast(df):
    """
    Build persistence forecast: tomorrow's siconc = today's siconc.
    
    Args:
        df: Filtered training data
    
    Returns:
        DataFrame with predictions and actuals
    """
    print_header("BUILDING PERSISTENCE FORECAST")
    
    # The "predicted" siconc for tomorrow is today's siconc
    df['siconc_predicted'] = df['siconc']
    
    # To get the "actual" siconc for tomorrow, we need the next day's observation
    # Join on (iceberg_id, date_next) matching to (iceberg_id, date)
    
    # Create a lookup table: for each (iceberg_id, date), what is the siconc?
    siconc_lookup = df[['iceberg_id', 'date', 'siconc']].copy()
    siconc_lookup = siconc_lookup.rename(columns={'date': 'date_next', 'siconc': 'siconc_actual'})
    
    # Merge to get tomorrow's actual siconc
    forecast_df = df[['iceberg_id', 'date', 'date_next', 'lat', 'lon', 'year', 'month', 
                      'siconc', 'siconc_predicted']].copy()
    forecast_df = forecast_df.merge(siconc_lookup, on=['iceberg_id', 'date_next'], how='left')
    
    print_stat("Rows before merge", f"{len(df):,}")
    print_stat("Rows after merge", f"{len(forecast_df):,}")
    
    # Drop rows where tomorrow's actual siconc is NaN
    initial_count = len(forecast_df)
    forecast_df = forecast_df[forecast_df['siconc_actual'].notna()].copy()
    print_stat("Rows with valid actual siconc", f"{len(forecast_df):,} ({100*len(forecast_df)/initial_count:.1f}%)")
    
    # Compute error
    forecast_df['error'] = forecast_df['siconc_predicted'] - forecast_df['siconc_actual']
    
    # Rename siconc to siconc_today for clarity
    forecast_df = forecast_df.rename(columns={'siconc': 'siconc_today'})
    
    return forecast_df


# ============================================================================
# ERROR METRICS
# ============================================================================

def compute_metrics(df):
    """
    Compute error metrics for persistence forecast.
    
    Args:
        df: DataFrame with 'error' column
    
    Returns:
        dict of metrics
    """
    errors = df['error'].values
    abs_errors = np.abs(errors)
    
    metrics = {
        'n': len(df),
        'mae': np.mean(abs_errors),
        'rmse': np.sqrt(np.mean(errors**2)),
        'bias': np.mean(errors),
        'within_0.1': np.sum(abs_errors <= 0.1),
        'within_0.2': np.sum(abs_errors <= 0.2),
    }
    
    return metrics


def print_metrics(metrics, label="OVERALL"):
    """Print metrics in a formatted table."""
    print(f"\n{label}:")
    print_stat("Predictions", f"{metrics['n']:,}")
    print_stat("MAE (Mean Absolute Error)", f"{metrics['mae']:.4f}")
    print_stat("RMSE (Root Mean Squared Error)", f"{metrics['rmse']:.4f}")
    print_stat("Mean Bias", f"{metrics['bias']:+.4f}")
    print_stat("Within 0.1 of actual", f"{metrics['within_0.1']:,} ({100*metrics['within_0.1']/metrics['n']:.1f}%)")
    print_stat("Within 0.2 of actual", f"{metrics['within_0.2']:,} ({100*metrics['within_0.2']/metrics['n']:.1f}%)")


# ============================================================================
# BREAKDOWN ANALYSIS
# ============================================================================

def add_season(df):
    """Add season column (DJF, MAM, JJA, SON)."""
    month_to_season = {
        12: 'DJF', 1: 'DJF', 2: 'DJF',  # Summer
        3: 'MAM', 4: 'MAM', 5: 'MAM',    # Autumn
        6: 'JJA', 7: 'JJA', 8: 'JJA',    # Winter
        9: 'SON', 10: 'SON', 11: 'SON'   # Spring
    }
    df['season'] = df['month'].map(month_to_season)
    return df


def add_ice_regime(df):
    """Add ice regime column based on siconc_today."""
    def classify_ice(siconc):
        if siconc < 0.15:
            return 'open_water'
        elif siconc <= 0.80:
            return 'marginal'
        else:
            return 'pack_ice'
    
    df['ice_regime'] = df['siconc_today'].apply(classify_ice)
    return df


def breakdown_by_category(df, category_col, category_name):
    """
    Break down metrics by a categorical variable.
    
    Args:
        df: DataFrame with errors
        category_col: Column name to group by
        category_name: Human-readable name
    
    Returns:
        DataFrame with metrics per category
    """
    print_header(f"BREAKDOWN BY {category_name.upper()}")
    
    categories = df[category_col].unique()
    results = []
    
    for cat in sorted(categories):
        cat_df = df[df[category_col] == cat]
        metrics = compute_metrics(cat_df)
        metrics['category'] = cat
        results.append(metrics)
        print_metrics(metrics, label=cat)
    
    return pd.DataFrame(results)


# ============================================================================
# OUTPUT GENERATION
# ============================================================================

def save_outputs(forecast_df, season_df, regime_df, overall_metrics, data_dir, test_mode=False):
    """
    Save results and report.
    
    Args:
        forecast_df: DataFrame with all predictions
        season_df: Metrics by season
        regime_df: Metrics by ice regime
        overall_metrics: Overall metrics dict
        data_dir: Output directory
        test_mode: If True, add _test suffix
    """
    print_header("SAVING OUTPUTS")
    
    suffix = "_test" if test_mode else ""
    
    # Save detailed results CSV
    results_cols = ['iceberg_id', 'date', 'siconc_today', 'siconc_predicted', 'siconc_actual', 'error']
    results_file = data_dir / f"seaice_persistence_results{suffix}.csv"
    forecast_df[results_cols].to_csv(results_file, index=False)
    print_success(f"Saved {results_file.name}")
    
    # Build markdown report
    md_content = f"""# Sea Ice Persistence Baseline

**BASELINE MODEL — Persistence Forecast**

This is a naive baseline that assumes tomorrow's sea ice concentration equals today's value.
This represents the minimum benchmark any ML model must beat to demonstrate predictive skill.

**NO ACCURACY CLAIMS**: Only raw error metrics are reported below.

---

## Model Description

**Forecast Rule**: `siconc(tomorrow) = siconc(today)`

This is the simplest possible forecast. It assumes no change in sea ice concentration from one day to the next.

---

## Dataset

- **Total predictions**: {overall_metrics['n']:,}
- **Filters applied**:
  - Only consecutive-day pairs (dt_days = 1)
  - Valid sea ice concentration at current position
  - GPS outliers excluded (outlier_flag = False)
  - Valid sea ice concentration at next position

---

## Error Metrics (Overall)

| Metric | Value |
|--------|-------|
| MAE (Mean Absolute Error) | {overall_metrics['mae']:.4f} |
| RMSE (Root Mean Squared Error) | {overall_metrics['rmse']:.4f} |
| Mean Bias | {overall_metrics['bias']:+.4f} |
| Within 0.1 of actual | {overall_metrics['within_0.1']:,} ({100*overall_metrics['within_0.1']/overall_metrics['n']:.1f}%) |
| Within 0.2 of actual | {overall_metrics['within_0.2']:,} ({100*overall_metrics['within_0.2']/overall_metrics['n']:.1f}%) |

**Interpretation**:
- MAE = average absolute difference between forecast and actual
- RMSE = penalizes larger errors more heavily than MAE
- Bias > 0 means the model over-predicts siconc on average
- Bias < 0 means the model under-predicts siconc on average

---

## Breakdown by Season

| Season | N | MAE | RMSE | Bias | Within 0.1 |
|--------|---|-----|------|------|------------|
"""
    
    for _, row in season_df.iterrows():
        md_content += f"| {row['category']} | {row['n']:,} | {row['mae']:.4f} | {row['rmse']:.4f} | {row['bias']:+.4f} | {row['within_0.1']:,} ({100*row['within_0.1']/row['n']:.1f}%) |\n"
    
    md_content += f"""
**Seasons**:
- DJF = Dec-Jan-Feb (Austral Summer)
- MAM = Mar-Apr-May (Austral Autumn)
- JJA = Jun-Jul-Aug (Austral Winter)
- SON = Sep-Oct-Nov (Austral Spring)

---

## Breakdown by Ice Regime

| Regime | N | MAE | RMSE | Bias | Within 0.1 |
|--------|---|-----|------|------|------------|
"""
    
    for _, row in regime_df.iterrows():
        md_content += f"| {row['category']} | {row['n']:,} | {row['mae']:.4f} | {row['rmse']:.4f} | {row['bias']:+.4f} | {row['within_0.1']:,} ({100*row['within_0.1']/row['n']:.1f}%) |\n"
    
    md_content += f"""
**Ice Regimes**:
- open_water: siconc < 0.15 (< 15% ice coverage)
- marginal: 0.15 ≤ siconc ≤ 0.80 (15-80% ice coverage)
- pack_ice: siconc > 0.80 (> 80% ice coverage)

---

## Key Findings

1. **Persistence is a reasonable short-term baseline**: Sea ice concentration changes relatively slowly over 1-day intervals.

2. **Seasonal variation**: Performance varies by season due to different ice dynamics (freeze/melt cycles).

3. **Ice regime dependence**: Errors may be higher in marginal ice zones where conditions change rapidly.

4. **This is the minimum benchmark**: Any ML model must achieve lower MAE/RMSE than this baseline to be considered useful.

---

## Data Integrity

✓ NO synthetic data (all values from real observations)  
✓ NO accuracy claims (raw error metrics only)  
✓ BASELINE model (minimum benchmark for ML models)

---

*Generated by: iceberg-trajectory-ml/scripts/ama5b_seaice_persistence.py*
"""
    
    # Save markdown report
    report_file = data_dir / f"seaice_persistence_report{suffix}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print_success(f"Saved {report_file.name}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Sea ice persistence baseline for CryoNav",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test mode (2015 only)
  python ama5b_seaice_persistence.py --test
  
  # Full dataset
  python ama5b_seaice_persistence.py
"""
    )
    parser.add_argument('--test', action='store_true', 
                       help='Test mode: use only 2015 data')
    
    args = parser.parse_args()
    
    # Print header
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "AMA-5b: Sea Ice Persistence Baseline" + " " * 22 + "║")
    print("║" + " " * 20 + "CryoNav AI - Iceberg Trajectory ML" + " " * 24 + "║")
    print("╚" + "=" * 78 + "╝")
    
    if args.test:
        print("\nTEST MODE: Using 2015 data only")
    
    # Set up paths
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data" / "validation"
    
    # Load data
    df = load_training_data(data_dir, test_mode=args.test)
    
    if len(df) == 0:
        print("\nERROR: No data remaining after filters")
        sys.exit(1)
    
    # Build persistence forecast
    forecast_df = build_persistence_forecast(df)
    
    if len(forecast_df) == 0:
        print("\nERROR: No valid forecasts generated")
        sys.exit(1)
    
    # Compute overall metrics
    print_header("ERROR METRICS")
    overall_metrics = compute_metrics(forecast_df)
    print_metrics(overall_metrics, label="OVERALL")
    
    # Add categorical variables
    forecast_df = add_season(forecast_df)
    forecast_df = add_ice_regime(forecast_df)
    
    # Breakdown by season
    season_df = breakdown_by_category(forecast_df, 'season', 'season')
    
    # Breakdown by ice regime
    regime_df = breakdown_by_category(forecast_df, 'ice_regime', 'ice regime')
    
    # Save outputs
    save_outputs(forecast_df, season_df, regime_df, overall_metrics, data_dir, test_mode=args.test)
    
    # Final summary
    print_header("COMPLETE")
    print_stat("Total predictions", f"{overall_metrics['n']:,}")
    print_stat("MAE", f"{overall_metrics['mae']:.4f}")
    print_stat("RMSE", f"{overall_metrics['rmse']:.4f}")
    print_stat("Output directory", str(data_dir))
    
    print("\n" + "=" * 80)
    print("✓ Persistence baseline computed successfully")
    print("=" * 80)
    print("\nThis is a BASELINE model. Any ML approach must beat these metrics.")
    print("Next steps:")
    print("  1. Review seaice_persistence_report.md")
    print("  2. Use these metrics as the minimum benchmark for ML models")
    print("  3. Proceed to AMA-6 (ML model development)")
    print()


if __name__ == "__main__":
    main()
