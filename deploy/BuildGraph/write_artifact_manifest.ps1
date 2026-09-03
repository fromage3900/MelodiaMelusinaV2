param(
    [Parameter(Mandatory = $true)]
    [string]$ArchiveDir,
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = "Stop"
$resolvedArchive = (Resolve-Path -LiteralPath $ArchiveDir).Path
$files = Get-ChildItem -LiteralPath $resolvedArchive -File -Recurse | ForEach-Object {
    # Windows PowerShell 5.1 does not expose .NET Core's Path.GetRelativePath.
    # The archive root is resolved above, so a normalized prefix trim is both
    # deterministic and compatible with the UE build host.
    $relative = $_.FullName.Substring($resolvedArchive.Length).TrimStart('\', '/')
    [ordered]@{
        path = ($relative -replace '\\', '/')
        bytes = $_.Length
        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}

$gitCommit = (& git -C (Split-Path $PSScriptRoot -Parent) rev-parse HEAD).Trim()
$manifest = [ordered]@{
    schema = "melodia.artifact_manifest.v1"
    generated_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    repository_commit = $gitCommit
    archive_dir = $resolvedArchive
    files = @($files)
}

$parent = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $parent | Out-Null
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
Write-Output "artifact manifest: $OutputPath"
