# AMA-2: Iceberg Selection Summary

## Selection Criteria

**Cape Town to Maitri Shipping Corridor**
- **Latitude**: -72° to -30° S
- **Longitude**: -20° to 60° E
- **Date Range**: 1993-01-01 to 2021-12-31
- **Minimum Positions**: 10 per iceberg

## Results

### Overview
- **Total Icebergs Selected**: 61
- **Total Positions**: 28,107
- **Date Range**: 1995-08-20 to 2021-12-31
- **Consecutive Position Pairs** (training rows): 28,046

### Positions per Year

| Year | Count |
|------|-------|
| 1995 | 17 |
| 1997 | 61 |
| 1998 | 15 |
| 2001 | 179 |
| 2004 | 84 |
| 2005 | 245 |
| 2006 | 441 |
| 2007 | 608 |
| 2008 | 654 |
| 2010 | 1,920 |
| 2011 | 1,996 |
| 2012 | 2,192 |
| 2013 | 826 |
| 2014 | 2,705 |
| 2015 | 3,607 |
| 2016 | 3,059 |
| 2017 | 1,661 |
| 2018 | 1,798 |
| 2019 | 1,403 |
| 2020 | 1,503 |
| 2021 | 3,133 |

### Size Classes

| Class | Icebergs |
|-------|----------|
| Giant | 15 |
| Large | 14 |
| Medium | 52 |
| Small | 22 |

### Top 10 Icebergs by Position Count

| Rank | Iceberg ID | Positions | Size Class |
|------|------------|-----------|------------|
| 1 | D20A | 3,226 | Medium |
| 2 | B15AB | 2,078 | Medium |
| 3 | B09G | 2,063 | Large |
| 4 | B15G | 1,644 | Giant |
| 5 | B15T | 1,636 | Medium |
| 6 | D26 | 1,559 | Medium |
| 7 | B15R | 1,144 | Medium |
| 8 | UK235 | 963 | Small |
| 9 | UK326 | 922 | Small |
| 10 | UK325 | 875 | Small |

## Files Generated

1. `selected_icebergs.csv` - One row per iceberg with summary stats
2. `selected_positions.csv` - All 28,107 positions of selected icebergs
3. `ama2_summary.md` - This file

## Next Steps (AMA-3)

Run `ama2_define_region.py` to:
- Calculate actual bounding box from selected positions
- Add buffer for environmental data download
- Generate `download_config.yaml`

---

**Generated**: 2026-11-05 13:34:13
