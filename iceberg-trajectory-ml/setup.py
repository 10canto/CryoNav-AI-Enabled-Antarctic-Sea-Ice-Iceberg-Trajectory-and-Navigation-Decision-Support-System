"""
Setup script for Iceberg Trajectory Prediction
Handles dependency installation and environment setup
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def install_packages():
    """Install required packages step by step"""
    print("🧊 Setting up Iceberg Trajectory Prediction environment")
    print("=" * 60)
    
    # Update pip first
    print("Updating pip...")
    run_command(f"{sys.executable} -m pip install --upgrade pip", "Pip update")
    
    # Install setuptools and wheel first
    print("\nInstalling build tools...")
    run_command(f"{sys.executable} -m pip install --upgrade setuptools wheel", "Build tools installation")
    
    # Core packages (install one by one to avoid conflicts)
    packages = [
        "numpy>=1.21.0",
        "pandas>=1.5.0", 
        "matplotlib>=3.5.0",
        "seaborn>=0.11.0",
        "scikit-learn>=1.2.0",
        "tqdm>=4.60.0",
        "plotly>=5.0.0"
    ]
    
    print("\nInstalling core packages...")
    for package in packages:
        success = run_command(f"{sys.executable} -m pip install '{package}'", f"Installing {package}")
        if not success:
            print(f"⚠️  Failed to install {package}, continuing...")
    
    # TensorFlow (special handling)
    print("\nInstalling TensorFlow...")
    tf_success = run_command(f"{sys.executable} -m pip install tensorflow>=2.10.0", "TensorFlow installation")
    
    if not tf_success:
        print("⚠️  TensorFlow installation failed. Trying CPU-only version...")
        run_command(f"{sys.executable} -m pip install tensorflow-cpu>=2.10.0", "TensorFlow CPU installation")
    
    # Optional packages
    print("\nInstalling optional packages...")
    optional_packages = ["jupyter>=1.0.0"]
    
    for package in optional_packages:
        run_command(f"{sys.executable} -m pip install '{package}'", f"Installing {package}")
    
    print("\n✅ Setup completed!")
    print("\nTo verify installation, run: python -c \"import numpy, pandas, sklearn, tensorflow; print('All packages imported successfully!')\"")

def main():
    """Main setup function"""
    if len(sys.argv) > 1 and sys.argv[1] == "install":
        install_packages()
    else:
        print("Usage: python setup.py install")
        print("This will install all required packages for iceberg trajectory prediction.")

if __name__ == "__main__":
    main()