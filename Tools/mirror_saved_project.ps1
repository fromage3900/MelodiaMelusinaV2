[CmdletBinding()]
param(
    [string]$Source = 'C:/EnvironmentPortfolio/BS_GodFile',
    [string]$Destination = '',
    [string]$LogDirectory = '',
    # Keep the dry-run and apply paths paired. Pass the same SnapshotId to both
    # invocations when an explicit snapshot name is preferred.
    [string]$SnapshotId = (Get-Date -Format 'yyyyMMdd'),
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($SnapshotId) -or $SnapshotId -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') {
    throw 'SnapshotId must contain only letters, numbers, dots, underscores, or hyphens.'
}
if ([string]::IsNullOrWhiteSpace($Destination)) {
    $Destination = "G:/BS_GodFile_Mirror/$SnapshotId"
}
if ([string]::IsNullOrWhiteSpace($LogDirectory)) {
    $LogDirectory = Join-Path ([IO.Path]::GetTempPath()) "melodia-mirror-$SnapshotId"
}
$sourceRoot = (Resolve-Path -LiteralPath $Source).Path.TrimEnd('\', '/')
$targetRoot = [IO.Path]::GetFullPath($Destination).TrimEnd('\', '/')
$approvedRoot = [IO.Path]::GetFullPath('G:/BS_GodFile_Mirror').TrimEnd('\', '/')
if (-not $targetRoot.StartsWith($approvedRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Destination must be a child of G:/BS_GodFile_Mirror, never the drive or mirror root.'
}
if (-not (Test-Path -LiteralPath "$sourceRoot/BS_GodFile.uproject")) { throw 'Source project missing' }
# Refuse junctions anywhere on the destination path before a possible /MIR deletion.
$ancestorPath = $targetRoot
while ($ancestorPath) {
    if (Test-Path -LiteralPath $ancestorPath) {
        if ((Get-Item -Force -LiteralPath $ancestorPath).Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Destination traverses a reparse point: $ancestorPath"
        }
    }
    $parentPath = [IO.Directory]::GetParent($ancestorPath)
    $ancestorPath = if ($parentPath) { $parentPath.FullName } else { $null }
}
$folders = @('Content', 'Config', 'Source', 'Plugins', 'Saved/Audit', 'Chapters', 'specs', 'Tools', 'melodia-design-system')
foreach ($relative in $folders) {
    if (-not (Test-Path -LiteralPath "$sourceRoot/$relative" -PathType Container)) {
        throw "Required source folder missing: $relative"
    }
    if ((Get-Item -LiteralPath "$sourceRoot/$relative").Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw "Source root is a junction; resolve explicitly: $relative"
    }
}
New-Item -ItemType Directory -Force -Path $LogDirectory | Out-Null
$receiptPath = Join-Path $LogDirectory 'dry-run.json'
if ($Apply) {
    if (Test-Path -LiteralPath $targetRoot) {
        $links = @(Get-ChildItem -LiteralPath $targetRoot -Recurse -Force -Attributes ReparsePoint)
        if ($links.Count) { throw 'Destination contains junctions or symlinks; resolve before /MIR.' }
    }
    if (-not (Test-Path -LiteralPath $receiptPath)) { throw 'Run and review the dry run first.' }
    $receipt = Get-Content -Raw -LiteralPath $receiptPath | ConvertFrom-Json
    if ($receipt.source -ne $sourceRoot -or $receipt.destination -ne $targetRoot) {
        throw 'Dry run paths do not match this apply.'
    }
    if (-not $receipt.snapshot_id -or $receipt.snapshot_id -ne $SnapshotId) {
        throw 'Dry run snapshot id does not match this apply.'
    }
    if (Get-Process UnrealEditor -ErrorAction SilentlyContinue) { throw 'Save and close the editor before mirroring.' }
}
$rows = @()
$prefix = if ($Apply) { 'apply' } else { 'dry' }
foreach ($relative in $folders) {
    $from = [IO.Path]::GetFullPath("$sourceRoot/$relative")
    $to = [IO.Path]::GetFullPath("$targetRoot/$relative")
    if (-not $to.StartsWith($targetRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe subtree' }
    $log = Join-Path $LogDirectory "$prefix-$($relative.Replace('/', '-')).log"
    $arguments = @($from, $to, '/MIR', '/XJ', '/R:0', '/W:0', '/BYTES', '/FP', '/NP', '/NDL',
                   '/XD', 'Intermediate', 'DerivedDataCache', 'Binaries', '__pycache__', 'autosave', 'autosaves',
                   '/XF', '*.blend1', '*.blend2', '*.blend@', '*_autosave.blend', '*.pyc', "/LOG:$log")
    if (-not $Apply) { $arguments += '/L' }
    & robocopy @arguments | Out-Null
    $code = $LASTEXITCODE
    if ($code -ge 8) { throw "Robocopy failed ($code): $log" }
    $summary = @(Get-Content -LiteralPath $log -Tail 12)
    $rows += [ordered]@{ subtree = $relative; exit_code = $code; log = $log; summary = $summary }
    Write-Output "$relative ($code)"
    $summary | Write-Output
}
# Root project descriptors are copied without /MIR so unrelated destination roots cannot be purged.
$rootLog = Join-Path $LogDirectory "$prefix-project.log"
$rootArgs = @($sourceRoot, $targetRoot, '*.uproject', '/R:0', '/W:0', '/BYTES', '/NP', "/LOG:$rootLog")
if (-not $Apply) { $rootArgs += '/L' }
& robocopy @rootArgs | Out-Null
if ($LASTEXITCODE -ge 8) { throw "Root descriptor copy failed: $rootLog" }
$output = [ordered]@{ source = $sourceRoot; destination = $targetRoot; snapshot_id = $SnapshotId;
    apply = [bool]$Apply; time = (Get-Date).ToUniversalTime().ToString('o'); rows = $rows;
    descriptor_log = $rootLog }
$output | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $LogDirectory "$prefix-run.json")
Write-Output "Summary: $LogDirectory/$prefix-run.json"
