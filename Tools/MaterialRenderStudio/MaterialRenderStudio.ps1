param(
    [string]$ProjectRoot = "C:\EnvironmentPortfolio\BS_GodFile",
    [string]$InventoryPath = "C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\MaterialRenderStudio\asset_inventory.json",
    [string]$RawDir = "C:\EnvironmentPortfolio\BS_GodFile\Saved\Screenshots\Monolith\MaterialRenderStudio\raw",
    [string]$OutputDir = "C:\EnvironmentPortfolio\BS_GodFile\Saved\Screenshots\Monolith\MaterialRenderStudio\portfolio",
    [string]$ManifestDir = "C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\MaterialRenderStudio"
)

Add-Type -AssemblyName System.Drawing

$null = New-Item -ItemType Directory -Force -Path $OutputDir
$IndividualDir = Join-Path $OutputDir "individual"
$null = New-Item -ItemType Directory -Force -Path $IndividualDir
$null = New-Item -ItemType Directory -Force -Path $ManifestDir
$inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json

function Get-SafeName([string]$value) {
    $safe = $value -replace '^/Game/', ''
    $safe = $safe -replace '[^A-Za-z0-9]+', '_'
    return $safe.Trim('_')
}

function New-Color([int]$r, [int]$g, [int]$b, [int]$a = 255) {
    return [System.Drawing.Color]::FromArgb([int]$a, [int]$r, [int]$g, [int]$b)
}

function Get-ReadableFont([float]$size, [bool]$bold = $false) {
    $style = if ($bold) { [System.Drawing.FontStyle]::Bold } else { [System.Drawing.FontStyle]::Regular }
    return [System.Drawing.Font]::new("Segoe UI", [float]$size, $style, [System.Drawing.GraphicsUnit]::Pixel)
}

function Get-CellSample($bitmap, [int]$x, [int]$y, [int]$w, [int]$h) {
    $sum = 0.0; $sum2 = 0.0; $count = 0
    $x0 = [Math]::Max(0, [int]($x + $w * 0.32)); $x1 = [Math]::Min($bitmap.Width - 1, [int]($x + $w * 0.68))
    $y0 = [Math]::Max(0, [int]($y + $h * 0.32)); $y1 = [Math]::Min($bitmap.Height - 1, [int]($y + $h * 0.68))
    for ($py = $y0; $py -le $y1; $py += 8) {
        for ($px = $x0; $px -le $x1; $px += 8) {
            $c = $bitmap.GetPixel($px, $py)
            $v = (0.2126 * $c.R) + (0.7152 * $c.G) + (0.0722 * $c.B)
            $sum += $v; $sum2 += ($v * $v); $count++
        }
    }
    if ($count -eq 0) { return @{ mean = 0.0; variance = 0.0 } }
    $mean = $sum / $count
    return @{ mean = $mean; variance = [Math]::Max(0.0, ($sum2 / $count) - ($mean * $mean)) }
}

function Add-Text($graphics, [string]$text, [float]$x, [float]$y, [float]$size, $color, [bool]$bold = $false) {
    $font = Get-ReadableFont $size $bold
    $brush = [System.Drawing.SolidBrush]::new($color)
    $graphics.DrawString($text, $font, $brush, $x, $y)
    $font.Dispose(); $brush.Dispose()
}

$groups = @{}
foreach ($asset in $inventory.assets) {
    $slash = $asset.package.LastIndexOf('/')
    $family = if ($slash -gt 0) { $asset.package.Substring(0, $slash) } else { $asset.root }
    if (-not $groups.ContainsKey($family)) { $groups[$family] = New-Object System.Collections.ArrayList }
    [void]$groups[$family].Add($asset)
}

$batches = New-Object System.Collections.ArrayList
$batchIndex = 1
$familyKeys = [System.Collections.Generic.List[string]]::new()
foreach ($key in $groups.Keys) { [void]$familyKeys.Add([string]$key) }
$familyKeys.Sort([System.StringComparer]::Ordinal)
foreach ($family in $familyKeys) {
    $items = @($groups[$family])
    for ($start = 0; $start -lt $items.Count; $start += 16) {
        $batchItems = @($items | Select-Object -Skip $start -First 16)
        $cols = [Math]::Ceiling([Math]::Sqrt($batchItems.Count))
        $safeFamily = Get-SafeName $family
        $rawName = "B{0:D3}_{1}.png" -f $batchIndex, $safeFamily
        $retry = Join-Path $RawDir ("B{0:D3}_{1}_Retry.png" -f $batchIndex, $safeFamily)
        $rawPath = Join-Path $RawDir $rawName
        if (Test-Path -LiteralPath $retry) { $rawPath = $retry }
        else {
            $retryMatch = Get-ChildItem -LiteralPath $RawDir -Filter ("B{0:D3}_*_Retry.png" -f $batchIndex) -File | Select-Object -First 1
            $baseMatch = Get-ChildItem -LiteralPath $RawDir -Filter ("B{0:D3}_*.png" -f $batchIndex) -File | Where-Object { $_.Name -notlike "*_Retry.png" } | Select-Object -First 1
            if ($retryMatch) { $rawPath = $retryMatch.FullName }
            elseif ($baseMatch) { $rawPath = $baseMatch.FullName }
        }
        $portfolioName = "B{0:D3}_{1}_Studio.png" -f $batchIndex, $safeFamily
        $portfolioPath = Join-Path $OutputDir $portfolioName
        [void]$batches.Add([pscustomobject]@{
            batch = $batchIndex; family = $family; safe_family = $safeFamily; columns = $cols
            items = $batchItems; raw_path = $rawPath; portfolio_path = $portfolioPath
        })
        $batchIndex++
    }
}

$renderRows = New-Object System.Collections.ArrayList
$flags = New-Object System.Collections.ArrayList
$signatureRows = New-Object System.Collections.ArrayList

foreach ($batch in $batches) {
    if (-not (Test-Path -LiteralPath $batch.raw_path)) {
        foreach ($asset in $batch.items) {
            [void]$renderRows.Add([pscustomobject]@{ path=$asset.path; class=$asset.class; family=$batch.family; batch=$batch.batch; raw_render=$null; portfolio_render=$null; status="missing_raw" })
            [void]$flags.Add([pscustomobject]@{ path=$asset.path; flag="missing_raw"; severity="error"; note="No Monolith capture file found for this batch." })
        }
        continue
    }

    $src = [System.Drawing.Bitmap]::FromFile($batch.raw_path)
    $rows = [Math]::Ceiling($batch.items.Count / $batch.columns)
    $tileW = 420; $tileH = 430; $headerH = 86
    $outW = [int]($tileW * $batch.columns); $outH = [int]($headerH + ($tileH * $rows))
    $dst = [System.Drawing.Bitmap]::new([int]$outW, [int]$outH, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [System.Drawing.Graphics]::FromImage($dst)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $bgRect = [System.Drawing.Rectangle]::new(0, 0, [int]$outW, [int]$outH)
    $bgBrush = [System.Drawing.Drawing2D.LinearGradientBrush]::new($bgRect, (New-Color 19 24 33), (New-Color 61 67 78), 90.0)
    $g.FillRectangle($bgBrush, $bgRect); $bgBrush.Dispose()
    Add-Text $g "MATERIAL RENDER STUDIO" 30 18 22 (New-Color 242 245 248) $true
    Add-Text $g ("{0}  |  {1} assets  |  neutral studio presentation" -f (Get-SafeName $batch.family), $batch.items.Count) 30 48 13 (New-Color 169 180 194) $false
    $accent = [System.Drawing.SolidBrush]::new((New-Color 225 164 94))
    $g.FillRectangle($accent, 30, 75, [Math]::Min(320, $outW-60), 3); $accent.Dispose()

    $cellW = $src.Width / $batch.columns; $cellH = $src.Height / $rows
    for ($i=0; $i -lt $batch.items.Count; $i++) {
        $asset = $batch.items[$i]
        $col = $i % $batch.columns; $row = [Math]::Floor($i / $batch.columns)
        $x = [int]($col * $tileW); $y = [int]($headerH + ($row * $tileH))
        $card = [System.Drawing.Rectangle]::new([int]($x+12), [int]($y+12), [int]($tileW-24), [int]($tileH-24))
        $cardBrush = [System.Drawing.SolidBrush]::new((New-Color 35 40 49))
        $g.FillRectangle($cardBrush, $card); $cardBrush.Dispose()
        $border = [System.Drawing.Pen]::new((New-Color 99 109 123), 1.0)
        $g.DrawRectangle($border, $card); $border.Dispose()

        $sx = [int]($col * $cellW); $sy = [int]($row * $cellH)
        $cropW = [int]($cellW * 0.58); $cropH = [int]($cellH * 0.58)
        $cropX = [int]($sx + (($cellW - $cropW) / 2)); $cropY = [int]($sy + (($cellH - $cropH) / 2))
        $dest = [System.Drawing.Rectangle]::new([int]($x+45), [int]($y+34), [int]($tileW-90), 285)
        $clip = [System.Drawing.Drawing2D.GraphicsPath]::new()
        $clip.AddEllipse($dest)
        $state = $g.Save(); $g.SetClip($clip)
        $g.DrawImage($src, $dest, [System.Drawing.Rectangle]::new([int]$cropX,[int]$cropY,[int]$cropW,[int]$cropH), [System.Drawing.GraphicsUnit]::Pixel)
        $g.Restore($state); $clip.Dispose()
        $shadow = [System.Drawing.SolidBrush]::new((New-Color 0 0 0 75))
        $g.FillEllipse($shadow, $x+112, $y+291, 196, 20); $shadow.Dispose()

        $shortName = [string]$asset.name
        if ($shortName.Length -gt 39) { $shortName = $shortName.Substring(0,36) + "..." }
        Add-Text $g $shortName ($x+24) ($y+341) 14 (New-Color 239 242 246) $true
        Add-Text $g $asset.class ($x+24) ($y+365) 11 (New-Color 159 171 185) $false

        $sample = Get-CellSample $src $sx $sy $cellW $cellH
        $mean = [double]$sample.mean; $variance = [double]$sample.variance
        $status = "ok"
        if ($mean -lt 7) { $status = "black"; [void]$flags.Add([pscustomobject]@{ path=$asset.path; flag="black"; severity="high"; note=("Central sample mean {0:N1}" -f $mean) }) }
        elseif ($variance -lt 2.5) { $status = "flat"; [void]$flags.Add([pscustomobject]@{ path=$asset.path; flag="flat"; severity="medium"; note=("Central sample variance {0:N1}" -f $variance) }) }
        [void]$signatureRows.Add([pscustomobject]@{ path=$asset.path; family=$batch.family; mean=[Math]::Round($mean,2); variance=[Math]::Round($variance,2) })
        $individualPath = Join-Path $IndividualDir ((Get-SafeName $asset.path) + ".png")
        [void]$renderRows.Add([pscustomobject]@{ path=$asset.path; class=$asset.class; family=$batch.family; batch=$batch.batch; raw_render=$batch.raw_path; portfolio_render=$individualPath; portfolio_batch=$batch.portfolio_path; status=$status })
    }
    $dst.Save($batch.portfolio_path, [System.Drawing.Imaging.ImageFormat]::Png)
    for ($i=0; $i -lt $batch.items.Count; $i++) {
        $asset = $batch.items[$i]
        $col = $i % $batch.columns; $row = [Math]::Floor($i / $batch.columns)
        $tileRect = [System.Drawing.Rectangle]::new([int]($col * $tileW), [int]($headerH + ($row * $tileH)), [int]$tileW, [int]$tileH)
        $individualPath = Join-Path $IndividualDir ((Get-SafeName $asset.path) + ".png")
        $tile = $dst.Clone($tileRect, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        $tile.Save($individualPath, [System.Drawing.Imaging.ImageFormat]::Png)
        $tile.Dispose()
    }
    $g.Dispose(); $src.Dispose(); $dst.Dispose()
}

# Conservative duplicate detection: flag only near-identical luminance signatures within the same sampled set.
for ($i=0; $i -lt $signatureRows.Count; $i++) {
    for ($j=$i+1; $j -lt $signatureRows.Count; $j++) {
        $a=$signatureRows[$i]; $b=$signatureRows[$j]
        if ($a.family -eq $b.family -and [Math]::Abs($a.mean-$b.mean) -lt 0.75 -and [Math]::Abs($a.variance-$b.variance) -lt 0.75) {
            [void]$flags.Add([pscustomobject]@{ path=$a.path; flag="possible_duplicate"; severity="low"; note=("Similar sampled luminance signature to {0}" -f $b.path) })
            [void]$flags.Add([pscustomobject]@{ path=$b.path; flag="possible_duplicate"; severity="low"; note=("Similar sampled luminance signature to {0}" -f $a.path) })
        }
    }
}

$manualTriage = @(
    @{ path="/Game/EnvSandbox/Materials/SDF/Instances/MI_Cosmic_BlueNebulaA.MI_Cosmic_BlueNebulaA"; flag="black_or_low_readability"; severity="high"; note="Predominantly black/low-readability in the generic sphere preview; verify emissive, scene-texture, and intended mesh context before material edits." },
    @{ path="/Game/EnvSandbox/Materials/SDF/Instances/MI_Cosmic_VoidDeep.MI_Cosmic_VoidDeep"; flag="black_or_low_readability"; severity="high"; note="Predominantly black/low-readability in the generic sphere preview; verify emissive and camera-facing inputs before material edits." },
    @{ path="/Game/EnvSandbox/Materials/Instances/Water/MI_GrandWater_ShorelinePond.MI_GrandWater_ShorelinePond"; flag="black_or_low_readability"; severity="medium"; note="Dark/flat in sphere preview; likely requires shoreline geometry, flow mask, or scene context." },
    @{ path="/Game/EnvSandbox/Materials/Instances/Water/MI_GrandWater_SwampMurk.MI_GrandWater_SwampMurk"; flag="flat_or_context_limited"; severity="medium"; note="Low feature separation in sphere preview; validate with intended water volume and depth inputs." },
    @{ path="/Game/EnvSandbox/Materials/Instances/Water/MI_GrandWater_WaterfallSheet.MI_GrandWater_WaterfallSheet"; flag="flat_or_context_limited"; severity="medium"; note="Sheet/flow material is not represented faithfully on a sphere; requires waterfall mesh and UV motion review." },
    @{ path="/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Gradient__Radial__002.MI_Melusina_Gradient__Radial__002"; flag="flat_or_support_pass"; severity="medium"; note="Mostly flat gray under generic sphere capture; review on the owning character mesh and expected gradient coordinates." },
    @{ path="/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Outline_004.MI_Melusina_Outline_004"; flag="flat_or_support_pass"; severity="low"; note="Outline/support pass is not a hero-surface candidate; review only in character render context." },
    @{ path="/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Outline_005.MI_Melusina_Outline_005"; flag="flat_or_support_pass"; severity="low"; note="Outline/support pass is not a hero-surface candidate; review only in character render context." }
)
foreach ($manual in $manualTriage) {
    if (@($renderRows | Where-Object { $_.path -eq $manual.path }).Count -gt 0) {
        [void]$flags.Add([pscustomobject]$manual)
    }
}

$manifest = [pscustomobject]@{
    studio_name = "Material Render Studio"
    map_asset = "/Game/EnvSandbox/Materials/RenderStudio/Material_Render_Studio"
    neutral_material = "/Game/EnvSandbox/Materials/RenderStudio/M_MaterialRenderStudio_Neutral"
    raw_capture_root = $RawDir
    portfolio_output_root = $OutputDir
    batch_count = $batches.Count
    asset_count = $renderRows.Count
    successful_asset_renders = @($renderRows | Where-Object { $_.status -ne "missing_raw" }).Count
    missing_asset_renders = @($renderRows | Where-Object { $_.status -eq "missing_raw" }).Count
    batches = $batches | ForEach-Object { [pscustomobject]@{ batch=$_.batch; family=$_.family; raw_render=$_.raw_path; portfolio_render=$_.portfolio_path; asset_count=$_.items.Count; assets=$_.items.path } }
    asset_renders = $renderRows
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $ManifestDir "render_manifest.json") -Encoding UTF8

$review = [pscustomobject]@{
    studio_name = "Material Render Studio"
    scope = $inventory.roots
    asset_count = $renderRows.Count
    successful_asset_renders = @($renderRows | Where-Object { $_.status -ne "missing_raw" }).Count
    flag_counts = @($flags | Group-Object flag | ForEach-Object { [pscustomobject]@{ flag=$_.Name; count=$_.Count } })
    flagged_assets = $flags
    strongest_assets = @(
        "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_GLOVES_001.MI_Melusina_GLOVES_001",
        "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Material_013.MI_Melusina_Material_013",
        "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Material_023.MI_Melusina_Material_023",
        "/Game/EnvSandbox/Materials/Instances/Water/MI_GrandWater_SakuraPond1.MI_GrandWater_SakuraPond1",
        "/Game/EnvSandbox/Materials/Instances/Environment/Magical/MI_Universal_GoldLeaf.MI_Universal_GoldLeaf",
        "/Game/EnvSandbox/Materials/SDF/Instances/MI_Cosmic_StarfieldA.MI_Cosmic_StarfieldA",
        "/Game/EnvSandbox/Materials/SDF/Instances/MI_SDF_Utility_N64PS1.MI_SDF_Utility_N64PS1"
    )
    weakest_candidates = @(
        "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Gradient__Radial__002.MI_Melusina_Gradient__Radial__002",
        "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Outline_004.MI_Melusina_Outline_004",
        "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Outline_005.MI_Melusina_Outline_005",
        "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Material_024.MI_Melusina_Material_024",
        "/Game/EnvSandbox/Materials/Instances/Water/MI_GrandWater_ShorelinePond.MI_GrandWater_ShorelinePond",
        "/Game/EnvSandbox/Materials/Instances/Water/MI_GrandWater_SwampMurk.MI_GrandWater_SwampMurk",
        "/Game/EnvSandbox/Materials/Instances/Water/MI_GrandWater_WaterfallSheet.MI_GrandWater_WaterfallSheet",
        "/Game/EnvSandbox/Materials/SDF/Instances/MI_Cosmic_BlueNebulaA.MI_Cosmic_BlueNebulaA",
        "/Game/EnvSandbox/Materials/SDF/Instances/MI_Cosmic_VoidDeep.MI_Cosmic_VoidDeep"
    )
    context_required_assets = @(
        "Water family instances that depend on flow/shoreline/scene geometry",
        "Melusina outline-only and gradient-only support instances",
        "Landscape and height-blend materials previewed on a sphere",
        "Materials using scene textures, RVT, Niagara, or actor-position inputs"
    )
    recommended_material_work = @(
        "Prioritize the weakest candidates only after a second pass on the intended mesh/UV/context; several are support passes rather than hero surfaces.",
        "For dark SDF/cosmic instances, add a dedicated emissive/contrast preview mode before changing production parameters so black results are separated from capture-context failure.",
        "Create dedicated flatness/readability checks for character gradients, outlines, and water sheets; these need asset-specific preview meshes rather than the generic sphere.",
        "Keep MI_Melusina_WaterHair on its existing water-hair parent and review it separately from surface-water assets."
    )
    presentation_limitations = @(
        "Monolith capture_material_grid supplies the Unreal source render but does not expose a custom background parameter; the portfolio pass adds the saved studio treatment around the captured object region.",
        "The saved Material Render Studio map is persistent and verified, but the current capture action remains an isolated preview scene. A future native map-camera capture action would remove the remaining HDRI pixels inside the object mask.",
        "A Monolith PIE native-capture test resolved MRS_Camera but returned an invalid uniform/black frame in the hidden editor viewport; native map-camera capture is therefore recorded as blocked rather than silently substituted."
    )
    review_method = "Central sphere-sample luminance/variance heuristics plus manual portfolio batch review; flags are triage signals, not material correctness proofs."
    preservation_notes = @("No production material was reparented or mass-replaced.", "MI_Melusina_WaterHair remains in scope for review but its source separation is unchanged.")
}
$review | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $ManifestDir "portfolio_review.json") -Encoding UTF8

$summary = [pscustomobject]@{ studio="Material Render Studio"; batches=$batches.Count; scoped_assets=$inventory.count_total; rendered_assets=@($renderRows | Where-Object { $_.status -ne "missing_raw" }).Count; missing=@($renderRows | Where-Object { $_.status -eq "missing_raw" }).Count; flags=$flags.Count; manifest=(Join-Path $ManifestDir "render_manifest.json"); review=(Join-Path $ManifestDir "portfolio_review.json"); output_dir=$OutputDir }
$summary | ConvertTo-Json -Compress
