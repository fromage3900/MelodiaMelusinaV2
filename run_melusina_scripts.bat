@echo off
REM ============================================================
REM Master Script Runner for Melusina/Melodia Unreal Editor Automation
REM Run from: C:\EnvironmentPortfolio\BS_GodFile
REM ============================================================

set UE_EDITOR="C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
set PROJECT_PATH="C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject"
set SCRIPTS_DIR="C:\EnvironmentPortfolio\BS_GodFile\Content\Python"

echo.
echo ============================================================
echo Melusina/Melodia Automation Scripts Runner
echo ============================================================
echo UE Editor: %UE_EDITOR%
echo Project: %PROJECT_PATH%
echo Scripts: %SCRIPTS_DIR%
echo.

REM Check if UE Editor exists
if not exist %UE_EDITOR% (
    echo ERROR: Unreal Editor not found at %UE_EDITOR%
    echo Please update the path in this script.
    pause
    exit /b 1
)

REM Check if project exists
if not exist %PROJECT_PATH% (
    echo ERROR: Project not found at %PROJECT_PATH%
    pause
    exit /b 1
)

echo Choose script to run:
echo 1. Create TP_Melusina Material Parameter Collection
echo 2. Create NS_Uni_WaterMist Niagara System
echo 3. Create MF_WaterBioluminescence_v7 Material Function
echo 4. Inspect SK_Melusina Material Slots (24, 26, 28)
echo 5. Review Core Blueprint Wiring
echo 6. Run ALL scripts sequentially
echo.
set /p CHOICE="Enter choice (1-6): "

if "%CHOICE%"=="1" (
    echo Running TP_Melusina MPC creation...
    %UE_EDITOR% %PROJECT_PATH% -ExecutePythonScript=%SCRIPTS_DIR%\create_tp_melusina_mpc.py
)
if "%CHOICE%"=="2" (
    echo Running NS_Uni_WaterMist Niagara creation...
    %UE_EDITOR% %PROJECT_PATH% -ExecutePythonScript=%SCRIPTS_DIR%\create_water_mist_niagara.py
)
if "%CHOICE%"=="3" (
    echo Running MF_WaterBioluminescence_v7 creation...
    %UE_EDITOR% %PROJECT_PATH% -ExecutePythonScript=%SCRIPTS_DIR%\create_water_bioluminescence_mf.py
)
if "%CHOICE%"=="4" (
    echo Running SK_Melusina material slots inspection...
    %UE_EDITOR% %PROJECT_PATH% -ExecutePythonScript=%SCRIPTS_DIR%\inspect_sk_melusina_slots.py
)
if "%CHOICE%"=="5" (
    echo Running Blueprint wiring review...
    %UE_EDITOR% %PROJECT_PATH% -ExecutePythonScript=%SCRIPTS_DIR%\review_blueprint_wiring.py
)
if "%CHOICE%"=="6" (
    echo Running ALL scripts sequentially...
    echo.
    echo [1/5] TP_Melusina MPC...
    %UE_EDITOR% %PROJECT_PATH% -ExecutePythonScript=%SCRIPTS_DIR%\create_tp_melusina_mpc.py
    timeout /t 10
    echo.
    echo [2/5] NS_Uni_WaterMist...
    %UE_EDITOR% %PROJECT_PATH% -ExecutePythonScript=%SCRIPTS_DIR%\create_water_mist_niagara.py
    timeout /t 10
    echo.
    echo [3/5] MF_WaterBioluminescence_v7...
    %UE_EDITOR% %PROJECT_PATH% -ExecutePythonScript=%SCRIPTS_DIR%\create_water_bioluminescence_mf.py
    timeout /t 10
    echo.
    echo [4/5] SK_Melusina Slots Inspection...
    %UE_EDITOR% %PROJECT_PATH% -ExecutePythonScript=%SCRIPTS_DIR%\inspect_sk_melusina_slots.py
    timeout /t 10
    echo.
    echo [5/5] Blueprint Wiring Review...
    %UE_EDITOR% %PROJECT_PATH% -ExecutePythonScript=%SCRIPTS_DIR%\review_blueprint_wiring.py
)

echo.
echo Done!
pause