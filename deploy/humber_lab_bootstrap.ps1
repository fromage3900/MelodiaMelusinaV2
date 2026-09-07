# Melodia Humber Lab bootstrap.
# No admin actions, no software installation, no persistence services.
[CmdletBinding()]
param(
    [ValidateSet("Check","Prepare")]
    [string]$Mode = "Check",
    [switch]$IConfirmAuthorizedUse
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ReportDir = Join-Path $ProjectRoot "Saved\Workstation"
$Machine = if ($env:COMPUTERNAME) { $env:COMPUTERNAME } else { "machine" }
$ReportPath = Join-Path $ReportDir ($Machine + "-humber-lab.json")
New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null

function Command-Exists {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

$GitAvailable = Command-Exists "git"
$LfsAvailable = $false
if ($GitAvailable) {
    & git lfs version *> $null
    $LfsAvailable = $LASTEXITCODE -eq 0
}

$UnrealRoot = $env:MELODIA_UNREAL_ROOT
if ([string]::IsNullOrWhiteSpace($UnrealRoot)) { $UnrealRoot = "C:\Program Files\Epic Games\UE_5.8" }
$UnrealCmd = Join-Path $UnrealRoot "Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$UnrealAvailable = Test-Path -LiteralPath $UnrealCmd -PathType Leaf

$BlenderCandidates = @()
if ($env:MELODIA_BLENDER_EXE) { $BlenderCandidates += $env:MELODIA_BLENDER_EXE }
$BlenderCandidates += @(
    "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
    "C:\Program Files\Blender Foundation\Blender\blender.exe"
)
$BlenderCmd = Get-Command blender.exe -ErrorAction SilentlyContinue
if ($BlenderCmd) { $BlenderCandidates += $BlenderCmd.Source }
$BlenderExe = $BlenderCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -First 1

$RootName = [IO.Path]::GetPathRoot($ProjectRoot).Substring(0,1)
$Drive = Get-PSDrive -Name $RootName -ErrorAction SilentlyContinue
$FreeGB = if ($Drive) { [math]::Round($Drive.Free / 1GB, 1) } else { $null }

if ($Mode -eq "Prepare") {
    if (-not $IConfirmAuthorizedUse) {
        throw "Prepare changes the local checkout. Re-run with -IConfirmAuthorizedUse only in an authorized Humber session."
    }
    if (-not $GitAvailable) { throw "Git is not available." }
    if (-not $LfsAvailable) { throw "Git LFS is not available." }

    $SyncScript = Join-Path $ProjectRoot "deploy\sync_workstation.ps1"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $SyncScript -Mode Sync -LfsProfile HumberSemester
    if ($LASTEXITCODE -ne 0) { throw "Workstation sync did not reach a safe state." }
}

$Branch = if ($GitAvailable) { (& git -C $ProjectRoot branch --show-current | Out-String).Trim() } else { "" }
$Head = if ($GitAvailable) { (& git -C $ProjectRoot rev-parse HEAD | Out-String).Trim() } else { "" }
$Status = if ($GitAvailable) { @(& git -C $ProjectRoot status --short) } else { @() }

$Report = [ordered]@{
    schema = "melodia.humber_lab_bootstrap.v1"
    generated_at = (Get-Date).ToString("o")
    machine = $Machine
    mode = $Mode
    project_root = $ProjectRoot
    git_available = $GitAvailable
    lfs_available = $LfsAvailable
    branch = $Branch
    head = $Head
    dirty = $Status.Count -gt 0
    unreal_58_available = $UnrealAvailable
    unreal_cmd = $(if ($UnrealAvailable) { $UnrealCmd } else { "" })
    blender_available = -not [string]::IsNullOrWhiteSpace([string]$BlenderExe)
    blender_exe = [string]$BlenderExe
    free_disk_gb = $FreeGB
    authorized_use_required_for_prepare = $true
    persistent_services_created = $false
}

$Report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $ReportPath -Encoding UTF8

Write-Host "====================================" -ForegroundColor Magenta
Write-Host " MELODIA HUMBER LAB BOOTSTRAP" -ForegroundColor Magenta
Write-Host "====================================" -ForegroundColor Magenta
Write-Host "Mode:       $Mode"
Write-Host "Branch:     $Branch"
Write-Host "HEAD:       $Head"
Write-Host "Dirty:      $($Status.Count -gt 0)"
Write-Host "Git LFS:    $LfsAvailable"
Write-Host "UE 5.8:     $UnrealAvailable"
Write-Host "Blender:    $BlenderExe"
Write-Host "Free disk:  $FreeGB GB"
Write-Host "Report:     $ReportPath"

if (-not $GitAvailable -or -not $LfsAvailable) { exit 1 }
if ($Mode -eq "Prepare" -and $Branch -ne "main") { exit 1 }
exit 0