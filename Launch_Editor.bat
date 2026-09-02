@echo off
setlocal
REM Canonical launcher for BS_GodFile -- always forces an in-memory DDC.
REM The in-memory DDC preserves the known-safe startup path after the former
REM F: drive/Zen cache became unreachable. Set MELODIA_UNREAL_ROOT per machine
REM when UE 5.8 is installed outside the documented default path.

set "UE_ROOT=%MELODIA_UNREAL_ROOT%"
if "%UE_ROOT%"=="" set "UE_ROOT=C:\Program Files\Epic Games\UE_5.8"

set "UE_EXE=%UE_ROOT%\Engine\Binaries\Win64\UnrealEditor.exe"
if not exist "%UE_EXE%" (
    echo Unreal Engine 5.8 was not found at:
    echo %UE_EXE%
    echo Set MELODIA_UNREAL_ROOT to the correct UE_5.8 installation path.
    exit /b 1
)

"%UE_EXE%" "%~dp0BS_GodFile.uproject" -DDC-ForceMemoryCache
endlocal
