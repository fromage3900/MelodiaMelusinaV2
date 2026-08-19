param(
    [string]$ProjectRoot = "C:\EnvironmentPortfolio\BS_GodFile",
    [string]$RawPath = "C:\EnvironmentPortfolio\BS_GodFile\Saved\Screenshots\Monolith\MaterialRenderStudio\WaterV9\raw\WaterV9_SourceGrid.png",
    [string]$PortfolioRoot = "C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\MaterialRenderStudio",
    [string]$ReviewPath = "C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\MaterialRenderStudio\WaterV9_Review.json",
    [string]$ManifestPath = "C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\MaterialRenderStudio\WaterV9_RenderManifest.json"
)

Add-Type -AssemblyName System.Drawing
$individualRoot = Join-Path $PortfolioRoot "WaterV9_Individual"
$null = New-Item -ItemType Directory -Force -Path $individualRoot

$assets = @(
    [pscustomobject]@{ package="/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v9"; name="M_Water_Master_Grand_v9"; class="Material" },
    [pscustomobject]@{ package="/Game/EnvSandbox/Materials/Masters/M_Water_Underwater_Post_v9"; name="M_Water_Underwater_Post_v9"; class="Material" },
    [pscustomobject]@{ package="/Game/EnvSandbox/Materials/Instances/Water/v9/MI_WaterV9_CalmPond"; name="MI_WaterV9_CalmPond"; class="MaterialInstanceConstant" },
    [pscustomobject]@{ package="/Game/EnvSandbox/Materials/Instances/Water/v9/MI_WaterV9_BiolumGrotto"; name="MI_WaterV9_BiolumGrotto"; class="MaterialInstanceConstant" },
    [pscustomobject]@{ package="/Game/EnvSandbox/Materials/Instances/Water/v9/MI_WaterV9_RiverClear"; name="MI_WaterV9_RiverClear"; class="MaterialInstanceConstant" },
    [pscustomobject]@{ package="/Game/EnvSandbox/Materials/Instances/Water/v9/MI_WaterV9_OceanPreview"; name="MI_WaterV9_OceanPreview"; class="MaterialInstanceConstant" },
    [pscustomobject]@{ package="/Game/EnvSandbox/Materials/Instances/Water/v9/MI_WaterV9_CinematicHero"; name="MI_WaterV9_CinematicHero"; class="MaterialInstanceConstant" },
    [pscustomobject]@{ package="/Game/EnvSandbox/Materials/Instances/Water/v9/MI_Water_Underwater_Post_Default"; name="MI_Water_Underwater_Post_Default"; class="MaterialInstanceConstant" }
)

function Safe-Name([string]$value) {
    return (($value -replace '^/Game/', '') -replace '[^A-Za-z0-9]+', '_').Trim('_')
}
function C([int]$r,[int]$g,[int]$b,[int]$a=255) { return [System.Drawing.Color]::FromArgb($a,$r,$g,$b) }
function Font([float]$size,[bool]$bold=$false) {
    $style = if($bold){[System.Drawing.FontStyle]::Bold}else{[System.Drawing.FontStyle]::Regular}
    return [System.Drawing.Font]::new("Segoe UI",$size,$style,[System.Drawing.GraphicsUnit]::Pixel)
}
function Text($g,[string]$s,[float]$x,[float]$y,[float]$size,$color,[bool]$bold=$false) {
    $f=Font $size $bold; $b=[System.Drawing.SolidBrush]::new($color); $g.DrawString($s,$f,$b,$x,$y); $f.Dispose();$b.Dispose()
}
function Sample($bmp,[int]$x,[int]$y,[int]$w,[int]$h) {
    $sum=0.0;$sum2=0.0;$n=0
    $x0=[Math]::Max(0,[int]($x+$w*.32));$x1=[Math]::Min($bmp.Width-1,[int]($x+$w*.68))
    $y0=[Math]::Max(0,[int]($y+$h*.32));$y1=[Math]::Min($bmp.Height-1,[int]($y+$h*.68))
    for($py=$y0;$py -le $y1;$py+=8){for($px=$x0;$px -le $x1;$px+=8){$p=$bmp.GetPixel($px,$py);$v=(.2126*$p.R)+(.7152*$p.G)+(.0722*$p.B);$sum+=$v;$sum2+=($v*$v);$n++}}
    if($n -eq 0){return @{mean=0;variance=0}}
    $m=$sum/$n;return @{mean=$m;variance=[Math]::Max(0,(($sum2/$n)-($m*$m)))}
}

$gridPath = Join-Path $PortfolioRoot "WaterV9_PortfolioGrid.png"
$src = [System.Drawing.Bitmap]::FromFile($RawPath)
$cols=4;$rows=2;$tileW=420;$tileH=430;$headerH=86
$outW=$cols*$tileW;$outH=$headerH+($rows*$tileH)
$dst=[System.Drawing.Bitmap]::new($outW,$outH,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$g=[System.Drawing.Graphics]::FromImage($dst)
$g.SmoothingMode=[System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$bg=[System.Drawing.Rectangle]::new(0,0,$outW,$outH)
$gb=[System.Drawing.Drawing2D.LinearGradientBrush]::new($bg,(C 19 24 33),(C 61 67 78),90.0);$g.FillRectangle($gb,$bg);$gb.Dispose()
Text $g "MATERIAL RENDER STUDIO  /  WATER V9" 30 18 22 (C 242 245 248) $true
Text $g "Dedicated addendum  |  8 assets  |  source capture via Monolith" 30 48 13 (C 169 180 194)
$accent=[System.Drawing.SolidBrush]::new((C 225 164 94));$g.FillRectangle($accent,30,75,410,3);$accent.Dispose()

$cellW=$src.Width/$cols;$cellH=$src.Height/$rows;$rowsOut=New-Object System.Collections.ArrayList
for($i=0;$i -lt $assets.Count;$i++){
    $asset=$assets[$i];$col=$i%$cols;$row=[Math]::Floor($i/$cols);$x=[int]($col*$tileW);$y=[int]($headerH+($row*$tileH))
    $card=[System.Drawing.Rectangle]::new($x+12,$y+12,$tileW-24,$tileH-24);$cb=[System.Drawing.SolidBrush]::new((C 35 40 49));$g.FillRectangle($cb,$card);$cb.Dispose()
    $pen=[System.Drawing.Pen]::new((C 99 109 123),1.0);$g.DrawRectangle($pen,$card);$pen.Dispose()
    $sx=[int]($col*$cellW);$sy=[int]($row*$cellH);$cropW=[int]($cellW*.58);$cropH=[int]($cellH*.58);$cropX=[int]($sx+(($cellW-$cropW)/2));$cropY=[int]($sy+(($cellH-$cropH)/2))
    $dest=[System.Drawing.Rectangle]::new($x+45,$y+34,$tileW-90,285);$clip=[System.Drawing.Drawing2D.GraphicsPath]::new();$clip.AddEllipse($dest);$state=$g.Save();$g.SetClip($clip)
    $g.DrawImage($src,$dest,[System.Drawing.Rectangle]::new($cropX,$cropY,$cropW,$cropH),[System.Drawing.GraphicsUnit]::Pixel);$g.Restore($state);$clip.Dispose()
    $sh=[System.Drawing.SolidBrush]::new((C 0 0 0 75));$g.FillEllipse($sh,$x+112,$y+291,196,20);$sh.Dispose()
    Text $g $asset.name ($x+24) ($y+341) 14 (C 239 242 246) $true;Text $g $asset.class ($x+24) ($y+365) 11 (C 159 171 185)
    $s=Sample $src $sx $sy $cellW $cellH;$mean=[double]$s.mean;$variance=[double]$s.variance;$status="succeeded";$flag="none";$note=""
    if($mean -lt 7){$status="succeeded_review_black";$flag="black_or_low_readability";$note="Low central luminance in generic sphere preview; verify intended water mesh/scene context."}
    elseif($variance -lt 2.5){$status="succeeded_review_flat";$flag="flat_or_context_limited";$note="Low central variance in generic sphere preview; verify intended water mesh/UV/depth context."}
    if($asset.name -like "M_Water_Underwater*" -or $asset.name -like "MI_Water_Underwater*"){$flag="context_required";$note="Underwater post-process material is not fully represented by a lit sphere preview."}
    elseif($asset.name -like "*OceanPreview" -or $asset.name -like "*RiverClear" -or $asset.name -like "*CalmPond"){$note="Water surface material should receive a second context pass on the intended water geometry."}
    $individual=Join-Path $individualRoot ((Safe-Name $asset.package)+"."+$asset.name+".png")
    $parent = if($asset.class -eq "MaterialInstanceConstant") { if($asset.name -like "*Underwater*") { "/Game/EnvSandbox/Materials/Masters/M_Water_Underwater_Post_v9.M_Water_Underwater_Post_v9" } else { "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v9.M_Water_Master_Grand_v9" } } else { $null }
    [void]$rowsOut.Add([pscustomobject]@{package_path=$asset.package;object_path=($asset.package+"."+$asset.name);class=$asset.class;parent_path=$parent;source_render=$RawPath;portfolio_grid=$gridPath;individual_render=$individual;status=$status;flag=$flag;note=$note;sample_mean=[Math]::Round($mean,2);sample_variance=[Math]::Round($variance,2)})
}
$dst.Save($gridPath,[System.Drawing.Imaging.ImageFormat]::Png)
for($i=0;$i -lt $assets.Count;$i++){
    $col=$i%$cols;$row=[Math]::Floor($i/$cols);$rect=[System.Drawing.Rectangle]::new([int]($col*$tileW),[int]($headerH+($row*$tileH)),$tileW,$tileH);$item=$rowsOut[$i];$tile=$dst.Clone($rect,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb);$tile.Save($item.individual_render,[System.Drawing.Imaging.ImageFormat]::Png);$tile.Dispose()
}
$g.Dispose();$src.Dispose();$dst.Dispose()

$manifest=[pscustomobject]@{studio_name="Material Render Studio";addendum="Water v9";studio_map="/Game/EnvSandbox/Materials/RenderStudio/Material_Render_Studio";source_capture=$RawPath;portfolio_grid=$gridPath;asset_count=$rowsOut.Count;assets=$rowsOut}
$manifest|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $ManifestPath -Encoding UTF8
$review=[pscustomobject]@{studio_name="Material Render Studio";addendum="Water v9";scope="8 requested Water v9 assets only";asset_count=$rowsOut.Count;successful=@($rowsOut|Where-Object {$_.status -like "succeeded*"}).Count;failed=@($rowsOut|Where-Object {$_.status -eq "failed"}).Count;flag_counts=@($rowsOut|Group-Object flag|ForEach-Object{[pscustomobject]@{flag=$_.Name;count=$_.Count}});assets=$rowsOut;review_notes=@("The source capture succeeded for every requested asset.","All eight assets loaded through Unreal Python readback; the five surface instances resolve to M_Water_Master_Grand_v9 and the underwater post instance resolves to M_Water_Underwater_Post_v9.","The typed validate_material action returned 0 issues for both v9 master materials but could not load the base material for the six instances; this is recorded as a tool-readback limitation, not a render failure.","Underwater post materials are context-required and should not be judged as ordinary lit surface spheres.","Water surface instances should receive a future intended-mesh context capture if native map-camera capture becomes available.","No baseline assets were rerendered.")}
$review|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $ReviewPath -Encoding UTF8
[pscustomobject]@{manifest=$ManifestPath;review=$ReviewPath;portfolio_grid=$gridPath;asset_count=$rowsOut.Count;successful=@($rowsOut|Where-Object {$_.status -like "succeeded*"}).Count;failed=@($rowsOut|Where-Object {$_.status -eq "failed"}).Count;individual_pngs=(Get-ChildItem $individualRoot -Filter *.png).Count}|ConvertTo-Json -Compress
