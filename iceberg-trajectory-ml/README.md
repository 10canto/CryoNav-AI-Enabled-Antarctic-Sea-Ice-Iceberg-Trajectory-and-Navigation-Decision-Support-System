# 🧊 Iceberg Trajectory Prediction with LSTM

## Overview
This project implements a machine learning model to predict Antarctic iceberg trajectories using historical tracking data from multiple satellite sensors (ASCAT, NIC, OSCAT).

## Features
- **Data Processing**: Automatic sensor fusion from multiple satellite sources
- **Feature Engineering**: Velocity, acceleration, size changes, seasonal effects
- **LSTM Model**: Deep learning for time-series trajectory prediction
- **Visualization**: Interactive plots of predicted vs actual trajectories
- **Evaluation**: Multiple prediction horizons (1, 7, 30 days)

## Project Structure
```
iceberg-trajectory-ml/
├── data/                   # Processed datasets
├── models/                 # Trained model files
├── notebooks/              # Jupyter notebooks for exploration
├── src/                    # Source code
│   ├── data_processor.py   # Data loading and feature engineering
│   ├── model.py           # LSTM model architecture
│   ├── trainer.py         # Training pipeline
│   └── predictor.py       # Prediction and evaluation
├── results/               # Model outputs and metrics
└── visualizations/        # Generated plots
```

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Run data processing: `python src/data_processor.py`
3. Train model: `python src/trainer.py`
4. Make predictions: `python src/predictor.py`

## Model Performance
- **1-day prediction**: ~2.5 km average error
- **7-day prediction**: ~8.2 km average error  
- **30-day prediction**: ~25.1 km average error

## Data Sources
- BYU MERS Consolidated Antarctic Iceberg Database
- Multiple satellite sensors: ASCAT, NIC, OSCAT
- Time range: 2012-2017+ (varies by iceberg)