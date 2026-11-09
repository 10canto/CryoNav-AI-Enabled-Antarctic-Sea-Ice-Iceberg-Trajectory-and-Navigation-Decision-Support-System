# CryoNav AI — Pipeline Development Notes
## Branch: A-AMAR | SIH 26059

---

## 1. PROJECT OVERVIEW

- **Goal:** Build a data and ML pipeline for Antarctic iceberg trajectory prediction
- **Model type:** Gray-box hybrid (physics leeway drift + ML calibration via Ridge Regression)
- **Data sources:** BYU Antarctic Iceberg Database v8.0, Copernicus Marine GLORYS12, ERA5 reanalysis via CDS
- **Team lead:** Anto
- **Deadline:** 7 Nov checkpoint (training table), 14 Nov (full model)

---

## 2. ANTO'S RULES (STRICT)

- No synthetic data — all data must come from real observational sources
- No accuracy claims — no R², no percentage accuracy quotes
- No files over 10 MB in the repository
- Training script must refuse to run if data report flags SYNTHETIC
- No .nc files committed to the repository

---

## 3. AMA-3: OCEAN FORCING (COMPLETED)

### What was done
- Streamed ocean current and sea ice data from Copernicus Marine using the `copernicusmarine` Python package
- Dataset: `cmems_mod_glo_phy_my_0.083deg_P1D-m` (GLORYS12, 1/12° daily resolution)
- Variables extracted: uo, vo (ocean currents), siconc (sea ice concentration), usi, vsi (sea ice velocity)
- Method: streaming via `copernicusmarine.open_dataset()` — no files downloaded to disk
- Data extracted at iceberg positions only, not full grid, to keep file sizes small
- Processed year-by-year to stay under 8 GB RAM

### Output
- 21 individual yearly files: `forcing_ocean_{year}.csv`
- Combined file: `forcing_ocean_all.csv` (28,107 rows, ~3.4 MB)
- Valid data rates: uo/vo 92.7%, siconc 85.3%
- NaN values occur over land and ice shelves — physically correct, not errors

### Problems faced and solutions

**Problem 1: Script flag mismatch**
- The script only supported `--year` (single year), not `--start-year` / `--end-year`
- Solution: Used a PowerShell `ForEach-Object` loop to iterate through 1995–2021

**Problem 2: Six years failed (1996, 1999, 2000, 2002, 2003, 2009)**
- Initially suspected server throttling
- Investigation: Ran a groupby count on `selected_positions.csv` — these years had zero iceberg positions in the BYU database
- Conclusion: Failures were expected and harmless; no data existed to query

**Problem 3: Combined file overwrite bug (CRITICAL)**
- After the full loop, `forcing_ocean_all.csv` contained only 2021 data (3,134 lines instead of 28,108)
- Root cause: Each year's run overwrote the combined file instead of appending to it
- First fix attempt: Used wildcard `forcing_ocean_1*.csv` which only matched 19xx years (1995, 1997, 1998) — missed all 20xx files
- Final fix: Changed wildcard to `forcing_ocean_*.csv` and used PowerShell `Set-Content` for the first file and `Add-Content` with `Select-Object -Skip 1` for subsequent files
- Result: 28,108 lines (28,107 data rows + 1 header)

**Problem 4: Depth dimension mismatch**
- uo/vo variables had a `depth` dimension; siconc/usi/vsi did not
- Calling `.isel(depth=0)` on the full Dataset crashed
- Solution: Handle depth selection per-variable, not on the entire Dataset

---

## 4. AMA-4: WIND FORCING (IN PROGRESS → NEARLY COMPLETE)

### What was done
- Downloaded ERA5 wind data from the Copernicus Climate Data Store (CDS) using the `cdsapi` Python package
- Dataset: `reanalysis-era5-single-levels` (ERA5, 0.25° resolution)
- Variables: u10, v10 (10-meter wind components)
- Method: download temporary .nc file → extract values at iceberg positions → delete .nc immediately
- Time step: 12:00 UTC only (to match daily ocean data)
- Bounding box: lat -75 to -42, lon -23 to 63

### Output (as of latest check)
- 20 of 21 yearly files completed (1995–2020; 2021 remaining)
- Combined file: `forcing_wind_all.csv` (after manual fix)
- Test result: 372/372 (100%) valid, u10 range -17 to +11 m/s

### Problems faced and solutions

**Problem 1: CDS license not accepted**
- Error: `403 Forbidden — required licences not accepted`
- Solution: Manually visited the ERA5 dataset page on the CDS website and clicked "Accept" on the license agreement

**Problem 2: CDS API v2 dimension name mismatch**
- Downloaded data used dimension names `valid_time`, `latitude`, `longitude`
- Script expected `time`, `lat`, `lon`
- Result: All extracted values were NaN (0/372 valid)
- Solution: Added `ds.rename()` call after loading to map new names to expected names

**Problem 3: Monthly batching too slow**
- Original design: one CDS request per month (~252 requests)
- CDS queue time: 3–30 minutes per request during peak hours
- Estimated total: 13–42 hours
- Solution: Changed to yearly batching (all 12 months in one request) — reduced to 21 requests, estimated 1–2 hours

**Problem 4: CDS queue throttling ("protection measures")**
- CDS displayed a warning about "Data Stores Service protection measures"
- Requests stuck in "accepted" status for 3+ hours during peak hours (EU daytime)
- Solution: Let the script run overnight during off-peak hours; queue cleared dramatically after midnight

**Problem 5: WiFi adapter power management killed the connection**
- Error: `WinError 10013 — socket forbidden` followed by `getaddrinfo failed`
- Cause: Windows turned off the WiFi adapter to save power even though sleep was disabled
- Solution: Opened Device Manager → Network adapters → WiFi adapter → Power Management tab → unchecked "Allow the computer to turn off this device to save power"

**Problem 6: Combined file overwrite bug (same as AMA-3)**
- `forcing_wind_all.csv` contained only 2020 data
- Root cause: Identical to the ocean overwrite bug — script overwrote instead of appending
- Diagnosis: Ran `has_wind` check per year — only 2020 showed 1.0, all others 0.0
- Solution: Manual PowerShell combine using the same `Set-Content` / `Add-Content` approach
- Result: `complete_case` in training table jumped from ~1,000 to 19,859 (71.7%)

**Problem 7: Considered switching to Copernicus Marine wind**
- Due to CDS slowness, proposed switching to Copernicus Marine for wind data
- Anto initially approved
- Investigation: Copernicus Marine catalog does not have a historical u10/v10 product covering 1995–2021 at global scale
- Anto reversed approval; confirmed ERA5 is the correct source

---

## 5. AMA-5: TRAINING TABLE (COMPLETED — PARTIAL, PENDING FULL WIND)

### What was done
- Built a script (`ama5_build_training_table.py`) that joins positions + ocean + wind into a single training table
- Computes observed drift velocity (u_obs, v_obs) from consecutive BYU positions
- Handles variable time gaps between observations (dt_days, max 3 days)
- Flags outliers (speed > 2 m/s) without deleting them
- Never fills NaN values (respects Anto's no-synthetic-data rule)
- Outputs: `training_table.csv`, `data_report.json`, `data_summary.md`
- Created `data_gate.py` helper that blocks training if data is flagged synthetic

### Output
- 27,707 step pairs from 61 icebergs across 21 years
- 27 columns including identity, position, displacement, target velocities, forcing inputs, and quality flags
- File size: 6.3 MB (under 10 MB limit)
- Complete cases: 19,859 (71.7%) after wind combine fix; expected ~22,000 (80%+) after 2021 wind

### Problems faced and solutions

**Problem 1: JSON serialization error**
- Error: `TypeError: Object of type int32 is not JSON serializable` when writing `data_report.json`
- Cause: The `years_included` list contained numpy int32 values instead of native Python ints
- Solution: Kiro fixed by converting numpy types to native Python types before `json.dump()`

**Problem 2: Data gate false positive**
- `data_gate.py` warned about the word "synthetic" appearing in the report
- The report contained `"synthetic": false` which is a PASS, not a FAIL
- Cause: The gate searched for the string "synthetic" anywhere in the file without checking the boolean value
- Solution: Updated gate logic to check the actual boolean value of the `synthetic` key

---

## 6. GIT AND BRANCH ISSUES

### Problems faced and solutions

**Problem 1: .gitignore blocking all validation data**
- `git status` showed only scripts staged, not CSV/JSON/MD files
- Cause: Line 12 of `.gitignore` contained `iceberg-trajectory-ml/data/validation/` which ignored the entire folder
- Additionally, there were incorrect allow-rules for `iceberg-trajectory-ml/data/training_table.csv` (wrong path)
- Solution: Replaced the blanket ignore with specific rules: ignore only `*.nc` and `temp_*` files within the validation folder

**Problem 2: Branch name confusion**
- Anto initially suggested branch `AMA_ml`
- Actual working branch was `A-AMAR`
- Solution: Asked Anto directly; he confirmed to keep `A-AMAR` to avoid breaking tracking

---

## 7. 7 NOV CHECKPOINT (PASSED)

### Deliverables submitted
- Commit `55896ac` on branch `A-AMAR`
- `training_table.csv` (27,707 rows, 6.3 MB)
- `data_report.json` (synthetic: false)
- `data_summary.md`
- All pipeline scripts (AMA-3, AMA-4, AMA-5, data gate)
- Ocean forcing complete, wind forcing partial

### Anto's feedback
- Checkpoint passed
- Confirmed ERA5 is the correct wind source
- Approved AMA-5b persistence baseline for 8 Nov
- Noted date error (said "tomorrow 7 Nov" when it was already 7 Nov)

---

## 8. ARCHITECTURE DECISIONS

### Data access methods
- **Copernicus Marine (ocean):** Streaming via `copernicusmarine.open_dataset()` — data stays on server, only extracted values transferred
- **CDS (wind):** Download-extract-delete cycle — CDS does not support streaming; temporary .nc files downloaded, values extracted at iceberg positions, files deleted immediately

### Model architecture
- Physics component: Leeway drift equation (iceberg velocity = weighted sum of ocean current, sea ice drag, and wind push)
- ML component: Ridge Regression to learn coefficients and residual corrections from 27,707 observations
- Combined: Gray-box hybrid where physics provides structure and ML fills gaps

### Train/test splitting strategy
- Temporal split: Train on 1995–2018, test on 2019–2021 (no future data leakage)
- Spatial split: Hold out entire iceberg IDs to test generalization to unseen icebergs
- No random k-fold splitting (would cause data leakage due to temporal autocorrelation)

### Backup plans if model underperforms
- Plan A: Pure physics baseline with textbook coefficients
- Plan B: Add more features (SST, bathymetry, distance to coast, lag features)
- Plan C: Try non-linear models (Random Forest, XGBoost)
- Plan D: Separate models by season and region
- Plan E: Ensemble of multiple models
- Plan F: Honest reporting with comparison to published benchmarks

---

## 9. KEY LESSONS LEARNED

1. **Always verify combined files after loop-based processing.** The overwrite bug occurred twice (ocean and wind). Individual yearly files were always safe; only the combined file was affected.

2. **CDS queue times are highly variable.** Peak hours (EU daytime) can mean 3+ hour waits per request. Off-peak (2–6 AM UTC) drops to 2–5 minutes. Batch requests by year, not month.

3. **Disabling sleep is not enough for overnight runs.** WiFi adapter power management is a separate setting that must also be disabled in Device Manager.

4. **PowerShell wildcards are literal.** `1*.csv` matches files starting with "1" only, not all files. Use `*.csv` for everything.

5. **Date format consistency matters in merges.** Although the final diagnosis was the overwrite bug, date format mismatch was a plausible alternative cause that should be checked in future pipeline steps.

6. **NaN in ocean/ice data over land is physically correct.** Do not attempt to fill or interpolate these values — it would violate the no-synthetic-data rule.

7. **Data quality flags are for filtering, not for ML input.** Flags like `complete_case` and `has_wind` should be used to select training rows, never as features in the model.

---

## 10. CURRENT STATUS AND NEXT STEPS

| Task | Status | Notes |
|------|--------|-------|
| AMA-1 Accounts | ✅ Complete | Copernicus Marine + CDS verified |
| AMA-2 Iceberg selection | ✅ Complete | 61 icebergs, 28,107 positions |
| AMA-3 Ocean forcing | ✅ Complete | 28,107 rows, 21 years |
| AMA-4 Wind forcing | 🔄 20/21 years | 2021 remaining; ETA ~30 min |
| AMA-5 Training table | ✅ Partial | 19,859 complete cases; re-run after 2021 wind |
| AMA-5b Sea-ice forecast | 📋 Planned | Persistence baseline on siconc; 8 Nov |
| AMA-6 Model training | 📋 Not started | Ridge Regression + temporal/spatial CV |
| AMA-7 Evaluation | 📋 Not started | |
| AMA-8 Uncertainty + handoff | 📋 Not started | |





CRITICAL PATH RULE: All files MUST be inside the existing iceberg-trajectory-ml/ folder. Do NOT create nested iceberg-trajectory-ml/iceberg-trajectory-ml/ paths.

Create iceberg-trajectory-ml/docs/AMA5_DEBUG_LOG.md

This is a personal debugging journal for AMA-5 (Training Table Assembly). Write it in first person, honest and detailed. Format: numbered mistakes, each with What Happened, How I Found It, and How I Fixed It.

Use the content below EXACTLY (do not invent additional bugs):

---

# AMA-5 Debug Log — Training Table Assembly

**Pipeline Step:** AMA-5 (Combine ocean + wind + positions into training table)
**Dates:** Late October 2025
**Script:** `iceberg-trajectory-ml/scripts/ama5_build_training_table.py`
**Output:** `training_table.csv` — 27,707 step pairs, 27 columns, 7.2 MB

---

## Mistake 1: Kiro Created Nested Folders (Again)

**What happened:**
Kiro generated the script at `iceberg-trajectory-ml/iceberg-trajectory-ml/scripts/ama5_build_training_table.py` instead of `iceberg-trajectory-ml/scripts/`. This is a recurring bug across every AMA step.

**How I found it:**
The script couldn't find the input files because the relative paths were wrong. `FileNotFoundError: selected_positions.csv`.

**How I fixed it:**
Moved the file to the correct location. Added "CRITICAL PATH RULE" to every Kiro prompt from that point forward.

---

## Mistake 2: Date Type Mismatch on Join

**What happened:**
The positions CSV had dates as strings (`"2020-01-15"`), but after loading the ocean and wind CSVs with pandas, the date column was sometimes parsed as `datetime64` and sometimes left as `object` depending on the file. The `pd.merge()` on `(iceberg_id, date)` silently produced zero matches because `"2020-01-15" != Timestamp("2020-01-15")`.

**How I found it:**
The merged DataFrame had 0 rows. I printed `positions['date'].dtype` and `ocean['date'].dtype` and saw they were different.

**How I fixed it:**
Added explicit `df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')` on ALL input DataFrames before merging. This ensures consistent string format.

---

## Mistake 3: Forgot Cosine Correction for Longitude Drift

**What happened:**
When computing observed drift velocity from consecutive positions, I calculated:
u_obs = (lon2 - lon1) * 111000 / dt_seconds

text

This is wrong because 1° of longitude is NOT 111 km at high latitudes. At -65°S, 1° of longitude is only about 47 km (111 × cos(65°)). The u_obs values were inflated by roughly 2×.

**How I found it:**
I compared the speed distribution to known Antarctic iceberg drift speeds (typically 0-0.5 m/s). My values were averaging ~0.08 m/s but some icebergs showed 0.8 m/s which seemed too high. I plotted u_obs vs latitude and saw the error grew at higher latitudes — classic cosine bug.

**How I fixed it:**
Changed to:
u_obs = (lon2 - lon1) * 111000 * cos(radians(mean_lat)) / dt_seconds
v_obs = (lat2 - lat1) * 111000 / dt_seconds

text

Where `mean_lat = (lat1 + lat2) / 2`. After the fix, the speed distribution matched expectations: mean 0.039 m/s, 69% stationary.

---

## Mistake 4: Variable Time Gaps Broke Velocity Calculation

**What happened:**
BYU data is nominally daily, but there are gaps of 2-5 days when the satellite didn't capture a position. My initial code assumed dt = 1 day always:
u_obs = dx / 86400 # assumed 1 day

text

For a 3-day gap, this overestimated velocity by 3×.

**How I found it:**
I added a `dt_days` column and printed its distribution. Saw values of 1, 2, 3, 5, 12, and even 45 days. The 45-day gap had an iceberg "moving" at 2 m/s which is physically impossible.

**How I fixed it:**
- Computed `dt_days = (date2 - date1).days` for each consecutive pair
- Set `--max-dt 3` flag: pairs with gaps > 3 days are excluded from the training table
- Used actual `dt_seconds = dt_days * 86400` in the velocity formula
- This reduced the dataset from 28,107 positions to 27,707 valid step pairs (only ~400 lost, mostly from the 6 years with zero data)

---

## Mistake 5: D21A GPS Glitch — 10.55 m/s Outlier

**What happened:**
Iceberg D21A had a single position jump that implied a speed of 10.55 m/s (~911 km/day). No iceberg moves that fast. This was clearly a scatterometry glitch in the BYU database.

**How I found it:**
After fixing the cosine and dt bugs, I plotted the speed histogram. There was a clean distribution below 0.5 m/s and then one single point at 10.55 m/s. I filtered for `speed > 2 m/s` and found exactly 2 rows, both D21A on consecutive days.

**How I fixed it:**
- Flagged rows with `speed > 2 m/s` as outliers (added `is_outlier` column)
- Dropped the 2 D21A rows from the training table
- Did NOT delete them from the raw data — they're still in `selected_positions.csv` for transparency
- Added a note in `data_summary.md` explaining the exclusion

---

## Mistake 6: Temptation to Fill NaN (Anto's Rule 1)

**What happened:**
After joining positions + ocean + wind, about 18% of rows had NaN in siconc, usi, vsi (because the iceberg was over an ice shelf or near land where GLORYS12 has no data). My first instinct was `df.fillna(0)` or `df.fillna(method='ffill')` to make the dataset "clean" for ML.

**How I found it:**
I re-read Anto's rules: "No synthetic data. Flag any generated values." Filling NaN with 0 is generating fake data — it tells the model "there is zero ice here" when the truth is "we don't know." This would bias the model, especially for icebergs near the coast.

**How I fixed it:**
- Removed all `fillna()` calls
- Kept NaN as NaN in the training table
- The ML model (Ridge Regression in AMA-6) handles NaN by dropping incomplete rows during training (22,631 complete cases out of 27,707)
- Added `complete_cases` count to `data_report.json` so this is transparent

---

## Mistake 7: siconc Units Mismatch (Fraction vs Percentage)

**What happened:**
GLORYS12 returns siconc as a fraction (0.0 to 1.0). The ice weight formula `w(siconc) = clip((siconc - 0.6) / 0.3, 0, 1)` expects fraction input. But when I checked the demo sea-ice export (which converts to 0-100%), I realized that if someone accidentally fed percentage values into the training table, the ice weight would be `clip((85 - 0.6) / 0.3, 0, 1) = 1.0` for ALL ice-covered cells, destroying the gradient.

**How I found it:**
Code review before running AMA-6. I printed `training_table['siconc'].describe()` and confirmed max was 0.97 (fraction), not 97 (percentage). Close call.

**How I fixed it:**
- Added a validation check in the script: `assert df['siconc'].max() <= 1.5, "siconc appears to be in percentage, not fraction"`
- Added units documentation to `data_summary.md`

---

## Mistake 8: File Size Creep

**What happened:**
The initial training table with all 27 columns at full float64 precision was 9.8 MB — dangerously close to Anto's 10 MB limit. Adding even one more column would have broken the rule.

**How I found it:**
`Get-ChildItem` showed 9.8 MB. I realized that float64 is overkill for ocean currents measured to ~0.01 m/s precision.

**How I fixed it:**
- Downcast float columns to float32: `df[col] = df[col].astype('float32')`
- This halved the file size to 7.2 MB with no meaningful precision loss
- Added a file size check at the end of the script: `assert file_size < 10 * 1024 * 1024`

---

## Summary

| # | Mistake | Root Cause | Impact if Unfixed |
|---|---------|-----------|-------------------|
| 1 | Nested folders | Kiro IDE bug | Script can't find inputs |
| 2 | Date type mismatch | Inconsistent parsing | 0 rows after merge |
| 3 | Missing cos(lat) | Geometry oversight | 2× velocity error at high lat |
| 4 | Fixed dt=1 day | Data assumption | 3-45× velocity error on gaps |
| 5 | D21A GPS glitch | Bad source data | 10.55 m/s outlier corrupts model |
| 6 | fillna temptation | ML habit | Synthetic data, violates Rule 1 |
| 7 | siconc units | Unit confusion | Ice weight always 1.0 |
| 8 | File size | float64 waste | Breaks 10 MB repo rule |

**Lessons learned:**
- Always print `.dtype`, `.describe()`, and `.shape` after every merge
- Antarctic geometry is not Cartesian — always use cos(lat) for longitude
- Real data is messy — gaps, glitches, and NaN are features, not bugs
- Anto's "no synthetic data" rule saved us from at least two silent errors

---

Do NOT add any content beyond what is specified above. Do NOT invent additional bugs.

CRITICAL PATH RULE: All files MUST be inside the existing iceberg-trajectory-ml/ folder. Do NOT create nested iceberg-trajectory-ml/iceberg-trajectory-ml/ paths.

Create TWO files. Do NOT create any nested folders.

---

FILE 1: iceberg-trajectory-ml/docs/AMA6_DEBUG_LOG.md

Write this EXACTLY as specified below. First person, honest, detailed.

---

# AMA-6 Debug Log — Calibrated Drift Model

**Pipeline Step:** AMA-6 (Gray-box physics + ML drift model)
**Dates:** Early November 2025
**Script:** `iceberg-trajectory-ml/scripts/ama6_train_drift_model.py`
**Output:** `drift_model.pkl`, `drift_model_coefficients.csv`, `ama6_evaluation.md`

---

## Mistake 1: Random Train/Test Split Destroyed the LSTM Model

**What happened:**
Before AMA-6, I tried an LSTM neural network for trajectory prediction. I used a standard random 80/20 train/test split (`train_test_split` from scikit-learn). The LSTM appeared to perform well on the test set. But when I tested it on a completely new iceberg, predictions were garbage.

**How I found it:**
Anto reviewed the code and pointed out that random splitting causes **temporal leakage**. If iceberg D20A has positions from 2010-2020, a random split puts some 2015 positions in training and some 2016 positions in testing. The model has already "seen" D20A's behavior at nearby dates, so it memorizes the trajectory instead of learning physics. The test error was artificially low.

**How I fixed it:**
- Switched to **temporal split**: train on ≤2017, test on 2018-2021
- Added **spatial split**: hold out 10 entire iceberg IDs (the model has never seen these icebergs during training)
- Added **combined split**: temporal AND spatial simultaneously (hardest test)
- The LSTM immediately stopped working under these honest splits — it had been memorizing, not learning
- This is why I switched from LSTM to Ridge Regression for AMA-6

**Lesson:** This was the most important mistake in the entire project. A random split would have given us a model that looks great in testing but fails in the real world. Anto's rule "no random train/test splits" saved us.

---

## Mistake 2: Textbook Physics Coefficients Were Wildly Wrong

**What happened:**
The standard leeway drift model uses textbook coefficients:
velocity = 0.9 * ocean_current + 0.2 * ice_velocity + 0.02 * wind

text

I started with these as the physics baseline. The results were terrible: MAE of 20+ km/day on the temporal test set. The "zero baseline" (predict no movement) was beating the physics model.

**How I found it:**
I compared the textbook physics predictions against the zero baseline:
- Textbook: 20.14 km/day MAE
- Zero (predict stationary): 3.24 km/day MAE
A model that says "the iceberg doesn't move" was 6× better than the physics model. That's a red flag.

**How I fixed it:**
- Ran OLS regression on the training data to find the ACTUAL coefficients for giant Antarctic icebergs
- Got: `u = 0.25*uo + 0.001*usi*ice_wt - 0.0005*u10` (current coefficient 0.25, not 0.9!)
- The textbook coefficients are for small Arctic sea ice floes, not 100 km² Antarctic tabular icebergs. Giant icebergs have enormous draft and inertia — they respond much less to currents and almost ignore wind.
- The calibrated physics model dropped to 4.09 km/day MAE, finally beating the zero baseline on moving icebergs.

**Lesson:** Never blindly trust textbook parameters. The physics is right (current + ice + wind) but the coefficients depend entirely on the object's size and shape.

---

## Mistake 3: Feature Scaling Broke Ridge Regression

**What happened:**
Ridge Regression penalizes large coefficients. But my features had wildly different scales:
- ocean_u: range -0.5 to 0.5 m/s
- wind_u: range -17 to +11 m/s
- lat: range -74 to -43 degrees
- siconc: range 0 to 1

The model was over-penalizing the wind and latitude features because their raw values are large, and under-penalizing the current features.

**How I found it:**
I printed the Ridge coefficients and saw that wind_u had a coefficient of 0.0001 while ocean_u had 0.25. The wind coefficient was being crushed by the L2 penalty, not because wind is unimportant, but because wind values are 30× larger.

**How I fixed it:**
- Added `StandardScaler` from scikit-learn to normalize all features to zero mean and unit variance BEFORE fitting Ridge
- Saved the scaler alongside the model in the .pkl file
- After scaling, the coefficients became comparable and the model properly weighted all forcing terms

---

## Mistake 4: Ice Weight Function Threshold Was Arbitrary

**What happened:**
The ice drag term uses `w(siconc) = clip((siconc - 0.6) / 0.3, 0, 1)`. This means ice drag only kicks in above 60% concentration and reaches full effect at 90%. I initially used 0.5/0.5 (kicks in at 50%, full at 100%) based on a guess.

**How I found it:**
I plotted model error vs siconc and saw that the model was over-predicting drift in the 50-70% concentration range. In reality, sea ice at 55% concentration is still broken floes that don't transmit much drag to a giant iceberg. The drag only becomes significant in consolidated pack ice (>60%).

**How I fixed it:**
- Tested thresholds of 0.4, 0.5, 0.6, 0.7 on the validation set
- 0.6/0.3 gave the best MAE on moving icebergs
- This matches the physical literature: the "ice bridge" effect in consolidated pack ice starts around 60-70% concentration
- Documented the choice in `ama6_evaluation.md`

---

## Mistake 5: Multi-Horizon Prediction Failed (48h, 72h)

**What happened:**
I tried to train the model for 48-hour and 72-hour prediction horizons by chaining consecutive position pairs. The results showed "insufficient data."

**How I found it:**
The BYU database provides roughly daily positions. To get a 48-hour pair, I need position(t) and position(t+2 days) for the same iceberg with no gaps. After filtering for dt_days ≈ 2, I had fewer than 500 samples — not enough for reliable evaluation. For 72h, even fewer.

**How I fixed it:**
- Accepted that 24 hours is the only validated horizon
- Added a clear note in the model config: "Do NOT use for 48h or 72h predictions"
- The inference function warns if dt_hours > 24
- This is honest. Claiming multi-day capability with insufficient data would violate Anto's rules.

---

## Mistake 6: Pickle Version Mismatch Warning

**What happened:**
After training the model on my machine (Python 3.14, scikit-learn 1.x), Anto tried to load the .pkl on his machine and got a `UserWarning: Trying to unpickle estimator Ridge from version X.Y.Z when using version 1.8.0`.

**How I found it:**
Anto sent me the warning message. The model still loaded and predictions were correct, but the warning was alarming.

**How I fixed it:**
- Confirmed that minor version differences in scikit-learn don't change the Ridge model format (it's just a weight vector and intercept)
- Added the scikit-learn version to `model_config.json` so the backend team knows what to match
- For the SIH demo, this is fine. For production, we'd use ONNX or a version-pinned environment.

---

## Summary

| # | Mistake | Root Cause | Impact if Unfixed |
|---|---------|-----------|-------------------|
| 1 | Random split leakage | ML habit | Model memorizes, fails on new icebergs |
| 2 | Textbook coefficients | Wrong scale assumption | Physics model worse than zero baseline |
| 3 | Feature scaling | Ridge sensitivity | Wind/lat features crushed by penalty |
| 4 | Ice weight threshold | Arbitrary guess | Over-prediction in marginal ice zone |
| 5 | Multi-horizon failure | Data limitation | False claims about 48h/72h capability |
| 6 | Pickle version | Environment mismatch | Warning on load (non-fatal) |

**Lessons learned:**
- Honest evaluation splits are more important than model complexity
- Textbook parameters don't transfer across scales (Arctic floes ≠ Antarctic tabular icebergs)
- When the zero baseline beats your physics model, your coefficients are wrong
- 24h is the honest horizon. Don't oversell.

---

FILE 2: iceberg-trajectory-ml/docs/AMA7_DEBUG_LOG.md

Write this EXACTLY as specified below.

---

# AMA-7 Debug Log — Evaluation

**Pipeline Step:** AMA-7 (Model evaluation and comparison)
**Dates:** 7 November 2025
**Script:** Evaluation section of `ama6_train_drift_model.py`
**Output:** `iceberg-trajectory-ml/data/validation/results/ama6_evaluation.md`

---

## Mistake 1: Almost Reported R² (Anto's Rule 2)

**What happened:**
My first evaluation draft included R² = 0.34 for the temporal split. I was about to commit it when I re-read Anto's rules: "No accuracy claims — no R² quotes."

**How I found it:**
Code review before pushing. I had `r2_score(y_true, y_pred)` in the evaluation loop.

**How I fixed it:**
- Removed all R² calculations
- Replaced with MAE, RMSE, and bias in physical units (km/day, m/s)
- R² is misleading for this problem anyway: a model that predicts "stationary" gets a decent R² because 69% of icebergs ARE stationary, but it's useless for the 31% that move
- Physical units are what the navigation team actually needs: "the prediction is off by 6 km" is meaningful, "R² = 0.34" is not

---

## Mistake 2: Evaluated on All Data Instead of Speed Categories

**What happened:**
The overall MAE was 3.85 km/day (temporal split). This number is dominated by the 4,443 stationary icebergs (MAE 3.27 km/day) because they're the majority. It hides the fact that fast icebergs (>10 km/day) have MAE 8.54 km/day — which is what actually matters for navigation safety.

**How I found it:**
I showed the overall MAE to Anto and he asked: "But what about the fast ones that threaten shipping lanes?" I realized the aggregate number was misleading.

**How I fixed it:**
- Added speed-category breakdown: stationary (<2), slow (2-5), moderate (5-10), fast (>10 km/day)
- This revealed the real story: ML beats calibrated physics on moderate and fast icebergs (the dangerous ones) but the zero baseline is hard to beat on stationary icebergs (because predicting "no movement" is trivially correct 69% of the time)
- Added the "moving icebergs only" evaluation: ML MAE 5.70 vs Calib 7.40 vs Zero 12.01 km/day for >4.3 km/day icebergs

---

## Mistake 3: Forgot the Zero Baseline

**What happened:**
My initial evaluation compared ML vs Calibrated Physics vs Textbook Physics. I didn't include the "zero baseline" (predict the iceberg doesn't move). Anto asked: "Is your model better than just assuming the iceberg stays put?"

**How I found it:**
Anto's question during review. This is a standard sanity check in trajectory prediction that I should have included from the start.

**How I fixed it:**
- Added zero baseline to all evaluation tables
- Results were humbling: on the combined split, zero baseline MAE is 0.29 km/day vs ML 3.03 km/day. The zero baseline "wins" on aggregate because most icebergs are stationary.
- BUT on moving icebergs (>8.6 km/day), zero baseline MAE is 15.28 km/day vs ML 7.79 km/day. The ML model cuts error in half for the icebergs that actually matter.
- This is the key pitch point: "On fast-moving icebergs — the ones that threaten shipping — ML reduces error by 49% compared to assuming no movement."

---

## Mistake 4: Spatial Split Results Were Initially Confusing

**What happened:**
The spatial split (10 held-out icebergs) showed much lower MAE than the temporal split: 2.99 vs 3.85 km/day for ML. This seemed backwards — shouldn't predicting unseen icebergs be harder?

**How I found it:**
I compared the split results and was confused. Then I checked which 10 icebergs were held out.

**How I fixed it:**
- The 10 held-out icebergs happened to be mostly slow-moving ones (B09G, B15G, etc. in the Weddell Sea). Their low speeds mean low MAE even with imperfect predictions.
- The temporal test set (2018-2021) includes D20A and other fast movers during their breakup period, which inflates the temporal MAE.
- This is NOT a bug — it's a data characteristic. I documented it in the evaluation report.
- Added per-iceberg breakdown for the spatial split to show the full picture.

---

## Mistake 5: Units Confusion (m/s vs km/day)

**What happened:**
The model predicts velocity in m/s, but the evaluation was initially reported in m/s. Anto said the navigation team thinks in km/day. My MAE of 0.045 m/s meant nothing to them.

**How I found it:**
Anto's feedback: "What does 0.045 m/s mean for a ship captain?"

**How I fixed it:**
- Converted all evaluation metrics to km/day: `speed_kmd = speed_ms * 86.4`
- 0.045 m/s → 3.89 km/day. Much more intuitive: "the prediction is off by about 4 km per day."
- Speed category thresholds also converted: 2 km/day ≈ 0.023 m/s, 10 km/day ≈ 0.116 m/s
- Kept m/s in the model internals but reported km/day in all evaluation outputs

---

## Summary

| # | Mistake | Root Cause | Impact if Unfixed |
|---|---------|-----------|-------------------|
| 1 | R² reporting | ML habit | Violates Anto's Rule 2, misleading metric |
| 2 | Aggregate-only evaluation | Statistical laziness | Hides poor performance on fast icebergs |
| 3 | Missing zero baseline | Evaluation oversight | Can't prove model is useful |
| 4 | Confusing spatial split | Data composition | Misinterpretation of results |
| 5 | m/s vs km/day | Unit mismatch | Results meaningless to end users |

**Lessons learned:**
- Always compare against the dumbest possible baseline (zero movement)
- Aggregate metrics lie — break down by speed category
- Report in the units your end users think in
- R² is dangerous for imbalanced datasets (69% stationary)
- Honest evaluation is more impressive than inflated numbers