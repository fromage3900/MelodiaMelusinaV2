@echo off
setlocal
set "ROOT=%~dp0"
set "UE_ROOT=%MELODIA_UNREAL_ROOT%"
if "%UE_ROOT%"=="" set "UE_ROOT=C:\Program Files\Epic Games\UE_5.8"
set "UE_EXE=%UE_ROOT%\Engine\Binaries\Win64\UnrealEditor.exe"
if not exist "%UE_EXE%" (
    echo Unreal Engine 5.8 not found at "%UE_EXE%".
    echo Set MELODIA_UNREAL_ROOT for this workstation.
    exit /b 1
)
"%UE_EXE%" "%ROOT%BS_GodFile.uproject" -ExecutePythonScript="%ROOT%Content\Python\create_tp_melusina_mpc.py" -Unattended -NoCompile -NoSound -NullRHI
endlocal
