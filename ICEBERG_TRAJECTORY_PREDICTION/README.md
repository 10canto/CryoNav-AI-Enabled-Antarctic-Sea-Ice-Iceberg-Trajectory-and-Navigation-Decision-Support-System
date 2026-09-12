# Antarctic Iceberg Trajectory Prediction System

## Overview
AI-powered drift prediction system that forecasts iceberg movement 24-72 hours ahead using physics-based modeling integrated with YOLO detection.

## Features
- YOLO-based iceberg detection integration (Guy 2's model)
- Physics-based drift prediction (ocean currents + wind + Coriolis)
- Monte Carlo uncertainty quantification
- REST API for real-time predictions
- Interactive visualizations
- Optional LSTM enhancement

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Run integrated demo
python main.py

# Start API server
python api_server.py
```

## Project Structure
```
ICEBERG_TRAJECTORY_PREDICTION/
├── models/          # YOLO weights (best.pt)
├── sample_images/   # Test satellite images
├── src/            # Source code modules
├── outputs/        # Generated predictions & visualizations
├── data/           # Environmental data
└── tests/          # Test suite
```

## Integration
This system receives iceberg detections from Guy 2's YOLO model and predicts their drift trajectories for maritime safety.
