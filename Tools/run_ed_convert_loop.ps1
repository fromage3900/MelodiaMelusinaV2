param(
    [Parameter(Mandatory=$true)][string]$Targets,   # comma-separated or file path to a list file
    [string]$MonolithUrl = "http://127.0.0.1:9316/mcp"
)

# Convert ED masters one-at-a-time through Monolith run_python.
# After each conversion, verifies the editor survived (health + /health endpoint).
# A deterministic crasher is recorded and the loop continues with the rest.
# A dead editor is relaunched (standard project launch) and awaited before continuing.

$ErrorActionPreference = "Stop"
$project = "C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject"
$ueExe = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$runner = "C:/EnvironmentPortfolio/BS_GodFile/Content/Python/convert_one_master.py"
$logFile = "C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\ed_convert_loop.log"

function Write-Log($msg) {
    $line = "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $msg
    Write-Output $line
    Add-Content -Path $logFile -Value $line
}

function Test-EditorAlive {
    try {
        $proc = Get-Process UnrealEditor -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -gt (Get-Date).AddMinutes(-20) }
        if (-not $proc) { return $false }
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:9316/health" -Method Get -TimeoutSec 10
        return ($resp.status -eq "ok")
    } catch { return $false }
}

function Start-EditorAndWait {
    Write-Log "  relaunching editor..."
    Start-Process $ueExe -ArgumentList $project -WorkingDirectory "C:\EnvironmentPortfolio\BS_GodFile"
    $deadline = (Get-Date).AddMinutes(12)
    do {
        Start-Sleep -Seconds 20
        if (Test-EditorAlive) { Write-Log "  editor healthy (port 9316 up)"; return $true }
    } while ((Get-Date) -lt $deadline)
    Write-Log "  ERROR: editor did not come back in 12 min"
    return $false
}

if (Test-Path $Targets) {
    $list = Get-Content $Targets | Where-Object { $_.Trim() -and -not $_.Trim().StartsWith("#") }
} else {
    $list = $Targets -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ }
}

Write-Log "=== ED convert loop: $($list.Count) targets ==="
$results = @()
$idx = 0
foreach ($target in $list) {
    $idx++
    if (-not (Test-EditorAlive)) {
        Write-Log "[$idx/$($list.Count)] editor down -> relaunch"
        if (-not (Start-EditorAndWait)) { $results += "$target|EDITOR_UNAVAILABLE"; continue }
    }
    Write-Log "[$idx/$($list.Count)] converting $target"
    $body = @{jsonrpc="2.0"; id=$idx; method="tools/call"; params=@{name="editor_query"; arguments=@{action="run_python"; mode="execute_file"; command="$runner $target"}}} | ConvertTo-Json -Depth 6
    $status = "UNKNOWN"
    try {
        $r = Invoke-RestMethod -Uri $MonolithUrl -Method Post -Body $body -ContentType "application/json" -TimeoutSec 300
        $t = ($r.result.content | Where-Object {$_.type -eq "text"}).text
        if ($t -match '"status":\s*"(converted|finished|skipped[^"]*)"') { $status = $Matches[1] }
        elseif ($t -match '\[(converted|finished|skipped[^\]]*)\]') { $status = $Matches[1] }
        elseif ($r.result.isError) { $status = "ISERROR" }
        else { $status = "OK_UNKNOWN" }
    } catch {
        $status = "CONNECTION_DROPPED"
    }
    # give the editor a moment; check it survived
    Start-Sleep -Seconds 8
    $alive = Test-EditorAlive
    if (-not $alive) { $status = "EDITOR_CRASHED" }
    $results += "$target|$status"
    Write-Log "  -> $status | editor_alive=$alive"
}

Write-Log "=== ED convert loop done ==="
$results | ForEach-Object { Write-Log "  $_" }
$results | Out-File -FilePath "C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\ed_convert_loop_results.txt" -Encoding utf8
