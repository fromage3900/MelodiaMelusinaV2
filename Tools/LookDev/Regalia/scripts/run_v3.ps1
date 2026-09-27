param([string]$Shots="",[int]$Samples=192,[int]$Res=1600,[string]$Extra="--kick 0.8",[switch]$Build)
$W='C:\EnvironmentPortfolio\_lookdev_work\regalia_v2'; $B='C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'; $I='C:\Users\froma\Documents\lookdev_regalia_v2\_incoming'; $O='C:\Users\froma\Documents\lookdev_regalia_v2\v3'
New-Item -ItemType Directory -Force $O | Out-Null
Copy-Item "$I\regalia_v3_build.py","$I\regalia_v3_render.py" "$W\scripts\" -Force
if($Build){
  if(Test-Path "$W\regalia_v3.blend"){ "V3-BLEND-EXISTS (not rebuilding)" } else {
    & $B -b --factory-startup "$W\regalia_v2d.blend" --python "$W\scripts\regalia_v3_build.py" 2>&1 | Select-String 'V3B|Traceback|Error|File "C:\\Env|line \d' | % { $_.Line.Substring(0,[Math]::Min(8000,$_.Line.Length)) }
  }
}
$t=Get-Date
$a=@('-b','--factory-startup',"$W\regalia_v3.blend",'--python',"$W\scripts\regalia_v3_render.py",'--') + @('--samples',"$Samples",'--res',"$Res") + $Extra.Split(' ')
if($Shots){ $a += $Shots.Split(' ') }
& $B @a 2>&1 | Select-String 'V2-|V3-|Traceback|Error:|File "C:\\Env' | % {$_.Line}
"render secs: $([int]((Get-Date)-$t).TotalSeconds)"
Remove-Item "$O\_renders.zip" -ErrorAction SilentlyContinue; Compress-Archive -Path "$O\*.png" -DestinationPath "$O\_renders.zip" -Force; "ZIPPED"
