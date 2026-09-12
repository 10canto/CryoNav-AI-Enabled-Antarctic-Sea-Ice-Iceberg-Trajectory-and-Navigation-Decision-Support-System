"""
FILE 1: src/detection_integration.py
Antarctic Iceberg Detection Integration
Wraps the trained YOLOv5 model (best.pt) for satellite image analysis.

NOTE: Weights are stored in weights/best.pt (NOT models/best.pt).
      The folder is named 'weights' to avoid shadowing the yolov5 repo's
      internal 'models' Python package during torch.hub loading.
"""

import cv2
import json
import os
import sys
import shutil
import tempfile
import numpy as np
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Internal YOLOv5 loader — isolates the sys.path conflict
# ---------------------------------------------------------------------------

def _load_yolov5(weight_path: Path):
    """
    Load a YOLOv5-format .pt file via torch.hub.

    Problem: torch.hub's yolov5 repo imports `from models.common import ...`
    but if a folder named 'models' exists anywhere on sys.path it shadows
    that internal package.  Solution: change cwd to a clean temp dir and
    prepend the yolov5 repo dir to sys.path for the duration of the load.
    """
    import torch

    hub_dir     = Path(torch.hub.get_dir())
    yv5_dirs    = sorted(hub_dir.glob("ultralytics_yolov5*"))

    if not yv5_dirs:
        print("   [loader] Downloading YOLOv5 repo to torch cache...")
        try:
            torch.hub.load("ultralytics/yolov5", "yolov5n",
                           pretrained=False, trust_repo=True, verbose=False)
        except Exception:
            pass
        yv5_dirs = sorted(hub_dir.glob("ultralytics_yolov5*"))

    if not yv5_dirs:
        raise RuntimeError("YOLOv5 repo not found in torch hub cache.")

    yv5_root     = yv5_dirs[-1]
    project_root = str(Path(__file__).parent.parent.resolve())
    orig_cwd     = Path.cwd()
    orig_sys     = sys.path.copy()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_pt = Path(tmpdir) / "best.pt"
        shutil.copy(weight_path, tmp_pt)

        # sys.path: yolov5 repo first, project root removed
        sys.path = [str(yv5_root)] + [
            p for p in sys.path
            if Path(p).resolve() != Path(project_root)
        ]
        os.chdir(tmpdir)

        try:
            model = torch.hub.load(
                str(yv5_root), "custom",
                path=str(tmp_pt),
                source="local",
                verbose=False,
                trust_repo=True,
            )
        finally:
            os.chdir(orig_cwd)
            sys.path = orig_sys

    return model


# ---------------------------------------------------------------------------
# IcebergDetector
# ---------------------------------------------------------------------------

class IcebergDetector:
    """
    Wraps the trained YOLO model for satellite iceberg detection.

    Geographic defaults match the Antarctic Peninsula region.
    Pass geo_bounds to detect_icebergs() to override for a different area.
    """

    DEFAULT_BOUNDS = {
        "lat_min": -70.0,
        "lat_max": -60.0,
        "lon_min": -70.0,
        "lon_max": -55.0,
    }

    def __init__(self, model_path: str = "weights/best.pt"):
        """
        Load the YOLO model.

        Args:
            model_path: Path to best.pt weights file.
                        Defaults to weights/best.pt (relative to cwd).
        """
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(
                f"🔴 Model weights not found: '{model_path}'\n"
                "   Expected: ICEBERG_TRAJECTORY_PREDICTION/weights/best.pt\n"
                "   Run:      python ../setup_project.py  to copy them."
            )

        print(f"🤖 Loading YOLO model: {model_path}")

        # Stage 1 — Ultralytics YOLOv8 API
        try:
            from ultralytics import YOLO
            self.model    = YOLO(str(model_path))
            self._backend = "ultralytics_v8"
            print(f"✅ Model loaded (YOLOv8 backend)")
            self.model_path = model_path
            return
        except TypeError:
            print("   ℹ️  YOLOv5 format detected — switching to torch.hub loader")
        except Exception as e:
            print(f"   ⚠️  Ultralytics error: {e}")

        # Stage 2 — torch.hub YOLOv5 (needs the weights/ rename trick)
        try:
            self.model    = _load_yolov5(model_path)
            self._backend = "yolov5_hub"
            print("✅ Model loaded (YOLOv5 backend)")
            self.model_path = model_path
            return
        except Exception as e:
            print(f"   ⚠️  YOLOv5 loader failed: {e}")

        # Stage 3 — download yolov8n as generic fallback
        print("⚠️  Using yolov8n fallback (generic — not iceberg-trained)")
        from ultralytics import YOLO
        self.model    = YOLO("yolov8n.pt")
        self._backend = "yolov8n_fallback"
        self.model_path = model_path
        print("✅ Fallback model ready")

    # ------------------------------------------------------------------

    def detect_icebergs(
        self,
        image_path: str,
        confidence_threshold: float = 0.25,
        geo_bounds: dict = None,
        meters_per_pixel: float = 10.0,
    ) -> list:
        """
        Detect icebergs in a satellite image.

        Args:
            image_path:           Path to satellite image (JPG/PNG/TIFF).
            confidence_threshold: Minimum YOLO confidence (0–1).
            geo_bounds:           Geographic extent of the image
                                  {lat_min, lat_max, lon_min, lon_max}.
                                  Defaults to Antarctic Peninsula region.
            meters_per_pixel:     Spatial resolution for size estimation.

        Returns:
            List of iceberg dicts with id, position, size_meters,
            confidence, bbox, source_image, and detection_time.
        """
        image_path = Path(image_path)
        bounds     = geo_bounds or self.DEFAULT_BOUNDS

        print(f"\n🛰️  Analysing: {image_path.name}")

        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"❌ Cannot read image: {image_path}")
        img_h, img_w = img.shape[:2]

        raw = self._infer(image_path, confidence_threshold)

        icebergs = []
        for idx, (x1, y1, x2, y2, conf) in enumerate(raw):
            cx   = (x1 + x2) / 2.0
            cy   = (y1 + y2) / 2.0
            w_px = x2 - x1
            h_px = y2 - y1

            lat = (bounds["lat_max"]
                   - (cy / img_h) * (bounds["lat_max"] - bounds["lat_min"]))
            lon = (bounds["lon_min"]
                   + (cx / img_w) * (bounds["lon_max"] - bounds["lon_min"]))

            width_m  = w_px * meters_per_pixel
            height_m = h_px * meters_per_pixel

            berg = {
                "id":             f"ICE_{datetime.utcnow().strftime('%Y%m%d')}_{idx:03d}",
                "detection_time": datetime.utcnow().isoformat() + "Z",
                "position": {
                    "lat": round(float(lat), 6),
                    "lon": round(float(lon), 6),
                },
                "size_meters": {
                    "width":   round(float(width_m),  1),
                    "height":  round(float(height_m), 1),
                    "area_m2": round(float(width_m * height_m), 1),
                },
                "pixel_bbox":     {"x1": int(x1), "y1": int(y1),
                                   "x2": int(x2), "y2": int(y2)},
                "confidence":     round(float(conf), 3),
                "source_image":   image_path.name,
                "detector_model": f"YOLO_{self._backend}",
            }
            icebergs.append(berg)
            print(f"   🧊 [{idx+1:2d}] {lat:.4f}°, {lon:.4f}°  "
                  f"{width_m:.0f}m x {height_m:.0f}m  conf={conf:.1%}")

        print(f"\n📊 Total detections: {len(icebergs)}")
        return icebergs

    # ------------------------------------------------------------------

    def _infer(self, image_path: Path, conf: float) -> list:
        """Run inference → list of (x1,y1,x2,y2,confidence)."""
        boxes = []
        if self._backend in ("ultralytics_v8", "yolov8n_fallback"):
            res = self.model(str(image_path), conf=conf, verbose=False)
            for b in res[0].boxes:
                x1, y1, x2, y2 = b.xyxy[0].cpu().numpy()
                boxes.append((x1, y1, x2, y2, float(b.conf[0])))
        elif self._backend == "yolov5_hub":
            res = self.model(str(image_path))
            df  = res.pandas().xyxy[0]
            for _, row in df.iterrows():
                if row["confidence"] >= conf:
                    boxes.append((row["xmin"], row["ymin"],
                                  row["xmax"], row["ymax"],
                                  row["confidence"]))
        return boxes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def visualize_detections(
    image_path: str,
    icebergs: list,
    output_path: str = "outputs/visualizations/detections.jpg",
) -> Path:
    """
    Draw red bounding boxes on the original satellite image.

    Args:
        image_path:  Original satellite image path.
        icebergs:    List from IcebergDetector.detect_icebergs().
        output_path: Where to write the annotated JPEG.

    Returns:
        Path to saved image.
    """
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Cannot read: {image_path}")
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    fig, ax = plt.subplots(1, figsize=(14, 11))
    ax.imshow(img_rgb)

    for berg in icebergs:
        b  = berg["pixel_bbox"]
        bw = b["x2"] - b["x1"]
        bh = b["y2"] - b["y1"]
        ax.add_patch(patches.Rectangle(
            (b["x1"], b["y1"]), bw, bh,
            linewidth=2, edgecolor="#ef4444", facecolor="none",
        ))
        ax.text(
            b["x1"], b["y1"] - 6,
            f"{berg['id']}\n{berg['confidence']:.0%} | "
            f"{berg['size_meters']['width']:.0f}x"
            f"{berg['size_meters']['height']:.0f}m",
            color="#ef4444", fontsize=7, weight="bold",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.75),
        )

    ax.set_title(
        f"Iceberg Detections — {Path(image_path).name}  "
        f"({len(icebergs)} detected)",
        fontsize=13, weight="bold",
    )
    ax.axis("off")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"🖼️  Saved detection image → {out}")
    return out


def save_detection_results(
    icebergs: list,
    output_path: str = "outputs/predictions/detections.json",
) -> Path:
    """Save detection list as JSON."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "detection_count": len(icebergs),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "icebergs": icebergs,
    }, indent=2))
    print(f"💾 Saved detections JSON → {out}")
    return out
