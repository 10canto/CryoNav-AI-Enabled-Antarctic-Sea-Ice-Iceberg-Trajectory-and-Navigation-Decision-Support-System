"""
FILE 5: api_server.py
FastAPI REST service for iceberg trajectory predictions.

Endpoints:
    GET  /          — service info
    GET  /health    — liveness probe
    POST /detect    — upload image -> detections + trajectories
    POST /predict   — predict from lat/lon
    GET  /docs      — Swagger UI (auto-generated)

Usage:
    python api_server.py
    uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
"""

import sys
import time
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent / "src"))

from detection_integration import IcebergDetector
from drift_physics import DriftPredictor, EnvironmentalData, drift_distance_km


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Iceberg Trajectory Prediction API",
    description=(
        "Antarctic iceberg drift forecasting.\n\n"
        "Integrates trained YOLOv5 detection (best.pt) with "
        "physics-based Monte Carlo drift prediction."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Shared service objects
# ---------------------------------------------------------------------------

_detector: Optional[IcebergDetector] = None
_predictor = DriftPredictor()
_env       = EnvironmentalData()


@app.on_event("startup")
def _startup():
    global _detector
    for path in ("weights/best.pt",
                 "../cryonav-backend/backend_ready/weights/best.pt"):
        p = Path(path)
        if p.exists():
            try:
                _detector = IcebergDetector(model_path=str(p))
                print(f"[API] Model loaded from {p}")
                return
            except Exception as e:
                print(f"[API] Could not load {p}: {e}")
    print("[API] Warning — no model found; /detect will return 503")


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class PredictRequest(BaseModel):
    iceberg_id:     str   = Field(..., example="ICE-047")
    latitude:       float = Field(..., ge=-90,  le=90,  example=-65.2)
    longitude:      float = Field(..., ge=-180, le=180, example=-64.5)
    forecast_hours: int   = Field(72,  ge=6,    le=120)
    n_simulations:  int   = Field(100, ge=10,   le=500)


class TrajectoryPoint(BaseModel):
    time_hours:     int
    latitude:       float
    longitude:      float
    uncertainty_km: Optional[float] = None
    timestamp:      str


class PredictResponse(BaseModel):
    iceberg_id:            str
    start_lat:             float
    start_lon:             float
    forecast_hours:        int
    trajectory:            List[TrajectoryPoint]
    total_drift_km:        float
    final_uncertainty_km:  float
    method:                str
    computation_time_ms:   float


# ---------------------------------------------------------------------------
# Shared logic
# ---------------------------------------------------------------------------

def _run_predict(req: PredictRequest) -> PredictResponse:
    t0   = time.time()
    cond = _env.get_conditions_at(req.latitude, req.longitude)
    traj = _predictor.predict_with_uncertainty(
        req.latitude, req.longitude,
        cond["ocean_current"], cond["wind"],
        hours=req.forecast_hours,
        n_simulations=req.n_simulations,
    )
    final  = traj[-1]
    dist   = drift_distance_km(req.latitude, req.longitude,
                               final["latitude"], final["longitude"])
    elapsed = (time.time() - t0) * 1000

    return PredictResponse(
        iceberg_id           = req.iceberg_id,
        start_lat            = req.latitude,
        start_lon            = req.longitude,
        forecast_hours       = req.forecast_hours,
        trajectory           = [TrajectoryPoint(**p) for p in traj],
        total_drift_km       = dist,
        final_uncertainty_km = final.get("uncertainty_km", 0.0),
        method               = f"physics_monte_carlo_n{req.n_simulations}",
        computation_time_ms  = round(elapsed, 1),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["Info"])
def root():
    """Service information and available endpoints."""
    return {
        "service": "Antarctic Iceberg Trajectory Prediction API",
        "version": "1.0.0",
        "status":  "operational",
        "model_loaded": _detector is not None,
        "endpoints": {
            "POST /detect":  "Upload satellite image -> detections + trajectories",
            "POST /predict": "Predict drift from lat/lon",
            "GET  /health":  "Liveness probe",
            "GET  /docs":    "Swagger UI",
        },
    }


@app.get("/health", tags=["Info"])
def health():
    """Liveness probe."""
    from datetime import datetime
    return {
        "status":       "healthy",
        "model_loaded": _detector is not None,
        "timestamp":    datetime.utcnow().isoformat() + "Z",
    }


@app.post("/detect", tags=["Detection + Prediction"])
async def detect(
    file: UploadFile = File(..., description="Satellite image (JPG/PNG)"),
    confidence: float = Query(0.25, ge=0.05, le=1.0),
    forecast_hours: int = Query(72, ge=6, le=120),
):
    """
    Upload a satellite image.
    Returns detected icebergs and their drift trajectories.
    """
    if _detector is None:
        raise HTTPException(503, "Detection model not available.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".tif", ".tiff"}:
        raise HTTPException(400, f"Unsupported file type: {suffix}")

    t0 = time.time()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        icebergs = _detector.detect_icebergs(
            str(tmp_path), confidence_threshold=confidence
        )
    finally:
        tmp_path.unlink(missing_ok=True)

    if not icebergs:
        return {
            "detection_count": 0,
            "predictions":     [],
            "message":         f"No icebergs at confidence >= {confidence}",
            "computation_time_ms": round((time.time() - t0) * 1000, 1),
        }

    results = []
    for berg in icebergs:
        req  = PredictRequest(
            iceberg_id     = berg["id"],
            latitude       = berg["position"]["lat"],
            longitude      = berg["position"]["lon"],
            forecast_hours = forecast_hours,
        )
        pred = _run_predict(req)
        results.append({
            "iceberg":    berg,
            "trajectory": [p.model_dump() for p in pred.trajectory],
            "drift_summary": {
                "total_drift_km":      pred.total_drift_km,
                "final_uncertainty_km": pred.final_uncertainty_km,
            },
        })

    return {
        "detection_count":    len(icebergs),
        "predictions":        results,
        "computation_time_ms": round((time.time() - t0) * 1000, 1),
    }


@app.post("/predict", response_model=PredictResponse, tags=["Prediction"])
def predict(req: PredictRequest):
    """Predict drift trajectory for a known iceberg position."""
    try:
        return _run_predict(req)
    except Exception as e:
        raise HTTPException(500, str(e))


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    print("Starting Iceberg Trajectory Prediction API...")
    print("Docs:  http://localhost:8000/docs")
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
