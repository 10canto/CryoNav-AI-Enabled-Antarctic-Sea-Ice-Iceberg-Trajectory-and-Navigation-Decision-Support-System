"""
Download Recent Ocean Current Data (October 2025 - October 2026)
Downloads 1 year of ocean current data for LSTM training
"""
import copernicusmarine
from pathlib import Path

def download_recent_ocean_data():
    """
    Download 1 year of ocean current data (Oct 2025 - Oct 2026)
    
    Size: ~200-300 MB
    Time: 5-10 minutes
    """
    
    print("\n" + "=" * 70)
    print("🌊 COPERNICUS MARINE - RECENT OCEAN DATA DOWNLOAD")
    print("=" * 70)
    
    print("\n📊 Download Configuration:")
    print("   Dataset: cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m")
    print("   Variables: uo (eastward), vo (northward) currents")
    print("   Region: Global (-180° to 180°, -80° to 90°)")
    print("   Time: October 2025 to October 2026 (1 year)")
    print("   Resolution: 0.083° (~9 km)")
    print("   Depth: 0.5m surface")
    print("   Frequency: Daily")
    print("\n   Expected size: ~200-300 MB")
    print("   Expected time: 5-10 minutes")
    
    # Output path
    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(exist_ok=True, parents=True)
    output_file = output_dir / "ocean_currents_2025_2026_daily.nc"
    
    print(f"\n💾 Output: {output_file.name}")
    
    # Check if already exists
    if output_file.exists():
        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"\n✅ File already exists ({file_size_mb:.1f} MB)")
        
        user_input = input("\n   Re-download? (y/n): ").strip().lower()
        if user_input != 'y':
            print("   Using existing file.")
            return str(output_file)
    
    print("\n🚀 Starting download...")
    print("   Please wait, this may take 5-10 minutes...")
    
    try:
        # Download ocean currents - RECENT YEAR ONLY
        copernicusmarine.subset(
            dataset_id="cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m",
            variables=["uo", "vo"],
            minimum_longitude=-180,
            maximum_longitude=179.91668701171875,
            minimum_latitude=-80,
            maximum_latitude=90,
            start_datetime="2025-10-01T00:00:00",  # October 2025
            end_datetime="2026-10-06T00:00:00",    # October 2026 (today)
            minimum_depth=0.49402499198913574,
            maximum_depth=0.49402499198913574,
            output_filename=str(output_file),
            force_download=True
        )
        
        print("\n✅ Download complete!")
        
        # Verify file
        if output_file.exists():
            file_size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"\n📊 Downloaded file:")
            print(f"   File: {output_file.name}")
            print(f"   Size: {file_size_mb:.1f} MB")
            print(f"   Path: {output_file}")
            
            print("\n🎯 Next Steps:")
            print("   1. Run: python integrate_ocean_training.py")
            print("   2. Train enhanced LSTM with ocean currents")
            
            return str(output_file)
        else:
            print("\n❌ Download failed - file not created")
            return None
            
    except Exception as e:
        print(f"\n❌ Download failed: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check credentials: python copernicus_login.py")
        print("   2. Check internet connection")
        print("   3. Verify dataset ID is correct")
        return None

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🧊 CRYONAV - OCEAN DATA DOWNLOADER (RECENT YEAR)")
    print("=" * 70)
    
    print("\n📋 Downloading:")
    print("   • 1 year of ocean current data (Oct 2025 - Oct 2026)")
    print("   • Daily resolution (~370 time steps)")
    print("   • Size: ~200-300 MB")
    print("   • Time: 5-10 minutes")
    
    print("\n🚀 Starting download...")
    
    # Download
    output_file = download_recent_ocean_data()
    
    if output_file:
        print("\n" + "=" * 70)
        print("🎉 SUCCESS!")
        print("=" * 70)
        print(f"\n✅ Ocean data downloaded: {Path(output_file).name}")
        print("\n🚀 Ready to integrate with iceberg data!")
        print("   Next: python integrate_ocean_training.py")
    else:
        print("\n" + "=" * 70)
        print("❌ Download failed")
        print("=" * 70)
        print("\n   Please check error messages and try again")
    
    print("\n" + "=" * 70)
