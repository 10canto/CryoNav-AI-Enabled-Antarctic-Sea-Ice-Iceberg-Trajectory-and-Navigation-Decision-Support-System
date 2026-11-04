"""
Pydantic response models for CryoNav AI API.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str


class IceZone(BaseModel):
    """Ice zone data model."""
    type: str
    percentage: int
    coordinates: List[List[float]]


class IceAnalysisResponse(BaseModel):
    """Ice analysis data response."""
    timestamp: str
    ice_zones: List[IceZone]
    average_concentration: int


class IcebergPosition(BaseModel):
    """Iceberg position model."""
    lat: float
    lon: float


class IcebergSize(BaseModel):
    """Iceberg size model."""
    length: int
    width: int


class Iceberg(BaseModel):
    """Iceberg data model."""
    id: str
    position: IcebergPosition
    size_meters: IcebergSize
    confidence: float
    detection_time: str


class IcebergsResponse(BaseModel):
    """Icebergs data response."""
    icebergs: List[Iceberg]


class TrajectoryPoint(BaseModel):
    """Trajectory point model."""
    time: str
    position: IcebergPosition
    uncertainty_radius_km: int


class Prediction(BaseModel):
    """Drift prediction model."""
    iceberg_id: str
    trajectory: List[TrajectoryPoint]


class PredictionsResponse(BaseModel):
    """Drift predictions response."""
    predictions: List[Prediction]


class Waypoint(BaseModel):
    """Route waypoint model."""
    lat: float
    lon: float


class Route(BaseModel):
    """Route option model."""
    type: str
    waypoints: List[Waypoint]
    distance_km: int
    time_hours: float
    fuel_liters: int
    risk_score: int


class RoutesResponse(BaseModel):
    """Routes data response."""
    routes: List[Route]
    current_selected: str


class RiskAssessmentResponse(BaseModel):
    """Risk assessment response."""
    level: str
    message: str
    ice_concentration: int
    nearest_iceberg_km: float
    collision_risk_percent: int


class ExplanationResponse(BaseModel):
    """Explanation text response."""
    explanation: str


class AdvanceTimeResponse(BaseModel):
    """Advance time response."""
    scenario: int
    message: str


class ResetDemoResponse(BaseModel):
    """Reset demo response."""
    message: str


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    scenario: int


class AlertRequest(BaseModel):
    """Alert request model."""
    message: str
    severity: str  # RED, ORANGE, YELLOW
    recipients: list[str] = ["bridge", "mission_control"]