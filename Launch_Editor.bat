@echo off
setlocal
REM Canonical launcher for BS_GodFile.
REM Default safety contract: do not open Unreal from a stale/wrong-branch checkout.
REM Escape hatch for intentional offline/feature work:
REM   set MELODIA_SKIP_SYNC_CHECK=1
REM Optional explicit feature-branch check:
REM   set MELODIA_SYNC_TARGET=Current

set "ROOT=%~dp0"
set "SYNC_TARGET=%MELODIA_SYNC_TARGET%"
if "%SYNC_TARGET%"=="" set "SYNC_TARGET=Main"

if /I not "%MELODIA_SKIP_SYNC_CHECK%"=="1" (
    echo [Melodia] Checking workstation Git baseline...
    powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%deploy\sync_workstation.ps1" -Mode Check -Target "%SYNC_TARGET%"
    if errorlevel 1 (
        echo.
        echo [Melodia] Refusing to open Unreal from an unsynchronized checkout.
        echo Fix the reported Git state first, or set MELODIA_SKIP_SYNC_CHECK=1 for an intentional override.
        exit /b 2
    )
)

set "UE_ROOT=%MELODIA_UNREAL_ROOT%"
if "%UE_ROOT%"=="" set "UE_ROOT=C:\Program Files\Epic Games\UE_5.8"

set "UE_EXE=%UE_ROOT%\Engine\Binaries\Win64\UnrealEditor.exe"
if not exist "%UE_EXE%" (
    echo Unreal Engine 5.8 was not found at:
    echo %UE_EXE%
    echo Set MELODIA_UNREAL_ROOT to the correct UE_5.8 installation path.
    exit /b 1
)

"%UE_EXE%" "%ROOT%BS_GodFile.uproject" -DDC-ForceMemoryCache
endlocal
