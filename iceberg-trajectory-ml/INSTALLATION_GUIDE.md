# 🧊 Iceberg Trajectory Prediction - Installation Guide

## Quick Start (Recommended)

### Option 1: Basic Data Processing First ⭐
**Start here if you're having package installation issues**

```bash
# Navigate to project directory
cd iceberg-trajectory-ml

# Run basic data processing (no ML dependencies needed)
python run_simple.py
```

This will:
- Process your iceberg CSV files
- Create engineered features
- Save processed data
- Work with just numpy, pandas, matplotlib

### Option 2: Step-by-Step Installation

1. **Update pip and install build tools:**
```bash
python -m pip install --upgrade pip
python -m pip install --upgrade setuptools wheel
```

2. **Install packages one by one:**
```bash
python -m pip install numpy pandas matplotlib
python -m pip install scikit-learn tqdm plotly seaborn
python -m pip install tensorflow  # or tensorflow-cpu for CPU only
```

3. **Run the pipeline:**
```bash
python main.py
```

### Option 3: Automated Setup
```bash
python setup.py install
```

## Troubleshooting Installation Issues

### Problem: "Cannot import setuptools.build_meta"
**Solution:**
```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install --no-build-isolation tensorflow
```

### Problem: TensorFlow installation fails
**Solutions:**
1. **Use CPU version:** `pip install tensorflow-cpu`
2. **Use conda:** `conda install tensorflow`
3. **Skip ML for now:** Just run `python run_simple.py`

### Problem: Python version conflicts
**Requirements:**
- Python 3.8 - 3.11 (TensorFlow compatibility)
- Python 3.14 might have issues with some packages

**Check your version:**
```bash
python --version
```

### Problem: Permission errors
**Solution (Windows):**
```bash
python -m pip install --user numpy pandas matplotlib
```

## Alternative: Minimal Setup

If you just want to process the data and explore it:

**Install only essential packages:**
```bash
pip install numpy pandas matplotlib jupyter
```

**Then run:**
```bash
python run_simple.py          # Process data
jupyter notebook              # Explore data
```

## System Requirements

### Minimum:
- Python 3.8+
- 4GB RAM
- 2GB disk space

### Recommended:
- Python 3.9-3.11
- 8GB+ RAM (for large datasets)
- 5GB disk space
- GPU (optional, for faster training)

## Package Versions That Work Well Together

**Stable combination (tested):**
```
numpy==1.21.6
pandas==1.5.3
matplotlib==3.6.3
scikit-learn==1.2.2
tensorflow==2.11.0
plotly==5.13.1
```

## Running Without Installation Issues

### 1. Data Processing Only
```bash
python run_simple.py
```
- Processes all your iceberg CSV files
- Creates engineered features
- Saves to `data/processed_icebergs_sample.csv`
- No ML dependencies needed

### 2. Manual Analysis
```python
import pandas as pd
import matplotlib.pyplot as plt

# Load processed data
df = pd.read_csv('data/processed_icebergs_sample.csv')

# Basic analysis
print(df.describe())
df.plot(x='datetime', y='speed_km_day')
plt.show()
```

### 3. External Tools
- **Excel/LibreOffice:** Open the CSV files directly
- **R/RStudio:** Use for statistical analysis
- **Tableau/PowerBI:** For visualization

## Testing Your Installation

**Test basic packages:**
```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
print("✅ Basic packages work!")
```

**Test ML packages:**
```python
import sklearn
import tensorflow as tf
print("✅ ML packages work!")
print(f"TensorFlow version: {tf.__version__}")
```

**Test the data processor:**
```bash
python -c "from src.data_processor import IcebergDataProcessor; print('✅ Data processor works!')"
```

## Project Structure After Installation

```
iceberg-trajectory-ml/
├── data/
│   └── processed_icebergs_sample.csv    ← Your processed data
├── src/
│   ├── data_processor.py                ← Feature engineering
│   ├── model.py                         ← LSTM model
│   ├── trainer.py                       ← Training pipeline
│   └── predictor.py                     ← Predictions
├── results/                             ← Training results (auto-created)
├── visualizations/                      ← Plots (auto-created)
├── run_simple.py                        ← Start here!
├── main.py                              ← Full pipeline
└── setup.py                             ← Installation helper
```

## Need Help?

1. **Start simple:** Run `python run_simple.py` first
2. **Check Python version:** Must be 3.8-3.11
3. **Try CPU-only TensorFlow:** `pip install tensorflow-cpu`
4. **Use virtual environment:** 
   ```bash
   python -m venv iceberg_env
   iceberg_env\Scripts\activate  # Windows
   pip install numpy pandas matplotlib
   ```

## Success Indicators

✅ **Data processing works:** CSV file created in `data/` folder  
✅ **Features created:** File has columns like `speed_km_day`, `vel_lat`, etc.  
✅ **No errors:** Python runs without import/installation errors  

**Ready to proceed with ML training!** 🚀