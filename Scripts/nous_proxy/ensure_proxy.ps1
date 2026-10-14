# Start nous_anthropic_proxy.py hidden if nothing is listening yet. Exit 1 if it never comes up.
$port = if ($env:NOUS_PROXY_PORT) { [int]$env:NOUS_PROXY_PORT } else { 47821 }
# Upstream model default: stepfun/step-5-preview:free (or override via NOUS_MODEL).
if (-not $env:NOUS_MODEL) { $env:NOUS_MODEL = 'stepfun/step-5-preview:free' }
$hermesDir = Join-Path $env:LOCALAPPDATA 'hermes'
if (Test-Path $hermesDir) {
    # PS 5.1 has no utf8NoBOM; write BOM-less UTF-8 via .NET so the proxy
    # never serves a model id with a leading U+FEFF (old bug: -Encoding UTF8).
    [System.IO.File]::WriteAllText((Join-Path $hermesDir 'active_proxy_model.txt'), $env:NOUS_MODEL, (New-Object System.Text.UTF8Encoding $false))
}
function Test-Up { try { $c = [Net.Sockets.TcpClient]::new('127.0.0.1', $port); $c.Close(); $true } catch { $false } }
if (Test-Up) {
    # Already running: sync it back to the Nous upstream in case a Gemini
    # session (claude.ps1 option 0) switched it; ignore 404 on older proxies.
    try {
        Invoke-RestMethod -Uri "http://127.0.0.1:$port/set_upstream" -Method Post `
            -ContentType 'application/json' `
            -Body ('{"upstream":"nous","model":"' + $env:NOUS_MODEL + '"}') -TimeoutSec 5 | Out-Null
    } catch {}
    exit 0
}
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = 'C:\Python314\python.exe' }
$script = Join-Path $PSScriptRoot 'nous_anthropic_proxy.py'
$log = Join-Path $PSScriptRoot 'proxy.log'
Start-Process -FilePath $py -ArgumentList "`"$script`"" -WindowStyle Hidden -RedirectStandardError $log | Out-Null
for ($i = 0; $i -lt 20; $i++) { Start-Sleep -Milliseconds 250; if (Test-Up) { exit 0 } }
Write-Host "[claude shim] Nous proxy failed to start; see $log. Falling back to stock Claude."
exit 1
