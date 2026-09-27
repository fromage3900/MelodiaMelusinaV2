param([string]$Shots="circlet tiara earrings necklace lineup",[int]$Samples=48,[int]$Res=800,[switch]$NoBuild)
$W='C:\EnvironmentPortfolio\_lookdev_work\regalia_v2'; $B='C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'; $O='C:\Users\froma\Documents\lookdev_regalia_v2'
Copy-Item "$O\_incoming\regalia_v2_*.py" "$W\scripts\" -Force
if(-not $NoBuild){ & $B -b --factory-startup --python "$W\scripts\regalia_v2_build.py" 2>&1 | Select-String 'Traceback|Error:|File "C:\\Env' | % {"BUILD: "+$_.Line} }
$t=Get-Date
& $B -b --factory-startup "$W\regalia_v2.blend" --python "$W\scripts\regalia_v2_render.py" -- $Shots.Split(' ') --samples $Samples --res $Res 2>&1 | Select-String 'V2-|Traceback|Error:|File "C:\\Env' | % {$_.Line}
"render secs: $([int]((Get-Date)-$t).TotalSeconds)"
Remove-Item "$O\_renders.zip" -ErrorAction SilentlyContinue; Compress-Archive -Path "$O\*.png" -DestinationPath "$O\_renders.zip" -Force; "ZIPPED"
