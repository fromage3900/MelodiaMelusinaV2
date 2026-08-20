@echo off
REM Melodia Asset Prep Script
REM Safely checks and verifies directories before Unreal intake
set "SCRIPT_DIR=%~dp0"
set "IMPORTS_DIR=%SCRIPT_DIR%..\Imports"

echo Preparing Imports directory for Unreal Engine Intake...
mkdir "%IMPORTS_DIR%\Environment\MusicalInstruments" 2>nul
mkdir "%IMPORTS_DIR%\Textures\ColorRamps" 2>nul
echo Folder structures verified. Ready for UE intake!
echo Please run unreal_asset_intake.py from the Unreal Python console.
pause
