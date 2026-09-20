#Requires -Version 5.1
<#
.SYNOPSIS
  Megascans + Brushify Floating Islands — disk census, Monolith parent histogram,
  Megascans batch-1 reparent onto Custom_MS masters.

.NOTES
  Run on fromage with UE BS_GodFile open and Monolith at http://127.0.0.1:9316/mcp
  HARD RULES: NEVER save_packages / recompile_material. Leave dirty for owner Ctrl+S.
  Default: -WhatIf for convert; pass -Convert -BatchSize 15 to mutate.
#>
param(
  [switch]$Convert,
  [int]$BatchSize = 15,
  [switch]$WhatIf,
  [string]$Root = 'C:\EnvironmentPortfolio\BS_GodFile',
  [string]$MonolithUrl = 'http://127.0.0.1:9316/mcp'
)
# Default: dry-run unless -Convert without -WhatIf
if (-not $Convert) { $WhatIf = $true }
elseif (-not $PSBoundParameters.ContainsKey('WhatIf')) { $WhatIf = $false }

$ErrorActionPreference = 'Stop'
$Audit = Join-Path $Root 'Saved\Audit'
$Content = Join-Path $Root 'Content'
New-Item -ItemType Directory -Force -Path $Audit | Out-Null

$MS_DEFAULT = '/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Default_Overwrite/M_MS_CustomDefault'
$MS_FOLIAGE = '/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Foliage_Overwrite/M_MS_CustomFoliage'
$MS_FOLIAGE_NOOP = '/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Foliage_Overwrite/M_MS_CustomFoliageNoOpacity'
$MS_FOLIAGE_NOWPO = '/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Foliage_Overwrite/M_MS_CustomFoliageNoWPO'
$MS_FOLIAGE_BOTH = '/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Foliage_Overwrite/M_MS_CustomFoliageNoOpacityNoWPO'
$MS_DECAL_CNR = '/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_Decal/M_MS_CustomDecal_CNR'
$MS_DECAL_CR = '/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_Decal/M_MS_CustomDecal_CR'

$STOCK_SURFACE = @(
  'M_MS_Default_Material','M_MS_Default_Material_VT','M_MS_Surface_Material','M_MS_Surface_Material_VT',
  'M_MS_Default_Material_VT_DynamicLayering','M_MS_Default_Material_VT_WaterTest'
)
$STOCK_FOLIAGE = @('M_MS_Foliage_Material','M_Foliage')
$STOCK_DECAL = @('M_MS_Decal_Material_VT','M_MS_Decal_Material_VT_NoNormalAlbedo1')
$CUSTOM_OK = @('M_MS_CustomDefault','M_MS_CustomFoliage','M_MS_CustomFoliageNoOpacity','M_MS_CustomFoliageNoWPO','M_MS_CustomFoliageNoOpacityNoWPO','M_MS_CustomDecal_CNR','M_MS_CustomDecal_CR')

function Invoke-MonolithTool {
  param([string]$Name, [hashtable]$Arguments = @{}, [int]$Id = 1)
  $bodyObj = @{ jsonrpc='2.0'; id=$Id; method='tools/call'; params=@{ name=$Name; arguments=$Arguments } }
  $body = $bodyObj | ConvertTo-Json -Depth 40 -Compress
  $headers = @{ 'Content-Type'='application/json'; 'Accept'='application/json, text/event-stream' }
  try {
    return Invoke-RestMethod -Uri $MonolithUrl -Method POST -Headers $headers -Body $body -TimeoutSec 120
  } catch {
    return @{ error = @{ message = $_.Exception.Message } }
  }
}
function Get-MonolithText($r) {
  if ($null -eq $r) { return 'ERROR: null' }
  if ($r.result -and $r.result.content) { return (($r.result.content | ForEach-Object { $_.text }) -join "`n") }
  if ($r.error) { return "ERROR: $($r.error.message)" }
  return ($r | ConvertTo-Json -Depth 12)
}

function Disk-To-GamePath([string]$fullPath) {
  $rel = $fullPath.Substring($Content.Length).TrimStart('\','/')
  $rel = $rel -replace '\\','/' -replace '\.uasset$',''
  return "/Game/$rel"
}

Write-Host '==== 1) DISK CENSUS ===='
$megaMis = @(Get-ChildItem (Join-Path $Content 'Megascans') -Recurse -Filter 'MI_*.uasset' -EA SilentlyContinue)
$brushRoot = Join-Path $Content 'Brushify - Floating Islands'
$brushMis = @(Get-ChildItem $brushRoot -Recurse -Filter 'MI_*.uasset' -EA SilentlyContinue)
$brushMs = @(Get-ChildItem $brushRoot -Recurse -Filter 'M_*.uasset' -EA SilentlyContinue | Where-Object { $_.Name -notlike 'MI_*' })
$greyDup = @(Get-ChildItem (Join-Path $Content 'Greybox_Kit') -Recurse -Directory -Filter '*Brushify*' -EA SilentlyContinue)
$envGrey = @(Get-ChildItem (Join-Path $Content 'EnvSandbox\Greybox_Kit') -Recurse -Directory -Filter '*Brushify*' -EA SilentlyContinue)

Write-Host "Megascans MI_*: $($megaMis.Count)"
Write-Host "Brushify FI MI_*: $($brushMis.Count)  M_*: $($brushMs.Count)"
Write-Host "Greybox Brushify dirs: $($greyDup.Count + $envGrey.Count)"

# Category buckets by path
function Classify-Mega([string]$p) {
  $l = $p.ToLower()
  if ($l -match '/foliage/|/plants?/|/trees?/') { return 'Foliage' }
  if ($l -match '/decals?/') { return 'Decals' }
  if ($l -match '/surfaces?/|/ground/') { return 'Surfaces' }
  if ($l -match '/3d/|/3d_assets?/|/assets/') { return '3D' }
  return 'Other'
}
$megaByCat = $megaMis | ForEach-Object { Classify-Mega (Disk-To-GamePath $_.FullName) } | Group-Object | Sort-Object Count -Descending
Write-Host 'Megascans by path category:'
$megaByCat | ForEach-Object { Write-Host ("  {0}: {1}" -f $_.Name, $_.Count) }

function Classify-Brush([string]$p) {
  $l = $p.ToLower()
  if ($l -match 'landscape|layerinfo|terrain') { return 'Landscape' }
  if ($l -match 'foliage|grass|plant|leaf|tree') { return 'Foliage' }
  if ($l -match 'fog|cloud|vfx|particle|sky') { return 'VFX' }
  if ($l -match 'rock|cliff|stone|boulder') { return 'RockCliff' }
  if ($l -match 'materialoverride|demo|example') { return 'DemoOverride' }
  return 'Other'
}
$brushByCat = $brushMis | ForEach-Object { Classify-Brush (Disk-To-GamePath $_.FullName) } | Group-Object | Sort-Object Count -Descending
Write-Host 'Brushify MI by class:'
$brushByCat | ForEach-Object { Write-Host ("  {0}: {1}" -f $_.Name, $_.Count) }

Write-Host '`n==== 2) MONOLITH INIT + SCHEMA ===='
$init = Invoke-MonolithTool -Name 'initialize' -Arguments @{} -Id 0
# Many servers want tools/list or initialize via method not tool — probe discover
$disc = Invoke-MonolithTool -Name 'monolith_discover' -Arguments @{ namespace = 'material' }
$discText = Get-MonolithText $disc
$discText.Substring(0, [Math]::Min(1500, $discText.Length)) | Write-Host
$schema = Invoke-MonolithTool -Name 'describe_query' -Arguments @{
  action = 'action_schema'; target_namespace = 'material'; target_action = 'set_instance_parent'
}
Write-Host 'set_instance_parent schema:'
Write-Host (Get-MonolithText $schema)

Write-Host '`n==== 3) PARENT HISTOGRAM (sample via get_material_properties) ===='
function Get-Parent([string]$assetPath) {
  $r = Invoke-MonolithTool -Name 'material_query' -Arguments @{
    action = 'get_material_properties'; asset_path = $assetPath
  }
  $t = Get-MonolithText $r
  if ($t -like 'ERROR:*') { return @{ parent = "ERROR:$t"; raw = $t } }
  try {
    $j = $t | ConvertFrom-Json
    $parent = $null
    foreach ($k in @('parent','parent_path','Parent','ParentPath','parent_material')) {
      if ($j.PSObject.Properties.Name -contains $k -and $j.$k) { $parent = [string]$j.$k; break }
    }
    if (-not $parent -and $j.properties) {
      $pp = $j.properties | Where-Object { $_.name -match '^[Pp]arent' } | Select-Object -First 1
      if ($pp) { $parent = [string]$pp.value }
    }
    if (-not $parent) { $parent = 'UNKNOWN' }
    return @{ parent = $parent; raw = $t }
  } catch {
    # fallback regex
    if ($t -match '"parent[^"]*"\s*:\s*"([^"]+)"') { return @{ parent = $Matches[1]; raw = $t } }
    return @{ parent = 'PARSE_FAIL'; raw = $t }
  }
}

function Build-Histogram($files, [int]$limit = 0) {
  $hist = @{}
  $rows = @()
  $n = 0
  foreach ($f in $files) {
    $n++
    if ($limit -gt 0 -and $n -gt $limit) { break }
    $gp = Disk-To-GamePath $f.FullName
    $info = Get-Parent $gp
    $p = $info.parent
    if (-not $hist.ContainsKey($p)) { $hist[$p] = 0 }
    $hist[$p]++
    $rows += [pscustomobject]@{ path = $gp; parent = $p; category = (Classify-Mega $gp) }
    if (($n % 25) -eq 0) { Write-Host "  ... $n / $($files.Count)" }
  }
  return @{ hist = $hist; rows = $rows }
}

# Full Megascans histogram (can be slow ~237)
Write-Host "Megascans parent pass ($($megaMis.Count))..."
$megaHist = Build-Histogram $megaMis
$megaHist.hist.GetEnumerator() | Sort-Object Value -Descending | ForEach-Object {
  Write-Host ("  {0}`t{1}" -f $_.Value, $_.Key)
}
$megaHist.rows | ConvertTo-Json -Depth 4 | Out-File (Join-Path $Audit 'megascans_parent_rows_2026-09-17.json') -Encoding utf8
$megaHist.hist | ConvertTo-Json | Out-File (Join-Path $Audit 'megascans_parent_hist_2026-09-17.json') -Encoding utf8

Write-Host "Brushify parent pass ($($brushMis.Count))..."
$brushHist = Build-Histogram $brushMis
$brushHist.hist.GetEnumerator() | Sort-Object Value -Descending | ForEach-Object {
  Write-Host ("  {0}`t{1}" -f $_.Value, $_.Key)
}
$brushHist.rows | ConvertTo-Json -Depth 4 | Out-File (Join-Path $Audit 'brushify_parent_rows_2026-09-17.json') -Encoding utf8
$brushHist.hist | ConvertTo-Json | Out-File (Join-Path $Audit 'brushify_parent_hist_2026-09-17.json') -Encoding utf8

function Parent-Stem([string]$p) {
  if (-not $p) { return '' }
  ($p -split '/')[-1]
}

$needConvert = @($megaHist.rows | Where-Object {
  $stem = Parent-Stem $_.parent
  ($STOCK_SURFACE + $STOCK_FOLIAGE + $STOCK_DECAL) -contains $stem -or
  ($_.parent -like '/Game/MSPresets/*')
})
$alreadyCustom = @($megaHist.rows | Where-Object { (Parent-Stem $_.parent) -in $CUSTOM_OK -or $_.parent -like '*/Custom_MS_Master/*' -or $_.parent -like '*/Custom_Decal/*' })
$alreadyMelodia = @($megaHist.rows | Where-Object { $_.parent -like '/Game/EnvSandbox/*' -or $_.parent -like '/Game/Melodia/*' })

Write-Host "`nNeed conversion (stock MSPresets/Quixel): $($needConvert.Count)"
Write-Host "Already Custom_MS: $($alreadyCustom.Count)"
Write-Host "Already Melodia/EnvSandbox: $($alreadyMelodia.Count)"

Write-Host '`n==== 4) MEGASCANS BATCH CONVERT ===='
$converted = @()
$failed = @()
if ($Convert) {
  # Prefer Surfaces still on stock
  $batch = @($needConvert | Where-Object { $_.category -eq 'Surfaces' } | Select-Object -First $BatchSize)
  if ($batch.Count -lt $BatchSize) {
    $batch += @($needConvert | Where-Object { $_.category -eq '3D' } | Select-Object -First ($BatchSize - $batch.Count))
  }
  if ($batch.Count -lt $BatchSize) {
    $batch += @($needConvert | Where-Object { $_.category -eq 'Foliage' } | Select-Object -First ($BatchSize - $batch.Count))
  }
  Write-Host "Batch size $($batch.Count) (WhatIf=$WhatIf Convert=$Convert)"
  foreach ($row in $batch) {
    $stem = Parent-Stem $row.parent
    $target = $MS_DEFAULT
    if ($row.category -eq 'Foliage' -or ($STOCK_FOLIAGE -contains $stem)) { $target = $MS_FOLIAGE }
    elseif ($row.category -eq 'Decals' -or ($STOCK_DECAL -contains $stem)) { $target = $MS_DECAL_CNR }

    Write-Host "→ $($row.path)"
    Write-Host "  from $($row.parent)"
    Write-Host "  to   $target"

    if ($WhatIf -and -not $Convert) { continue }
    if ($WhatIf) {
      Write-Host '  (WhatIf — skip mutate; re-run with -Convert -WhatIf:$false)'
      continue
    }

    $before = Invoke-MonolithTool -Name 'material_query' -Arguments @{ action='get_instance_parameters'; asset_path=$row.path }
    $beforeText = Get-MonolithText $before
    $r = Invoke-MonolithTool -Name 'material_query' -Arguments @{
      action = 'set_instance_parent'
      asset_path = $row.path
      parent_path = $target
    }
    $rt = Get-MonolithText $r
    $after = Invoke-MonolithTool -Name 'material_query' -Arguments @{ action='get_instance_parameters'; asset_path=$row.path }
    $val = Invoke-MonolithTool -Name 'material_query' -Arguments @{ action='validate_material'; asset_path=$row.path }
    $ok = ($rt -notlike 'ERROR:*')
    $entry = [pscustomobject]@{
      path = $row.path; from = $row.parent; to = $target; ok = $ok
      set_result = $rt.Substring(0, [Math]::Min(800, $rt.Length))
      validate = (Get-MonolithText $val).Substring(0, [Math]::Min(400, (Get-MonolithText $val).Length))
    }
    if ($ok) { $converted += $entry } else { $failed += $entry }
    Write-Host "  ok=$ok"
  }
} else {
  Write-Host 'Convert skipped (pass -Convert -WhatIf:$false to mutate). Listing candidates:'
  $needConvert | Select-Object -First 20 | ForEach-Object { Write-Host "  $($_.category)`t$($_.path)`t← $($_.parent)" }
}

$summary = [ordered]@{
  stamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss zzz')
  megascans_mi_disk = $megaMis.Count
  brushify_mi_disk = $brushMis.Count
  brushify_m_disk = $brushMs.Count
  greybox_brushify_dirs = @($greyDup + $envGrey | ForEach-Object { $_.FullName })
  need_conversion = $needConvert.Count
  already_custom = $alreadyCustom.Count
  already_melodia = $alreadyMelodia.Count
  converted_count = $converted.Count
  failed_count = $failed.Count
  converted = $converted
  failed = $failed
  megascans_hist = $megaHist.hist
  brushify_hist = $brushHist.hist
}
$summary | ConvertTo-Json -Depth 8 | Out-File (Join-Path $Audit 'IMPORT_MATS_MEGASCANS_BRUSHIFY_LIVE_2026-09-17.json') -Encoding utf8
Write-Host "`nWrote $Audit\IMPORT_MATS_MEGASCANS_BRUSHIFY_LIVE_2026-09-17.json"
Write-Host 'DONE. Owner Ctrl+S any dirty packages. NEVER agent save_packages.'
