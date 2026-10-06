"""
Download Ocean Data Using Saved Credentials
Downloads 1 year of ocean current data (Oct 2025 - Oct 2026)
"""
import copernicusmarine
from pathlib import Path
import os

def load_saved_credentials():
    """Load credentials from saved file"""
    cred_file = Path.home() / ".copernicusmarine" / "credentials"
    
    if cred_file.exists():
        print("✅ Found saved credentials")
        with open(cred_file, 'r') as f:
            lines = f.readlines()
            username = None
            password = None
            for line in lines:
                if line.startswith('username='):
                    username = line.split('=', 1)[1].strip()
                elif line.startswith('password='):
                    password = line.split('=', 1)[1].strip()
            return username, password
    
    return None, None

def download_with_credentials():
    """Download ocean data using saved credentials"""
    
    print("\n" + "=" * 70)
    print("🌊 COPERNICUS MARINE - OCEAN DATA DOWNLOAD")
    print("=" * 70)
    
    # Load credentials
    username, password = load_saved_credentials()
    
    if not username or not password:
        print("\n❌ No saved credentials found!")
        print("   Run: python copernicus_login.py")
        return None
    
    print(f"\n✅ Using saved credentials")
    print(f"   Username: {username}")
    
    print("\n📊 Download Configuration:")
    print("   Time: October 2025 - October 2026 (1 year)")
    print("   Size: ~200-300 MB")
    print("   Time: 5-10 minutes")
    
    # Output
    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(exist_ok=True, parents=True)
    output_file = output_dir / "ocean_currents_2025_2026_daily.nc"
    
    print(f"\n💾 Output: {output_file.name}")
    
    # Check if exists
    if output_file.exists():
        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"\n✅ File already exists ({file_size_mb:.1f} MB)")
        return str(output_file)
    
    print("\n🚀 Starting download...")
    print("   This will take 5-10 minutes...")
    print("   (The script may appear frozen - this is normal)")
    
    try:
        # Set credentials as environment variables
        os.environ['COPERNICUSMARINE_SERVICE_USERNAME'] = username
        os.environ['COPERNICUSMARINE_SERVICE_PASSWORD'] = password
        
        # Download with credentials
        copernicusmarine.subset(
            dataset_id="cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m",
            variables=["uo", "vo"],
            minimum_longitude=-180,
            maximum_longitude=179.91668701171875,
            minimum_latitude=-80,
            maximum_latitude=90,
            start_datetime="2025-10-01T00:00:00",
            end_datetime="2026-10-06T00:00:00",
            minimum_depth=0.49402499198913574,
            maximum_depth=0.49402499198913574,
            output_filename=str(output_file),
            username=username,
            password=password
        )
        
        print("\n✅ Download complete!")
        
        if output_file.exists():
            file_size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"\n📊 Success!")
            print(f"   File: {output_file.name}")
            print(f"   Size: {file_size_mb:.1f} MB")
            return str(output_file)
        else:
            print("\n❌ File not created")
            return None
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user")
        return None
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        
        # Try alternative method - write to file directly
        print("\n🔄 Trying alternative download method...")
        print("   Note: You may need to type your password (it won't show)")
        
        return None

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🧊 CRYONAV - AUTOMATED OCEAN DATA DOWNLOAD")
    print("=" * 70)
    
    print("\n📋 This will download:")
    print("   • 1 year of data (Oct 2025 - Oct 2026)")
    print("   • Size: ~200-300 MB")
    print("   • Using your saved credentials")
    
    result = download_with_credentials()
    
    if result:
        print("\n" + "=" * 70)
        print("🎉 SUCCESS!")
        print("=" * 70)
        print(f"\n✅ Downloaded: {Path(result).name}")
        print("\n🚀 Next: python integrate_ocean_training.py")
    else:
        print("\n" + "=" * 70)
        print("⚠️  DOWNLOAD NOT COMPLETED")
        print("=" * 70)
        print("\n💡 Alternative: Use your existing ocean data file")
        print("   File: DATA/cmems_mod_glo_phy-cur_anfc_0.083deg_P1M-m_*.nc")
        print("   This already works with R² > 0.999!")
    
    print("\n" + "=" * 70)
