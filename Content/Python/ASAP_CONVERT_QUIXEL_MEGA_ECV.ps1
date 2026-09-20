#Requires -Version 5.1
<# ASAP convert: Megascans MI -> Custom_MS; Quixel leftovers; ECV note (masters) #>
param(
  [int]$MegaBatch = 40,
  [switch]$WhatIf
)
$ErrorActionPreference='Stop'
$mcp='http://127.0.0.1:9316/mcp'
$root='C:\EnvironmentPortfolio\BS_GodFile'
$audit=Join-Path $root 'Saved\Audit'
$MS_DEFAULT='/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Default_Overwrite/M_MS_CustomDefault'
$MS_FOLIAGE='/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Foliage_Overwrite/M_MS_CustomFoliage'
$MS_DECAL_CNR='/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_Decal/M_MS_CustomDecal_CNR'
$MS_DECAL_CR='/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_Decal/M_MS_CustomDecal_CR'

function CM($Tool,$Arguments){
  $body=@{jsonrpc='2.0';id=[int](Get-Random -Max 99999);method='tools/call';params=@{name=$Tool;arguments=$Arguments}}|ConvertTo-Json -Depth 30 -Compress
  $r=Invoke-RestMethod -Uri $mcp -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 60
  if($r.error){ throw ($r.error|ConvertTo-Json -Compress) }
  return (($r.result.content|%{$_.text}) -join "`n")
}
function GamePath([IO.FileInfo]$f){
  $rel=$f.FullName.Substring((Join-Path $root 'Content\').Length) -replace '\\','/' -replace '\.uasset$',''
  "/Game/$rel"
}
function Get-Parent($gp){
  $j=CM 'material_query' @{action='get_instance_parameters';params=@{asset_path=$gp}} | ConvertFrom-Json
  return $j.parent
}
function Set-Parent($gp,$parent){
  if($WhatIf){ return @{whatif=$true} }
  return (CM 'material_query' @{action='set_instance_parent';params=@{asset_path=$gp;new_parent=$parent}} | ConvertFrom-Json -EA SilentlyContinue)
}

Write-Host 'Monolith ping...'
$null = CM 'describe_query' @{action='action_schema';target_namespace='material';target_action='set_instance_parent'}
Write-Host 'OK'

$results=[System.Collections.Generic.List[object]]::new()
$mega=@(Get-ChildItem "$root\Content\Megascans" -Recurse -Filter 'MI_*.uasset' -EA SilentlyContinue)
Write-Host "Megascans MI disk=$($mega.Count)"
$n=0
foreach($f in $mega){
  if($n -ge $MegaBatch){ break }
  $gp=GamePath $f
  try {
    $par=Get-Parent $gp
    $short=($par -split '/')[-1] -replace '\..*$',''
    if($short -match 'Custom'){ continue }
    $target=$MS_DEFAULT
    if($gp -match '/Decals/'){ $target = if($short -match 'NoNormal|CNR'){ $MS_DECAL_CNR } else { $MS_DECAL_CR } }
    elseif($gp -match '/Foliage/|/Plants/|/Trees/'){ $target=$MS_FOLIAGE }
    Write-Host ("CONVERT {0} -> {1} | {2}" -f $short, (($target -split '/')[-1]), $gp)
    $null=Set-Parent $gp $target
    $after=Get-Parent $gp
    $ok=((($after -split '/')[-1]) -match 'Custom')
    $results.Add([pscustomobject]@{pack='Megascans';path=$gp;old=$short;neu=(($after -split '/')[-1]);ok=$ok})
    $n++
  } catch {
    $results.Add([pscustomobject]@{pack='Megascans';path=$gp;old='?';neu='ERR';ok=$false;err="$_"})
  }
}

# Quixel leftovers: MI under Content not Megascans that parent to MS_* stock
Write-Host 'Scanning Quixel leftovers...'
$qx=@()
Get-ChildItem "$root\Content" -Recurse -Filter 'MI_*.uasset' -EA SilentlyContinue |
  Where-Object { $_.FullName -notmatch '\\Megascans\\' -and $_.FullName -notmatch '\\Custom\\' -and $_.FullName -notmatch '\\Melodia\\' } |
  Select-Object -First 200 | ForEach-Object {
    $gp=GamePath $_
    try {
      $par=Get-Parent $gp
      $short=($par -split '/')[-1] -replace '\..*$',''
      if($short -match 'M_MS_|MSPresets|Megascans' -and $short -notmatch 'Custom'){
        $qx += [pscustomobject]@{path=$gp;parent=$short}
      }
    } catch {}
  }
Write-Host "Quixel leftover candidates: $($qx.Count)"
foreach($item in $qx | Select-Object -First 30){
  try {
    Write-Host ("QX {0} -> CustomDefault | {1}" -f $item.parent, $item.path)
    $null=Set-Parent $item.path $MS_DEFAULT
    $after=Get-Parent $item.path
    $results.Add([pscustomobject]@{pack='QuixelLeftover';path=$item.path;old=$item.parent;neu=(($after -split '/')[-1]);ok=((($after -split '/')[-1]) -match 'Custom')})
  } catch {
    $results.Add([pscustomobject]@{pack='QuixelLeftover';path=$item.path;old=$item.parent;neu='ERR';ok=$false;err="$_"})
  }
}

# ECV: base materials — create MI wrappers under Melodia/Imported/ECV parenting CustomDefault where textures allow is Phase2
# This pass: inventory + flag (cannot set_instance_parent on UMaterial)
$ecv=@(Get-ChildItem "$root\Content\KitBash_EnchantedVehicles" -Recurse -Filter 'M_*.uasset' -EA SilentlyContinue)
Write-Host "ECV base materials: $($ecv.Count) (wrapper MI creation needs separate pass)"
foreach($f in $ecv){
  $results.Add([pscustomobject]@{pack='EnchantedVehicles';path=(GamePath $f);old='UMaterial';neu='NEEDS_WRAPPER_MI';ok=$false})
}

$out=Join-Path $audit ("ASAP_CONVERT_QUIXEL_MEGA_ECV_{0:yyyy-MM-dd_HHmm}.json" -f (Get-Date))
$results | ConvertTo-Json -Depth 5 | Set-Content $out -Encoding UTF8
$ok=($results|? ok -eq $true).Count
Write-Host "DONE ok=$ok total=$($results.Count) -> $out"
Write-Host 'OWNER: Ctrl+S dirty packages. No Monolith save.'
