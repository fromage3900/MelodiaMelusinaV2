#requires -Version 5.1
<#
.SYNOPSIS
  Register a self-hosted GitHub Actions runner for the Melodia UE58 lanes.
.DESCRIPTION
  Resolves the latest actions/runner win-x64 release, verifies SHA-256,
  extracts, and configures the runner with the exact labels required by
  .github/workflows/unreal_build.yml and melodia_aws_publish.yml:
  [self-hosted, Windows, UE58].
  Get the registration token (valid ~1 hour) from:
  https://github.com/fromage3900/MelodiaMelusinaV2/settings/actions/runners/new?arch=x64&platform=windows
  Service install (-InstallService) requires an elevated shell.
.EXAMPLE
  .\register_ue58_runner.ps1 -Token <TOKEN>
  .\register_ue58_runner.ps1 -Token <TOKEN> -InstallService
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$Token,
  [string]$RepoUrl = 'https://github.com/fromage3900/MelodiaMelusinaV2',
  [string]$RunnerName = 'ue58-workstation',
  [string]$InstallDir = 'C:\actions-runner',
  [switch]$InstallService
)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# 1. Resolve the latest runner release (win-x64).
$rel = Invoke-RestMethod -Uri 'https://api.github.com/repos/actions/runner/releases/latest' -TimeoutSec 30
$asset = $rel.assets | Where-Object { $_.name -match '^actions-runner-win-x64-[\d\.]+\.zip$' } | Select-Object -First 1
if (-not $asset) { throw 'No actions-runner-win-x64 asset in the latest release.' }
Write-Host "Latest runner: $($rel.tag_name) - $($asset.name) ($([math]::Round($asset.size / 1MB, 1)) MB)"

# 2. Download.
$zip = Join-Path $env:TEMP $asset.name
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zip -TimeoutSec 600

# 3. Verify SHA-256 against the release notes when they carry it.
$expected = $null
foreach ($line in ($rel.body -split "`n")) {
  if ($line -match [regex]::Escape($asset.name)) {
    $m = [regex]::Match($line, '[A-Fa-f0-9]{64}')
    if ($m.Success) { $expected = $m.Value.ToLower(); break }
  }
}
$actual = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
if ($expected -and $actual -ne $expected) { throw "SHA-256 mismatch: expected $expected, got $actual" }
if ($expected) { Write-Host 'SHA-256 verified.' } else { Write-Warning 'Checksum not found in release notes; download unverified.' }

# 4. Extract.
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory($zip, $InstallDir)

# 5. Configure with the exact three labels the workflows select on.
Push-Location $InstallDir
try {
  .\config.cmd --unattended --url $RepoUrl --token $Token --name $RunnerName --labels self-hosted,Windows,UE58 --work (Join-Path $InstallDir '_work') --replace
} finally { Pop-Location }

# 6. Optional Windows service (elevated shell).
if ($InstallService) {
  Push-Location $InstallDir
  try { .\svc.cmd install; .\svc.cmd start } finally { Pop-Location }
}

Write-Host ''
Write-Host "Runner '$RunnerName' registered. Verify labels at:"
Write-Host '  Settings -> Actions -> Runners  (self-hosted / Windows / UE58)'
Write-Host 'Then test: Actions -> Unreal Build + Tests -> Run workflow.'
