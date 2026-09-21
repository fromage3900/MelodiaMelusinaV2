# Closeout audit runner - sequential on purpose.
#
# Two Blender gates at once is the documented crash/mis-compare class (three
# concurrent Blenders on 2026-09-08 cost five crashes and 39 unsaved packages),
# so the audits run one after another and the exit code of each is recorded.
#
# Launched detached because a Blender pass outlives the 30s tool-call budget:
#   Start-Process powershell -ArgumentList '-NoProfile','-ExecutionPolicy',
#     'Bypass','-File','deploy/_closeout_audits.ps1' -WindowStyle Hidden
# Poll for Saved/Audit/closeout_audits.done.

$blender = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
$out = 'Saved\Audit'
New-Item -ItemType Directory -Force -Path $out | Out-Null
Remove-Item "$out\closeout_audits.done" -ErrorAction SilentlyContinue
$lines = @()

# 1. link-failure surface across every registered builder (the silently-dropped
#    link class: a sub-effect miswired while Gate A stays green).
& $blender --background --factory-startup --python deploy/_melodia_health_gn_links.py 2>&1 | Out-File -Encoding utf8 "$out\closeout_gn_links_2026-09-20.log"
$lines += "gn_links=$LASTEXITCODE"

# 2. ladder regression guard (rail tube, option removal, join-error slide).
& $blender --background --factory-startup --python deploy/_melodia_health_paris_ladder.py 2>&1 | Out-File -Encoding utf8 "$out\closeout_ladder_health_2026-09-20.log"
$lines += "ladder_health=$LASTEXITCODE"

# 3. preset library + brand refs (pure Python, no bpy).
python deploy/_melodia_preset_audit.py 2>&1 | Out-File -Encoding utf8 "$out\closeout_preset_audit_2026-09-20.log"
$lines += "preset_audit=$LASTEXITCODE"

$lines | Set-Content "$out\closeout_exit_codes.txt"
"DONE" | Set-Content "$out\closeout_audits.done"
