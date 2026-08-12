# Run the fixed Melodia Studio blender smoke queue headlessly.
param()

$ErrorActionPreference = "Continue"
$deploy = $PSScriptRoot
$queuePath = Join-Path $deploy "blender_smoke_queue.json"
$queue = Get-Content $queuePath -Raw | ConvertFrom-Json

$blender = @(
    "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
    "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $blender) {
    Write-Error "Blender 5.2/5.1 not found"
}

$results = @()
$failed = $false

foreach ($job in $queue.jobs) {
    $script = Join-Path $deploy $job.script
    if (-not (Test-Path $script)) {
        Write-Host "[SKIP] $($job.id) - missing $($job.script)"
        $results += [pscustomobject]@{ id = $job.id; status = "skip"; reason = "missing script" }
        continue
    }
    Write-Host "=== JOB $($job.id) ==="
    # Blender writes progress to stderr; do not treat that as a terminating error.
    cmd /c "`"$blender`" --background --factory-startup --python `"$script`""
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        Write-Host "[FAIL] $($job.id) exit=$code"
        $results += [pscustomobject]@{ id = $job.id; status = "fail"; exit = $code }
        $failed = $true
    } else {
        Write-Host "[PASS] $($job.id)"
        $results += [pscustomobject]@{ id = $job.id; status = "pass"; exit = 0 }
    }
}

$auditDir = Join-Path (Split-Path $deploy -Parent) "Saved\Audit"
New-Item -ItemType Directory -Force -Path $auditDir | Out-Null
$out = Join-Path $auditDir "blender_smoke_last.json"
$results | ConvertTo-Json -Depth 4 | Set-Content -Path $out -Encoding UTF8
Write-Host "Wrote $out"

if ($failed) { exit 1 }
Write-Host "smoke queue: ALL PASS"
