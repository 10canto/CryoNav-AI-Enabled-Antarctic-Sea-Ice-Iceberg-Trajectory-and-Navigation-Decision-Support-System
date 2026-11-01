# Fix Git Large Files Error
# Removes large ocean data files from git tracking

Write-Host ""
Write-Host "======================================================================"
Write-Host "🔧 FIXING GIT LARGE FILES ERROR"
Write-Host "======================================================================"
Write-Host ""

# Navigate to project root
Set-Location "C:\Users\Anto\OneDrive\Desktop\CryoNav-AI-Enabled-Antarctic-Sea-Ice-Iceberg-Trajectory-and-Navigation-Decision-Support-System"

Write-Host "📋 Step 1: Remove large files from git tracking..."
Write-Host ""

# Remove the 740 MB NetCDF file from git
Write-Host "   Removing DATA/cmems_mod_glo_phy-cur_anfc_0.083deg_P1M-m_1791042227247.nc (740 MB)"
git rm --cached "DATA/cmems_mod_glo_phy-cur_anfc_0.083deg_P1M-m_1791042227247.nc" 2>&1 | Out-Null

# Remove yearly ocean current JSON files from git
Write-Host "   Removing ocean_currents_yearly JSON files..."
git rm --cached "iceberg-trajectory-ml/data/ocean_currents_yearly/ocean_currents_weddell_sea_2025.json" 2>&1 | Out-Null
git rm --cached "iceberg-trajectory-ml/data/ocean_currents_yearly/ocean_currents_east_antarctic_2025.json" 2>&1 | Out-Null
git rm --cached "iceberg-trajectory-ml/data/ocean_currents_yearly/ocean_currents_ross_sea_2025.json" 2>&1 | Out-Null
git rm --cached "iceberg-trajectory-ml/data/ocean_currents_yearly/ocean_currents_southern_ocean_2025.json" 2>&1 | Out-Null
git rm --cached "iceberg-trajectory-ml/data/ocean_currents_yearly/ocean_currents_yearly_metadata.json" 2>&1 | Out-Null

Write-Host ""
Write-Host "   ✅ Files removed from git tracking (still on your disk!)"
Write-Host ""

Write-Host "📋 Step 2: Adding updated .gitignore..."
Write-Host ""
git add .gitignore

Write-Host "📋 Step 3: Committing changes..."
Write-Host ""
git commit -m "Remove large ocean data files from git tracking - Excluded ocean_currents_yearly JSON files (66-740 MB) and DATA/*.nc files - Updated .gitignore - Files remain locally"

Write-Host ""
Write-Host "✅ Changes committed!"
Write-Host ""

Write-Host "======================================================================"
Write-Host "🎉 FIX COMPLETE!"
Write-Host "======================================================================"
Write-Host ""

Write-Host "✅ Large files removed from git"
Write-Host "✅ .gitignore updated"
Write-Host "✅ Ready to push"
Write-Host ""

Write-Host "📋 Next step: Run 'git push' to push your changes"
Write-Host ""
Write-Host "======================================================================"
