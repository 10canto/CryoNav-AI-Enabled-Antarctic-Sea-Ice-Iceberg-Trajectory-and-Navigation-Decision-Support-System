"""
Iceberg Trajectory Predictor
Make predictions and visualize results
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
from pathlib import Path
from model import IcebergTrajectoryLSTM
from data_processor import IcebergDataProcessor
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class IcebergPredictor:
    """
    Make predictions and create visualizations for iceberg trajectories
    """
    
    def __init__(self, model_path: str, output_dir: str):
        """
        Initialize predictor with trained model
        
        Args:
            model_path: Path to saved model (without extension)
            output_dir: Directory to save prediction results
        """
        self.model_path = model_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load trained model
        self.model = IcebergTrajectoryLSTM()
        self.model.load_model(model_path)
        
        print(f"Loaded model with:")
        print(f"  Sequence length: {self.model.sequence_length} days")
        print(f"  Prediction horizon: {self.model.prediction_horizon} days")
        print(f"  Features: {len(self.model.feature_columns)}")
    
    def prepare_prediction_input(self, df: pd.DataFrame, iceberg_id: str, 
                                start_date: str = None) -> np.ndarray:
        """
        Prepare input sequence for prediction
        
        Args:
            df: Processed iceberg dataframe
            iceberg_id: ID of iceberg to predict
            start_date: Starting date for prediction (if None, uses last available data)
        
        Returns:
            Input sequence array
        """
        # Filter for specific iceberg
        iceberg_data = df[df['iceberg_id'] == iceberg_id].copy()
        iceberg_data = iceberg_data.sort_values('datetime').reset_index(drop=True)
        
        if len(iceberg_data) < self.model.sequence_length:
            raise ValueError(f"Insufficient data for {iceberg_id}. Need {self.model.sequence_length} observations, got {len(iceberg_data)}")
        
        # Select date range
        if start_date:
            start_dt = pd.to_datetime(start_date)
            # Find the sequence ending at start_date
            mask = iceberg_data['datetime'] <= start_dt
            if mask.sum() < self.model.sequence_length:
                raise ValueError(f"Insufficient data before {start_date}")
            iceberg_data = iceberg_data[mask].tail(self.model.sequence_length)
        else:
            # Use the last sequence_length observations
            iceberg_data = iceberg_data.tail(self.model.sequence_length)
        
        # Extract features
        feature_data = iceberg_data[self.model.feature_columns].values
        
        # Reshape for model input (1 sample, sequence_length, n_features)
        input_sequence = feature_data.reshape(1, self.model.sequence_length, -1)
        
        return input_sequence, iceberg_data
    
    def predict_trajectory(self, df: pd.DataFrame, iceberg_id: str,
                          start_date: str = None) -> Dict:
        """
        Predict trajectory for a specific iceberg
        
        Returns:
            Dictionary with prediction results
        """
        print(f"Predicting trajectory for {iceberg_id}...")
        
        # Prepare input
        input_sequence, input_data = self.prepare_prediction_input(df, iceberg_id, start_date)
        
        # Make prediction
        predictions = self.model.predict(input_sequence)  # Shape: (1, prediction_horizon, 2)
        
        # Extract predictions
        pred_coords = predictions[0]  # Shape: (prediction_horizon, 2)
        
        # Create prediction dataframe
        last_date = input_data['datetime'].iloc[-1]
        pred_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), 
                                 periods=self.model.prediction_horizon, freq='D')
        
        pred_df = pd.DataFrame({
            'datetime': pred_dates,
            'pred_lat': pred_coords[:, 0],
            'pred_lon': pred_coords[:, 1],
            'day_ahead': range(1, self.model.prediction_horizon + 1)
        })
        
        result = {
            'iceberg_id': iceberg_id,
            'input_data': input_data,
            'predictions': pred_df,
            'prediction_start_date': last_date.strftime('%Y-%m-%d'),
            'last_known_position': (input_data['lat'].iloc[-1], input_data['lon'].iloc[-1])
        }
        
        return result
    
    def evaluate_predictions(self, df: pd.DataFrame, iceberg_id: str,
                           test_start_date: str) -> Dict:
        """
        Evaluate predictions against actual trajectory
        
        Args:
            df: Full iceberg dataframe including test period
            iceberg_id: Iceberg to evaluate
            test_start_date: Date to start prediction from
        
        Returns:
            Evaluation results
        """
        print(f"Evaluating predictions for {iceberg_id} from {test_start_date}...")
        
        # Make prediction
        prediction_result = self.predict_trajectory(df, iceberg_id, test_start_date)
        
        # Get actual trajectory for comparison
        iceberg_data = df[df['iceberg_id'] == iceberg_id].copy()
        iceberg_data = iceberg_data.sort_values('datetime').reset_index(drop=True)
        
        test_start_dt = pd.to_datetime(test_start_date)
        actual_data = iceberg_data[iceberg_data['datetime'] > test_start_dt].head(self.model.prediction_horizon)
        
        if len(actual_data) == 0:
            return {'error': 'No actual data available for evaluation period'}\n        \n        # Calculate errors\n        errors = []\n        daily_errors = {}\n        \n        for i, (_, pred_row) in enumerate(prediction_result['predictions'].iterrows()):\n            if i < len(actual_data):\n                actual_row = actual_data.iloc[i]\n                \n                # Haversine distance error\n                error_km = self.haversine_distance(\n                    pred_row['pred_lat'], pred_row['pred_lon'],\n                    actual_row['lat'], actual_row['lon']\n                )\n                \n                errors.append(error_km)\n                daily_errors[f'day_{i+1}'] = {\n                    'error_km': error_km,\n                    'pred_lat': pred_row['pred_lat'],\n                    'pred_lon': pred_row['pred_lon'],\n                    'actual_lat': actual_row['lat'],\n                    'actual_lon': actual_row['lon'],\n                    'date': pred_row['datetime'].strftime('%Y-%m-%d')\n                }\n        \n        evaluation_result = {\n            'iceberg_id': iceberg_id,\n            'test_period': test_start_date,\n            'prediction_result': prediction_result,\n            'actual_data': actual_data,\n            'daily_errors': daily_errors,\n            'summary_metrics': {\n                'mean_error_km': np.mean(errors),\n                'median_error_km': np.median(errors),\n                'max_error_km': np.max(errors),\n                'std_error_km': np.std(errors),\n                'rmse_km': np.sqrt(np.mean(np.array(errors)**2))\n            }\n        }\n        \n        return evaluation_result\n    \n    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:\n        \"\"\"\n        Calculate Haversine distance between two points\n        \"\"\"\n        if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):\n            return np.nan\n            \n        R = 6371  # Earth's radius in km\n        \n        # Convert to radians\n        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])\n        \n        # Haversine formula\n        dlat = lat2 - lat1\n        dlon = lon2 - lon1\n        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2\n        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))\n        \n        return R * c\n    \n    def plot_trajectory_prediction(self, prediction_result: Dict, actual_data: pd.DataFrame = None,\n                                 save_path: str = None, show_plot: bool = True):\n        \"\"\"\n        Create interactive trajectory prediction plot\n        \"\"\"\n        input_data = prediction_result['input_data']\n        predictions = prediction_result['predictions']\n        iceberg_id = prediction_result['iceberg_id']\n        \n        # Create plotly figure\n        fig = go.Figure()\n        \n        # Historical trajectory (input data)\n        fig.add_trace(go.Scattermapbox(\n            lat=input_data['lat'],\n            lon=input_data['lon'],\n            mode='lines+markers',\n            marker=dict(size=8, color='blue'),\n            line=dict(color='blue', width=3),\n            name='Historical Track',\n            hovertemplate='<b>Historical</b><br>'\n                         'Date: %{text}<br>'\n                         'Lat: %{lat:.4f}<br>'\n                         'Lon: %{lon:.4f}<extra></extra>',\n            text=input_data['datetime'].dt.strftime('%Y-%m-%d')\n        ))\n        \n        # Predicted trajectory\n        fig.add_trace(go.Scattermapbox(\n            lat=predictions['pred_lat'],\n            lon=predictions['pred_lon'],\n            mode='lines+markers',\n            marker=dict(size=10, color='red', symbol='diamond'),\n            line=dict(color='red', width=3, dash='dash'),\n            name='Predicted Track',\n            hovertemplate='<b>Prediction Day %{text}</b><br>'\n                         'Date: %{customdata}<br>'\n                         'Lat: %{lat:.4f}<br>'\n                         'Lon: %{lon:.4f}<extra></extra>',\n            text=predictions['day_ahead'],\n            customdata=predictions['datetime'].dt.strftime('%Y-%m-%d')\n        ))\n        \n        # Actual trajectory (if provided for evaluation)\n        if actual_data is not None and len(actual_data) > 0:\n            fig.add_trace(go.Scattermapbox(\n                lat=actual_data['lat'],\n                lon=actual_data['lon'],\n                mode='lines+markers',\n                marker=dict(size=10, color='green', symbol='circle'),\n                line=dict(color='green', width=3),\n                name='Actual Track',\n                hovertemplate='<b>Actual</b><br>'\n                             'Date: %{text}<br>'\n                             'Lat: %{lat:.4f}<br>'\n                             'Lon: %{lon:.4f}<extra></extra>',\n                text=actual_data['datetime'].dt.strftime('%Y-%m-%d')\n            ))\n        \n        # Calculate center point for map\n        all_lats = list(input_data['lat']) + list(predictions['pred_lat'])\n        all_lons = list(input_data['lon']) + list(predictions['pred_lon'])\n        \n        if actual_data is not None and len(actual_data) > 0:\n            all_lats.extend(actual_data['lat'])\n            all_lons.extend(actual_data['lon'])\n        \n        center_lat = np.mean(all_lats)\n        center_lon = np.mean(all_lons)\n        \n        # Update layout\n        fig.update_layout(\n            title=f'Iceberg {iceberg_id} Trajectory Prediction',\n            mapbox=dict(\n                style='open-street-map',\n                center=dict(lat=center_lat, lon=center_lon),\n                zoom=6\n            ),\n            height=600,\n            showlegend=True\n        )\n        \n        if save_path:\n            fig.write_html(save_path)\n            print(f\"Interactive plot saved to {save_path}\")\n        \n        if show_plot:\n            fig.show()\n        \n        return fig\n    \n    def create_evaluation_report(self, evaluation_results: List[Dict], save_path: str = None):\n        \"\"\"\n        Create comprehensive evaluation report\n        \"\"\"\n        print(\"Creating evaluation report...\")\n        \n        # Aggregate metrics\n        all_errors = []\n        iceberg_summaries = []\n        \n        for result in evaluation_results:\n            if 'error' not in result:\n                metrics = result['summary_metrics']\n                iceberg_summaries.append({\n                    'iceberg_id': result['iceberg_id'],\n                    'test_date': result['test_period'],\n                    'mean_error_km': metrics['mean_error_km'],\n                    'max_error_km': metrics['max_error_km'],\n                    'rmse_km': metrics['rmse_km']\n                })\n                \n                # Collect all daily errors\n                for day_error in result['daily_errors'].values():\n                    all_errors.append(day_error['error_km'])\n        \n        # Overall statistics\n        overall_stats = {\n            'num_icebergs_evaluated': len(iceberg_summaries),\n            'overall_mean_error_km': np.mean(all_errors),\n            'overall_median_error_km': np.median(all_errors),\n            'overall_std_error_km': np.std(all_errors),\n            'overall_max_error_km': np.max(all_errors),\n            'overall_rmse_km': np.sqrt(np.mean(np.array(all_errors)**2))\n        }\n        \n        # Create summary plot\n        fig, axes = plt.subplots(2, 2, figsize=(15, 10))\n        fig.suptitle('Iceberg Trajectory Prediction Evaluation', fontsize=16, fontweight='bold')\n        \n        # Error distribution\n        axes[0, 0].hist(all_errors, bins=30, alpha=0.7, color='skyblue', edgecolor='black')\n        axes[0, 0].axvline(overall_stats['overall_mean_error_km'], color='red', linestyle='--', \n                          label=f'Mean: {overall_stats[\"overall_mean_error_km\"]:.1f} km')\n        axes[0, 0].set_title('Prediction Error Distribution')\n        axes[0, 0].set_xlabel('Error (km)')\n        axes[0, 0].set_ylabel('Frequency')\n        axes[0, 0].legend()\n        \n        # Per-iceberg mean errors\n        iceberg_names = [s['iceberg_id'] for s in iceberg_summaries]\n        mean_errors = [s['mean_error_km'] for s in iceberg_summaries]\n        \n        axes[0, 1].bar(range(len(iceberg_names)), mean_errors, color='lightcoral', alpha=0.7)\n        axes[0, 1].set_title('Mean Error by Iceberg')\n        axes[0, 1].set_xlabel('Iceberg ID')\n        axes[0, 1].set_ylabel('Mean Error (km)')\n        axes[0, 1].tick_params(axis='x', rotation=45)\n        \n        if len(iceberg_names) <= 10:  # Only show labels if not too many\n            axes[0, 1].set_xticks(range(len(iceberg_names)))\n            axes[0, 1].set_xticklabels(iceberg_names, rotation=45, ha='right')\n        \n        # Error vs prediction day\n        daily_errors_by_day = {}\n        for result in evaluation_results:\n            if 'error' not in result:\n                for day_key, day_data in result['daily_errors'].items():\n                    day_num = int(day_key.split('_')[1])\n                    if day_num not in daily_errors_by_day:\n                        daily_errors_by_day[day_num] = []\n                    daily_errors_by_day[day_num].append(day_data['error_km'])\n        \n        days = sorted(daily_errors_by_day.keys())\n        mean_errors_by_day = [np.mean(daily_errors_by_day[day]) for day in days]\n        std_errors_by_day = [np.std(daily_errors_by_day[day]) for day in days]\n        \n        axes[1, 0].errorbar(days, mean_errors_by_day, yerr=std_errors_by_day, \n                          marker='o', capsize=5, color='green')\n        axes[1, 0].set_title('Error vs Prediction Horizon')\n        axes[1, 0].set_xlabel('Days Ahead')\n        axes[1, 0].set_ylabel('Mean Error (km)')\n        axes[1, 0].grid(True, alpha=0.3)\n        \n        # Performance statistics table\n        axes[1, 1].axis('off')\n        stats_text = f\"\"\"\n        PERFORMANCE SUMMARY\n        \n        Icebergs Evaluated: {overall_stats['num_icebergs_evaluated']}\n        \n        Overall Mean Error: {overall_stats['overall_mean_error_km']:.2f} km\n        Overall Median Error: {overall_stats['overall_median_error_km']:.2f} km\n        Overall RMSE: {overall_stats['overall_rmse_km']:.2f} km\n        Overall Max Error: {overall_stats['overall_max_error_km']:.2f} km\n        \n        Standard Deviation: {overall_stats['overall_std_error_km']:.2f} km\n        \"\"\"\n        \n        axes[1, 1].text(0.1, 0.9, stats_text, transform=axes[1, 1].transAxes, \n                        fontsize=12, verticalalignment='top', fontfamily='monospace',\n                        bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))\n        \n        plt.tight_layout()\n        \n        if save_path:\n            plt.savefig(save_path, dpi=300, bbox_inches='tight')\n            print(f\"Evaluation report saved to {save_path}\")\n        \n        plt.show()\n        \n        # Save detailed results\n        report = {\n            'overall_statistics': overall_stats,\n            'iceberg_summaries': iceberg_summaries,\n            'daily_error_statistics': {\n                f'day_{day}': {\n                    'mean_error_km': np.mean(daily_errors_by_day[day]),\n                    'std_error_km': np.std(daily_errors_by_day[day]),\n                    'median_error_km': np.median(daily_errors_by_day[day])\n                } for day in days\n            }\n        }\n        \n        if save_path:\n            json_path = save_path.replace('.png', '.json')\n            with open(json_path, 'w') as f:\n                json.dump(report, f, indent=2, default=str)\n            print(f\"Detailed evaluation data saved to {json_path}\")\n        \n        return report\n\ndef main():\n    \"\"\"\n    Demo prediction and evaluation\n    \"\"\"\n    print(\"🧊 Iceberg Trajectory Predictor Demo 🧊\\n\")\n    \n    # Paths\n    model_path = r\"C:\\Users\\Anto\\OneDrive\\Desktop\\CryoNav-AI-Enabled-Antarctic-Sea-Ice-Iceberg-Trajectory-and-Navigation-Decision-Support-System\\iceberg-trajectory-ml\\results\\models\\iceberg_lstm_30_7\"\n    data_path = r\"C:\\Users\\Anto\\OneDrive\\Desktop\\CryoNav-AI-Enabled-Antarctic-Sea-Ice-Iceberg-Trajectory-and-Navigation-Decision-Support-System\\iceberg-trajectory-ml\\data\\processed_icebergs.csv\"\n    output_dir = r\"C:\\Users\\Anto\\OneDrive\\Desktop\\CryoNav-AI-Enabled-Antarctic-Sea-Ice-Iceberg-Trajectory-and-Navigation-Decision-Support-System\\iceberg-trajectory-ml\\visualizations\"\n    \n    try:\n        # Initialize predictor\n        predictor = IcebergPredictor(model_path, output_dir)\n        \n        # Load data\n        print(\"Loading processed data...\")\n        df = pd.read_csv(data_path)\n        df['datetime'] = pd.to_datetime(df['datetime'])\n        \n        # Get list of icebergs with sufficient data\n        iceberg_counts = df.groupby('iceberg_id').size()\n        suitable_icebergs = iceberg_counts[iceberg_counts >= predictor.model.sequence_length + 30].index\n        \n        if len(suitable_icebergs) == 0:\n            print(\"No icebergs with sufficient data found!\")\n            return\n        \n        print(f\"Found {len(suitable_icebergs)} icebergs suitable for prediction\")\n        \n        # Make predictions for a few icebergs\n        evaluation_results = []\n        \n        for i, iceberg_id in enumerate(suitable_icebergs[:5]):  # Test first 5 icebergs\n            print(f\"\\n--- Processing {iceberg_id} ({i+1}/{min(5, len(suitable_icebergs))}) ---\")\n            \n            # Find a good test date (80% through the data)\n            iceberg_data = df[df['iceberg_id'] == iceberg_id].sort_values('datetime')\n            test_idx = int(len(iceberg_data) * 0.8)\n            test_date = iceberg_data.iloc[test_idx]['datetime'].strftime('%Y-%m-%d')\n            \n            try:\n                # Evaluate prediction\n                eval_result = predictor.evaluate_predictions(df, iceberg_id, test_date)\n                \n                if 'error' not in eval_result:\n                    evaluation_results.append(eval_result)\n                    \n                    # Create trajectory plot\n                    plot_path = Path(output_dir) / f\"trajectory_{iceberg_id}.html\"\n                    predictor.plot_trajectory_prediction(\n                        eval_result['prediction_result'],\n                        eval_result['actual_data'],\n                        save_path=str(plot_path),\n                        show_plot=False\n                    )\n                    \n                    # Print results\n                    metrics = eval_result['summary_metrics']\n                    print(f\"  Mean error: {metrics['mean_error_km']:.2f} km\")\n                    print(f\"  Max error: {metrics['max_error_km']:.2f} km\")\n                else:\n                    print(f\"  Skipped: {eval_result['error']}\")\n                    \n            except Exception as e:\n                print(f\"  Error processing {iceberg_id}: {str(e)}\")\n        \n        # Create evaluation report\n        if evaluation_results:\n            print(f\"\\nCreating evaluation report for {len(evaluation_results)} icebergs...\")\n            report_path = Path(output_dir) / \"evaluation_report.png\"\n            report = predictor.create_evaluation_report(evaluation_results, str(report_path))\n            \n            print(f\"\\n🎉 Prediction evaluation completed!\")\n            print(f\"📁 Results saved to: {output_dir}\")\n            print(f\"📊 Overall mean error: {report['overall_statistics']['overall_mean_error_km']:.2f} km\")\n        else:\n            print(\"❌ No successful evaluations completed\")\n    \n    except FileNotFoundError:\n        print(\"❌ Required files not found!\")\n        print(\"Please run trainer.py first to train the model.\")\n    except Exception as e:\n        print(f\"❌ Error during prediction: {str(e)}\")\n        raise\n\nif __name__ == \"__main__\":\n    main()"