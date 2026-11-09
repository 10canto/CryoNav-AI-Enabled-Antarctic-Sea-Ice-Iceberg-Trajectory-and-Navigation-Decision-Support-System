import pickle
from pathlib import Path

pkl_path = Path(__file__).parent.parent / "data" / "validation" / "drift_model.pkl"
print(f"Loading from: {pkl_path}")
print(f"Exists: {pkl_path.exists()}")
print(f"Size: {pkl_path.stat().st_size} bytes")

with open(pkl_path, 'rb') as f:
    data = pickle.load(f)
    print(f"Loaded successfully!")
    print(f"Keys: {list(data.keys())}")
    print(f"Features: {len(data['features'])}")
