@echo off
REM Run Substrate Toon conversion (all masters + param fix + instance profiles)
set UE=C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe
set PROJECT=G:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject
set SCRIPT=G:/EnvironmentPortfolio/BS_GodFile/Content/Python/run_toon_conversion.py
set LOG=G:\EnvironmentPortfolio\BS_GodFile\Saved\Logs\toon_conversion.log

echo Running Substrate Toon conversion...
"%UE%" "%PROJECT%" -ExecutePythonScript="%SCRIPT%" -stdout -unattended -nosplash -log="%LOG%"
echo Exit code: %ERRORLEVEL%
echo Log: %LOG%
echo Report: G:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\substrate_toon_conversion.json
