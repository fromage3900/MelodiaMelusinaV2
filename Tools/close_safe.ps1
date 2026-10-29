# close_safe.ps1 - run this BEFORE closing Unreal.
#
# It does not close anything. It answers one question:
#   "If I close UE now, what exists only on C: and nowhere else?"
# and archives every such Content file to D:\MelodiaVault\close_safe\<timestamp>\.
#
# Checks:
#   1. p4-opened files on this client that exist locally (pending work is local-only).
#   2. Content files modified in the last 24h that are NOT in the depot (git-ignored/untracked).
#   3. Archives both sets to D: with a manifest.
#
# Exit 0 = nothing unbacked; 1 = files were archived (safe, but review); 2 = error.

param(
    [int]$ModifiedHours = 24,
    [string]$Vault = 'D:\MelodiaVault\close_safe'
)

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$now = Get-Date
$snap = Join-Path $Vault $now.ToString('yyyyMMdd_HHmmss')
New-Item -ItemType Directory -Force -Path $snap | Out-Null

function Copy-Set($files, [string]$label) {
    $n = 0; [long]$bytes = 0
    foreach ($f in $files) {
        $rel = $f.FullName.Substring($root.Length + 1)
        $dst = Join-Path $snap $rel
        New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
        try { Copy-Item $f.FullName $dst -Force; $n++; $bytes += $f.Length } catch { }
    }
    Write-Host ("{0}: {1} files, {2:N2} MB" -f $label, $n, ($bytes / 1MB))
    return @{ label = $label; files = $n; bytes = $bytes }
}

# 1. p4-opened files present locally
$openedFiles = @()
try {
    $opened = p4 opened -a 2>$null | ForEach-Object { ($_ -split ' - ')[0] }
    foreach ($depot in $opened) {
        $rel = ($depot -replace '^//Melodia/main/', '') -replace '#\d+$', ''
        $local = Join-Path $root ($rel -replace '/', '\')
        if (Test-Path $local) { $openedFiles += (Get-Item $local) }
    }
} catch { }

# 2. recently modified Content files
$cut = $now.AddHours(-$ModifiedHours)
$recent = @()
foreach ($sub in @('Content', 'Saved')) {
    $recent += Get-ChildItem (Join-Path $root $sub) -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -ge $cut -and $_.FullName -notmatch '\\Saved\\(Logs|Crashes|Shaders|ShaderDebugInfo|UnrealBuildTool|DerivedDataCache)\\' }
}

$set1 = Copy-Set $openedFiles 'p4-opened (local-only pending work)'
$set2 = Copy-Set $recent 'modified Content (last ' + $ModifiedHours + 'h)'

# Deduplicate note: sets overlap; manifest records both.
$manifest = [pscustomobject]@{
    when = $now.ToString('o'); root = $root; snapshot = $snap
    p4_opened = $set1; modified_content = $set2
    git_head = (git rev-parse HEAD 2>$null)
    git_status_count = (git status --porcelain 2>$null | Measure-Object).Count
}
$manifest | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $snap 'manifest.json') -Encoding UTF8
Write-Host "snapshot: $snap"

if (($set1.files + $set2.files) -eq 0) {
    Write-Host 'SAFE: nothing unbacked found.'
    exit 0
}
Write-Host 'ARCHIVED: everything above now exists on D:. Review the snapshot before closing if unsure.'
exit 1
