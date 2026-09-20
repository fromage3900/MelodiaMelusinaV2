#Requires -Version 5.1
param([int]$BatchSize=15,[switch]$WhatIf)
$mcp='http://127.0.0.1:9316/mcp'
$MS_DEFAULT='/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Default_Overwrite/M_MS_CustomDefault'
function CM($Tool,$Arguments){
  $body=@{jsonrpc='2.0';id=[int](Get-Random -Max 99999);method='tools/call';params=@{name=$Tool;arguments=$Arguments}}|ConvertTo-Json -Depth 25 -Compress
  $r=Invoke-RestMethod -Uri $mcp -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 90
  if($r.error){throw ($r.error|ConvertTo-Json -Compress)}
  return (($r.result.content|%{$_.text}) -join "`n")
}
$root='C:\EnvironmentPortfolio\BS_GodFile'
$mis=Get-ChildItem "$root\Content\Megascans" -Recurse -Filter 'MI_*.uasset'
$done=0
foreach($f in $mis){
  if($done -ge $BatchSize){break}
  $rel=$f.FullName.Substring("$root\Content\".Length) -replace '\\','/' -replace '\.uasset$',''
  $gp="/Game/$rel"
  $info=CM 'material_query' @{action='get_instance_parameters';params=@{asset_path=$gp}}|ConvertFrom-Json
  $par=($info.parent -split '/')[-1]
  if($par -match 'Custom'){continue}
  if($WhatIf){ Write-Host "WOULD $par -> CustomDefault $gp"; $done++; continue }
  $null=CM 'material_query' @{action='set_instance_parent';params=@{asset_path=$gp;new_parent=$MS_DEFAULT}}
  $after=CM 'material_query' @{action='get_instance_parameters';params=@{asset_path=$gp}}|ConvertFrom-Json
  Write-Host ("{0} -> {1} | {2}" -f $par, (($after.parent -split '/')[-1]), $gp)
  $done++
}
Write-Host "Converted/planned: $done (no save — owner Ctrl+S)"
