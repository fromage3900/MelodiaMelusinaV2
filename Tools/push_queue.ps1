# push_queue.ps1 — SAFE retry of ONE non-main branch push.
#
# This used to push main plus a hard-coded list of old branches in the background.
# That behavior is intentionally removed because it can make two workstations race.
#
# Usage:
#   powershell -File Tools\push_queue.ps1
#   powershell -File Tools\push_queue.ps1 -Branch feature/my-lane
#
# Rules:
# - active checkout only
# - one branch only
# - main is forbidden
# - dirty worktree is forbidden
# - no force push
# - no automatic merge/rebase/reset/clean/stash

param(
    [string]$Branch = "",
    [int]$Rounds = 12,
    [int]$Seconds = 60
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $repo 'Saved\Audit'
$log = Join-Path $logDir 'push_queue_log.txt'
$lock = Join-Path $logDir 'push_queue.lock'

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$current = (& git -C $repo branch --show-current 2>$null | Out-String).Trim()
if ([string]::IsNullOrWhiteSpace($Branch)) {
    $Branch = $current
}

if ($Branch -ne $current) {
    throw "Refusing to push '$Branch' while active checkout is '$current'. Switch explicitly first."
}
if ($Branch -eq 'main') {
    throw "Background/retry pushing main is forbidden. Use deploy\sync_workstation.ps1 and an explicit reviewed push."
}

$dirty = @(& git -C $repo status --porcelain)
if ($dirty.Count -gt 0) {
    throw "Working tree is dirty. Commit the intended exact batch before running a push retry."
}

if (Test-Path $lock) {
    Write-Host "push queue lock exists; another instance may be running"
    exit 1
}

New-Item -ItemType File -Path $lock | Out-Null
try {
    foreach ($round in 1..$Rounds) {
        "[$(Get-Date -Format o)] round $round/$Rounds branch=$Branch" | Tee-Object $log -Append

        & git -C $repo fetch --prune origin 2>&1 | Out-Null

        $remoteRef = "refs/remotes/origin/$Branch"
        & git -C $repo show-ref --verify --quiet $remoteRef
        $hasRemote = $LASTEXITCODE -eq 0

        if ($hasRemote) {
            $delta = (& git -C $repo rev-list --left-right --count "HEAD...origin/$Branch" 2>$null | Out-String).Trim() -split '\s+'
            if ($delta.Count -ge 2) {
                $ahead = [int]$delta[0]
                $behind = [int]$delta[1]
                if ($behind -gt 0) {
                    throw "Remote branch moved ahead/diverged. Refusing background push; reconcile explicitly."
                }
                if ($ahead -eq 0) {
                    "[$(Get-Date -Format o)] branch already published" | Tee-Object $log -Append
                    exit 0
                }
            }
        }

        $output = (& git -C $repo push origin "HEAD:refs/heads/$Branch" 2>&1 | Out-String)
        if ($LASTEXITCODE -eq 0) {
            "[$(Get-Date -Format o)] PUSHED $Branch" | Tee-Object $log -Append
            exit 0
        }

        "[$(Get-Date -Format o)] FAILED $Branch :: $($output.Trim() -replace '\s+', ' ')" | Tee-Object $log -Append
        if ($round -lt $Rounds) {
            Start-Sleep -Seconds $Seconds
        }
    }

    throw "Push retry rounds exhausted for $Branch"
}
finally {
    Remove-Item $lock -ErrorAction SilentlyContinue
}
