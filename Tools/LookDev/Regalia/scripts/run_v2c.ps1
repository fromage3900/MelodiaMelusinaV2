param([string]$Shots="earrings lineup_real",[int]$Samples=192,[int]$Res=1600,[string]$Extra="--kick 0.8")
$W='C:\EnvironmentPortfolio\_lookdev_work\regalia_v2'; $B='C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'; $I='C:\Users\froma\Documents\lookdev_regalia_v2\_incoming'; $O='C:\Users\froma\Documents\lookdev_regalia_v2\v2c'
New-Item -ItemType Directory -Force $O | Out-Null
Copy-Item "$I\regalia_v2c_render.py" "$W\scripts\" -Force
$t=Get-Date
$a=@('-b','--factory-startup',"$W\regalia_v2b.blend",'--python',"$W\scripts\regalia_v2c_render.py",'--') + $Shots.Split(' ') + @('--samples',"$Samples",'--res',"$Res") + $Extra.Split(' ')
& $B @a 2>&1 | Select-String 'V2-|Traceback|Error:|File "C:\\Env' | % {$_.Line}
"render secs: $([int]((Get-Date)-$t).TotalSeconds)"
Get-ChildItem $O | % { "$($_.Name) $($_.Length)" }
"DONE"
