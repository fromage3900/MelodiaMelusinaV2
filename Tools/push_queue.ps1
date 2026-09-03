# push_queue.ps1 — retry queued branch pushes until github.com answers.
# Idempotent: only pushes refs that are ahead of their upstream (or unbacked).
# Lock-file guarded so two instances never run at once.
# Log: Saved/Audit/push_queue_log.txt   Lock: Saved/Audit/push_queue.lock
#
# Usage:  powershell -File Tools\push_queue.ps1            (foreground)
#         Start-Process powershell -ArgumentList '-File Tools\push_queue.ps1' -WindowStyle Hidden
# Stop:   Remove-Item Saved\Audit\push_queue.lock, or kill the powershell process.

$ErrorActionPreference = 'Continue'
$repo    = 'C:\EnvironmentPortfolio\BS_GodFile'
$log     = Join-Path $repo 'Saved\Audit\push_queue_log.txt'
$lock    = Join-Path $repo 'Saved\Audit\push_queue.lock'
$refs    = @(
    'main',
    'feature/p0-phase1-allowlist-quill-trigger',
    'backup/pre-consolidation-2026-08-30',
    'cursor/model-lanes-agents-slim-f425',
    'feature/credits-20260813',
    'feature/echo-topo-chapter2',
    'feature/sea-above-choralsheep-20260826'
)
$rounds  = 24          # x 5 min = 2 h cap
$seconds = 300

Set-Location $repo

if (Test-Path $lock) {
    "[$(Get-Date -Format o)] lock exists - another instance running, exiting" | Tee-Object $log -Append
    exit 0
}
New-Item -ItemType File -Path $lock | Out-Null
try {
    foreach ($round in 1..$rounds) {
        "[$(Get-Date -Format o)] round $round/$rounds" | Tee-Object $log -Append
        $pending = @()
        foreach ($ref in $refs) {
            # ahead-of-upstream check; unbacked branches are always attempted
            $ahead = git rev-list --count "$ref@{upstream}..$ref" 2>$null
            if ($null -eq $ahead -or [int]$ahead -gt 0) {
                $r = git push origin "${ref}:refs/heads/${ref}" 2>&1 | Out-String
                if ($LASTEXITCODE -eq 0) {
                    "[$(Get-Date -Format o)] PUSHED  $ref" | Tee-Object $log -Append
                } else {
                    "[$(Get-Date -Format o)] FAILED  $ref :: $($r.Trim() -replace '\s+', ' ')" | Tee-Object $log -Append
                    $pending += $ref
                }
            } else {
                "[$(Get-Date -Format o)] current $ref" | Tee-Object $log -Append
            }
        }
        if ($pending.Count -eq 0) {
            "[$(Get-Date -Format o)] ALL REFS SYNCED - done" | Tee-Object $log -Append
            exit 0
        }
        if ($round -lt $rounds) { Start-Sleep -Seconds $seconds }
    }
    "[$(Get-Date -Format o)] rounds exhausted - still pending: $($pending -join ', ')" | Tee-Object $log -Append
    exit 1
}
finally {
    Remove-Item $lock -ErrorAction SilentlyContinue
}
