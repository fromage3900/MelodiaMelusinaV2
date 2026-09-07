# Queue one reproducible render job onto origin/render-queue.
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][ValidateSet("Blender","UnrealMRQ")][string]$Mode,
  [Parameter(Mandatory=$true)][string]$JobName,
  [string]$SourceRef="main",
  [string]$Remote="origin",
  [string]$QueueBranch="render-queue",
  [string]$BlendFile="",
  [int]$StartFrame=1,
  [int]$EndFrame=1,
  [ValidateSet("PNG","OPEN_EXR","JPEG")][string]$BlenderFormat="PNG",
  [string]$Map="",
  [string]$LevelSequence="",
  [string]$MoviePipelineConfig="",
  [switch]$DryRun
)
$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot

function G([string[]]$A,[switch]$AllowFailure){
  $o=@(& git -C $Root @A 2>&1 | ForEach-Object {[string]$_})
  $c=if($null -ne $LASTEXITCODE){[int]$LASTEXITCODE}else{0}
  if(-not $AllowFailure -and $c -ne 0){throw "git failed: "+($A -join " ")+" :: "+($o -join " ")}
  return [pscustomobject]@{Code=$c;Lines=$o;Text=($o -join [Environment]::NewLine).Trim()}
}

G @("fetch",$Remote,$SourceRef,$QueueBranch) | Out-Null
$SourceSha=(G @("rev-parse",$Remote+"/"+$SourceRef+"^{commit}")).Text
if($SourceSha -notmatch "^[0-9a-f]{40}$"){throw "Could not resolve source ref."}

$Slug=($JobName.ToLowerInvariant() -replace "[^a-z0-9._-]+","-").Trim("-")
if([string]::IsNullOrWhiteSpace($Slug)){throw "Invalid JobName."}
$JobId=(Get-Date -Format "yyyyMMdd_HHmmssfff")+"_"+$Slug+"_"+$SourceSha.Substring(0,8)

$M=[ordered]@{schema="melodia.render_queue_job.v1";id=$JobId;created_at=(Get-Date).ToString("o");source_ref=$SourceRef;source_sha=$SourceSha;mode=$Mode;job_name=$JobName}

if($Mode -eq "Blender"){
  if([string]::IsNullOrWhiteSpace($BlendFile)){throw "BlendFile required."}
  if([IO.Path]::IsPathRooted($BlendFile) -or $BlendFile.Contains("..")){throw "BlendFile must be repository-relative."}
  if((G @("cat-file","-e",$SourceSha+":"+$BlendFile) -AllowFailure).Code -ne 0){throw "BlendFile is not tracked at source SHA."}
  if($EndFrame -lt $StartFrame){throw "EndFrame must be >= StartFrame."}
  $M.blender=[ordered]@{blend_file=$BlendFile;start_frame=$StartFrame;end_frame=$EndFrame;format=$BlenderFormat}
}else{
  if([string]::IsNullOrWhiteSpace($Map) -or [string]::IsNullOrWhiteSpace($MoviePipelineConfig)){throw "Map and MoviePipelineConfig required."}
  $M.unreal=[ordered]@{map=$Map;level_sequence=$LevelSequence;movie_pipeline_config=$MoviePipelineConfig}
}

$Json=$M|ConvertTo-Json -Depth 8
Write-Host $Json
if($DryRun){exit 0}

$Tmp=Join-Path $env:TEMP ("melodia-render-queue-"+[guid]::NewGuid().ToString("N"))
try{
  G @("worktree","add","--detach",$Tmp,$Remote+"/"+$QueueBranch)|Out-Null
  $Inbox=Join-Path $Tmp "RenderQueue\Inbox"
  New-Item -ItemType Directory -Path $Inbox -Force|Out-Null
  $File=Join-Path $Inbox ($JobId+".json")
  $Json|Set-Content -LiteralPath $File -Encoding UTF8
  & git -C $Tmp add ("RenderQueue/Inbox/"+$JobId+".json")
  if($LASTEXITCODE -ne 0){throw "Queue stage failed."}
  & git -C $Tmp -c user.name="Melodia Render Queue" -c user.email="render-queue@local.invalid" commit -m ("queue(render): "+$JobId)
  if($LASTEXITCODE -ne 0){throw "Queue commit failed."}
  & git -C $Tmp push $Remote ("HEAD:refs/heads/"+$QueueBranch)
  if($LASTEXITCODE -ne 0){throw "Queue push failed; fetch and retry."}
  Write-Host ("Queued "+$JobId) -ForegroundColor Green
}finally{
  & git -C $Root worktree remove --force $Tmp 2>$null|Out-Null
  if(Test-Path $Tmp){Remove-Item $Tmp -Recurse -Force -ErrorAction SilentlyContinue}
}
