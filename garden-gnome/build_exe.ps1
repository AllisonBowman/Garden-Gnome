# Rebuilds GardenGnome.exe after code changes.
# Requires the Windows build venv (.venv-win) -- see README "Rebuilding the .exe".
Set-Location $PSScriptRoot

.\.venv-win\Scripts\python.exe -m PyInstaller run_app.py `
  --name GardenGnome `
  --onefile `
  --add-data "app/static;app/static" `
  --add-data "app/data/species_catalog.json;app/data" `
  --collect-all uvicorn `
  --collect-all fastapi `
  --collect-all starlette `
  --collect-all pydantic `
  --collect-all pydantic_core `
  --collect-all sqlmodel `
  --collect-all sqlalchemy `
  --noconfirm

Copy-Item -Path "dist\GardenGnome.exe" -Destination "GardenGnome.exe" -Force
Write-Output "Built: $PSScriptRoot\GardenGnome.exe"
