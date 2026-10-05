"""
Simple Iceberg Position Predictor API
Input: python predict_iceberg_position.py -66.5 45.2
Output: Future iceberg positions
"""

import sys
import json
from working_predictor import WorkingIcebergPredictor

def predict_position(lat, lon):
    """
    Simple function to predict iceberg position
    
    Args:
        lat: Latitude (-90 to -40)
        lon: Longitude (-180 to 180)
    
    Returns:
        Prediction results as dictionary
    """
    predictor = WorkingIcebergPredictor()
    result = predictor.predict_trajectory(lat, lon)
    return result

def main():
    """Command line interface"""
    
    if len(sys.argv) == 1:
        # Interactive mode
        print("🧊 ICEBERG TRAJECTORY PREDICTOR")
        print("=" * 40)
        print("Enter iceberg coordinates to get trajectory prediction")
        
        predictor = WorkingIcebergPredictor()
        
        print(f"\n📊 Current Icebergs Available:")
        if predictor.current_icebergs is not None:
            for _, iceberg in predictor.current_icebergs.head(5).iterrows():
                print(f"   {iceberg['Iceberg']}: ({iceberg['Lat']}, {iceberg['Lon']}) - {iceberg['Area_km2']:.1f} km²")
            print(f"   ... and {len(predictor.current_icebergs)-5} more icebergs")
        
        while True:
            try:
                print(f"\n" + "="*40)
                lat_input = input("Enter latitude (-90 to -40): ")
                if lat_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                lon_input = input("Enter longitude (-180 to 180): ")
                
                lat = float(lat_input)
                lon = float(lon_input)
                
                # Make prediction
                result = predict_position(lat, lon)
                
                print(f"\n📍 INPUT: ({lat}, {lon})")
                print(f"🌍 REGION: {result['metadata']['region']}")
                print(f"📅 SEASON: {result['metadata']['season']}")
                print(f"🏃 SPEED: {result['metadata']['base_speed_km_day']} km/day")
                
                print(f"\n🔮 PREDICTIONS:")
                print(f"{'Days':>4} {'Latitude':>10} {'Longitude':>11} {'Distance':>9} {'Confidence':>12}")
                print(f"{'-'*4} {'-'*10} {'-'*11} {'-'*9} {'-'*12}")
                
                for period, pred in result['predictions'].items():
                    days = period.replace('_days', '')
                    print(f"{days:>4} {pred['predicted_lat']:>10.4f} {pred['predicted_lon']:>11.4f} {pred['distance_km']:>6.1f} km {pred['confidence']:>12}")
                
                # Find nearest current iceberg
                nearest = predictor.find_nearest_iceberg(lat, lon)
                if nearest:
                    print(f"\n📍 Nearest current iceberg: {nearest['iceberg_id']} ({nearest['distance_km']:.1f} km away)")
                
            except KeyboardInterrupt:
                print(f"\nGoodbye! 👋")
                break
            except ValueError:
                print(f"❌ Please enter valid numbers")
            except Exception as e:
                print(f"❌ Error: {e}")
    
    elif len(sys.argv) == 3:
        # Command line mode
        try:
            lat = float(sys.argv[1])
            lon = float(sys.argv[2])
            
            result = predict_position(lat, lon)
            
            print(f"🧊 Iceberg Trajectory Prediction")
            print(f"Input Position: ({lat}, {lon})")
            print(f"Region: {result['metadata']['region']}")
            print(f"Season: {result['metadata']['season']}")
            print(f"Base Speed: {result['metadata']['base_speed_km_day']} km/day")
            print(f"")
            print(f"Future Positions:")
            
            for period, pred in result['predictions'].items():
                days = period.replace('_days', '')
                print(f"  {days:>2} days: ({pred['predicted_lat']:7.3f}, {pred['predicted_lon']:8.3f}) - {pred['distance_km']:5.1f} km - {pred['confidence']}")
                
        except ValueError:
            print("❌ Error: Please provide valid latitude and longitude numbers")
            print("Usage: python predict_iceberg_position.py -66.5 45.2")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    else:
        print("🧊 Iceberg Trajectory Predictor")
        print("")
        print("Usage:")
        print("  Interactive: python predict_iceberg_position.py")
        print("  Command line: python predict_iceberg_position.py <latitude> <longitude>")
        print("")
        print("Examples:")
        print("  python predict_iceberg_position.py -66.5 45.2")
        print("  python predict_iceberg_position.py -72.1 -25.5")
        print("")
        print("Valid ranges:")
        print("  Latitude: -90 to -40 (Antarctic region)")
        print("  Longitude: -180 to 180")

if __name__ == "__main__":
    main()