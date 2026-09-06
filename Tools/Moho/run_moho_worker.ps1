[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$JobPath,
    [string]$OutputRoot = ""
)

$ErrorActionPreference = "Stop"
$workerRoot = Split-Path -Parent $PSScriptRoot
$projectRoot = Split-Path -Parent $workerRoot
$job = [IO.Path]::GetFullPath($JobPath)

if (-not (Test-Path -LiteralPath $job -PathType Leaf)) {
    throw "Moho job file not found: $job"
}

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path $workerRoot "output"
}

$output = [IO.Path]::GetFullPath($OutputRoot)
$projectPrefix = $projectRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if (-not $output.StartsWith($projectPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "OutputRoot must remain inside the project worker area: $projectRoot"
}

New-Item -ItemType Directory -Path $output -Force | Out-Null
$jobHash = (Get-FileHash -LiteralPath $job -Algorithm SHA256).Hash
$record = [ordered]@{
    generated_at = (Get-Date).ToString("o")
    status = "staged-only"
    job = $job
    job_sha256 = $jobHash
    output_root = $output
    moho_executable = $env:MELODIA_MOHO_ROOT
    note = "Execution is intentionally not implemented until a supported Moho automation contract is documented."
}

$recordPath = Join-Path $output "moho-worker-last-job.json"
$record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $recordPath -Encoding UTF8
Write-Host "Moho worker scaffold recorded a staged job." -ForegroundColor Cyan
Write-Host "Job:    $job"
Write-Host "SHA256: $jobHash"
Write-Host "Record: $recordPath"