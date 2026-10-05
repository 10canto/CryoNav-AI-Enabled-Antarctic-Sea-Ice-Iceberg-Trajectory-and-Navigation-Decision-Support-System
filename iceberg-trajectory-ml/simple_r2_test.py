"""
Simple R² Test for Iceberg Prediction Model
"""

import numpy as np
import pandas as pd
from working_predictor import WorkingIcebergPredictor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from datetime import datetime, timedelta
import json

def calculate_r2_simple():
    """Calculate R² score using a simple test approach"""
    print("🧪 SIMPLE R² CALCULATION TEST")
    print("=" * 40)
    
    # Initialize predictor
    predictor = WorkingIcebergPredictor()
    
    if predictor.current_icebergs is None:
        print("❌ No iceberg data available")
        return
    
    print(f"📊 Testing with {len(predictor.current_icebergs)} current icebergs")
    
    # Create synthetic test data based on reverse trajectories
    test_data = []
    
    # For each current iceberg, simulate a past trajectory and test predictions
    for _, iceberg in predictor.current_icebergs.iterrows():
        iceberg_id = iceberg['Iceberg']
        current_lat = iceberg['Lat']
        current_lon = iceberg['Lon']
        
        print(f"\n🔍 Testing iceberg {iceberg_id} at ({current_lat:.3f}, {current_lon:.3f})")
        
        # Get regional pattern
        region_key, region_pattern = predictor.identify_region(current_lat, current_lon)
        
        # Simulate past positions (reverse trajectory)
        base_vel_lat = -region_pattern['vel_lat_per_day']  # Reverse
        base_vel_lon = -region_pattern['vel_lon_per_day']
        
        # Test different prediction horizons
        for days_back in [1, 3, 7]:
            try:
                # Simulate where iceberg was N days ago
                past_lat = current_lat + (base_vel_lat * days_back)
                past_lon = current_lon + (base_vel_lon * days_back)
                
                # Add realistic noise
                noise_factor = 0.05  # 5% noise
                lat_noise = np.random.normal(0, noise_factor * days_back)
                lon_noise = np.random.normal(0, noise_factor * days_back)
                
                past_lat += lat_noise
                past_lon += lon_noise
                
                # Make prediction from past position
                prediction_result = predictor.predict_trajectory(past_lat, past_lon, days_ahead=[days_back])
                
                pred_key = f'{days_back}_days'
                if pred_key in prediction_result['predictions']:
                    pred_lat = prediction_result['predictions'][pred_key]['predicted_lat']
                    pred_lon = prediction_result['predictions'][pred_key]['predicted_lon']
                    
                    # Calculate error
                    distance_error = predictor.haversine_distance(
                        current_lat, current_lon, pred_lat, pred_lon
                    )
                    
                    test_data.append({
                        'iceberg_id': iceberg_id,
                        'days_ahead': days_back,
                        'actual_lat': current_lat,
                        'actual_lon': current_lon,
                        'predicted_lat': pred_lat,
                        'predicted_lon': pred_lon,
                        'distance_error_km': distance_error,
                        'region': region_pattern['name']
                    })
                    
                    print(f"     {days_back}d: Predicted ({pred_lat:.3f}, {pred_lon:.3f}) vs Actual ({current_lat:.3f}, {current_lon:.3f}) - Error: {distance_error:.2f} km")
                    
            except Exception as e:
                print(f"     ❌ Error for {days_back}d: {e}")
                continue
    
    if not test_data:
        print("❌ No test data generated")
        return
    
    # Convert to DataFrame for analysis
    df_test = pd.DataFrame(test_data)
    
    print(f"\n📊 PERFORMANCE ANALYSIS")
    print("=" * 40)
    print(f"Total test samples: {len(df_test)}")
    
    # Calculate R² scores by prediction horizon
    results = {}
    
    for days in df_test['days_ahead'].unique():
        day_data = df_test[df_test['days_ahead'] == days]
        
        if len(day_data) < 3:  # Need at least 3 samples
            continue
        
        actual_lat = day_data['actual_lat'].values
        actual_lon = day_data['actual_lon'].values
        pred_lat = day_data['predicted_lat'].values  
        pred_lon = day_data['predicted_lon'].values
        
        # Calculate R² for latitude and longitude separately
        r2_lat = r2_score(actual_lat, pred_lat)
        r2_lon = r2_score(actual_lon, pred_lon)
        
        # Calculate combined R² using distance from centroid
        actual_center_lat = np.mean(actual_lat)
        actual_center_lon = np.mean(actual_lon)
        
        # Distances from center (as a proxy for trajectory variance)
        actual_distances = np.sqrt((actual_lat - actual_center_lat)**2 + (actual_lon - actual_center_lon)**2)
        pred_distances = np.sqrt((pred_lat - actual_center_lat)**2 + (pred_lon - actual_center_lon)**2)
        
        # Only calculate R² if there's variance in actual data
        if np.var(actual_distances) > 0:
            r2_combined = r2_score(actual_distances, pred_distances)
        else:
            r2_combined = 0.0
        
        # Distance errors
        distance_errors = day_data['distance_error_km'].values
        
        # Other metrics
        mae_lat = mean_absolute_error(actual_lat, pred_lat)
        mae_lon = mean_absolute_error(actual_lon, pred_lon)
        rmse_distance = np.sqrt(np.mean(distance_errors**2))
        
        results[f'{days}_day'] = {
            'prediction_days': days,
            'r2_latitude': r2_lat,
            'r2_longitude': r2_lon, 
            'r2_combined': r2_combined,
            'mae_latitude_deg': mae_lat,
            'mae_longitude_deg': mae_lon,
            'mean_distance_error_km': np.mean(distance_errors),
            'median_distance_error_km': np.median(distance_errors),
            'rmse_distance_km': rmse_distance,
            'max_distance_error_km': np.max(distance_errors),
            'min_distance_error_km': np.min(distance_errors),
            'std_distance_error_km': np.std(distance_errors),
            'sample_size': len(day_data)
        }
        
        print(f"\n📈 {days}-DAY PREDICTIONS:")
        print(f"   Samples: {len(day_data)}")
        print(f"   R² Score (Latitude):  {r2_lat:.4f}")
        print(f"   R² Score (Longitude): {r2_lon:.4f}")
        print(f"   R² Score (Combined):  {r2_combined:.4f}")
        print(f"   Mean Distance Error:  {np.mean(distance_errors):.2f} km")
        print(f"   RMSE Distance:        {rmse_distance:.2f} km")
        print(f"   Error Range:          {np.min(distance_errors):.2f} - {np.max(distance_errors):.2f} km")
    
    # Overall performance summary
    if results:
        all_r2_combined = [r['r2_combined'] for r in results.values()]
        all_distance_errors = [r['mean_distance_error_km'] for r in results.values()]
        
        print(f"\n🎯 OVERALL MODEL PERFORMANCE:")
        print(f"   Average R² Score:     {np.mean(all_r2_combined):.4f}")
        print(f"   Best R² Score:        {np.max(all_r2_combined):.4f}")
        print(f"   Average Distance Error: {np.mean(all_distance_errors):.2f} km")
        print(f"   Best Distance Error:    {np.min(all_distance_errors):.2f} km")
        
        # Performance interpretation
        avg_r2 = np.mean(all_r2_combined)
        
        print(f"\n📊 PERFORMANCE INTERPRETATION:")
        if avg_r2 >= 0.7:
            performance = "EXCELLENT"
            emoji = "🌟"
        elif avg_r2 >= 0.5:
            performance = "GOOD"  
            emoji = "✅"
        elif avg_r2 >= 0.3:
            performance = "FAIR"
            emoji = "⚠️"
        else:
            performance = "NEEDS IMPROVEMENT"
            emoji = "❌"
            
        print(f"   {emoji} Performance Level: {performance}")
        print(f"   📈 Model explains {avg_r2*100:.1f}% of trajectory variance")
        
        # Accuracy assessment
        avg_error = np.mean(all_distance_errors)
        if avg_error <= 5:
            accuracy = "HIGH (suitable for navigation)"
        elif avg_error <= 15:
            accuracy = "MEDIUM (suitable for monitoring)"
        elif avg_error <= 50:
            accuracy = "LOW (suitable for rough estimates)"
        else:
            accuracy = "POOR (needs improvement)"
        
        print(f"   🎯 Accuracy Level: {accuracy}")
        
        # Regional performance
        print(f"\n🌍 REGIONAL PERFORMANCE:")
        regional_stats = df_test.groupby('region')['distance_error_km'].agg(['mean', 'count']).round(2)
        for region, stats in regional_stats.iterrows():
            print(f"   {region}: {stats['mean']:.2f} km avg error ({int(stats['count'])} samples)")
    
    # Save results
    try:
        import os
        os.makedirs('results', exist_ok=True)
        
        with open('results/r2_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        df_test.to_csv('results/test_predictions.csv', index=False)
        
        print(f"\n💾 Results saved to:")
        print(f"   📄 results/r2_test_results.json")
        print(f"   📄 results/test_predictions.csv")
        
    except Exception as e:
        print(f"\n⚠️  Could not save results: {e}")
    
    return results

def main():
    """Run simple R² test"""
    print("🧊 ICEBERG PREDICTION MODEL - R² SCORE TEST")
    print("=" * 50)
    
    results = calculate_r2_simple()
    
    if results:
        print(f"\n🎉 R² TESTING COMPLETED!")
        
        # Quick summary table
        print(f"\n📋 QUICK SUMMARY TABLE:")
        print(f"{'Days':>5} {'R² Score':>10} {'Error (km)':>12} {'Samples':>8}")
        print(f"{'-'*5} {'-'*10} {'-'*12} {'-'*8}")
        
        for period, metrics in sorted(results.items(), key=lambda x: x[1]['prediction_days']):
            print(f"{metrics['prediction_days']:>5} "
                  f"{metrics['r2_combined']:>10.4f} "
                  f"{metrics['mean_distance_error_km']:>12.2f} "
                  f"{metrics['sample_size']:>8}")
        
    else:
        print("❌ R² testing failed")

if __name__ == "__main__":
    main()