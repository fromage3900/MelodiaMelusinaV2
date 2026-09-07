# Melodia generic foreground render worker.
# Designed for the home PC first, and usable on any machine/session you are authorized to use.
# It creates no service, performs no network discovery, and makes no project edits.
[CmdletBinding()]
param(
    [ValidateSet("Probe","Blender","UnrealMRQ")]
    [string]$Mode = "Probe",

    [switch]$IConfirmAuthorizedUse,
    [switch]$Execute,
    [string]$JobName = "",

    [string]$BlendFile = "",
    [int]$StartFrame = 1,
    [int]$EndFrame = 1,
    [ValidateSet("PNG","OPEN_EXR","JPEG")]
    [string]$BlenderFormat = "PNG",
    [string]$BlenderOutput = "",

    [string]$Map = "",
    [string]$LevelSequence = "",
    [string]$MoviePipelineConfig = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ProjectFile = Join-Path $ProjectRoot "BS_GodFile.uproject"
$OutRoot = Join-Path $ProjectRoot "Saved\RenderFarm"

function Find-Blender {
    $candidates = @()
    if ($env:MELODIA_BLENDER_EXE) { $candidates += $env:MELODIA_BLENDER_EXE }
    $candidates += @(
        "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
        "C:\Program Files\Blender Foundation\Blender\blender.exe"
    )
    $cmd = Get-Command blender.exe -ErrorAction SilentlyContinue
    if ($cmd) { $candidates += $cmd.Source }
    foreach ($p in $candidates) {
        if ($p -and (Test-Path -LiteralPath $p -PathType Leaf)) { return $p }
    }
    return $null
}

function Find-UnrealCmd {
    $root = $env:MELODIA_UNREAL_ROOT
    if ([string]::IsNullOrWhiteSpace($root)) { $root = "C:\Program Files\Epic Games\UE_5.8" }
    $p = Join-Path $root "Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
    if (Test-Path -LiteralPath $p -PathType Leaf) { return $p }
    return $null
}

function Git-Text {
    param([string[]]$Arguments)
    try { return (& git -C $ProjectRoot @Arguments 2>$null | Out-String).Trim() } catch { return "" }
}

$BlenderExe = Find-Blender
$UnrealCmd = Find-UnrealCmd
$Head = Git-Text @("rev-parse","HEAD")
$Branch = Git-Text @("branch","--show-current")
$Machine = if ($env:COMPUTERNAME) { $env:COMPUTERNAME } else { "machine" }

Write-Host "====================================" -ForegroundColor Magenta
Write-Host " MELODIA RENDER WORKER" -ForegroundColor Magenta
Write-Host "====================================" -ForegroundColor Magenta
Write-Host "Machine: $Machine"
Write-Host "Branch:  $Branch"
Write-Host "HEAD:    $Head"
Write-Host "Blender: $BlenderExe"
Write-Host "Unreal:  $UnrealCmd"

if ($Mode -eq "Probe") { exit 0 }

if (-not $IConfirmAuthorizedUse) {
    throw "Re-run with -IConfirmAuthorizedUse only on a machine/session you are authorized to use."
}

if ([string]::IsNullOrWhiteSpace($JobName)) {
    $JobName = (Get-Date -Format "yyyyMMdd_HHmmss") + "_" + $Mode + "_" + $Machine
}

$JobRoot = Join-Path $OutRoot $JobName
$LogRoot = Join-Path $JobRoot "logs"
New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null

$Manifest = [ordered]@{
    schema = "melodia.render_worker_job.v1"
    generated_at = (Get-Date).ToString("o")
    machine = $Machine
    mode = $Mode
    job = $JobName
    branch = $Branch
    head = $Head
    execute = [bool]$Execute
}

if ($Mode -eq "Blender") {
    if (-not $BlenderExe) { throw "Blender executable not found." }
    if (-not (Test-Path -LiteralPath $BlendFile -PathType Leaf)) { throw "Blend file not found: $BlendFile" }
    if ($EndFrame -lt $StartFrame) { throw "EndFrame must be greater than or equal to StartFrame." }

    if ([string]::IsNullOrWhiteSpace($BlenderOutput)) {
        $FrameRoot = Join-Path $JobRoot "frames"
        New-Item -ItemType Directory -Path $FrameRoot -Force | Out-Null
        $BlenderOutput = Join-Path $FrameRoot "frame_#####"
    } else {
        $Parent = Split-Path -Parent $BlenderOutput
        if ($Parent) { New-Item -ItemType Directory -Path $Parent -Force | Out-Null }
    }

    $Args = @(
        "-b", $BlendFile,
        "-o", $BlenderOutput,
        "-F", $BlenderFormat,
        "-s", [string]$StartFrame,
        "-e", [string]$EndFrame,
        "-a"
    )

    $Manifest.blend_file = $BlendFile
    $Manifest.start_frame = $StartFrame
    $Manifest.end_frame = $EndFrame
    $Manifest.output = $BlenderOutput
    $Manifest.command = $BlenderExe + " " + ($Args -join " ")

    Write-Host $Manifest.command -ForegroundColor Cyan
    if ($Execute) {
        & $BlenderExe @Args 2>&1 | Tee-Object -FilePath (Join-Path $LogRoot "blender.log")
        if ($LASTEXITCODE -ne 0) { throw "Blender render exited with $LASTEXITCODE." }
    }
}

if ($Mode -eq "UnrealMRQ") {
    if (-not $UnrealCmd) { throw "UnrealEditor-Cmd.exe for UE 5.8 not found. Set MELODIA_UNREAL_ROOT if needed." }
    if (-not (Test-Path -LiteralPath $ProjectFile -PathType Leaf)) { throw "Project file missing." }
    if ([string]::IsNullOrWhiteSpace($Map)) { throw "-Map is required." }
    if ([string]::IsNullOrWhiteSpace($MoviePipelineConfig)) { throw "-MoviePipelineConfig is required." }

    $Args = @($ProjectFile, $Map, "-game")
    if (-not [string]::IsNullOrWhiteSpace($LevelSequence)) {
        $Args += "-LevelSequence=$LevelSequence"
    }
    $Args += @(
        "-MoviePipelineConfig=$MoviePipelineConfig",
        "-windowed",
        "-resx=1280",
        "-resy=720",
        "-log",
        "-notexturestreaming"
    )

    $Manifest.map = $Map
    $Manifest.level_sequence = $LevelSequence
    $Manifest.movie_pipeline_config = $MoviePipelineConfig
    $Manifest.command = $UnrealCmd + " " + ($Args -join " ")

    Write-Host $Manifest.command -ForegroundColor Cyan
    Write-Host "Farm unit: keep each temporal camera cut / Level Sequence shot intact." -ForegroundColor Yellow
    if ($Execute) {
        & $UnrealCmd @Args 2>&1 | Tee-Object -FilePath (Join-Path $LogRoot "unreal_mrq.log")
        if ($LASTEXITCODE -ne 0) { throw "Unreal MRQ exited with $LASTEXITCODE." }
    }
}

$ManifestPath = Join-Path $JobRoot "manifest.json"
$Manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ManifestPath -Encoding UTF8
Write-Host "Manifest: $ManifestPath" -ForegroundColor Green