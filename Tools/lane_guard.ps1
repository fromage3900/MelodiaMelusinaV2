# lane_guard.ps1 - read-only daily loss/regression guard for the shared Melodia checkout.
#
# What it does (no mutations except writing its own manifest + JSON report):
#   1. Content manifest (path, size, mtime) and diff against the previous manifest:
#      reports MISSING files (loss), ADDED files, and RESIZED files.
#   2. Git: branch/HEAD, dirty/staged counts, foreign staged entries, unpushed commits,
#      merge-in-progress, unmerged rows, stash count, recovery-ref count.
#   3. Perforce: server reachable, opened-file count, pending changelists, checkpoint age.
#   4. Disk free space.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File Tools\lane_guard.ps1
#   powershell ... -File Tools\lane_guard.ps1 -SkipManifest     # fast git/p4 only
#
# Exit codes: 0 = pass, 1 = warnings (loss or unpushed/pending work), 2 = critical.

param(
    [string]$ManifestDir = 'D:\MelodiaArchive\manifests',
    [switch]$SkipManifest
)

$ErrorActionPreference = 'Continue'
$script:exitCode = 0
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Fail([string]$msg) { Write-Host "FAIL  $msg" -ForegroundColor Red; $script:exitCode = 2 }
function Warn([string]$msg) { Write-Host "WARN  $msg" -ForegroundColor Yellow; if ($script:exitCode -lt 1) { $script:exitCode = 1 } }
function Ok([string]$msg)   { Write-Host "ok    $msg" -ForegroundColor Green }

$report = [ordered]@{
    schema    = 'melodia.lane_guard.v1'
    when      = (Get-Date).ToString('o')
    repo      = $root
    manifest  = $null
    git       = [ordered]@{}
    perforce  = [ordered]@{}
    disk_free_gb = [math]::Round((Get-PSDrive C).Free / 1GB, 2)
}

# ---------------------------------------------------------------- Content manifest
if (-not $SkipManifest) {
    New-Item -ItemType Directory -Force -Path $ManifestDir | Out-Null
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $newCsv = Join-Path $ManifestDir ("content_manifest_$stamp.csv")
    $files = @()
    foreach ($sub in @('Content', 'Saved')) {
        $files += Get-ChildItem $sub -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch '\\Saved\\(Logs|Crashes|Shaders|ShaderDebugInfo|UnrealBuildTool|DerivedDataCache)\\' }
    }
    $files |
        Select-Object @{ n = 'path'; e = { $_.FullName.Substring($root.Length + 1) } },
                      Length,
                      @{ n = 'mtime'; e = { $_.LastWriteTime.ToString('o') } } |
        Export-Csv -Path $newCsv -NoTypeInformation -Encoding UTF8

    $prev = Get-ChildItem $ManifestDir -Filter 'content_manifest_*.csv' |
        Where-Object { $_.FullName -ne $newCsv } |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1

    $current = @{}
    foreach ($f in $files) { $current[$f.FullName.Substring($root.Length + 1)] = $f.Length }

    $missing = @(); $added = @(); $resized = @()
    if ($prev) {
        $prevMap = @{}
        Import-Csv $prev.FullName | ForEach-Object { $prevMap[$_.path] = [long]$_.Length }
        foreach ($k in $prevMap.Keys) {
            if (-not $current.ContainsKey($k)) { $missing += $k }
            elseif ($current[$k] -ne $prevMap[$k]) { $resized += $k }
        }
        foreach ($k in $current.Keys) { if (-not $prevMap.ContainsKey($k)) { $added += $k } }
        Ok ("manifest: {0} files, {1:N2} GB; diff vs {2}: missing={3} added={4} resized={5}" -f `
            $files.Count, ((($files | Measure-Object Length -Sum).Sum) / 1GB), $prev.Name, $missing.Count, $added.Count, $resized.Count)
        if ($missing.Count -gt 0) { Warn ("CONTENT MISSING: " + (($missing | Select-Object -First 8) -join ', ')) }
        if ($resized.Count -gt 0) { Warn ("content resized (may be intentional): " + (($resized | Select-Object -First 8) -join ', ')) }
    }
    else {
        Ok ("manifest baseline created: {0} files, {1:N2} GB (no previous manifest to diff)" -f $files.Count, ((($files | Measure-Object Length -Sum).Sum) / 1GB))
    }
    $prevCsvPath = $null
    if ($prev) { $prevCsvPath = $prev.FullName }
    $report.manifest = [ordered]@{
        new_csv = $newCsv; previous_csv = $prevCsvPath
        files = $files.Count; missing = $missing; added_count = $added.Count; resized = $resized
    }
}
else {
    Ok 'manifest skipped (-SkipManifest)'
}

# ---------------------------------------------------------------- git
$branch = (git rev-parse --abbrev-ref HEAD 2>$null)
$head = (git rev-parse --short HEAD 2>$null)
$dirty = (git status --porcelain 2>$null | Measure-Object).Count
$staged = (git diff --cached --name-only 2>$null | Measure-Object).Count
$unmerged = (git status --porcelain 2>$null | Select-String '^U|^DD|^AA' | Measure-Object).Count
$merge = Test-Path '.git\MERGE_HEAD'
$stash = (git stash list 2>$null | Measure-Object).Count
$recoveryRefs = (git for-each-ref refs/recovery 2>$null | Measure-Object).Count
$originExists = $false
$unpushed = 0
if ($branch -and $branch -ne 'HEAD') {
    git rev-parse --verify "origin/$branch" *> $null
    $originExists = ($LASTEXITCODE -eq 0)
    if ($originExists) { $unpushed = (git log --oneline "origin/$branch..HEAD" 2>$null | Measure-Object).Count }
}

$report.git = [ordered]@{
    branch = $branch; head = $head; dirty = $dirty; staged = $staged
    unpushed = $unpushed; origin_branch = $originExists; merge_in_progress = $merge
    unmerged_rows = $unmerged; stash_commits = $stash; recovery_refs = $recoveryRefs
}
Ok ("git: {0}@{1} dirty={2} staged={3} unpushed={4} stash={5} recovery_refs={6}" -f $branch, $head, $dirty, $staged, $unpushed, $stash, $recoveryRefs)
if ($merge) { Fail 'MERGE IN PROGRESS - do not commit until the corridor finishes' }
if ($unmerged -gt 0) { Fail ("unmerged rows: {0}" -f $unmerged) }
if ($unpushed -gt 0) { Warn ("{0} unpushed commit(s) - push to origin (offsite copy)" -f $unpushed) }
if ($staged -gt 0) { Warn ("{0} staged entr(y/ies) - commit with an explicit pathspec only" -f $staged) }
if ($stash -gt 0) { Warn ("{0} git stash entr(y/ies) - stash is local-only; pin under refs/recovery or drop" -f $stash) }

# ---------------------------------------------------------------- fabric canon (editor-free byte scan)
$canonMIs = @(
    'Content\EnvSandbox\Materials\Instances\FarawayMother\P2\MI_Mother_Corset.uasset',
    'Content\EnvSandbox\Materials\Instances\FarawayMother\P2\MI_Mother_Cradle.uasset',
    'Content\EnvSandbox\Materials\Instances\FarawayMother\P2\MI_Mother_Gown.uasset',
    'Content\EnvSandbox\Materials\Instances\FarawayMother\P2\MI_Mother_Mantle.uasset',
    'Content\EnvSandbox\Materials\Instances\FarawayMother\P2\MI_Mother_Ornament.uasset',
    'Content\EnvSandbox\Materials\Instances\FarawayMother\P2\MI_Mother_Veil.uasset',
    'Content\Melodia\Characters\Melusina\Materials\MI_Melusina_Shorewake_Cymatic_Bodice.uasset',
    'Content\Melodia\Characters\Melusina\Materials\MI_Melusina_Shorewake_Cymatic_Collar.uasset',
    'Content\Melodia\Characters\Melusina\Materials\MI_Melusina_Shorewake_Cymatic_Skirt.uasset',
    'Content\EnvSandbox\Materials\Instances\Melusina\MI_Melusina_SorrowSeam.uasset'
)
$canonBad = @()
foreach ($rel in $canonMIs) {
    $p = Join-Path $root $rel
    if (-not (Test-Path $p)) { $canonBad += "missing:$rel"; continue }
    try {
        $fs = [System.IO.File]::Open($p, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        $len = $fs.Length; $bytes = New-Object byte[] $len
        $fs.Read($bytes, 0, [int]$len) | Out-Null; $fs.Close()
        $latin = [System.Text.Encoding]::GetEncoding(28591).GetString($bytes)
        $utf16 = [System.Text.Encoding]::Unicode.GetString($bytes)
        $hasNikki = ($latin.Contains('M_Master_Nikki') -or $utf16.Contains('M_Master_Nikki'))
        $hasWrong = ($latin.Contains('M_Universal_Enhanced_Fabric') -or $utf16.Contains('M_Universal_Enhanced_Fabric'))
        if (-not $hasNikki -or $hasWrong) { $canonBad += $rel }
    }
    catch { $canonBad += "unreadable:$rel" }
}
$wrongMasterPath = Join-Path $root 'Content\EnvSandbox\Materials\Masters\M_Universal_Enhanced_Fabric.uasset'
if (Test-Path $wrongMasterPath) { $canonBad += 'wrong master M_Universal_Enhanced_Fabric resurrected on disk' }
$report['canon'] = [ordered]@{ fabric_mis = $canonMIs.Count; violations = $canonBad }
if ($canonBad.Count -gt 0) {
    Warn ("CANON VIOLATION: " + (($canonBad | Select-Object -First 6) -join ', '))
}
else {
    Ok 'canon: 10 fabric MIs parented to M_Master_Nikki; wrong master absent'
}

# ---------------------------------------------------------------- perforce
$p4Up = $false
try { $p4Up = ((Get-NetTCPConnection -LocalPort 1666 -State Listen -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0) } catch { $p4Up = $false }
$opened = 0; $pending = @(); $ckptAgeHours = $null
if ($p4Up) {
    $opened = (p4 opened -a 2>$null | Measure-Object).Count
    $pending = @(p4 changes -s pending -u $env:USERNAME -m 20 2>$null)
    $ckpt = Get-ChildItem 'D:\perforce\root' -Filter 'checkpoint.*.gz' -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($ckpt) { $ckptAgeHours = [math]::Round(((Get-Date) - $ckpt.LastWriteTime).TotalHours, 1) }
    Ok ("p4: up, opened={0}, pending CLs={1}, checkpoint age={2}h" -f $opened, $pending.Count, $ckptAgeHours)
    if ($opened -gt 200) { Warn ("{0} files pending in Perforce - shelve or submit WIP (pending CL is not protection)" -f $opened) }
    if ($ckptAgeHours -ne $null -and $ckptAgeHours -gt 24) { Warn ("latest checkpoint is {0}h old - run p4 admin checkpoint -Z" -f $ckptAgeHours) }
}
else {
    Fail 'p4d is DOWN on port 1666 - start it (Startup\MelodiaP4d.cmd) before trusting Content state'
}
$report.perforce = [ordered]@{ up = $p4Up; opened = $opened; pending = $pending; checkpoint_age_hours = $ckptAgeHours }

# ---------------------------------------------------------------- disk + report
Ok ("disk: C: free {0} GB" -f $report.disk_free_gb)
if ($report.disk_free_gb -lt 5) { Warn 'C: free < 5 GB - caches will silently abort saves (Zen guard)' }

$report.exit_code = $script:exitCode
$outDir = Join-Path $root 'Saved\Audit\LaneGuard'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$outJson = Join-Path $outDir ("lane_guard_{0}.json" -f (Get-Date -Format 'yyyyMMdd_HHmmss'))
$report | ConvertTo-Json -Depth 5 | Set-Content $outJson -Encoding UTF8
Write-Host "report: $outJson"
Write-Host ("VERDICT: {0}" -f @('PASS', 'WARN', 'FAIL')[$script:exitCode])
exit $script:exitCode
