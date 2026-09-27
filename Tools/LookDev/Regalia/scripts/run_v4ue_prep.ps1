$W='C:\EnvironmentPortfolio\_lookdev_work\regalia_v2'; $B='C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'; $I='C:\Users\froma\Documents\lookdev_regalia_v2\_incoming'
$E="$W\ue_export_v4"; New-Item -ItemType Directory -Force $E | Out-Null
Copy-Item "$I\v4ue_dump_rig.py","$I\v4ue_export_fbx.py" "$W\scripts\" -Force
$src='C:\EnvironmentPortfolio\harp_bow_pipeline\Melusina_Harp_HERO01_ArcherPoseV09_ARP_R09_HotPass.blend'
$m0=(Get-Item $src).LastWriteTime
if(-not (Test-Path "$E\melusina_rig_dump_v4.json")){
  & $B -b --factory-startup --disable-autoexec $src --python "$W\scripts\v4ue_dump_rig.py" 2>&1 | Select-String 'V4UE|Traceback|Error' | % {$_.Line}
}
"src mtime unchanged: $((Get-Item $src).LastWriteTime -eq $m0)"
& $B -b --factory-startup --disable-autoexec "$W\regalia_v4_it2.blend" --python "$W\scripts\v4ue_export_fbx.py" 2>&1 | Select-String 'V4UE|Traceback|Error|line \d' | % {$_.Line}
Get-ChildItem $E | select Name,Length | ft -auto
