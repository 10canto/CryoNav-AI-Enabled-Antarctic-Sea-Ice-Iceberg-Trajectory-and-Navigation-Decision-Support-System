
"""
AMA-2: Preliminary historical iceberg selection.

Source:
DA.*A/consolidated_database_v8.0/updated7_consol/

Rules:
- Historical period: 1993-2021
- At least 10 distinct actual observation dates
- NIC/SASS observation flag must equal 1
- Invalid coordinates (0,0) are excluded

.*he geographical corridor and size-class classification
must be confirmed before final selection.
"""

import csv
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median


PROJECT_DIR = Path(__file__).resolve().parent
REPO_ROOT = PROJECT_DIR.parent

SOURCE_DIR = (
    REPO_ROOT
    / "DATA"
    / "consolidated_database_v8.0"
    / "updated7_consol"
)

OUTPUT_DIR = PROJECT_DIR / "data" / "validation"

START_YEAR = 1993
END_YEAR = 2021
MIN_OBSERVATION_DAYS = 10

SENSORS = ("nic", "sass", "qscat", "seawinds")


def parse_date(value):
    """Convert YYYYDDD date into a Python date."""
    value = str(value).strip()

    if len(value) != 7 or not value.isdigit():
        return None

    year = int(value[:4])
    day_of_year = int(value[4:])

    if not START_YEAR - 15 <= year <= END_YEAR + 15:
        return None

    days_in_year = (
        datetime(year + 1, 1, 1) - datetime(year, 1, 1)
    ).days

    if not 1 <= day_of_year <= days_in_year:
        return None

    return (
        datetime(year, 1, 1) + timedelta(days=day_of_year - 1)
    ).date()


def number(value):
    """Safely convert a value into a float."""
    try:
        result = float(value)
        return result if result == result else None
    except (TypeError, ValueError):
        return None


def valid_coordinates(lat, lon):
    """Check that coordinates are valid and not missing."""
    if lat is None or lon is None:
        return False

    return (
        -90 <= lat <= 90
        and -180 <= lon <= 180
        and not (lat == 0 and lon == 0)
    )


def process_iceberg(file_path):
    iceberg_id = file_path.stem.upper()

    actual_dates = set()
    interpolated_dates = set()
    corridor_dates = set()
    latitude_values = []
    longitude_values = []
    size_1_values = []
    size_2_values = []

    row_count = 0

    with file_path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("CSV has no header")

        for row in reader:
            row_count += 1

            row = {
                str(k).strip().lower(): v
                for k, v in row.items()
                if k is not None
            }

            observation_date = parse_date(row.get("date"))

            if observation_date is None:
                continue

            if not START_YEAR <= observation_date.year <= END_YEAR:
                continue
            regional_actual_found = False

            for sensor in SENSORS:
                lat = number(row.get(f"{sensor}_1"))
                lon = number(row.get(f"{sensor}_2"))
                flag = number(row.get(f"{sensor}_3"))

                if not valid_coordinates(lat, lon):
                    continue



                if flag == 1:
                    actual_dates.add(observation_date)
                    latitude_values.append(lat)
                    longitude_values.append(lon)

                    # Cape Town-to-Maitri region
                    if (
                        -72.0 <= lat <= -30.0
                        and -15.0 <= lon <= 40.0
                    ):
                        corridor_dates.add(observation_date)
                        regional_actual_found = True

                elif flag == 0:
                    interpolated_dates.add(observation_date)


            for field, values in (
                ("size_1", size_1_values),
                ("size_2", size_2_values),
            ):
                value = number(row.get(field))
                if value is not None and value > 0:
                    values.append(value)

    dates = sorted(actual_dates)
    corridor_dates_sorted = sorted(corridor_dates)

    return {
        "iceberg_id": iceberg_id,
        "source_file": file_path.name,
        "total_records": row_count,
        "actual_observation_days": len(actual_dates),
        "corridor_observation_days": len(corridor_dates),
        "corridor_first_observation": (
    corridor_dates_sorted[0].isoformat()
    if corridor_dates_sorted else ""
),
"corridor_last_observation": (
    corridor_dates_sorted[-1].isoformat()
    if corridor_dates_sorted else ""
),
        "interpolated_days": len(interpolated_dates),
        "first_observation": dates[0].isoformat() if dates else "",
        "last_observation": dates[-1].isoformat() if dates else "",
        "years_observed": ",".join(
            str(year) for year in sorted({d.year for d in dates})
        ),
        "corridor_years_observed": ",".join(
    str(year) for year in sorted(
        {d.year for d in corridor_dates_sorted}
    )
),
        "latitude_min": min(latitude_values) if latitude_values else "",
        "latitude_max": max(latitude_values) if latitude_values else "",
        "longitude_min": min(longitude_values) if longitude_values else "",
        "longitude_max": max(longitude_values) if longitude_values else "",
        "size_1_measurement_count": len(size_1_values),
        "size_2_measurement_count": len(size_2_values),
    "size_1_median_raw": median(size_1_values) if size_1_values else "",
    "size_2_median_raw": median(size_2_values) if size_2_values else "",
    "size_1_median_km": round(median(size_1_values) * 1.852, 3) if size_1_values else "",
    "size_2_median_km": round(median(size_2_values) * 1.852, 3) if size_2_values else "",
    "representative_length_m": round(median(size_1_values) * 1852, 2) if size_1_values else "",
    "size_class": (
        "UNKNOWN" if not size_1_values else
        "Small" if median(size_1_values) * 1852 < 60 else
        "Medium" if median(size_1_values) * 1852 < 120 else
                "Large" if median(size_1_values) * 1852 <= 200 else
                "Very Large"
            ),
        "selection_status": (
            "PRELIMINARY_CANDIDATE"
            if len(corridor_dates) >= MIN_OBSERVATION_DAYS
            else "NOT_ELIGIBLE"
        ),
    }


def main():
    if not SOURCE_DIR.is_dir():
        raise FileNotFoundError(
            f"Historical database folder not found: {SOURCE_DIR}"
        )

    files = sorted(
        p for p in SOURCE_DIR.glob("*.csv")
        if p.is_file()
    )

    if not files:
        raise FileNotFoundError(
            f"No CSV files found in {SOURCE_DIR}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summaries = []
    errors = []

    print(f"Source folder: {SOURCE_DIR}")
    print(f"CSV files found: {len(files)}")
    print("Scanning historical iceberg tracks...\n")

    for index, file_path in enumerate(files, start=1):
        try:
            summaries.append(process_iceberg(file_path))
        except Exception as exc:
            errors.append({
                "source_file": file_path.name,
                "error": str(exc),
            })

        if index % 100 == 0:
            print(f"Processed {index}/{len(files)} files")

    eligible = [
        item for item in summaries
       if item["corridor_observation_days"] >= MIN_OBSERVATION_DAYS]


    candidates_path = OUTPUT_DIR / "selected_icebergs.csv"
    all_path = OUTPUT_DIR / "iceberg_scan_all.csv"
    errors_path = OUTPUT_DIR / "scan_errors.csv"
    years_path = OUTPUT_DIR / "iceberg_year_counts.csv"
    coverage_path = OUTPUT_DIR / "data_coverage_report.md"

    fieldnames = list(summaries[0].keys()) if summaries else []

    with all_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)

    with candidates_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(eligible)

    with errors_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["source_file", "error"]
        )
        writer.writeheader()
        writer.writerows(errors)

    year_counts = {}

    for item in eligible:
        for year in item["corridor_years_observed"].split(","):
            if year:
                year_counts.setdefault(year, set()).add(
                    item["iceberg_id"]
                )

    with years_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["year", "eligible_iceberg_count"])

        for year in sorted(year_counts):
            writer.writerow([year, len(year_counts[year])])
      # Build final AMA-2 data coverage report
    size_class_order = ["Small", "Medium", "Large", "Very Large", "UNKNOWN"]
    size_class_counts = {name: 0 for name in size_class_order}

    for item in eligible:
        size_class = item.get("size_class") or "UNKNOWN"
        size_class_counts.setdefault(size_class, 0)
        size_class_counts[size_class] += 1

    first_dates = [
        item["corridor_first_observation"]
        for item in eligible
        if item.get("corridor_first_observation")
    ]
    last_dates = [
        item["corridor_last_observation"]
        for item in eligible
        if item.get("corridor_last_observation")
    ]

    coverage_start = min(first_dates) if first_dates else "Not available"
    coverage_end = max(last_dates) if last_dates else "Not available"

    report_lines = [
        "# AMA-2: Iceberg Validation Data Coverage Report",
        "",
        "## Selection criteria",
        "- Historical period: 1993–2021",
        "- Geographic box: latitude -72 to -30, longitude -15 to 40",
        f"- Minimum actual regional observation days: {MIN_OBSERVATION_DAYS}",
        "- Representative size: median of available size_1 measurements",
        "- Source size unit: nautical miles; converted to metres using 1 NM = 1,852 m",
        "- Icebergs with missing size measurements are retained as UNKNOWN.",
        "",
        "## Dataset summary",
        f"- Files scanned: {len(files)}",
        f"- Successfully processed: {len(summaries)}",
        f"- Files with errors: {len(errors)}",
        f"- Selected icebergs: {len(eligible)}",
        f"- First regional observation: {coverage_start}",
        f"- Last regional observation: {coverage_end}",
        "",
        "## Size-class distribution",
        "| Size class | Number of icebergs |",
        "|---|---:|",
    ]

    for size_class in size_class_order:
        report_lines.append(
            f"| {size_class} | {size_class_counts[size_class]} |"
        )

    report_lines.extend([
        "",
        "## Year-wise iceberg counts",
        "| Year | Number of icebergs observed |",
        "|---|---:|",
    ])

    for year in sorted(year_counts):
        report_lines.append(
            f"| {year} | {len(year_counts[year])} |"
        )

    report_lines.extend([
        "",
        "## Individual iceberg size measurements",
        "| Iceberg ID | size_1 measurement count | Median size_1 (NM) | Representative length (m) | Size class |",
        "|---|---:|---:|---:|---|",
    ])

    for item in sorted(eligible, key=lambda x: x["iceberg_id"]):
        report_lines.append(
            f"| {item['iceberg_id']} "
            f"| {item.get('size_1_measurement_count', 0)} "
            f"| {item.get('size_1_median_raw', '')} "
            f"| {item.get('representative_length_m', '')} "
            f"| {item.get('size_class', 'UNKNOWN')} |"
        )

    report_lines.extend([
        "",
        "## Measurement notes",
        "- The measurement count indicates how many valid size_1 measurements "
        "were used to calculate each iceberg's median.",
        "- UNKNOWN means no valid size_1 measurement was available.",
        "- Size classes: Small <60 m; Medium 60 to <120 m; "
        "Large 120 to 200 m; Very Large >200 m.",
        "",
    ])

    with coverage_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print("\n========== AMA-2 PRELIMINARY RESULTS ==========")
    print(f"Files scanned: {len(files)}")
    print(f"Successfully processed: {len(summaries)}")
    print(f"Files with errors: {len(errors)}")
    print(f"Candidates with >=10 actual observation days: {len(eligible)}")
    print("\nOutputs:")
    print(candidates_path)
    print(all_path)
    print(years_path)
    print(errors_path)

    print("\nTeam leader confirmed the geographic corridor and size classifications.")
    print(f"Final coverage report: {coverage_path}")


if __name__ == "__main__":
    main()
