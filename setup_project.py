"""
One-shot project setup script.
Run from the Hackathon root directory:

    python setup_project.py

What it does:
  1. Creates all required output directories
  2. Copies best.pt from the cryonav-backend into models/
  3. Copies up to 10 sample images from cryonav-backend/backend_ready/sample_detections/
  4. Verifies all source modules are present
  5. Prints the quick-start commands
"""

import shutil
from pathlib import Path

ROOT   = Path(__file__).parent
TARGET = ROOT / "ICEBERG_TRAJECTORY_PREDICTION"


def _ensure_dirs():
    dirs = [
        "models",
        "sample_images",
        "outputs/visualizations",
        "outputs/predictions",
        "outputs/reports",
        "data/environmental",
        "src",
        "tests",
    ]
    for d in dirs:
        (TARGET / d).mkdir(parents=True, exist_ok=True)
    print("[setup] Output directories ready")


def _copy_model():
    dest = TARGET / "weights" / "best.pt"
    if dest.exists():
        print(f"[setup] weights/best.pt already present ({dest.stat().st_size // 1024} KB) — skipping")
        return

    candidates = [
        ROOT / "cryonav-backend" / "backend_ready" / "weights" / "best.pt",
        ROOT / "cryonav-backend" / "app" / "detection_models" / "iceberg_detection" / "weights" / "best.pt",
    ]
    for src in candidates:
        if src.exists():
            (TARGET / "weights").mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dest)
            print(f"[setup] Copied model: {src.name}  ({dest.stat().st_size // 1024} KB)")
            return

    print("[setup] WARNING — best.pt not found in any known location.")
    print("         Copy it manually to:  ICEBERG_TRAJECTORY_PREDICTION/models/best.pt")


def _copy_sample_images():
    dest_dir = TARGET / "sample_images"
    existing = list(dest_dir.glob("*.*"))
    if existing:
        print(f"[setup] sample_images/ already has {len(existing)} file(s) — skipping")
        return

    sources = [
        ROOT / "cryonav-backend" / "backend_ready" / "sample_detections",
        ROOT / "cryonav-backend" / "data",
    ]
    copied = 0
    for src_dir in sources:
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.tif"):
            for img in sorted(src_dir.rglob(ext))[:10 - copied]:
                shutil.copy(img, dest_dir / img.name)
                copied += 1
                if copied >= 10:
                    break
        if copied >= 10:
            break

    if copied:
        print(f"[setup] Copied {copied} sample image(s) to sample_images/")
    else:
        print("[setup] No sample images found — add images to sample_images/ manually")
        print("        Then run:  python main.py")


def _verify_modules():
    required = [
        TARGET / "src" / "detection_integration.py",
        TARGET / "src" / "drift_physics.py",
        TARGET / "src" / "visualization.py",
        TARGET / "src" / "__init__.py",
        TARGET / "main.py",
        TARGET / "api_server.py",
        TARGET / "requirements.txt",
        TARGET / "weights" / "best.pt",
    ]
    ok = True
    for f in required:
        status = "OK" if f.exists() else "MISSING"
        marker = "✓" if f.exists() else "✗"
        print(f"  {marker}  {f.relative_to(ROOT)}  [{status}]")
        if not f.exists():
            ok = False
    return ok


def main():
    print("=" * 60)
    print("  ICEBERG TRAJECTORY PREDICTION — Project Setup")
    print("=" * 60)

    _ensure_dirs()
    _copy_model()
    _copy_sample_images()

    print("\n[setup] Verifying modules:")
    ok = _verify_modules()

    print()
    if ok:
        print("=" * 60)
        print("  SETUP COMPLETE")
        print("=" * 60)
    else:
        print("=" * 60)
        print("  SETUP COMPLETE (with warnings — see MISSING items above)")
        print("=" * 60)

    print("""
Quick Start:

  cd ICEBERG_TRAJECTORY_PREDICTION

  # Install dependencies
  pip install -r requirements.txt

  # Run full pipeline (auto-detects first image in sample_images/)
  python main.py

  # Run with synthetic data (no image required)
  python main.py --mock

  # Start the REST API  →  http://localhost:8001/docs
  python api_server.py

  # Lower confidence if nothing detected
  python main.py --confidence 0.15
""")


if __name__ == "__main__":
    main()
