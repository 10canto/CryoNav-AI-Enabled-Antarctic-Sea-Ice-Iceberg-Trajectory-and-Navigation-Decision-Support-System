"""
AMA-1 Acceptance Test: Data Service Access
===========================================
Tests that both required data service credentials are configured and working.

Acceptance check (from team Excel plan, AMA-1):
    "A tiny CDS request and a tiny Copernicus Marine request both succeed."

Usage:
    python scripts/test_data_access.py

What this script does:
    1. Checks that the copernicusmarine package is importable.
    2. Checks that copernicusmarine can authenticate with the saved local
       credentials (does NOT download any data).
    3. Checks that ~/.cdsapirc exists and is structurally valid (url + key
       fields present, key is not a placeholder).
    4. Checks that the cdsapi package is importable.
    5. Submits the smallest possible authenticated CDS request (a single
       variable, single level, single month) to confirm the key is accepted.

Security:
    - Credentials are never printed, logged, or written to any file.
    - The key value is only checked for presence and placeholder patterns;
      its actual value is never echoed.
    - Network requests are only made when the script is run directly
      (guarded by __main__), never on import.

Outputs:
    EXIT 0  All checks passed (PASS for both services).
    EXIT 1  One or both checks failed (FAIL lines explain what to fix).
"""

# ---------------------------------------------------------------------------
# Standard library only at module level – safe to import anywhere.
# ---------------------------------------------------------------------------
import sys
import os
import pathlib
import textwrap

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_PASS = "PASS"
_FAIL = "FAIL"
_SKIP = "SKIP"


def _header(text: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}")


def _result(label: str, status: str, detail: str = "") -> None:
    """Print a single check result line."""
    tag = f"[{status}]"
    line = f"  {tag:<8} {label}"
    if detail:
        line += f"\n           {detail}"
    print(line)


def _indent(text: str, spaces: int = 11) -> str:
    return textwrap.indent(textwrap.dedent(text).strip(), " " * spaces)


# ---------------------------------------------------------------------------
# 1.  Copernicus Marine check
# ---------------------------------------------------------------------------

def check_copernicus_marine() -> bool:
    """
    Returns True when the copernicusmarine package is installed AND the
    credentials stored at ~/.copernicusmarine/credentials allow a successful
    'describe' metadata call (no data download).

    Distinguishes:
        - Package missing            → install instructions
        - Credentials file missing   → login instructions
        - Auth/network failure       → specific error message
        - Success                    → PASS
    """
    _header("Copernicus Marine Service")

    # --- 1a. Package importable? -------------------------------------------
    try:
        import copernicusmarine  # noqa: F401  (checked at runtime, not at import)
        _result("Package 'copernicusmarine' importable", _PASS)
    except ImportError:
        _result(
            "Package 'copernicusmarine' importable",
            _FAIL,
            "Run:  pip install copernicusmarine>=1.3.0",
        )
        return False

    # --- 1b. Credentials file present? -------------------------------------
    #
    # The copernicusmarine client stores credentials at one of three locations
    # depending on the client version:
    #   ~/.copernicusmarine/.copernicusmarine-credentials  (v2.x default)
    #   ~/.copernicusmarine/credentials                    (v1.x)
    #   ~/.config/copernicusmarine/credentials             (some installs)
    #
    # We check all known locations.  We only check EXISTENCE and the
    # presence of 'username' / 'password' keys – we never read or print values.
    cred_paths = [
        pathlib.Path.home() / ".copernicusmarine" / ".copernicusmarine-credentials",
        pathlib.Path.home() / ".copernicusmarine" / "credentials",
        pathlib.Path.home() / ".config" / "copernicusmarine" / "credentials",
    ]
    cred_file = next((p for p in cred_paths if p.exists()), None)

    if cred_file is None:
        _result(
            "Credentials file present",
            _FAIL,
            _indent("""
                No credentials file found.  Run once to save them:

                    python -c "import copernicusmarine; copernicusmarine.login()"

                You will be prompted for your Copernicus Marine username and
                password (https://marine.copernicus.eu – free account).
                The client stores them locally; nothing is written to this repo.
            """),
        )
        return False

    # Check file has at least 'username' and 'password' keys (value not read).
    #
    # copernicusmarine v2.x stores credentials as a single Base64-encoded line
    # rather than plain INI text.  We check both the raw content and, if that
    # misses the keys, the Base64-decoded content.  The decoded text is only
    # used for the key-name presence check – the values are never read or printed.
    import base64
    try:
        raw = cred_file.read_text(encoding="utf-8").strip()
        try:
            decoded = base64.b64decode(raw).decode("utf-8")
        except Exception:
            decoded = ""
        search_text = raw + decoded          # key names appear in one of these
        has_username = "username" in search_text
        has_password = "password" in search_text
    except OSError as exc:
        _result("Credentials file readable", _FAIL, str(exc))
        return False

    if not (has_username and has_password):
        _result(
            "Credentials file structure",
            _FAIL,
            "File exists but is missing 'username' or 'password' fields. "
            "Re-run:  python -c \"import copernicusmarine; copernicusmarine.login()\"",
        )
        return False

    _result("Credentials file present and structured correctly", _PASS)

    # --- 1c. Authenticated metadata call (no download) ---------------------
    #
    # copernicusmarine.describe() queries the CMEMS catalogue and requires a
    # valid login.  We request only the specific dataset used in AMA-3 so the
    # response is small.  We do NOT call .subset() or .open_dataset() –
    # those download data.
    print(
        "\n  Attempting authenticated metadata call "
        "(copernicusmarine.describe)...\n"
        "  This does NOT download any data.\n"
    )

    try:
        import copernicusmarine
        import logging

        # Silence the copernicusmarine logger for this call.
        # The library writes to stderr via a StreamHandler, so
        # contextlib.redirect_stdout has no effect.  Raising the logger
        # level to WARNING suppresses the INFO/DEBUG auth and progress lines.
        cm_logger = logging.getLogger("copernicusmarine")
        prev_level = cm_logger.level
        cm_logger.setLevel(logging.WARNING)
        try:
            desc = copernicusmarine.describe(
                contains=["cmems_mod_glo_phy_my_0.083deg_P1D-m"],
                disable_progress_bar=True,
                raise_on_error=True,
            )
        finally:
            cm_logger.setLevel(prev_level)

        # describe() returns a CopernicusMarineCatalogue, never None.
        # With raise_on_error=True, auth failures raise before we get here.
        _result(
            "Authenticated metadata call (copernicusmarine.describe)",
            _PASS,
            "Credentials accepted; catalogue query succeeded.",
        )
        return True

    except Exception as exc:
        err = str(exc)
        exc_type = type(exc).__name__
        # Never print the full traceback – it might contain credential paths.
        short_err = err[:200] if len(err) > 200 else err
        _result(
            "Authenticated metadata call",
            _FAIL,
            f"Exception type: {exc_type}\n"
            f"           Error: {short_err}\n"
            "           Check your internet connection and that your Copernicus\n"
            "           Marine account is active (https://marine.copernicus.eu).",
        )
        return False


# ---------------------------------------------------------------------------
# 2.  Climate Data Store (CDS / ERA5) check
# ---------------------------------------------------------------------------

_CDSAPIRC = pathlib.Path.home() / ".cdsapirc"

_PLACEHOLDER_PATTERNS = {
    "YOUR_API_KEY_HERE",
    "YOUR-UID:YOUR-API-KEY",
    "UID:API-KEY",
    "<your-api-key>",
    "INSERT_KEY",
}

_CDS_SETUP_INSTRUCTIONS = _indent("""
    1. Create a free account at https://cds.climate.copernicus.eu
    2. On the ERA5 dataset page, accept the licence terms.
    3. Go to your profile page and copy your API key.
    4. Create the file  C:\\Users\\Amar\\.cdsapirc  (or ~/.cdsapirc)
       with exactly this content (replace the placeholder):

           url: https://cds.climate.copernicus.eu/api
           key: YOUR_API_KEY_HERE

    The key looks like a long alphanumeric string.
    Nothing is stored in the repository – this file lives only on your machine.
""")


def _parse_cdsapirc() -> tuple[bool, str]:
    """
    Reads ~/.cdsapirc and checks it has 'url' and 'key' fields, and that
    the key is not an obvious placeholder.

    Returns:
        (ok: bool, reason: str)  – reason is empty string on success.

    The key VALUE is never printed or stored.
    """
    if not _CDSAPIRC.exists():
        return False, f"File not found: {_CDSAPIRC}"

    try:
        text = _CDSAPIRC.read_text(encoding="utf-8")
    except OSError as exc:
        return False, f"Cannot read file: {exc}"

    # Parse the simple key: value format (also handles YAML-style).
    fields: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if ":" in line and not line.startswith("#"):
            k, _, v = line.partition(":")
            fields[k.strip().lower()] = v.strip()

    if "url" not in fields:
        return False, "Missing 'url' field."
    if "key" not in fields:
        return False, "Missing 'key' field."

    key_val = fields["key"]

    # Check for empty key
    if not key_val:
        return False, "'key' field is empty."

    # Check for placeholder values (case-insensitive)
    if any(p.lower() in key_val.lower() for p in _PLACEHOLDER_PATTERNS):
        return (
            False,
            "The 'key' field still contains a placeholder value. "
            "Replace it with your real CDS API key.",
        )

    return True, ""


def check_cds() -> bool:
    """
    Returns True when:
        - ~/.cdsapirc is present with valid url/key fields (not placeholders)
        - cdsapi package is importable
        - A minimal authenticated CDS request succeeds

    The actual key value is never printed or stored.
    """
    _header("Climate Data Store (CDS / ERA5)")

    # --- 2a. ~/.cdsapirc present and valid? --------------------------------
    ok, reason = _parse_cdsapirc()
    if not ok:
        _result(
            "~/.cdsapirc configuration",
            _FAIL,
            f"{reason}\n{_CDS_SETUP_INSTRUCTIONS}",
        )
        return False

    _result("~/.cdsapirc present and key field is not a placeholder", _PASS)

    # --- 2b. Package importable? -------------------------------------------
    try:
        import cdsapi  # noqa: F401
        _result("Package 'cdsapi' importable", _PASS)
    except ImportError:
        _result(
            "Package 'cdsapi' importable",
            _FAIL,
            "Run:  pip install cdsapi>=0.7.0",
        )
        return False

    # --- 2c. Authenticated request -----------------------------------------
    #
    # We request a single variable (10m u-wind), pressure level 1000 hPa,
    # one specific day (1 January 1979), area of 1 x 1 degree, NetCDF format.
    # This is the absolute minimum the CDS API accepts.  The resulting file is
    # < 10 KB.  We write it to a temp file and delete it immediately.
    #
    # This IS a real authenticated request, so it verifies the key works.
    # We distinguish this explicitly from a public metadata lookup.
    print(
        "\n  Attempting minimal authenticated CDS request...\n"
        "  (1 variable, 1 day, 1x1 deg area  –  file will be < 10 KB)\n"
        "  This confirms your API key is accepted by the CDS server.\n"
    )

    import tempfile

    tmp_path = pathlib.Path(tempfile.mktemp(suffix="_cds_test.nc"))

    try:
        import cdsapi

        # Silence the cdsapi progress bar / URL messages so we control output.
        import logging
        logging.getLogger("cdsapi").setLevel(logging.ERROR)

        client = cdsapi.Client(quiet=True)

        client.retrieve(
            "reanalysis-era5-pressure-levels",
            {
                "product_type": "reanalysis",
                "variable": "u_component_of_wind",
                "pressure_level": "1000",
                "year": "1979",
                "month": "01",
                "day": "01",
                "time": "00:00",
                "area": [1, 0, 0, 1],       # 1 x 1 degree box (N, W, S, E)
                "format": "netcdf",
            },
            str(tmp_path),
        )

        # Confirm the file was actually created and is non-empty.
        if tmp_path.exists() and tmp_path.stat().st_size > 0:
            file_kb = tmp_path.stat().st_size / 1024
            _result(
                "Authenticated CDS request (ERA5 reanalysis)",
                _PASS,
                f"Key accepted; test file received ({file_kb:.1f} KB). "
                "File deleted now.",
            )
            tmp_path.unlink(missing_ok=True)
            return True
        else:
            _result(
                "Authenticated CDS request",
                _FAIL,
                "Request completed but no output file was created.",
            )
            return False

    except Exception as exc:
        tmp_path.unlink(missing_ok=True)   # clean up if partly written

        err = str(exc)
        short_err = err[:300] if len(err) > 300 else err

        # Give specific guidance for the most common errors.
        hint = ""
        if "401" in err or "Unauthorized" in err or "authentication" in err.lower():
            hint = "\n           Hint: API key rejected. Check the key in ~/.cdsapirc."
        elif "403" in err or "licence" in err.lower() or "terms" in err.lower():
            hint = (
                "\n           Hint: Licence not accepted. Go to the ERA5 dataset page "
                "at https://cds.climate.copernicus.eu and click 'Accept terms'."
            )
        elif "timeout" in err.lower() or "connection" in err.lower():
            hint = "\n           Hint: Network error. Check your internet connection."

        _result(
            "Authenticated CDS request",
            _FAIL,
            f"Error: {short_err}{hint}",
        )
        return False


# ---------------------------------------------------------------------------
# 3.  Summary
# ---------------------------------------------------------------------------

def print_summary(copernicus_ok: bool, cds_ok: bool) -> None:
    _header("AMA-1 Acceptance Check Summary")

    cm_status = _PASS if copernicus_ok else _FAIL
    cds_status = _PASS if cds_ok else _FAIL

    print(f"  Copernicus Marine  [{cm_status}]")
    print(f"  CDS / ERA5         [{cds_status}]")

    print()
    if copernicus_ok and cds_ok:
        print("  Both services ready.  AMA-1 acceptance check: PASS")
        print()
        print("  You can proceed to AMA-2 (validation set selection) and")
        print("  AMA-3 (download daily currents and sea ice).")
    else:
        print("  AMA-1 acceptance check: FAIL")
        print()
        print("  Fix the issues listed above, then re-run:")
        print("      python scripts/test_data_access.py")

    print()


# ---------------------------------------------------------------------------
# Entry point – network requests only run when executed directly.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\nAMA-1 Data Service Access Test")
    print("This script NEVER prints, logs, or stores your credentials.")
    print("Network requests are made only to verify authentication.")

    copernicus_ok = check_copernicus_marine()
    cds_ok = check_cds()

    print_summary(copernicus_ok, cds_ok)

    sys.exit(0 if (copernicus_ok and cds_ok) else 1)
