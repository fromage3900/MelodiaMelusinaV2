<#
.SYNOPSIS
    Launches the UE 5.8 editor with BS_GodFile for Claireon proxy integration.
.DESCRIPTION
    Referenced by .claireon/launch_editor.json. The Claireon proxy calls this
    with optional -SkipBuild when an editor instance is needed for tool_search/python_execute.
.PARAMETER ProjectPath
    Path to BS_GodFile.uproject
.PARAMETER SkipBuild
    If present, skips the build step (faster iterative launches)
#>
param(
    [string]$ProjectPath = "",
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'

# Resolve paths
$worktreeRoot = Split-Path -Parent $MyInvocation.MyCommand.Path  # Scripts/
$worktreeRoot = Resolve-Path (Join-Path $worktreeRoot '..') | Select-Object -ExpandProperty Path

if ([string]::IsNullOrWhiteSpace($ProjectPath)) {
    $ProjectPath = Join-Path $worktreeRoot 'BS_GodFile.uproject'
}
$ProjectPath = [System.IO.Path]::GetFullPath($ProjectPath)

# UE 5.8 engine location
$enginePath = 'C:\Program Files\Epic Games\UE_5.8'
$ubt = Join-Path $enginePath 'Engine\Binaries\DotNET\UnrealBuildTool\UnrealBuildTool.exe'
$editorExe = Join-Path $enginePath 'Engine\Binaries\Win64\UnrealEditor.exe'
$editorCmd = Join-Path $enginePath 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'

Write-Host "[LaunchEditor] Project: $ProjectPath"
Write-Host "[LaunchEditor] Engine:  $enginePath"

if (-not (Test-Path $editorExe)) {
    Write-Error "UnrealEditor.exe not found at $editorExe"
    exit 1
}

# Build the editor target if not skipped
if (-not $SkipBuild) {
    Write-Host "[LaunchEditor] Building BS_GodFileEditor..."
    $buildArgs = @(
        'BS_GodFileEditor',
        'Win64',
        'Development',
        "-Project=`"$ProjectPath`",
        '-WaitMutex',
        '-NoHotReload'
    )
    & $ubt $buildArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Build failed (exit $LASTEXITCODE)"
        exit $LASTEXITCODE
    }
}

# Launch with -StartMCPServer to auto-start Claireon on load
$launchArgs = @(
    "`"$ProjectPath`"",
    '-StartMCPServer'
)

Write-Host "[LaunchEditor] Starting editor with Claireon MCP server..."
Start-Process -FilePath $editorExe -ArgumentList $launchArgs
