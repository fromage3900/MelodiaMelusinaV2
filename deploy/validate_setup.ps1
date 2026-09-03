# Portable setup validation for the Melodia workspace.
#
# Resolution order for paths:
#   explicit parameter -> environment variable -> Config/paths.json -> default
#
# This script is intentionally non-destructive. It never installs Unreal,
# Marketplace plugins, Blender, Python, Node, or external services.
param(
    [switch]$Verbose,
    [switch]$StrictOptional,
    [switch]$SkipServices,
    [switch]$CheckWebsite,
    [switch]$CheckLfsHydration,
    [switch]$RequirePluginBinaries,
    [string]$WebsiteRoot
)

$ErrorActionPreference = "Stop"
$deploy = $PSScriptRoot
$projectRoot = Split-Path -Parent $deploy
$workspaceRoot = Split-Path -Parent $projectRoot
$configPath = Join-Path $projectRoot "Config\paths.json"
$script:issues = 0
$script:warnings = 0

function Get-PropertyValue {
    param([object]$Object, [string]$Name)
    if ($null -eq $Object) { return $null }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Write-Check {
    param(
        [string]$Label,
        [ValidateSet("OK", "WARN", "FAIL")]
        [string]$Status,
        [string]$Detail
    )
    $color = switch ($Status) {
        "OK" { "Green" }
        "WARN" { "Yellow" }
        "FAIL" { "Red" }
    }
    Write-Host ("  [{0,-4}] {1}: {2}" -f $Status, $Label, $Detail) -ForegroundColor $color
    if ($Status -eq "FAIL") { $script:issues++ }
    if ($Status -eq "WARN") { $script:warnings++ }
}

function Resolve-ConfiguredPath {
    param(
        [string]$Name,
        [string]$Explicit,
        [string]$Fallback
    )
    if (-not [string]::IsNullOrWhiteSpace($Explicit)) {
        $value = $Explicit
    } else {
        $environmentVariables = Get-PropertyValue $script:config "environment_variables"
        $environmentName = Get-PropertyValue $environmentVariables $Name
        $value = if ($environmentName) {
            [Environment]::GetEnvironmentVariable([string]$environmentName)
        } else {
            $null
        }
        if ([string]::IsNullOrWhiteSpace($value)) {
            $configuredPaths = Get-PropertyValue $script:config "paths"
            $value = Get-PropertyValue $configuredPaths $Name
        }
        if ([string]::IsNullOrWhiteSpace($value)) {
            $defaults = Get-PropertyValue $script:config "defaults"
            $value = Get-PropertyValue $defaults $Name
        }
        if ([string]::IsNullOrWhiteSpace($value)) { $value = $Fallback }
    }
    if ([string]::IsNullOrWhiteSpace($value)) { return "" }
    $value = [Environment]::ExpandEnvironmentVariables([string]$value)
    if (-not [IO.Path]::IsPathRooted($value)) {
        $value = Join-Path $workspaceRoot $value
    }
    return [IO.Path]::GetFullPath($value)
}

function Test-TcpPort {
    param([int]$Port, [int]$TimeoutMilliseconds = 700)
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $async = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        if (-not $async.AsyncWaitHandle.WaitOne($TimeoutMilliseconds)) { return $false }
        $client.EndConnect($async)
        return $true
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

function Test-HttpEndpoint {
    param([string]$Uri)
    try {
        $response = Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
    } catch {
        return $false
    }
}

function Test-CommandVersion {
    param(
        [string]$Name,
        [int]$MinimumMajor,
        [int]$MinimumMinor,
        [switch]$Required,
        [switch]$ExactMinor
    )
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        Write-Check $Name $(if ($Required) { "FAIL" } else { "WARN" }) "not found on PATH"
        return
    }
    try {
        $raw = & $Name --version 2>&1 | Out-String
        $match = [regex]::Match($raw, "(?<major>\d+)\.(?<minor>\d+)")
        if (-not $match.Success) {
            Write-Check $Name "WARN" "found at $($command.Source), version was not parseable"
            return
        }
        $major = [int]$match.Groups["major"].Value
        $minor = [int]$match.Groups["minor"].Value
        $meetsMinimum = ($major -gt $MinimumMajor) -or
            ($major -eq $MinimumMajor -and $minor -ge $MinimumMinor)
        $matchesBaseline = $major -eq $MinimumMajor -and
            (-not $ExactMinor -or $minor -eq $MinimumMinor)
        if ($meetsMinimum -and $matchesBaseline) {
            Write-Check $Name "OK" "$($match.Value) at $($command.Source)"
        } elseif ($meetsMinimum) {
            Write-Check $Name "WARN" `
                "$($match.Value) found; documented baseline is $MinimumMajor.$MinimumMinor"
        } else {
            Write-Check $Name $(if ($Required) { "FAIL" } else { "WARN" }) `
                "$($match.Value) is below required $MinimumMajor.$MinimumMinor"
        }
    } catch {
        Write-Check $Name $(if ($Required) { "FAIL" } else { "WARN" }) "version check failed: $($_.Exception.Message)"
    }
}

function Test-LfsPointer {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $false
    }
    $firstLine = Get-Content -LiteralPath $Path -TotalCount 1 -ErrorAction SilentlyContinue
    return $firstLine -eq "version https://git-lfs.github.com/spec/v1"
}

try {
    $script:config = if (Test-Path $configPath) {
        Get-Content $configPath -Raw | ConvertFrom-Json
    } else {
        [pscustomobject]@{}
    }
} catch {
    Write-Host "Unable to parse $configPath`: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

$configuredPaths = Get-PropertyValue $script:config "paths"
$ueRoot = Resolve-ConfiguredPath "unreal" "" "C:\Program Files\Epic Games\UE_5.8"
$blenderRoot = Resolve-ConfiguredPath "blender" "" "C:\Program Files\Blender Foundation\Blender 5.2"
$voicevoxRoot = Resolve-ConfiguredPath "voicevox" "" ""
$materialMakerRoot = Resolve-ConfiguredPath "material_maker" "" ""
$website = Resolve-ConfiguredPath "website" $WebsiteRoot (Join-Path $workspaceRoot "my-site-clean")
$ueExe = Join-Path $ueRoot "Engine\Binaries\Win64\UnrealEditor.exe"
$blenderExe = Join-Path $blenderRoot "blender.exe"
$projectFile = Join-Path $projectRoot "BS_GodFile.uproject"
$collaboratorManifest = Join-Path $projectRoot "deploy\collaborator_ue_manifest.txt"

Write-Host "========================================="
Write-Host " MELODIA PORTABLE SETUP CHECK"
Write-Host " $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host " Project:  $projectRoot"
Write-Host " Website:  $website"
Write-Host "========================================="
Write-Host ""
Write-Check "paths.json" $(if (Test-Path $configPath) { "OK" } else { "WARN" }) `
    $(if (Test-Path $configPath) { "loaded" } else { "using defaults" })

Write-Host ""
Write-Host "Core tools and engine" -ForegroundColor Cyan
Write-Check "Unreal Engine" $(if (Test-Path $ueExe) { "OK" } else { "FAIL" }) `
    $(if (Test-Path $ueExe) { "$ueRoot (5.8)" } else { "missing $ueExe" })
Write-Check "BS_GodFile.uproject" $(if (Test-Path $projectFile) { "OK" } else { "FAIL" }) `
    $(if (Test-Path $projectFile) { $projectFile } else { "missing $projectFile" })
Write-Check "Blender" $(if (Test-Path $blenderExe) { "OK" } else { "WARN" }) `
    $(if (Test-Path $blenderExe) { "$blenderRoot (configured 5.2)" } else { "missing $blenderExe; required for Geometry mode" })
if ($voicevoxRoot) {
    Write-Check "VOICEVOX path" $(if (Test-Path $voicevoxRoot) { "OK" } else { "WARN" }) $voicevoxRoot
}
if ($materialMakerRoot) {
    Write-Check "Material Maker path" $(if (Test-Path $materialMakerRoot) { "OK" } else { "WARN" }) $materialMakerRoot
}

Test-CommandVersion "python" 3 11 -Required -ExactMinor
Test-CommandVersion "node" 20 0 -Required:$false

$git = Get-Command git -ErrorAction SilentlyContinue
if ($null -eq $git) {
    Write-Check "git" "FAIL" "not found on PATH"
} else {
    try {
        $lfs = git lfs version 2>&1 | Out-String
        Write-Check "Git LFS" $(if ($lfs -match "git-lfs") { "OK" } else { "FAIL" }) $lfs.Trim()
    } catch {
        Write-Check "Git LFS" "FAIL" "git lfs is unavailable"
    }
}

Write-Host ""
Write-Host "Project plugins" -ForegroundColor Cyan
$manifestRecords = @()
$requiredPluginManifests = @()
if (Test-Path -LiteralPath $collaboratorManifest -PathType Leaf) {
    $manifestRecords = @(
        Get-Content -LiteralPath $collaboratorManifest |
            Where-Object { $_ -and -not $_.Trim().StartsWith("#") } |
            ForEach-Object {
                $parts = $_.Trim() -split "\s+"
                if ($parts.Count -ge 2) {
                    [pscustomobject]@{ Type = $parts[0]; Name = $parts[1]; Path = $(if ($parts.Count -ge 3) { $parts[2] } else { "" }) }
                }
            }
    )
    $requiredPluginManifests = @(
        $manifestRecords | Where-Object { $_.Type -eq "PLUGIN" } |
            ForEach-Object { @{ Name = $_.Name; Path = $_.Path } }
    )
} else {
    Write-Check "Collaborator manifest" "FAIL" "missing $collaboratorManifest"
}
Write-Host "Required sparse paths" -ForegroundColor Cyan
$requiredSparsePaths = @($manifestRecords | Where-Object { $_.Type -eq "SPARSE" })
foreach ($sparse in $requiredSparsePaths) {
    $relativeSparsePath = $sparse.Name.TrimStart("/") -replace "/", "\"
    $absoluteSparsePath = Join-Path $projectRoot $relativeSparsePath
    Write-Check "Sparse path $($sparse.Name)" $(if (Test-Path -LiteralPath $absoluteSparsePath) { "OK" } else { "FAIL" }) `
        $(if (Test-Path -LiteralPath $absoluteSparsePath) { $absoluteSparsePath } else { "missing; rerun the UE-capable sparse checkout" })
}
foreach ($plugin in $requiredPluginManifests) {
    $manifestPath = Join-Path $projectRoot $plugin.Path
    if (Test-Path -LiteralPath $manifestPath -PathType Leaf) {
        Write-Check "Plugin $($plugin.Name) manifest" "OK" $manifestPath
    } else {
        Write-Check "Plugin $($plugin.Name) manifest" "FAIL" "missing $manifestPath; rerun the UE-capable sparse checkout"
        continue
    }

    $pluginRoot = Split-Path -Parent $manifestPath
    $sourcePath = Join-Path $pluginRoot "Source"
    if (Test-Path -LiteralPath $sourcePath -PathType Container) {
        Write-Check "Plugin $($plugin.Name) source" "OK" $sourcePath
    } else {
        Write-Check "Plugin $($plugin.Name) source" "FAIL" "missing $sourcePath"
    }

    $binaryPath = Join-Path $pluginRoot "Binaries\Win64"
    $pluginDlls = if (Test-Path -LiteralPath $binaryPath -PathType Container) {
        @(Get-ChildItem -LiteralPath $binaryPath -Filter "*.dll" -File -ErrorAction SilentlyContinue)
    } else {
        @()
    }
    if ($pluginDlls.Count -gt 0) {
        Write-Check "Plugin $($plugin.Name) binaries" "OK" "$($pluginDlls.Count) Win64 DLL(s)"
    } elseif ($RequirePluginBinaries) {
        Write-Check "Plugin $($plugin.Name) binaries" "FAIL" "not built; run the closed-editor UE 5.8 -NoUBA build"
    } else {
        Write-Check "Plugin $($plugin.Name) binaries" "WARN" "source-only checkout; run the closed-editor UE 5.8 -NoUBA build before opening the project"
    }
}

if ($CheckLfsHydration) {
    Write-Host ""
    Write-Host "Required LFS hydration" -ForegroundColor Cyan
    $requiredLfsPrefixes = @()
    if (Test-Path -LiteralPath $collaboratorManifest -PathType Leaf) {
        $requiredLfsPrefixes = @(
            Get-Content -LiteralPath $collaboratorManifest |
                Where-Object { $_ -and -not $_.Trim().StartsWith("#") } |
                ForEach-Object {
                    $parts = $_.Trim() -split "\s+"
                    if ($parts.Count -ge 2 -and $parts[0] -eq "LFS") {
                        $parts[1] -replace "/\*\*$", "/"
                    }
                }
        )
    }
    $trackedLfsFiles = @(git -C $projectRoot lfs ls-files --name-only 2>$null)
    $lfsMissing = 0
    $lfsFailurePaths = @()
    foreach ($relativePath in $trackedLfsFiles) {
        $normalizedPath = ([string]$relativePath).Trim()
        if ([string]::IsNullOrWhiteSpace($normalizedPath)) { continue }
        $isRequired = $false
        foreach ($prefix in $requiredLfsPrefixes) {
            if ($normalizedPath.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
                $isRequired = $true
                break
            }
        }
        if (-not $isRequired) { continue }
        $absolutePath = Join-Path $projectRoot ($normalizedPath -replace "/", "\")
        if (-not (Test-Path -LiteralPath $absolutePath -PathType Leaf)) {
            $lfsMissing++
            $lfsFailurePaths += "$normalizedPath (missing)"
            continue
        }
        if (Test-LfsPointer $absolutePath) {
            $lfsMissing++
            $lfsFailurePaths += "$normalizedPath (pointer)"
        }
    }
    if ($lfsMissing -eq 0) {
        Write-Check "Required LFS files" "OK" "hydrated"
    } else {
        Write-Check "Required LFS files" "FAIL" "$lfsMissing pointer or missing file(s); run git lfs pull with the collaborator tier includes"
        $lfsFailurePaths | Select-Object -First 10 | ForEach-Object {
            Write-Host "    - $_" -ForegroundColor Yellow
        }
    }
} else {
    Write-Check "Required LFS files" "WARN" "not checked; rerun with -CheckLfsHydration after git lfs pull"
}

if (Test-Path $website) {
    Write-Host ""
    Write-Host "Website checkout" -ForegroundColor Cyan
    $websitePackage = Join-Path $website "package.json"
    $websiteLock = Join-Path $website "package-lock.json"
    Write-Check "Website root" "OK" $website
    Write-Check "package.json" $(if (Test-Path $websitePackage) { "OK" } else { "FAIL" }) `
        $(if (Test-Path $websitePackage) { "present" } else { "missing $websitePackage" })
    Write-Check "package-lock.json" $(if (Test-Path $websiteLock) { "OK" } else { "FAIL" }) `
        $(if (Test-Path $websiteLock) { "present; npm ci is reproducible" } else { "missing; npm ci cannot run" })
    Write-Check "site env example" $(if (Test-Path (Join-Path $website ".env.local.example")) { "OK" } else { "WARN" }) `
        "secrets must be supplied outside tracked files"
} elseif ($CheckWebsite) {
    Write-Check "Website root" "FAIL" "not found at $website"
} else {
    Write-Check "Website root" "WARN" "not found at $website (not required for Unreal-only work)"
}

if (-not $SkipServices) {
    Write-Host ""
    Write-Host "Optional service health" -ForegroundColor Cyan
    $services = @(
        @{ Name = "Monolith MCP"; Port = 9316; Uri = "http://127.0.0.1:9316/health" },
        @{ Name = "LiveLink"; Port = 9876; Uri = $null },
        @{ Name = "VOICEVOX"; Port = 50021; Uri = "http://127.0.0.1:50021/version" },
        @{ Name = "Melusina Voice"; Port = 50022; Uri = $null },
        @{ Name = "Ollama"; Port = 11434; Uri = "http://127.0.0.1:11434" },
        @{ Name = "Quantum"; Port = 8008; Uri = "http://127.0.0.1:8008/health" }
    )
    foreach ($service in $services) {
        $up = if ($service.Uri) {
            Test-HttpEndpoint $service.Uri
        } else {
            Test-TcpPort $service.Port
        }
        if ($up) {
            Write-Check $service.Name "OK" "127.0.0.1:$($service.Port)"
        } elseif ($StrictOptional) {
            Write-Check $service.Name "FAIL" "not reachable at 127.0.0.1:$($service.Port)"
        } else {
            Write-Check $service.Name "WARN" "not running; start only for workflows that require it"
        }
    }
}

Write-Host ""
Write-Host "========================================="
Write-Host " SETUP CHECK SUMMARY"
Write-Host "========================================="
Write-Host " Issues:   $script:issues"
Write-Host " Warnings: $script:warnings"
if ($script:issues -eq 0) {
    Write-Host " Core setup is usable; optional services are reported above." -ForegroundColor Green
    Write-Host " Next: read QUICKSTART.md, then run the ECHO status command."
} else {
    Write-Host " Setup is incomplete. Fix failures before editor/build work." -ForegroundColor Red
}
Write-Host "========================================="

exit $(if ($script:issues -eq 0) { 0 } else { 1 })