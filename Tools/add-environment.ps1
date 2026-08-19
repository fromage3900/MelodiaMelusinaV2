# add-environment.ps1 — Scaffold a new environment page from the template
#
# Creates a new environment page (wix/your-env.html) from environment-template.html
# with all %%TOKENS%% replaced using the values you provide.
#
# Usage:
#   .\tools\add-environment.ps1 -Slug "crystal-cavern" -Name "Crystal Cavern"
#
# Interactive mode (if you omit -Slug):
#   .\tools\add-environment.ps1

param(
    [string]$Slug = "",
    [string]$Name = "",
    [string]$WorldNum = "",
    [string]$HeroTitle = "",
    [string]$HeroLede = "",
    [string]$KickerJapanese = "",
    [string]$KickerEnglish = "",
    [string]$Triangles = "",
    [string]$DrawCalls = "",
    [string]$Materials = "",
    [string]$PcgGraphs = "",
    [switch]$OpenInEditor
)

$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $PSScriptRoot
$templatePath = Join-Path $scriptRoot "my-site-clean\wix\environment-template.html"
$outputDir    = Join-Path $scriptRoot "my-site-clean\wix"

# --- Interactive mode -----------------------------------------------------
if (-not $Slug) {
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════╗"
    Write-Host "  ║     Add New Environment Page (Interactive)   ║"
    Write-Host "  ╚══════════════════════════════════════════════╝"
    Write-Host ""

    $Slug = Read-Host "  Slug (e.g. crystal-cavern)"
    $Name = Read-Host "  Display Name (e.g. Crystal Cavern)"
    $WorldNum = Read-Host "  World number (e.g. 05)"
    $HeroTitle = Read-Host "  Hero H1 title (e.g. Light through crystal)"
    $HeroLede = Read-Host "  Hero lede paragraph (long description)"
    $KickerJapanese = Read-Host "  Japanese ribbon (e.g. 水晶の洞窟)"
    $KickerEnglish = Read-Host "  English subtitle (e.g. Subterranean crystal)"
    $Triangles = Read-Host "  Triangle count (e.g. 55k)"
    $DrawCalls = Read-Host "  Draw calls (e.g. 30)"
    $Materials = Read-Host "  Material count (e.g. 20)"
    $PcgGraphs = Read-Host "  PCG graph count (e.g. 6)"
    $confirmed = Read-Host "`n  Create page '$Slug'? (y/n)"

    if ($confirmed -ne "y") {
        Write-Host "  Cancelled."
        exit 0
    }
}

# --- Validate -------------------------------------------------------------
if (-not (Test-Path $templatePath)) {
    Write-Host "  [FAIL] Template not found at wix/environment-template.html"
    exit 1
}

$outputPath = Join-Path $outputDir "$Slug.html"
if (Test-Path $outputPath) {
    $overwrite = Read-Host "  [WARN] $Slug.html already exists. Overwrite? (y/n)"
    if ($overwrite -ne "y") {
        Write-Host "  Cancelled."
        exit 0
    }
}

# --- Compute derived values -----------------------------------------------
$worldLabel = "World $WorldNum · $Name"
$ribbon = "$KickerJapanese · $KickerEnglish"

# --- Build replacement map ------------------------------------------------
$replacements = @{
    "%%ENV_SLUG%%"     = $Slug
    "%%ENV_NAME%%"     = $Name
    "%%WORLD_LABEL%%"  = $worldLabel
    "%%RIBBON%%"       = $ribbon
    "%%HERO_TITLE%%"   = $HeroTitle
    "%%HERO_LEDE%%"    = $HeroLede
    "%%TRIANGLES%%"    = $Triangles
    "%%DRAW_CALLS%%"   = $DrawCalls
    "%%MATERIAL_COUNT%%" = $Materials
    "%%PCG_COUNT%%"    = $PcgGraphs

    # Sensible defaults for things the user will customize later
    "%%META_DESC%%"      = "$Name — stylized $KickerEnglish environment built in UE5. $HeroTitle"
    "%%OG_DESC%%"        = "$Name environment: $KickerEnglish. $HeroTitle Infinity Nikki–aligned."
    "%%OG_IMAGE%%"       = "WP_${Name}.png"
    "%%HERO_POSTER%%"    = "WP_${Name}_terrain.png"
    "%%HERO_WEBM%%"      = "WP_${Name}.webm"
    "%%STATS_INTRO%%"    = "Stylized environment with Substrate Toon materials, PCG scattering, and $KickerEnglish dressing."

    "%%SECTION2_EYEBROW%%"   = "Hero Stills"
    "%%SECTION2_TITLE%%"     = "Establishing + route proof."
    "%%SECTION2_DESC%%"      = "Hero renders establishing the environment composition and player route."
    "%%BREAKDOWN_IMG_1%%"    = "hero_${Slug}_establishing.png"
    "%%BREAKDOWN_ALT_1%%"    = "${Name} establishing shot"
    "%%BREAKDOWN_LABEL_1%%"  = "Establishing · Hero angle"
    "%%BREAKDOWN_IMG_2%%"    = "hero_${Slug}_route.png"
    "%%BREAKDOWN_ALT_2%%"    = "${Name} route"
    "%%BREAKDOWN_LABEL_2%%"  = "Player route · Walkable path"
    "%%BREAKDOWN_IMG_3%%"    = "hero_${Slug}_materials.png"
    "%%BREAKDOWN_ALT_3%%"    = "${Name} material isolate"
    "%%BREAKDOWN_LABEL_3%%"  = "Material isolate · Surface language"

    "%%SECTION3_EYEBROW%%"   = "Detail Shots"
    "%%SECTION3_TITLE%%"     = "${Name} macro gallery."
    "%%SECTION3_DESC%%"      = "Architectural and prop detail renders — ornaments, props, and signature elements."
    "%%MACRO_IMG_1%%"        = "ornaments/${Slug}_detail_1.png"
    "%%MACRO_ALT_1%%"        = "${Name} detail 1"
    "%%MACRO_IMG_2%%"        = "ornaments/${Slug}_detail_2.png"
    "%%MACRO_ALT_2%%"        = "${Name} detail 2"
    "%%MACRO_IMG_3%%"        = "ornaments/${Slug}_detail_3.png"
    "%%MACRO_ALT_3%%"        = "${Name} detail 3"
    "%%MACRO_IMG_4%%"        = "ornaments/${Slug}_detail_4.png"
    "%%MACRO_ALT_4%%"        = "${Name} detail 4"
    "%%MACRO_IMG_5%%"        = "ornaments/${Slug}_detail_5.png"
    "%%MACRO_ALT_5%%"        = "${Name} detail 5"
    "%%MACRO_IMG_6%%"        = "ornaments/${Slug}_detail_6.png"
    "%%MACRO_ALT_6%%"        = "${Name} detail 6"

    "%%PCG_SECTION_TITLE%%"  = "Procedural dressing proof."
    "%%PCG_SECTION_DESC%%"   = "PCG graphs drive environmental dressing, scatter, and placement."
    "%%PCG_TAG_1%%"          = "Scatter"
    "%%PCG_NAME_1%%"         = "PCG_${Name}Scatter"
    "%%PCG_DESC_1%%"         = "${Name} object scattering with density falloff."
    "%%PCG_TAG_2%%"          = "Dressing"
    "%%PCG_NAME_2%%"         = "PCG_${Name}Dressing"
    "%%PCG_DESC_2%%"         = "Environmental dressing along player route."
    "%%PCG_TAG_3%%"          = "Ground"
    "%%PCG_NAME_3%%"         = "PCG_${Name}Groundcover"
    "%%PCG_DESC_3%%"         = "Groundcover with biome blending and slope exclusion."
}

# --- Apply replacements ---------------------------------------------------
$content = Get-Content $templatePath -Raw
foreach ($key in $replacements.Keys) {
    $content = $content -replace [regex]::Escape($key), $replacements[$key]
}

# --- Write output ---------------------------------------------------------
Set-Content $outputPath $content -NoNewline
Write-Host ""
Write-Host "  [OK] Created wix/$Slug.html"
Write-Host ""
Write-Host "  ── Post-creation checklist ──"
Write-Host "  1. Replace hero images:"
Write-Host "       landscape-loops/WP_${Name}.webm       (hero video loop)"
Write-Host "       landscape-loops/WP_${Name}_terrain.png (poster image)"
Write-Host "       unreal/hero_${Slug}_*.png              (breakdown stills)"
Write-Host "  2. Replace macro images under ornaments/"
Write-Host "  3. Update OG image path if different"
Write-Host "  4. Add to application-hub.html environment grid"
Write-Host "  5. Add to index.html environment grid"
Write-Host "  6. Run deploy\quick-deploy.ps1 to publish"
Write-Host ""

if ($OpenInEditor -and (Test-Path $outputPath)) {
    Invoke-Item $outputPath
}