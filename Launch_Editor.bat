@echo off
REM Canonical launcher for BS_GodFile -- always forces an in-memory DDC.
REM Added 2026-08-26 after the local Zen/DDC cache on F:\UE_DDC became
REM unreachable and crashed editor startup ("Unable to use cache graph
REM 'Installed' because it has no writable nodes available").
REM -DDC-ForceMemoryCache is command-line-only (FParse::Param in
REM DerivedDataBackends.cpp) -- there is no .ini equivalent, so this
REM script is the only way to make the bypass automatic. Trade-off:
REM no persistent shader/asset cache between sessions -- slower cold
REM starts, but immune to the F: drive/ZenServer failure mode.
"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "%~dp0BS_GodFile.uproject" -DDC-ForceMemoryCache
