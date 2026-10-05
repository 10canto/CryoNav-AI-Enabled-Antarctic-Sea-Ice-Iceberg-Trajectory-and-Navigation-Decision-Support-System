"""
Training Pipeline for Iceberg Trajectory Prediction
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import os
import json
from datetime import datetime
from model import IcebergTrajectoryLSTM
from data_processor import IcebergDataProcessor
import warnings
warnings.filterwarnings('ignore')

class IcebergTrajectoryTrainer:
    """
    Training pipeline for iceberg trajectory prediction
    """
    
    def __init__(self, 
                 data_path: str,
                 output_dir: str,
                 sequence_length: int = 30,
                 prediction_horizon: int = 7):
        """
        Initialize the trainer
        
        Args:
            data_path: Path to processed iceberg data CSV
            output_dir: Directory to save results
            sequence_length: Number of past days for input
            prediction_horizon: Number of future days to predict
        """
        self.data_path = data_path
        self.output_dir = Path(output_dir)
        self.sequence_length = sequence_length
        self.prediction_horizon = prediction_horizon
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "models").mkdir(exist_ok=True)
        (self.output_dir / "plots").mkdir(exist_ok=True)
        
        self.model = None
        self.training_history = None
        self.data_stats = {}
    
    def load_data(self) -> pd.DataFrame:
        """
        Load processed iceberg data
        """
        print(f"Loading data from {self.data_path}")
        
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        
        df = pd.read_csv(self.data_path)
        
        # Convert datetime column
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
        
        print(f"Loaded {len(df)} observations for {df['iceberg_id'].nunique()} icebergs")
        
        # Data statistics
        self.data_stats = {
            'total_observations': len(df),
            'unique_icebergs': df['iceberg_id'].nunique(),
            'date_range': {
                'start': df['datetime'].min().strftime('%Y-%m-%d'),
                'end': df['datetime'].max().strftime('%Y-%m-%d')
            },
            'iceberg_stats': {
                'avg_observations_per_iceberg': len(df) / df['iceberg_id'].nunique(),
                'min_observations': df.groupby('iceberg_id').size().min(),
                'max_observations': df.groupby('iceberg_id').size().max()
            }
        }
        
        return df
    
    def analyze_data(self, df: pd.DataFrame):
        """
        Create data analysis plots and statistics
        """
        print("Creating data analysis plots...")
        
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Iceberg Dataset Analysis', fontsize=16, fontweight='bold')
        
        # 1. Observations per iceberg
        iceberg_counts = df.groupby('iceberg_id').size().sort_values(ascending=False)
        axes[0, 0].hist(iceberg_counts, bins=30, alpha=0.7, color='skyblue')
        axes[0, 0].set_title('Observations per Iceberg')
        axes[0, 0].set_xlabel('Number of Observations')
        axes[0, 0].set_ylabel('Number of Icebergs')
        
        # 2. Speed distribution
        if 'speed_km_day' in df.columns:
            speed_clean = df['speed_km_day'].dropna()
            speed_clean = speed_clean[speed_clean < speed_clean.quantile(0.99)]  # Remove outliers
            axes[0, 1].hist(speed_clean, bins=50, alpha=0.7, color='lightcoral')
            axes[0, 1].set_title('Iceberg Speed Distribution')
            axes[0, 1].set_xlabel('Speed (km/day)')
            axes[0, 1].set_ylabel('Frequency')
        
        # 3. Size distribution
        if 'area_km2' in df.columns:
            size_clean = df['area_km2'].dropna()
            size_clean = size_clean[size_clean > 0]
            axes[0, 2].hist(np.log10(size_clean + 1), bins=30, alpha=0.7, color='lightgreen')
            axes[0, 2].set_title('Iceberg Size Distribution (log scale)')
            axes[0, 2].set_xlabel('Log10(Area km²)')
            axes[0, 2].set_ylabel('Frequency')
        
        # 4. Temporal distribution
        df['month'] = df['datetime'].dt.month
        monthly_counts = df['month'].value_counts().sort_index()
        axes[1, 0].bar(monthly_counts.index, monthly_counts.values, color='gold', alpha=0.7)
        axes[1, 0].set_title('Observations by Month')
        axes[1, 0].set_xlabel('Month')
        axes[1, 0].set_ylabel('Number of Observations')
        
        # 5. Spatial distribution
        if 'lat' in df.columns and 'lon' in df.columns:
            scatter = axes[1, 1].scatter(df['lon'], df['lat'], 
                                       c=df['speed_km_day'] if 'speed_km_day' in df.columns else 'blue',
                                       alpha=0.5, s=1, cmap='viridis')
            axes[1, 1].set_title('Iceberg Positions')
            axes[1, 1].set_xlabel('Longitude')
            axes[1, 1].set_ylabel('Latitude')
            if 'speed_km_day' in df.columns:
                plt.colorbar(scatter, ax=axes[1, 1], label='Speed (km/day)')
        
        # 6. Feature correlation heatmap
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            im = axes[1, 2].imshow(corr_matrix, cmap='RdBu_r', vmin=-1, vmax=1)
            axes[1, 2].set_title('Feature Correlations')
            axes[1, 2].set_xticks(range(len(corr_matrix.columns)))
            axes[1, 2].set_yticks(range(len(corr_matrix.columns)))
            axes[1, 2].set_xticklabels(corr_matrix.columns, rotation=45, ha='right')
            axes[1, 2].set_yticklabels(corr_matrix.columns)
            plt.colorbar(im, ax=axes[1, 2])
        
        plt.tight_layout()
        plot_path = self.output_dir / "plots" / "data_analysis.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"Data analysis plot saved to {plot_path}")
    
    def train_model(self, df: pd.DataFrame):
        """
        Train the LSTM model
        """
        print(f"Training LSTM model (sequence_length={self.sequence_length}, prediction_horizon={self.prediction_horizon})")
        
        # Initialize model
        self.model = IcebergTrajectoryLSTM(
            sequence_length=self.sequence_length,
            prediction_horizon=self.prediction_horizon,
            lstm_units=[128, 64, 32],  # 3-layer LSTM
            dropout_rate=0.3,
            learning_rate=0.001
        )
        
        # Prepare data
        X_train, X_test, y_train, y_test = self.model.prepare_data(df)
        
        # Train model
        model_path = self.output_dir / "models" / f"iceberg_lstm_{self.sequence_length}_{self.prediction_horizon}"
        
        self.training_history = self.model.train(
            X_train, y_train, X_test, y_test,
            epochs=200,
            batch_size=64,
            model_save_path=str(model_path) + "_model.h5"
        )
        
        # Save model
        self.model.save_model(str(model_path))
        
        # Store test data for evaluation
        self.X_test = X_test
        self.y_test = y_test
        
        print("Model training completed!")
        
        return self.training_history
    
    def plot_training_history(self):
        """
        Plot training history
        """
        if self.training_history is None:
            print("No training history available")
            return
        
        print("Creating training history plots...")
        
        fig, axes = plt.subplots(1, 2, figsize=(15, 5))
        
        # Loss plot
        axes[0].plot(self.training_history['loss'], label='Training Loss', color='blue')
        axes[0].plot(self.training_history['val_loss'], label='Validation Loss', color='red')
        axes[0].set_title('Model Loss')
        axes[0].set_xlabel('Epoch')
        axes[0].set_ylabel('Mean Squared Error')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # MAE plot
        if 'mae' in self.training_history:
            axes[1].plot(self.training_history['mae'], label='Training MAE', color='blue')
            axes[1].plot(self.training_history['val_mae'], label='Validation MAE', color='red')
            axes[1].set_title('Model MAE')
            axes[1].set_xlabel('Epoch')
            axes[1].set_ylabel('Mean Absolute Error')
            axes[1].legend()
            axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plot_path = self.output_dir / "plots" / "training_history.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"Training history plot saved to {plot_path}")
    
    def evaluate_model(self):
        """
        Evaluate model performance
        """
        if self.model is None or not hasattr(self, 'X_test'):
            print("Model not trained yet")
            return
        
        print("Evaluating model performance...")
        
        # Make predictions on test set
        predictions = self.model.predict(self.X_test)
        
        # Calculate metrics for each prediction step
        metrics = {}
        
        for step in range(self.prediction_horizon):
            y_true_step = self.y_test[:, step, :]  # (n_samples, 2)
            y_pred_step = predictions[:, step, :]  # (n_samples, 2)
            
            # Calculate distance errors (using Haversine formula)
            distance_errors = []
            for i in range(len(y_true_step)):
                true_lat, true_lon = y_true_step[i]
                pred_lat, pred_lon = y_pred_step[i]
                
                # Haversine distance
                R = 6371  # Earth's radius in km
                dlat = np.radians(pred_lat - true_lat)
                dlon = np.radians(pred_lon - true_lon)
                a = np.sin(dlat/2)**2 + np.cos(np.radians(true_lat)) * np.cos(np.radians(pred_lat)) * np.sin(dlon/2)**2
                c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
                distance = R * c
                distance_errors.append(distance)
            
            distance_errors = np.array(distance_errors)
            
            metrics[f'day_{step+1}'] = {
                'mean_error_km': np.mean(distance_errors),
                'median_error_km': np.median(distance_errors),
                'std_error_km': np.std(distance_errors),
                'max_error_km': np.max(distance_errors),
                'mae_lat': np.mean(np.abs(y_true_step[:, 0] - y_pred_step[:, 0])),
                'mae_lon': np.mean(np.abs(y_true_step[:, 1] - y_pred_step[:, 1]))
            }
        
        # Print results
        print("\n=== MODEL PERFORMANCE ===")
        for day, day_metrics in metrics.items():
            print(f"\n{day.upper()} AHEAD:")
            print(f"  Mean distance error: {day_metrics['mean_error_km']:.2f} km")
            print(f"  Median distance error: {day_metrics['median_error_km']:.2f} km")
            print(f"  Std distance error: {day_metrics['std_error_km']:.2f} km")
            print(f"  Max distance error: {day_metrics['max_error_km']:.2f} km")
        
        # Save metrics
        metrics_path = self.output_dir / "models" / "performance_metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        return metrics
    
    def save_training_report(self):
        """
        Save comprehensive training report
        """
        report = {
            'training_config': {
                'sequence_length': self.sequence_length,
                'prediction_horizon': self.prediction_horizon,
                'model_architecture': self.model.lstm_units if self.model else None,
                'dropout_rate': self.model.dropout_rate if self.model else None,
                'learning_rate': self.model.learning_rate if self.model else None
            },
            'data_statistics': self.data_stats,
            'training_completed': datetime.now().isoformat(),
            'training_history': self.training_history
        }
        
        report_path = self.output_dir / "training_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Training report saved to {report_path}")

def main():
    """
    Main training pipeline
    """
    print("🧊 Starting Iceberg Trajectory Prediction Training Pipeline 🧊\n")
    
    # Configuration
    data_path = r"C:\Users\Anto\OneDrive\Desktop\CryoNav-AI-Enabled-Antarctic-Sea-Ice-Iceberg-Trajectory-and-Navigation-Decision-Support-System\iceberg-trajectory-ml\data\processed_icebergs.csv"
    output_dir = r"C:\Users\Anto\OneDrive\Desktop\CryoNav-AI-Enabled-Antarctic-Sea-Ice-Iceberg-Trajectory-and-Navigation-Decision-Support-System\iceberg-trajectory-ml\results"
    
    # Initialize trainer
    trainer = IcebergTrajectoryTrainer(
        data_path=data_path,
        output_dir=output_dir,
        sequence_length=30,  # Use 30 days of history
        prediction_horizon=7  # Predict 7 days ahead
    )
    
    try:
        # Step 1: Load data
        df = trainer.load_data()
        
        # Step 2: Data analysis
        trainer.analyze_data(df)
        
        # Step 3: Train model
        training_history = trainer.train_model(df)
        
        # Step 4: Plot training results
        trainer.plot_training_history()
        
        # Step 5: Evaluate model
        metrics = trainer.evaluate_model()
        
        # Step 6: Save report
        trainer.save_training_report()
        
        print("\n🎉 Training pipeline completed successfully!")
        print(f"📁 Results saved to: {trainer.output_dir}")
        
    except FileNotFoundError:
        print("❌ Data file not found!")
        print("Please run data_processor.py first to process the raw iceberg data.")
    except Exception as e:
        print(f"❌ Error during training: {str(e)}")
        raise

if __name__ == "__main__":
    main()