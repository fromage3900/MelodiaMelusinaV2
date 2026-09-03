# Melodia workstation inspection helper.
# This script is read-only with respect to the workstation except for its
# local JSON report under Saved\Workstation\, which is ignored by the repo.
[CmdletBinding()]
param(
    [string]$OutputPath = ""
)

$ErrorActionPreference = "SilentlyContinue"
$projectRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $projectRoot "Config\paths.json"

function Get-FirstCommandPath {
    param([string[]]$Names)

    foreach ($name in $Names) {
        $command = Get-Command $name -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -ne $command) {
            return [string]$command.Source
        }
    }
    return $null
}

function Get-FirstExistingPath {
    param([string[]]$Candidates)

    foreach ($candidate in $Candidates) {
        $item = Get-ChildItem -Path $candidate -File -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($null -ne $item) {
            return [string]$item.FullName
        }
    }
    return $null
}

function Get-UserOrProcessEnvironmentValue {
    param([string]$Name)

    $value = [Environment]::GetEnvironmentVariable($Name, "Process")
    if ([string]::IsNullOrWhiteSpace($value)) {
        $value = [Environment]::GetEnvironmentVariable($Name, "User")
    }
    return $value
}

function Get-ConfiguredRoot {
    param(
        [string]$EnvironmentName,
        [string]$ConfigName,
        [string]$Fallback
    )

    $value = Get-UserOrProcessEnvironmentValue $EnvironmentName
    if ([string]::IsNullOrWhiteSpace($value) -and $null -ne $script:config) {
        $paths = $script:config.paths
        if ($null -ne $paths) {
            $value = $paths.$ConfigName
        }
        if ([string]::IsNullOrWhiteSpace($value)) {
            $defaults = $script:config.defaults
            if ($null -ne $defaults) {
                $value = $defaults.$ConfigName
            }
        }
    }
    if ([string]::IsNullOrWhiteSpace($value)) {
        $value = $Fallback
    }
    return $value
}

function Get-Gigabytes {
    param([double]$Bytes)
    if ($Bytes -le 0) { return $null }
    return [math]::Round($Bytes / 1GB, 1)
}

$script:config = $null
if (Test-Path -LiteralPath $configPath -PathType Leaf) {
    try {
        $script:config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
    } catch {
        $script:config = $null
    }
}

$computer = Get-CimInstance Win32_ComputerSystem | Select-Object -First 1
$os = Get-CimInstance Win32_OperatingSystem | Select-Object -First 1
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$memoryModules = @(Get-CimInstance Win32_PhysicalMemory)
$gpus = @(Get-CimInstance Win32_VideoController)
$ramGb = if ($null -ne $computer) { Get-Gigabytes $computer.TotalPhysicalMemory } else { $null }

$profile = if ($null -eq $ramGb) {
    "unknown"
} elseif ($ramGb -lt 24) {
    "worker-first-16GB"
} elseif ($ramGb -lt 48) {
    "hybrid-32GB"
} else {
    "full-candidate"
}

$machineName = if ([string]::IsNullOrWhiteSpace($env:COMPUTERNAME)) {
    "machine"
} else {
    $env:COMPUTERNAME
}

$ueRoot = Get-ConfiguredRoot `
    -EnvironmentName "MELODIA_UNREAL_ROOT" `
    -ConfigName "unreal" `
    -Fallback "C:\Program Files\Epic Games\UE_5.8"

$blenderRoot = Get-ConfiguredRoot `
    -EnvironmentName "MELODIA_BLENDER_ROOT" `
    -ConfigName "blender" `
    -Fallback "C:\Program Files\Blender Foundation\Blender 5.2"

$toolPaths = [ordered]@{
    git = Get-FirstCommandPath @("git")
    git_lfs = $null
    python = Get-FirstCommandPath @("python", "py")
    node = Get-FirstCommandPath @("node")
    rider = Get-FirstCommandPath @("rider64", "rider")
    vscode = Get-FirstCommandPath @("code")
    blender = Get-FirstCommandPath @("blender")
    powershell = Get-FirstCommandPath @("pwsh", "powershell")
    aws = Get-FirstCommandPath @("aws")
    ollama = Get-FirstCommandPath @("ollama")
}

if ($null -ne $toolPaths.git) {
    $lfsVersion = (& git lfs version 2>&1 | Out-String).Trim()
    if ($lfsVersion -match "git-lfs") {
        $toolPaths.git_lfs = $lfsVersion
    }
}

$commonPaths = [ordered]@{
    rider = Get-FirstExistingPath @(
        "$env:LOCALAPPDATA\JetBrains\Toolbox\apps\Rider\*\*\*\bin\rider64.exe",
        "$env:ProgramFiles\JetBrains\JetBrains Rider *\bin\rider64.exe"
    )
    vscode = Get-FirstExistingPath @(
        "$env:LOCALAPPDATA\Programs\Microsoft VS Code\Code.exe",
        "$env:ProgramFiles\Microsoft VS Code\Code.exe"
    )
    blender = Get-FirstExistingPath @(
        (Join-Path $blenderRoot "blender.exe")
    )
    unreal = Get-FirstExistingPath @(
        (Join-Path $ueRoot "Engine\Binaries\Win64\UnrealEditor.exe")
    )
}

$volumes = @()
try {
    $volumes = @(Get-Volume |
        Where-Object { $_.DriveType -eq "Fixed" } |
        ForEach-Object {
            [ordered]@{
                drive = if ($_.DriveLetter) { "$($_.DriveLetter):" } else { $null }
                label = $_.FileSystemLabel
                free_gb = Get-Gigabytes $_.SizeRemaining
                size_gb = Get-Gigabytes $_.Size
            }
        })
} catch {
    $volumes = @()
}

$gpuRecords = @($gpus | ForEach-Object {
    $vram = $null
    if ($_.AdapterRAM -gt 0 -and $_.AdapterRAM -lt 17592186044416) {
        $vram = Get-Gigabytes $_.AdapterRAM
    }
    [ordered]@{
        name = $_.Name
        driver_version = $_.DriverVersion
        vram_gb = $vram
    }
})

$memoryRecords = @($memoryModules | ForEach-Object {
    [ordered]@{
        manufacturer = $_.Manufacturer
        capacity_gb = Get-Gigabytes $_.Capacity
        speed_mhz = $_.Speed
        part_number = $_.PartNumber
    }
})

$checks = [ordered]@{
    project_file = [ordered]@{
        present = Test-Path -LiteralPath (Join-Path $projectRoot "BS_GodFile.uproject")
        path = Join-Path $projectRoot "BS_GodFile.uproject"
    }
    validate_script = [ordered]@{
        present = Test-Path -LiteralPath (Join-Path $projectRoot "deploy\validate_setup.ps1")
        path = Join-Path $projectRoot "deploy\validate_setup.ps1"
    }
    vsconfig = [ordered]@{
        present = Test-Path -LiteralPath (Join-Path $projectRoot ".vsconfig")
        path = Join-Path $projectRoot ".vsconfig"
    }
    unreal_editor = [ordered]@{
        present = $null -ne $commonPaths.unreal
        path = $commonPaths.unreal
        root = $ueRoot
    }
    blender = [ordered]@{
        present = $null -ne $commonPaths.blender
        path = $commonPaths.blender
        root = $blenderRoot
    }
    git = [ordered]@{
        present = $null -ne $toolPaths.git
        path = $toolPaths.git
    }
    git_lfs = [ordered]@{
        present = $null -ne $toolPaths.git_lfs
        detail = $toolPaths.git_lfs
    }
}

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $reportDirectory = Join-Path $projectRoot "Saved\Workstation"
    $OutputPath = Join-Path $reportDirectory "$machineName-workstation-report.json"
}

$reportDirectory = Split-Path -Parent $OutputPath
if (-not [string]::IsNullOrWhiteSpace($reportDirectory)) {
    New-Item -ItemType Directory -Path $reportDirectory -Force | Out-Null
}

$report = [ordered]@{
    generated_at = (Get-Date).ToString("o")
    machine = [ordered]@{
        computer_name = $machineName
        manufacturer = if ($null -ne $computer) { $computer.Manufacturer } else { $null }
        model = if ($null -ne $computer) { $computer.Model } else { $null }
        os = if ($null -ne $os) { $os.Caption } else { $null }
        os_version = if ($null -ne $os) { $os.Version } else { $null }
        ram_gb = $ramGb
        profile = $profile
        cpu = if ($null -ne $cpu) { $cpu.Name } else { $null }
        logical_processors = if ($null -ne $cpu) { $cpu.NumberOfLogicalProcessors } else { $null }
    }
    memory_modules = $memoryRecords
    gpus = $gpuRecords
    fixed_volumes = $volumes
    configured_roots = [ordered]@{
        unreal = $ueRoot
        blender = $blenderRoot
    }
    tool_paths = $toolPaths
    common_install_paths = $commonPaths
    checks = $checks
    repository_root = $projectRoot
    report_path = $OutputPath
}

$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding UTF8

Write-Host "========================================="
Write-Host " MELODIA WORKSTATION INSPECTION"
Write-Host "========================================="
Write-Host "Machine: $machineName"
Write-Host "RAM:     $ramGb GB"
Write-Host "Profile: $profile"
Write-Host "CPU:     $($report.machine.cpu)"
Write-Host "Report:  $OutputPath"
Write-Host ""

Write-Host "GPU(s):"
if ($gpuRecords.Count -eq 0) {
    Write-Host "  [WARN] No GPU record found"
} else {
    foreach ($gpu in $gpuRecords) {
        $vramText = if ($null -ne $gpu.vram_gb) { "$($gpu.vram_gb) GB VRAM" } else { "VRAM unavailable" }
        Write-Host "  - $($gpu.name) ($vramText)"
    }
}

Write-Host ""
Write-Host "Project/tool checks:"
foreach ($entry in $checks.GetEnumerator()) {
    $status = if ($entry.Value.present) { "OK" } else { "WARN" }
    $detail = if ($entry.Value.path) { $entry.Value.path } else { $entry.Value.detail }
    Write-Host ("  [{0,-4}] {1}: {2}" -f $status, $entry.Key, $detail)
}

Write-Host ""
Write-Host "Fixed volumes:"
foreach ($volume in $volumes) {
    Write-Host "  - $($volume.drive) $($volume.label): $($volume.free_gb) GB free / $($volume.size_gb) GB"
}

Write-Host ""
Write-Host "This report is local and ignored. Do not commit it or place credentials in it."
