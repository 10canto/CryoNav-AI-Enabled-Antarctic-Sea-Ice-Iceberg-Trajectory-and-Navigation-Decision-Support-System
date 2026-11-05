# CryoNav AI - Data Setup Guide

This guide walks you through setting up access to the two main data sources for the iceberg trajectory ML pipeline:
1. **Copernicus Marine Service** - Ocean currents, temperature, salinity
2. **CDS (Climate Data Store)** - ERA5 atmospheric reanalysis (wind, pressure, etc.)

> **⚠️ IMPORTANT**: This pipeline uses a **streaming-first architecture**. Data is NOT downloaded to disk as NetCDF files. Instead, we stream directly into xarray for processing. See `ARCHITECTURE.md` for details.

---

## Prerequisites

Ensure you have Python 3.8+ and the required packages installed:

```powershell
pip install cdsapi copernicusmarine xarray netCDF4
```

---

## 1. Copernicus Marine Service Setup

### Step 1.1: Create Account

1. Go to: **https://data.marine.copernicus.eu/register**
2. Fill out the registration form
3. Verify your email address
4. Login at: **https://data.marine.copernicus.eu/products**

### Step 1.2: Configure Credentials

Run the login command and enter your credentials when prompted:

```powershell
copernicusmarine login
```

Enter:
- **Username**: Your registered email or username
- **Password**: Your password

Credentials are stored securely and will be used automatically for future downloads.

### Step 1.3: Browse Available Datasets

Useful datasets for iceberg trajectory modeling:
- `cmems_mod_glo_phy_my_0.083deg_P1D-m` - Global ocean physics (currents, temp, salinity)
- `cmems_obs-sl_glo_phy-ssh_my_allsat-l4-duacs-0.25deg_P1D` - Sea surface height

You can explore datasets at: **https://data.marine.copernicus.eu/**

---

## 2. CDS (Climate Data Store) Setup

### Step 2.1: Create Account

1. Go to: **https://cds.climate.copernicus.eu/user/register**
2. Complete registration and verify email
3. Login at: **https://cds.climate.copernicus.eu/**

### Step 2.2: Accept Dataset Licenses

**Important:** You must accept the license for each dataset before downloading.

1. Go to: **https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels**
2. Scroll down and click **"Download data"**
3. Accept the **Terms of Use** when prompted
4. Repeat for any other datasets you need

### Step 2.3: Get Your API Key

1. Login and go to: **https://cds.climate.copernicus.eu/api-how-to**
2. You'll see your UID and API key displayed like:

```
url: https://cds.climate.copernicus.eu/api/v2
key: 12345:abcdef12-3456-7890-abcd-ef1234567890
```

### Step 2.4: Create Configuration File (Windows)

On Windows, create the file at: `C:\Users\<YourUsername>\.cdsapirc`

**Option A: Using PowerShell**

```powershell
# Create the file
$cdsrc = "$env:USERPROFILE\.cdsapirc"

# Add your credentials (replace with YOUR values from the CDS website)
@"
url: https://cds.climate.copernicus.eu/api/v2
key: YOUR_UID:YOUR_API_KEY
"@ | Out-File -FilePath $cdsrc -Encoding ASCII

# Verify it was created
Get-Content $cdsrc
```

**Option B: Using Notepad**

1. Open Notepad
2. Paste these two lines (with YOUR credentials):
```
url: https://cds.climate.copernicus.eu/api/v2
key: YOUR_UID:YOUR_API_KEY
```
3. Save as: `C:\Users\<YourUsername>\.cdsapirc`
4. **Important**: Set "Save as type" to "All Files" and use encoding "ANSI" or "UTF-8"

### Step 2.5: Verify File Format

The file should look exactly like this (with your actual key):

```
url: https://cds.climate.copernicus.eu/api/v2
key: 12345:abcdef12-3456-7890-abcd-ef1234567890
```

- No extra spaces or blank lines
- Colon and space after `url:` and `key:`
- No quotes around the values

---

## 3. Verify Your Setup

### Step 3.1: Run Account Check Script

This checks both accounts using the streaming approach:

```powershell
cd iceberg-trajectory-ml
python scripts/ama1_check_accounts.py
```

Expected output:
```
✓ PASS: CDS - Test download successful (tempfile, loaded to memory)
✓ PASS: Copernicus Marine - Streaming access valid
```

**What this script does**:
- For CDS: Downloads to tempfile, loads to xarray, then deletes tempfile
- For Copernicus Marine: Streams directly into xarray (no disk download)
- Verifies credentials work for streaming data access

---

## 4. Troubleshooting

### Common CDS Errors

#### ❌ `Client error: 403 Forbidden`
**Problem**: License not accepted for the dataset

**Solution**:
1. Go to: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels
2. Click "Download data"
3. Accept the Terms of Use checkbox
4. Wait 5-10 minutes for permissions to propagate
5. Try again

#### ❌ `Invalid API key`
**Problem**: Wrong UID or API key in `.cdsapirc`

**Solution**:
1. Re-check your key at: https://cds.climate.copernicus.eu/api-how-to
2. Verify `.cdsapirc` has correct format (see Step 2.5 above)
3. No extra spaces or quotes

#### ❌ `Request queued... (timeout after 5 minutes)`
**Problem**: CDS server is busy

**Solution**:
- This is normal during peak hours (European business hours)
- Wait and try again later
- Your request remains in the queue and will eventually process

#### ❌ `FileNotFoundError: .cdsapirc`
**Problem**: Config file not in the right location

**Solution**:
```powershell
# Check if file exists
Test-Path "$env:USERPROFILE\.cdsapirc"

# Show where it should be
Write-Host "$env:USERPROFILE\.cdsapirc"
```

### Common Copernicus Marine Errors

#### ❌ `Authentication failed` / `401 Unauthorized`
**Problem**: Invalid credentials

**Solution**:
```powershell
# Re-login with correct credentials
copernicusmarine login

# Check if credentials are stored
copernicusmarine login --check-credentials-valid
```

#### ❌ `Dataset not found`
**Problem**: Dataset ID changed or is unavailable

**Solution**:
- Check current dataset IDs at: https://data.marine.copernicus.eu/
- Use `copernicusmarine describe` to list available datasets

#### ❌ `No data available for the specified parameters`
**Problem**: Requested time/space range has no data

**Solution**:
- Check dataset temporal coverage (some datasets have delays)
- Verify lat/lon coordinates are within dataset bounds
- Try a different date range

### Network Issues

If both services fail:
1. Check internet connection
2. Try from a different network (corporate firewalls may block)
3. Check if services are down:
   - CDS status: https://cds.climate.copernicus.eu/
   - Copernicus Marine: https://marine.copernicus.eu/

---

## 5. Next Steps

Once the account check script passes:

✅ **You're ready to stream data!**

Typical workflow:
1. Define spatial/temporal extent for your study area
2. Use `copernicusmarine.open_dataset()` to stream ocean data directly
3. Use `cdsapi.retrieve()` with tempfiles for atmospheric data
4. Process with `xarray` in memory (no persistent NetCDF files)
5. Save only the final `training_table.csv`

**Architecture Notes**:
- See `ARCHITECTURE.md` for the streaming-first design
- AMA-3: Write ocean data streaming helper functions
- AMA-4: Write ERA5 tempfile streaming helper functions
- AMA-5: Build the final training_table.csv

---

## Quick Reference

### Useful Commands

```powershell
# Check CDS config
Get-Content "$env:USERPROFILE\.cdsapirc"

# Re-login to Copernicus Marine
copernicusmarine login

# Test streaming access
python scripts/ama1_check_accounts.py
```

### Key URLs

- **CDS Registration**: https://cds.climate.copernicus.eu/user/register
- **CDS API Key**: https://cds.climate.copernicus.eu/api-how-to
- **CDS Datasets**: https://cds.climate.copernicus.eu/datasets/
- **Copernicus Marine Registration**: https://data.marine.copernicus.eu/register
- **Copernicus Marine Datasets**: https://data.marine.copernicus.eu/products

### Support

- **CDS Support**: https://support.ecmwf.int/
- **Copernicus Marine Support**: servicedesk.cmems@mercator-ocean.eu
- **cdsapi Documentation**: https://cds.climate.copernicus.eu/api-how-to
- **copernicusmarine Documentation**: https://help.marine.copernicus.eu/

---

**Last Updated**: 2024-11-05  
**AMA-1 Task**: Data Account Setup & Verification
