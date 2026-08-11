# Install Melodia Monolith skills into the user jcode skills directory.
# Idempotent. Run from repo root: .\deploy\install_jcode_melodia_skills.ps1
param(
    [string]$RepoRoot = "",
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

if (-not $RepoRoot) {
    $RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
}

$skillsSrc = Join-Path $RepoRoot "Plugins\Monolith\Skills"
$skillsDst = Join-Path $env:USERPROFILE ".jcode\skills"

# High-value set for Melodia (plan v1)
$SkillNames = @(
    "unreal-materials",
    "material-reference",
    "unreal-niagara",
    "unreal-cpp",
    "unreal-debugging",
    "unreal-build"
)

if (-not (Test-Path $skillsSrc)) {
    Write-Error "Monolith Skills not found at $skillsSrc"
}

New-Item -ItemType Directory -Force -Path $skillsDst | Out-Null

foreach ($name in $SkillNames) {
    $srcFile = Join-Path $skillsSrc "$name\$name.md"
    if (-not (Test-Path $srcFile)) {
        Write-Warning "Skip missing skill source: $srcFile"
        continue
    }

    $dstDir = Join-Path $skillsDst $name
    $dstFile = Join-Path $dstDir "SKILL.md"

    if ($WhatIf) {
        Write-Host "Would install $name -> $dstFile"
        continue
    }

    New-Item -ItemType Directory -Force -Path $dstDir | Out-Null

    $body = Get-Content -Raw -Path $srcFile
    # Ensure jcode-style frontmatter has a name; keep existing YAML if present
    if ($body -notmatch '(?m)^---\s*$') {
        $body = @"
---
name: $name
description: Melodia bridge — Monolith skill $name
type: skill
---

$body
"@
    }

    # Always write SKILL.md (jcode convention); overwrite for idempotent refresh from repo
    Set-Content -Path $dstFile -Value $body -Encoding utf8
    Write-Host "Installed skill: $name"
}

Write-Host "Done. Skills root: $skillsDst"
Write-Host "In jcode: /skills to list; skills inject by semantic match or slash command."
