# Consume queued render jobs on the home PC. One-shot; no daemon.
[CmdletBinding()]
param(
  [string]$Remote="origin",
  [string]$QueueBranch="render-queue",
  [ValidateRange(1,100)][int]$MaxJobs=1,
  [switch]$Execute,
  [switch]$AllowCheckout
)
$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
$Runner=Join-Path $Root "deploy\render_worker.ps1"
$LedgerDir=Join-Path $Root "Saved\RenderFarm"
$LedgerPath=Join-Path $LedgerDir "queue-ledger.json"
New-Item -ItemType Directory -Path $LedgerDir -Force|Out-Null

function G([string[]]$A,[switch]$AllowFailure){
  $o=@(& git -C $Root @A 2>&1 | ForEach-Object {[string]$_})
  $c=if($null -ne $LASTEXITCODE){[int]$LASTEXITCODE}else{0}
  if(-not $AllowFailure -and $c -ne 0){throw "git failed: "+($A -join " ")+" :: "+($o -join " ")}
  return [pscustomobject]@{Code=$c;Lines=$o;Text=($o -join [Environment]::NewLine).Trim()}
}

G @("fetch",$Remote,"main",$QueueBranch)|Out-Null
$Paths=(G @("ls-tree","-r","--name-only",$Remote+"/"+$QueueBranch,"--","RenderQueue/Inbox")).Lines | Where-Object {$_ -match "^RenderQueue/Inbox/.+\.json$"} | Sort-Object

$Ledger=[ordered]@{schema="melodia.render_queue_ledger.v1";jobs=[ordered]@{}}
if(Test-Path $LedgerPath){
  $Loaded=Get-Content $LedgerPath -Raw|ConvertFrom-Json -AsHashtable
  if($Loaded.jobs){$Ledger=$Loaded}
}

$Pending=@()
foreach($P in $Paths){
  $Raw=(G @("show",$Remote+"/"+$QueueBranch+":"+$P)).Text
  $J=$Raw|ConvertFrom-Json
  if($J.id -and -not $Ledger.jobs.ContainsKey([string]$J.id)){$Pending+=$J}
}

if($Pending.Count -eq 0){Write-Host "No pending render jobs." -ForegroundColor Green;exit 0}
$Pending|Select-Object -First $MaxJobs|ForEach-Object{Write-Host ("PENDING "+$_.id+" ["+$_.mode+"] "+$_.source_sha)}

if(-not $Execute){Write-Host "Inspection only. Use -Execute -AllowCheckout in a dedicated clean render clone." -ForegroundColor Yellow;exit 0}
if(@(G @("status","--short")).Lines.Count -gt 0){throw "Worker checkout is dirty."}

$OriginalBranch=(G @("branch","--show-current")).Text
$OriginalHead=(G @("rev-parse","HEAD")).Text

try{
  foreach($J in ($Pending|Select-Object -First $MaxJobs)){
    $Id=[string]$J.id
    $Sha=[string]$J.source_sha
    if((G @("cat-file","-e",$Sha+"^{commit}") -AllowFailure).Code -ne 0){G @("fetch",$Remote,"main")|Out-Null}
    if((G @("cat-file","-e",$Sha+"^{commit}") -AllowFailure).Code -ne 0){$Ledger.jobs[$Id]=[ordered]@{status="failed";error="source SHA unavailable";at=(Get-Date).ToString("o")};continue}
    if((G @("rev-parse","HEAD")).Text -ne $Sha){
      if(-not $AllowCheckout){$Ledger.jobs[$Id]=[ordered]@{status="blocked";error="HEAD differs; use AllowCheckout in dedicated clone";at=(Get-Date).ToString("o")};continue}
      G @("switch","--detach",$Sha)|Out-Null
    }
    try{
      if($J.mode -eq "Blender"){
        $A=@("-NoProfile","-ExecutionPolicy","Bypass","-File",$Runner,"-Mode","Blender","-BlendFile",(Join-Path $Root ([string]$J.blender.blend_file)),"-StartFrame",([string]$J.blender.start_frame),"-EndFrame",([string]$J.blender.end_frame),"-BlenderFormat",([string]$J.blender.format),"-JobName",$Id,"-IConfirmAuthorizedUse","-Execute")
      }else{
        $A=@("-NoProfile","-ExecutionPolicy","Bypass","-File",$Runner,"-Mode","UnrealMRQ","-Map",([string]$J.unreal.map),"-LevelSequence",([string]$J.unreal.level_sequence),"-MoviePipelineConfig",([string]$J.unreal.movie_pipeline_config),"-JobName",$Id,"-IConfirmAuthorizedUse","-Execute")
      }
      & powershell @A
      if($LASTEXITCODE -ne 0){throw "render_worker exit "+$LASTEXITCODE}
      $Ledger.jobs[$Id]=[ordered]@{status="completed";at=(Get-Date).ToString("o");source_sha=$Sha;output=(Join-Path $Root ("Saved\RenderFarm\"+$Id))}
    }catch{
      $Ledger.jobs[$Id]=[ordered]@{status="failed";at=(Get-Date).ToString("o");source_sha=$Sha;error=$_.Exception.Message}
    }finally{
      $Ledger|ConvertTo-Json -Depth 10|Set-Content $LedgerPath -Encoding UTF8
    }
  }
}finally{
  if($AllowCheckout){
    if($OriginalBranch){G @("switch",$OriginalBranch) -AllowFailure|Out-Null}else{G @("switch","--detach",$OriginalHead) -AllowFailure|Out-Null}
  }
}
Write-Host ("Ledger "+$LedgerPath) -ForegroundColor Gray
