"""
FILE 4: main.py
End-to-end Antarctic Iceberg Trajectory Prediction Demo

Detection (YOLOv5/best.pt) -> Drift Physics -> Monte Carlo -> Visualisation

Usage:
    python main.py                              # auto-finds first sample image
    python main.py --image path/to/img.jpg      # specific image
    python main.py --mock                       # synthetic icebergs (no image)
    python main.py --confidence 0.15            # lower detection threshold
    python main.py --hours 48                   # 48h instead of 72h forecast
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent / "src"))

from detection_integration import (
    IcebergDetector, visualize_detections, save_detection_results,
)
from drift_physics import DriftPredictor, EnvironmentalData, drift_distance_km
from visualization import (
    plot_detections, plot_trajectories, plot_integrated_results,
)

SEP  = "=" * 70
STEP = "-" * 70


def _banner(text: str) -> None:
    print(f"\n{STEP}\n  {text}\n{STEP}")


def _find_sample() -> Path | None:
    d = Path("sample_images")
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.tif", "*.tiff"):
        imgs = sorted(d.glob(ext))
        if imgs:
            return imgs[0]
    return None


def _mock_icebergs(n: int = 4) -> list:
    """Synthetic icebergs for testing without a real image."""
    from datetime import datetime
    rng   = np.random.default_rng(7)
    bergs = []
    for i in range(n):
        lat = -65.0 + rng.uniform(-2.0, 2.0)
        lon = -64.0 + rng.uniform(-3.0, 3.0)
        w   = rng.uniform(250, 1400)
        h   = rng.uniform(150, 1000)
        bergs.append({
            "id": f"ICE_MOCK_{i:03d}",
            "detection_time": datetime.utcnow().isoformat() + "Z",
            "position": {"lat": round(float(lat), 6),
                         "lon": round(float(lon), 6)},
            "size_meters": {"width":   round(float(w), 1),
                            "height":  round(float(h), 1),
                            "area_m2": round(float(w * h), 1)},
            "pixel_bbox":     {"x1": 0, "y1": 0, "x2": 0, "y2": 0},
            "confidence":     round(float(rng.uniform(0.65, 0.97)), 3),
            "source_image":   "synthetic_mock",
            "detector_model": "MOCK",
        })
        print(f"   🧊 [{i+1}] {lat:.4f}, {lon:.4f}  "
              f"{w:.0f}x{h:.0f}m  conf={bergs[-1]['confidence']:.0%}")
    return bergs


def run_pipeline(
    image_path: Path | None = None,
    mock: bool = False,
    confidence: float = 0.25,
    hours: int = 72,
    n_simulations: int = 100,
) -> dict:
    """Run the full detection -> prediction -> visualisation pipeline."""

    t0_total = time.time()

    print(f"\n{SEP}")
    print("  ANTARCTIC ICEBERG TRAJECTORY PREDICTION SYSTEM")
    print(f"  Detection -> Drift Physics -> Monte Carlo -> Visualisation")
    print(SEP)

    # ----------------------------------------------------------------
    # STEP 1: DETECTION
    # ----------------------------------------------------------------
    _banner("STEP 1 | ICEBERG DETECTION  (YOLOv5 best.pt)")

    icebergs = []

    if mock:
        print("🎭 Mock mode — generating synthetic icebergs...")
        icebergs = _mock_icebergs(n=4)

    else:
        if image_path is None:
            image_path = _find_sample()
        if image_path is None:
            print("❌ No image found in sample_images/ and --mock not set.")
            print("   Add a satellite image to sample_images/  or run with --mock")
            sys.exit(1)

        try:
            detector = IcebergDetector(model_path="weights/best.pt")
        except FileNotFoundError as e:
            print(e)
            sys.exit(1)

        icebergs = detector.detect_icebergs(
            image_path,
            confidence_threshold=confidence,
        )

        if not icebergs:
            print(f"❌ No icebergs detected at confidence >= {confidence}.")
            print("   Try:  python main.py --confidence 0.15")
            print("   Or:   python main.py --mock")
            sys.exit(1)

        visualize_detections(image_path, icebergs)

    save_detection_results(icebergs)
    print(f"\n✅ Detected {len(icebergs)} iceberg(s)")

    # ----------------------------------------------------------------
    # STEP 2: PREDICTION
    # ----------------------------------------------------------------
    _banner(f"STEP 2 | DRIFT PREDICTION  ({hours}h, {n_simulations} MC runs)")

    predictor   = DriftPredictor()
    env_data    = EnvironmentalData()
    predictions = []

    for berg in icebergs:
        lat = berg["position"]["lat"]
        lon = berg["position"]["lon"]

        print(f"\n  🧊 {berg['id']}  ({lat:.4f}, {lon:.4f})")

        cond  = env_data.get_conditions_at(lat, lon)
        ocean = cond["ocean_current"]
        wind  = cond["wind"]

        print(f"     Ocean: u={ocean['u']:+.2f} m/s  v={ocean['v']:+.2f} m/s")
        print(f"     Wind:  u={wind['u']:+.2f} m/s  v={wind['v']:+.2f} m/s")

        traj  = predictor.predict_with_uncertainty(
            lat, lon, ocean, wind,
            hours=hours, n_simulations=n_simulations,
        )

        final = traj[-1]
        dist  = drift_distance_km(lat, lon,
                                  final["latitude"], final["longitude"])

        print(f"     {hours}h position: "
              f"{final['latitude']:.4f}, {final['longitude']:.4f}")
        print(f"     72h drift:      {dist} km")
        print(f"     Uncertainty:    +/-{final['uncertainty_km']} km")

        predictions.append({
            "iceberg":                  berg,
            "trajectory":               traj,
            "environmental_conditions": cond,
            "drift_summary": {
                "total_distance_km":    dist,
                "final_uncertainty_km": final["uncertainty_km"],
                "forecast_hours":       hours,
            },
        })

    print(f"\n✅ Predictions ready for {len(predictions)} iceberg(s)")

    # ----------------------------------------------------------------
    # STEP 3: SAVE RESULTS
    # ----------------------------------------------------------------
    _banner("STEP 3 | SAVE RESULTS")

    out_json = Path("outputs/predictions/trajectories.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(predictions, indent=2))
    print(f"💾 Trajectories JSON   → {out_json}")

    # ----------------------------------------------------------------
    # STEP 4: VISUALISATION
    # ----------------------------------------------------------------
    _banner("STEP 4 | VISUALISATION")

    plot_detections(icebergs)
    plot_trajectories(predictions)
    plot_integrated_results(icebergs, predictions)

    # ----------------------------------------------------------------
    # STEP 5: SUMMARY
    # ----------------------------------------------------------------
    total_s   = time.time() - t0_total
    avg_drift = float(np.mean(
        [p["drift_summary"]["total_distance_km"] for p in predictions]
    ))

    _banner("PIPELINE COMPLETE")
    print(f"  {'Icebergs detected':<25} {len(icebergs)}")
    print(f"  {'Forecasts generated':<25} {len(predictions)}")
    print(f"  {'Average {hours}h drift':<25} {avg_drift:.1f} km".replace("{hours}", str(hours)))
    print(f"  {'Total runtime':<25} {total_s:.1f} s")
    print()
    print("  Output files:")
    print("    outputs/predictions/detections.json")
    print("    outputs/predictions/trajectories.json")
    print("    outputs/visualizations/detections.jpg")
    print("    outputs/visualizations/detection_map.png")
    print("    outputs/visualizations/trajectories.png")
    print("    outputs/visualizations/integrated.png")
    print(f"\n  Pipeline complete! Check the outputs/ folder.")
    print(SEP + "\n")

    return {
        "iceberg_count":    len(icebergs),
        "prediction_count": len(predictions),
        "avg_drift_km":     round(avg_drift, 1),
        "runtime_s":        round(total_s, 1),
    }


def _args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Antarctic Iceberg Trajectory Prediction — demo pipeline"
    )
    p.add_argument("--image",       type=Path,  default=None,
                   help="Satellite image path")
    p.add_argument("--mock",        action="store_true",
                   help="Skip YOLO, use synthetic icebergs")
    p.add_argument("--confidence",  type=float, default=0.25,
                   help="YOLO confidence threshold (default 0.25)")
    p.add_argument("--hours",       type=int,   default=72,
                   help="Forecast horizon hours (default 72)")
    p.add_argument("--simulations", type=int,   default=100,
                   help="Monte Carlo ensemble size (default 100)")
    return p.parse_args()


if __name__ == "__main__":
    a = _args()
    run_pipeline(
        image_path    = a.image,
        mock          = a.mock,
        confidence    = a.confidence,
        hours         = a.hours,
        n_simulations = a.simulations,
    )
