"""
CryoNav AI - Antarctic Ship Navigation System
FastAPI Backend for Hackathon Demo
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models import (
    HealthResponse,
    IceAnalysisResponse,
    IcebergsResponse,
    PredictionsResponse,
    RoutesResponse,
    RiskAssessmentResponse,
    ExplanationResponse,
    AdvanceTimeResponse,
    ResetDemoResponse,
    ErrorResponse,
)

# Import iceberg service for AI detection
from app.services import iceberg_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state variable for demo scenarios
current_scenario = 0
MAX_SCENARIO = 3

# Base path for scenario data
DATA_BASE_PATH = Path(__file__).parent.parent / "data" / "scenarios"

app = FastAPI(
    title="CryoNav AI API",
    description="Antarctic Ship Navigation System - Hackathon Demo",
    version="1.0.0",
    docs_url=None,  # Disable Swagger UI
    redoc_url=None,  # Disable ReDoc
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_scenario_path(scenario: int) -> Path:
    """Get the path to a scenario's data directory."""
    return DATA_BASE_PATH / f"scenario_{scenario}"


def read_json_file(filepath: Path) -> dict:
    """Read and parse a JSON file, return error dict if not found."""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return {"error": "Data not available", "scenario": current_scenario}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filepath}: {e}")
        return {"error": "Invalid data format", "scenario": current_scenario}


def read_text_file(filepath: Path) -> str:
    """Read a text file, return error message if not found."""
    try:
        with open(filepath, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return "Explanation not available"


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    logger.info("GET /api/health called")
    return HealthResponse(
        status="CryoNav API Running",
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


@app.get("/api/ice-analysis", response_model=IceAnalysisResponse)
async def get_ice_analysis():
    """Get ice analysis data for current scenario."""
    logger.info(f"GET /api/ice-analysis called (scenario={current_scenario})")
    filepath = get_scenario_path(current_scenario) / "ice_data.json"
    data = read_json_file(filepath)
    if "error" in data:
        return JSONResponse(status_code=404, content=data)
    return data


@app.get("/api/icebergs", response_model=IcebergsResponse)
async def get_icebergs():
    """
    Get iceberg data for current scenario.
    
    This endpoint uses the iceberg_service which automatically chooses between:
    - Pre-calculated scenario data (fast demo mode)
    - Real-time YOLO detection (if USE_REAL_MODEL=True)
    """
    logger.info(f"GET /api/icebergs called (scenario={current_scenario})")
    
    # Use service layer instead of direct file reading
    data = iceberg_service.get_icebergs(scenario=current_scenario)
    
    if "error" in data.get("metadata", {}):
        return JSONResponse(status_code=404, content=data)
    return data


@app.get("/api/predict-drift", response_model=PredictionsResponse)
async def get_drift_predictions(iceberg_id: Optional[str] = Query(None)):
    """Get drift predictions for current scenario, optionally filtered by iceberg_id."""
    logger.info(f"GET /api/predict-drift called (scenario={current_scenario}, iceberg_id={iceberg_id})")
    filepath = get_scenario_path(current_scenario) / "predictions.json"
    data = read_json_file(filepath)
    
    if "error" in data:
        return JSONResponse(status_code=404, content=data)
    
    if iceberg_id and "predictions" in data:
        filtered = [p for p in data["predictions"] if p.get("iceberg_id") == iceberg_id]
        return {"predictions": filtered}
    
    return data


@app.get("/api/routes", response_model=RoutesResponse)
async def get_routes():
    """Get route options for current scenario."""
    logger.info(f"GET /api/routes called (scenario={current_scenario})")
    filepath = get_scenario_path(current_scenario) / "routes.json"
    data = read_json_file(filepath)
    if "error" in data:
        return JSONResponse(status_code=404, content=data)
    return data


@app.get("/api/risk-assessment", response_model=RiskAssessmentResponse)
async def get_risk_assessment():
    """Get risk assessment for current scenario."""
    logger.info(f"GET /api/risk-assessment called (scenario={current_scenario})")
    
    # Read ice data for metrics
    ice_filepath = get_scenario_path(current_scenario) / "ice_data.json"
    ice_data = read_json_file(ice_filepath)
    
    # Read icebergs for nearest distance
    iceberg_filepath = get_scenario_path(current_scenario) / "icebergs.json"
    iceberg_data = read_json_file(iceberg_filepath)
    
    # Determine risk level based on scenario
    if current_scenario == 0:
        level = "GREEN"
        message = "All systems normal"
        collision_risk = 0
    elif current_scenario == 1:
        level = "YELLOW"
        message = "Iceberg detected - monitoring situation"
        collision_risk = 12
    elif current_scenario == 2:
        level = "ORANGE"
        message = "Warning - hazard approaching"
        collision_risk = 34
    else:  # scenario 3
        level = "RED"
        message = "EMERGENCY - immediate danger"
        collision_risk = 87
    
    # Calculate metrics
    ice_concentration = ice_data.get("average_concentration", 0) if "error" not in ice_data else 0
    
    # Calculate nearest iceberg distance (mock calculation for demo)
    nearest_iceberg_km = 0
    if "error" not in iceberg_data and iceberg_data.get("icebergs"):
        # Mock: scenario 1 ~45km, scenario 2 ~15km, scenario 3 ~3.2km
        if current_scenario == 1:
            nearest_iceberg_km = 45
        elif current_scenario == 2:
            nearest_iceberg_km = 18
        elif current_scenario == 3:
            nearest_iceberg_km = 3.2
    
    return RiskAssessmentResponse(
        level=level,
        message=message,
        ice_concentration=ice_concentration,
        nearest_iceberg_km=nearest_iceberg_km,
        collision_risk_percent=collision_risk,
    )


@app.get("/api/explanation", response_model=ExplanationResponse)
async def get_explanation():
    """Get explanation text for current scenario."""
    logger.info(f"GET /api/explanation called (scenario={current_scenario})")
    filepath = get_scenario_path(current_scenario) / "explanation.txt"
    explanation = read_text_file(filepath)
    return ExplanationResponse(explanation=explanation)


# ============================================================================
# NEW YOLO MODEL ENDPOINTS
# ============================================================================

@app.get("/api/icebergs-live")
async def get_icebergs_live(
    image_path: str = Query(..., description="Path to satellite image file"),
    confidence: float = Query(0.7, ge=0.0, le=1.0, description="Detection confidence threshold")
):
    """
    Real-time iceberg detection using YOLO model.
    
    This endpoint ALWAYS uses the live AI model, regardless of USE_REAL_MODEL setting.
    Perfect for demonstrating real AI capability to judges.
    
    Args:
        image_path: Path to satellite image (local file system)
        confidence: Confidence threshold (0.0 to 1.0)
        
    Returns:
        Iceberg detections with bounding boxes and positions
        
    Example:
        GET /api/icebergs-live?image_path=/path/to/sentinel1.jpg&confidence=0.75
    """
    logger.info(f"GET /api/icebergs-live called: image={image_path}, conf={confidence}")
    
    try:
        # Validate image path
        if not iceberg_service.validate_image_path(image_path):
            raise HTTPException(
                status_code=400,
                detail=f"Image file not found or not accessible: {image_path}"
            )
        
        # Force live detection
        result = iceberg_service.get_icebergs_live(
            image_path=image_path,
            confidence_threshold=confidence
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Live detection failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Detection error: {str(e)}"
        )


@app.post("/api/icebergs-upload")
async def upload_and_detect(
    file: UploadFile = File(...),
    confidence: float = Query(0.7, ge=0.0, le=1.0)
):
    """
    Upload satellite image and detect icebergs.
    
    Useful for testing with new images without file system access.
    
    Args:
        file: Uploaded image file (JPG, PNG, TIF)
        confidence: Detection confidence threshold
        
    Returns:
        Iceberg detections from uploaded image
    """
    import tempfile
    import shutil
    
    logger.info(f"POST /api/icebergs-upload called: file={file.filename}, conf={confidence}")
    
    try:
        # Validate file type
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.tif', '.tiff'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {allowed_extensions}"
            )
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
        
        try:
            # Run detection
            result = iceberg_service.get_icebergs_live(
                image_path=tmp_path,
                confidence_threshold=confidence
            )
            
            # Add filename to metadata
            result["metadata"]["uploaded_filename"] = file.filename
            
            return result
            
        finally:
            # Clean up temp file
            try:
                Path(tmp_path).unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload detection failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Detection error: {str(e)}"
        )


@app.get("/api/model-status")
async def get_model_status():
    """
    Get YOLO model and service status.
    
    Returns information about:
    - Current mode (demo vs live)
    - Model loaded status
    - Available scenarios
    - Configuration
    """
    logger.info("GET /api/model-status called")
    
    try:
        status = iceberg_service.get_service_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        return {
            "error": str(e),
            "mode": "unknown"
        }


@app.post("/api/model-mode")
async def set_model_mode(use_real_model: bool = Query(..., description="True for live AI, False for demo")):
    """
    Toggle between demo mode and live AI mode.
    
    Args:
        use_real_model: True to enable real-time YOLO detection, False for scenario data
        
    Returns:
        Status after mode change
        
    Example:
        POST /api/model-mode?use_real_model=true
    """
    logger.info(f"POST /api/model-mode called: use_real_model={use_real_model}")
    
    try:
        result = iceberg_service.set_mode(use_real_model)
        return result
    except Exception as e:
        logger.error(f"Failed to set mode: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Mode change failed: {str(e)}"
        )


# ============================================================================
# SEA-ICE ENDPOINT
# ============================================================================

@app.get("/api/seaice")
async def get_seaice(date: str = Query("2020-08-15", description="Date in YYYY-MM-DD format")):
    """
    Get sea-ice concentration data for a specific date.
    
    # Real data: Copernicus Marine GLORYS12 reanalysis via A-AMAR pipeline
    
    Args:
        date: Date in YYYY-MM-DD format (default: 2020-08-15)
        
    Returns:
        Sea-ice concentration grid with cells containing lat, lon, concentration
    """
    logger.info(f"GET /api/seaice called: date={date}")
    
    # Path to the sea-ice data file (relative to backend folder)
    seaice_file = Path(__file__).parent.parent.parent / "iceberg-trajectory-ml" / "data" / "validation" / "demo_seaice_grid.json"
    
    # Check if file exists
    if not seaice_file.exists():
        logger.error(f"Sea-ice data file not found: {seaice_file}")
        return JSONResponse(
            status_code=503,
            content={
                "error": "Sea-ice data not available",
                "simulated": False
            }
        )
    
    try:
        # Read the JSON file
        with open(seaice_file, "r") as f:
            data = json.load(f)
        
        # Filter to requested date and skip null/NaN/missing concentrations
        cells = []
        for row in data:
            if row.get("date") == date:
                concentration = row.get("concentration")
                # Skip if concentration is None, NaN, or missing
                if concentration is not None and not (isinstance(concentration, float) and concentration != concentration):
                    cells.append({
                        "lat": row["lat"],
                        "lon": row["lon"],
                        "concentration": concentration
                    })
        
        # Return response
        return {
            "date": date,
            "source": "Copernicus Marine GLORYS12 reanalysis",
            "grid_resolution_deg": 2.0,
            "cells": cells
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse sea-ice JSON: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "error": "Sea-ice data not available",
                "simulated": False
            }
        )
    except Exception as e:
        logger.error(f"Failed to read sea-ice data: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "error": "Sea-ice data not available",
                "simulated": False
            }
        )


# ============================================================================
# EXISTING ENDPOINTS CONTINUE BELOW
# ============================================================================

@app.post("/api/advance-time", response_model=AdvanceTimeResponse)
async def advance_time():
    """Advance to next scenario (loops back to 0 after max)."""
    global current_scenario
    logger.info(f"POST /api/advance-time called (current={current_scenario})")
    
    current_scenario = (current_scenario + 1) % (MAX_SCENARIO + 1)
    
    return AdvanceTimeResponse(
        scenario=current_scenario,
        message=f"Advanced to scenario {current_scenario}",
    )


@app.post("/api/reset-demo", response_model=ResetDemoResponse)
async def reset_demo():
    """Reset demo to initial scenario (0)."""
    global current_scenario
    logger.info("POST /api/reset-demo called")
    
    current_scenario = 0
    
    return ResetDemoResponse(message="Demo reset to initial state")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
