# _cam_check.py — verify the 3-arg viewport camera call in UE 5.8. Read-only (camera move only).
import unreal

lsub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
pos = unreal.Vector(-3000.0, 1500.0, 800.0)
rot = unreal.MathLibrary.find_look_at_rotation(pos, unreal.Vector(-1567.0, 1005.0, 560.0))
ok = None
try:
    lsub.set_level_viewport_camera_info(pos, rot, 'LevelEditorViewport')
    ok = 'ok-key'
except TypeError as e:
    ok = 'TypeError: ' + str(e)
except Exception as e:
    ok = 'ERR: ' + type(e).__name__ + ' ' + str(e)
back = None
try:
    back = lsub.get_level_viewport_camera_info()
except Exception as e:
    back = 'get_err ' + str(e)
print('CC set result:', ok)
print('CC read back:', back)