param([string]$Shots="circlet tiara earrings lineup lineup_real",[int]$Samples=64,[int]$Res=900,[string]$Extra="",[switch]$NoBuild)
$W='C:\EnvironmentPortfolio\_lookdev_work\regalia_v2'; $B='C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'; $I='C:\Users\froma\Documents\lookdev_regalia_v2\_incoming'; $O='C:\Users\froma\Documents\lookdev_regalia_v2\v2b'
New-Item -ItemType Directory -Force $O | Out-Null
Copy-Item "$I\regalia_v2b_*.py" "$W\scripts\" -Force
if(-not $NoBuild){ & $B -b --factory-startup --python "$W\scripts\regalia_v2b_build.py" 2>&1 | Select-String 'Traceback|Error:|File "C:\\Env' | % {"BUILD: "+$_.Line} }
$t=Get-Date
$a=@('-b','--factory-startup',"$W\regalia_v2b.blend",'--python',"$W\scripts\regalia_v2b_render.py",'--') + $Shots.Split(' ') + @('--samples',"$Samples",'--res',"$Res")
if($Extra){ $a += $Extra.Split(' ') }
& $B @a 2>&1 | Select-String 'V2-|Traceback|Error:|File "C:\\Env' | % {$_.Line}
"render secs: $([int]((Get-Date)-$t).TotalSeconds)"
Remove-Item "$O\_renders.zip" -ErrorAction SilentlyContinue; Compress-Archive -Path "$O\*.png" -DestinationPath "$O\_renders.zip" -Force; "ZIPPED"
