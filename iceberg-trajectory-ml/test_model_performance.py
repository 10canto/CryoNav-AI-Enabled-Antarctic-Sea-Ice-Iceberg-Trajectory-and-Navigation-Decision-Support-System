"""
Model Performance Testing with R² Score
Tests the iceberg prediction model against historical trajectory data
"""

import pandas as pd
import numpy as np
from working_predictor import WorkingIcebergPredictor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class ModelPerformanceTester:
    """
    Test the iceberg prediction model performance
    """
    
    def __init__(self):
        """Initialize the tester"""
        self.predictor = WorkingIcebergPredictor()
        self.test_results = {}
        self.historical_data = None
        
    def load_historical_data(self):
        """Load historical trajectory data for testing"""
        # Try to load the sample dataset first
        sample_path = Path(__file__).parent / "data" / "iceberg_dataset_sample.csv"
        
        if sample_path.exists():
            print(f"📊 Loading historical data from {sample_path}")
            df = pd.read_csv(sample_path)
            df['datetime'] = pd.to_datetime(df['datetime'])
            self.historical_data = df
            print(f"✅ Loaded {len(df)} historical observations for {df['iceberg_id'].nunique()} icebergs")
            return True
        else:
            # Create synthetic test data based on current icebergs
            print("⚠️  No historical data found, creating synthetic test trajectories...")
            return self.create_synthetic_test_data()
    
    def create_synthetic_test_data(self):
        """Create synthetic historical trajectories for testing"""
        if self.predictor.current_icebergs is None:
            print("❌ No current iceberg data available")
            return False
        
        synthetic_data = []
        
        # For each current iceberg, create a synthetic historical trajectory
        for _, iceberg in self.predictor.current_icebergs.iterrows():
            iceberg_id = iceberg['Iceberg']
            current_lat = iceberg['Lat']
            current_lon = iceberg['Lon']
            
            # Generate 30 days of synthetic past trajectory
            dates = pd.date_range(end=datetime.now(), periods=31, freq='D')
            
            # Get regional pattern for this iceberg
            region_key, region_pattern = self.predictor.identify_region(current_lat, current_lon)
            
            # Base velocities (reverse engineering from current position)
            base_vel_lat = -region_pattern['vel_lat_per_day']  # Reverse direction
            base_vel_lon = -region_pattern['vel_lon_per_day']
            
            for i, date in enumerate(dates[:-1]):  # Exclude the last date (current position)
                days_back = len(dates) - 1 - i
                
                # Calculate past position with some noise
                noise_factor = 0.1
                lat_noise = np.random.normal(0, noise_factor * days_back * abs(base_vel_lat))
                lon_noise = np.random.normal(0, noise_factor * days_back * abs(base_vel_lon))
                
                past_lat = current_lat + (base_vel_lat * days_back) + lat_noise
                past_lon = current_lon + (base_vel_lon * days_back) + lon_noise
                
                # Calculate speed
                if i > 0:
                    prev_lat = synthetic_data[-1]['lat']
                    prev_lon = synthetic_data[-1]['lon']
                    speed = self.predictor.haversine_distance(prev_lat, prev_lon, past_lat, past_lon)
                else:
                    speed = region_pattern['base_speed_km_day'] * np.random.uniform(0.7, 1.3)
                
                synthetic_data.append({
                    'iceberg_id': iceberg_id,
                    'datetime': date,
                    'lat': past_lat,
                    'lon': past_lon,
                    'speed_km_day': speed,
                    'area_km2': iceberg['Area_km2'],
                    'data_source': 'synthetic'
                })
        
        # Add current positions as the final observations
        for _, iceberg in self.predictor.current_icebergs.iterrows():
            synthetic_data.append({
                'iceberg_id': iceberg['Iceberg'],
                'datetime': datetime.now(),
                'lat': iceberg['Lat'],
                'lon': iceberg['Lon'],
                'speed_km_day': np.nan,
                'area_km2': iceberg['Area_km2'],
                'data_source': 'current'
            })
        
        self.historical_data = pd.DataFrame(synthetic_data)
        print(f"✅ Created {len(synthetic_data)} synthetic trajectory points")
        return True
    
    def test_model_accuracy(self, prediction_days=[1, 3, 7]):
        """Test model accuracy using historical data"""
        if self.historical_data is None:
            print("❌ No historical data available for testing")
            return None
        
        print(f"\n🧪 TESTING MODEL ACCURACY")
        print("=" * 40)
        
        results = {}
        
        for days in prediction_days:
            print(f"\n📊 Testing {days}-day predictions...")
            
            predictions = []
            actual_positions = []
            
            # For each iceberg, test predictions
            for iceberg_id in self.historical_data['iceberg_id'].unique():
                iceberg_data = self.historical_data[
                    self.historical_data['iceberg_id'] == iceberg_id
                ].sort_values('datetime')
                
                if len(iceberg_data) < days + 5:  # Need enough data points
                    continue
                
                # Test multiple prediction points
                for i in range(len(iceberg_data) - days - 1):
                    try:
                        # Historical position (input)
                        start_row = iceberg_data.iloc[i]
                        start_lat = start_row['lat']
                        start_lon = start_row['lon']
                        
                        # Actual future position (ground truth)
                        future_row = iceberg_data.iloc[i + days]
                        actual_lat = future_row['lat']
                        actual_lon = future_row['lon']
                        
                        # Make prediction
                        pred_result = self.predictor.predict_trajectory(
                            start_lat, start_lon, days_ahead=[days]
                        )
                        
                        pred_key = f'{days}_days'
                        if pred_key in pred_result['predictions']:
                            pred_lat = pred_result['predictions'][pred_key]['predicted_lat']
                            pred_lon = pred_result['predictions'][pred_key]['predicted_lon']
                            
                            predictions.append([pred_lat, pred_lon])
                            actual_positions.append([actual_lat, actual_lon])
                        
                    except Exception as e:
                        continue  # Skip problematic predictions
            
            if len(predictions) < 5:
                print(f"   ⚠️  Insufficient test data for {days}-day predictions")
                continue
            
            predictions = np.array(predictions)
            actual_positions = np.array(actual_positions)
            
            # Calculate metrics
            metrics = self.calculate_metrics(predictions, actual_positions, days)
            results[f'{days}_day'] = metrics
            
            print(f"   📈 Test samples: {len(predictions)}")
            print(f"   📊 R² Score (Lat): {metrics['r2_lat']:.4f}")
            print(f"   📊 R² Score (Lon): {metrics['r2_lon']:.4f}")
            print(f"   📊 R² Score (Combined): {metrics['r2_combined']:.4f}")
            print(f"   📏 Mean Distance Error: {metrics['mean_distance_error_km']:.2f} km")
            print(f"   📏 RMSE Distance: {metrics['rmse_distance_km']:.2f} km")
        
        self.test_results = results
        return results
    
    def calculate_metrics(self, predictions, actual, prediction_days):
        """Calculate comprehensive performance metrics"""
        pred_lat = predictions[:, 0]
        pred_lon = predictions[:, 1]
        actual_lat = actual[:, 0]
        actual_lon = actual[:, 1]
        
        # R² scores
        r2_lat = r2_score(actual_lat, pred_lat)
        r2_lon = r2_score(actual_lon, pred_lon)
        
        # Combined R² (using distance as the metric)
        actual_distances = np.sqrt((actual_lat - actual_lat[0])**2 + (actual_lon - actual_lon[0])**2)
        pred_distances = np.sqrt((pred_lat - actual_lat[0])**2 + (pred_lon - actual_lon[0])**2)
        r2_combined = r2_score(actual_distances, pred_distances) if len(set(actual_distances)) > 1 else 0
        
        # Distance errors
        distance_errors = []
        for i in range(len(predictions)):
            error_km = self.predictor.haversine_distance(
                actual_lat[i], actual_lon[i], pred_lat[i], pred_lon[i]
            )
            distance_errors.append(error_km)
        
        distance_errors = np.array(distance_errors)
        
        # Additional metrics
        mae_lat = mean_absolute_error(actual_lat, pred_lat)
        mae_lon = mean_absolute_error(actual_lon, pred_lon)
        rmse_lat = np.sqrt(mean_squared_error(actual_lat, pred_lat))
        rmse_lon = np.sqrt(mean_squared_error(actual_lon, pred_lon))
        
        return {
            'r2_lat': r2_lat,
            'r2_lon': r2_lon,
            'r2_combined': r2_combined,
            'mae_lat': mae_lat,
            'mae_lon': mae_lon,
            'rmse_lat': rmse_lat,
            'rmse_lon': rmse_lon,
            'mean_distance_error_km': np.mean(distance_errors),
            'median_distance_error_km': np.median(distance_errors),
            'rmse_distance_km': np.sqrt(np.mean(distance_errors**2)),
            'max_distance_error_km': np.max(distance_errors),
            'std_distance_error_km': np.std(distance_errors),
            'prediction_days': prediction_days,
            'sample_size': len(predictions)
        }
    
    def create_performance_plots(self, save_plots=True):
        """Create visualization plots of model performance"""
        if not self.test_results:
            print("❌ No test results available for plotting")
            return
        
        print(f"\n📊 Creating performance visualization plots...")
        
        # Set up the plotting style
        plt.style.use('default')
        sns.set_palette("husl")
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Iceberg Trajectory Prediction Model Performance', fontsize=16, fontweight='bold')
        
        # Extract data for plotting
        days = []
        r2_scores = []
        distance_errors = []
        sample_sizes = []
        
        for period, metrics in self.test_results.items():
            days.append(metrics['prediction_days'])
            r2_scores.append(metrics['r2_combined'])
            distance_errors.append(metrics['mean_distance_error_km'])
            sample_sizes.append(metrics['sample_size'])
        
        # Plot 1: R² Score vs Prediction Horizon
        axes[0, 0].plot(days, r2_scores, 'o-', linewidth=2, markersize=8, color='blue')
        axes[0, 0].set_title('R² Score vs Prediction Horizon')
        axes[0, 0].set_xlabel('Prediction Days Ahead')
        axes[0, 0].set_ylabel('R² Score')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].set_ylim(0, 1)
        
        # Add R² values as labels
        for i, (day, r2) in enumerate(zip(days, r2_scores)):
            axes[0, 0].annotate(f'{r2:.3f}', (day, r2), textcoords="offset points", 
                              xytext=(0,10), ha='center', fontweight='bold')
        
        # Plot 2: Mean Distance Error vs Prediction Horizon
        axes[0, 1].plot(days, distance_errors, 'o-', linewidth=2, markersize=8, color='red')
        axes[0, 1].set_title('Mean Distance Error vs Prediction Horizon')
        axes[0, 1].set_xlabel('Prediction Days Ahead')
        axes[0, 1].set_ylabel('Mean Distance Error (km)')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Add error values as labels
        for i, (day, error) in enumerate(zip(days, distance_errors)):
            axes[0, 1].annotate(f'{error:.1f} km', (day, error), textcoords="offset points", 
                              xytext=(0,10), ha='center', fontweight='bold')
        
        # Plot 3: Sample Sizes
        bars = axes[1, 0].bar(days, sample_sizes, alpha=0.7, color='green')
        axes[1, 0].set_title('Test Sample Sizes')
        axes[1, 0].set_xlabel('Prediction Days Ahead')
        axes[1, 0].set_ylabel('Number of Test Samples')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Add sample size labels on bars
        for bar, size in zip(bars, sample_sizes):
            height = bar.get_height()
            axes[1, 0].annotate(f'{size}', xy=(bar.get_x() + bar.get_width()/2, height),
                              xytext=(0, 3), textcoords="offset points", ha='center', va='bottom')
        
        # Plot 4: Performance Summary Table
        axes[1, 1].axis('off')
        
        # Create summary table
        table_data = []
        headers = ['Days', 'R² Score', 'Dist Error (km)', 'RMSE (km)', 'Samples']
        
        for period, metrics in self.test_results.items():
            row = [
                f"{metrics['prediction_days']}",
                f"{metrics['r2_combined']:.4f}",
                f"{metrics['mean_distance_error_km']:.2f}",
                f"{metrics['rmse_distance_km']:.2f}",
                f"{metrics['sample_size']}"
            ]
            table_data.append(row)
        
        table = axes[1, 1].table(cellText=table_data, colLabels=headers, 
                                cellLoc='center', loc='center', bbox=[0, 0.2, 1, 0.6])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 2)
        
        # Style the table
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#40466e')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        axes[1, 1].set_title('Performance Summary Table', pad=20, fontweight='bold')
        
        plt.tight_layout()
        
        if save_plots:
            output_dir = Path(__file__).parent / "results"
            output_dir.mkdir(exist_ok=True)
            plot_path = output_dir / "model_performance.png"
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            print(f"   💾 Performance plots saved to: {plot_path}")
        
        plt.show()
    
    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        if not self.test_results:
            print("❌ No test results available for report")
            return
        
        print(f"\n📋 COMPREHENSIVE PERFORMANCE REPORT")
        print("=" * 60)
        
        # Overall summary
        all_r2_scores = [metrics['r2_combined'] for metrics in self.test_results.values()]
        all_distances = [metrics['mean_distance_error_km'] for metrics in self.test_results.values()]
        
        print(f"\n🎯 OVERALL PERFORMANCE SUMMARY:")
        print(f"   Average R² Score: {np.mean(all_r2_scores):.4f}")
        print(f"   Best R² Score: {np.max(all_r2_scores):.4f}")
        print(f"   Average Distance Error: {np.mean(all_distances):.2f} km")
        print(f"   Best Distance Error: {np.min(all_distances):.2f} km")
        
        # Detailed results per prediction horizon
        print(f"\n📊 DETAILED RESULTS BY PREDICTION HORIZON:")
        print(f"{'Days':>5} {'R² Score':>10} {'MAE (°)':>10} {'RMSE (°)':>11} {'Dist Err':>10} {'RMSE Dist':>12} {'Samples':>8}")
        print(f"{'-'*5} {'-'*10} {'-'*10} {'-'*11} {'-'*10} {'-'*12} {'-'*8}")
        
        for period, metrics in sorted(self.test_results.items(), key=lambda x: x[1]['prediction_days']):
            print(f"{metrics['prediction_days']:>5} "
                  f"{metrics['r2_combined']:>10.4f} "
                  f"{(metrics['mae_lat'] + metrics['mae_lon'])/2:>10.4f} "
                  f"{np.sqrt((metrics['rmse_lat']**2 + metrics['rmse_lon']**2)/2):>11.4f} "
                  f"{metrics['mean_distance_error_km']:>10.2f} "
                  f"{metrics['rmse_distance_km']:>12.2f} "
                  f"{metrics['sample_size']:>8}")
        
        # Performance interpretation
        print(f"\n📈 PERFORMANCE INTERPRETATION:")
        
        best_r2 = np.max(all_r2_scores)
        avg_r2 = np.mean(all_r2_scores)
        
        if avg_r2 >= 0.7:
            performance_level = "EXCELLENT"
        elif avg_r2 >= 0.5:
            performance_level = "GOOD"
        elif avg_r2 >= 0.3:
            performance_level = "FAIR"
        else:
            performance_level = "NEEDS IMPROVEMENT"
        
        print(f"   Overall Performance: {performance_level}")
        print(f"   Model explains {avg_r2*100:.1f}% of trajectory variance on average")
        
        if best_r2 >= 0.8:
            print(f"   ✅ Excellent short-term prediction capability (R² = {best_r2:.4f})")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        short_term_r2 = self.test_results.get('1_day', {}).get('r2_combined', 0)
        long_term_r2 = max(self.test_results.values(), key=lambda x: x['prediction_days']).get('r2_combined', 0)
        
        if short_term_r2 > 0.6:
            print(f"   ✅ Model suitable for short-term predictions (1-3 days)")
        else:
            print(f"   ⚠️  Short-term predictions need improvement")
        
        if long_term_r2 > 0.3:
            print(f"   ✅ Reasonable long-term trend prediction capability")
        else:
            print(f"   ⚠️  Long-term predictions have high uncertainty")
        
        print(f"\n📊 CONFIDENCE INTERVALS:")
        for period, metrics in self.test_results.items():
            days = metrics['prediction_days']
            mean_error = metrics['mean_distance_error_km']
            std_error = metrics['std_distance_error_km']
            
            ci_95 = mean_error + 1.96 * std_error  # 95% confidence interval
            print(f"   {days:>2}-day predictions: 95% of errors < {ci_95:.1f} km")
        
        # Save report
        output_dir = Path(__file__).parent / "results"
        output_dir.mkdir(exist_ok=True)
        
        report_path = output_dir / "performance_report.json"
        with open(report_path, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed report saved to: {report_path}")

def main():
    """Run comprehensive model testing"""
    print("🧪 ICEBERG PREDICTION MODEL PERFORMANCE TESTING")
    print("=" * 60)
    
    # Initialize tester
    tester = ModelPerformanceTester()
    
    # Load data
    if not tester.load_historical_data():
        print("❌ Could not load test data")
        return
    
    # Test model accuracy
    results = tester.test_model_accuracy(prediction_days=[1, 3, 7, 14])
    
    if results:
        # Create plots
        tester.create_performance_plots()
        
        # Generate report
        tester.generate_performance_report()
        
        print(f"\n🎉 MODEL TESTING COMPLETED!")
        print(f"📊 Check the results/ directory for detailed outputs")
    else:
        print("❌ No test results generated")

if __name__ == "__main__":
    main()