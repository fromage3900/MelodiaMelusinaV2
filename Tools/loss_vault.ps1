# loss_vault.ps1 - continuous recovery snapshots of modified Content.
#
# WHY: this project's shared checkout gets overwritten by syncs/checkouts/resets.
# A save is not persistence. This vault copies every Content file modified in the
# recent window to D:\MelodiaVault, so the worst case is the snapshot interval,
# never months of work.
#
# Runs from the user's Startup folder (no admin):
#   powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File Tools\loss_vault.ps1
# One-shot: add -Once
#
# Snapshot layout:
#   D:\MelodiaVault\YYYYMMDD\YYYYMMDD_HHmmss\Content\<relative path...>
#   ...\manifest.json, git_status.txt, git_head.txt, git_stash.txt, p4_opened.txt
#
# Retention: 7 days (configurable).

param(
    [int]$IntervalSeconds = 300,
    [int]$LookbackMinutes = 20,
    [int]$RetentionDays = 7,
    [switch]$Once
)

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
$vault = 'D:\MelodiaVault'
$log = Join-Path $vault 'vault.log'
$pidFile = Join-Path $vault 'vault.pid'
New-Item -ItemType Directory -Force -Path $vault | Out-Null

function Write-Log([string]$msg) {
    try { "$(Get-Date -Format o) $msg" | Out-File $log -Append -Encoding UTF8 } catch { }
}

function Test-OtherInstance {
    if (Test-Path $pidFile) {
        $other = Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($other -and (Get-Process -Id ([int]$other) -ErrorAction SilentlyContinue)) { return $true }
    }
    return $false
}

function Invoke-Snapshot {
    $now = Get-Date
    $snap = Join-Path (Join-Path $vault $now.ToString('yyyyMMdd')) $now.ToString('yyyyMMdd_HHmmss')
    New-Item -ItemType Directory -Force -Path $snap | Out-Null

    $cut = $now.AddMinutes(-$LookbackMinutes)
    $files = @()
    foreach ($sub in @('Content', 'Saved')) {
        $files += Get-ChildItem (Join-Path $root $sub) -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -ge $cut -and $_.FullName -notmatch '\\Saved\\(Logs|Crashes|Shaders|ShaderDebugInfo|UnrealBuildTool|DerivedDataCache)\\' }
    }

    $n = 0; [long]$bytes = 0
    foreach ($f in $files) {
        $rel = $f.FullName.Substring($root.Length + 1)
        $dst = Join-Path $snap $rel
        New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
        try { Copy-Item $f.FullName $dst -Force; $n++; $bytes += $f.Length } catch { Write-Log "copy_fail $rel" }
    }

    try { git -C $root status --porcelain 2>$null | Set-Content (Join-Path $snap 'git_status.txt') -Encoding UTF8 } catch { }
    try { git -C $root rev-parse HEAD 2>$null | Set-Content (Join-Path $snap 'git_head.txt') -Encoding UTF8 } catch { }
    try { git -C $root stash list 2>$null | Set-Content (Join-Path $snap 'git_stash.txt') -Encoding UTF8 } catch { }
    try { p4 opened -a 2>$null | Set-Content (Join-Path $snap 'p4_opened.txt') -Encoding UTF8 } catch { }

    [pscustomobject]@{
        when = $now.ToString('o'); root = $root; files = $n; bytes = $bytes
        lookback_minutes = $LookbackMinutes; head = (Get-Content (Join-Path $snap 'git_head.txt') -ErrorAction SilentlyContinue | Select-Object -First 1)
    } | ConvertTo-Json | Set-Content (Join-Path $snap 'manifest.json') -Encoding UTF8

    Write-Log "snapshot $snap files=$n bytes=$bytes"

    Get-ChildItem $vault -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^\d{8}$' } |
        Where-Object { [datetime]::ParseExact($_.Name, 'yyyyMMdd', $null) -lt $now.AddDays(-$RetentionDays) } |
        ForEach-Object { Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue; Write-Log "pruned $($_.Name)" }
}

if ($Once) { Invoke-Snapshot; exit 0 }

if (Test-OtherInstance) { Write-Log "already running - exit"; exit 0 }
$PID | Set-Content $pidFile -Encoding ASCII
Write-Log "vault started pid=$PID interval=${IntervalSeconds}s"
while ($true) {
    try { Invoke-Snapshot } catch { Write-Log "snapshot_exc $($_.Exception.Message)" }
    Start-Sleep -Seconds $IntervalSeconds
}
