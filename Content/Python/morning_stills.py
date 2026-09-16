import unreal, time

shots = [
    ((750.0, 1650.0, 631.0), (-18.0, -130.0, 0.0)),
    ((300.0, 1400.0, 300.0), (-10.0, 144.0, 0.0)),
]
ok = True
try:
    setcam = unreal.EditorLevelLibrary.set_level_viewport_camera_info
except Exception as e:
    print("VIEWPORT_API_MISSING " + str(e)[:150])
    ok = False
if ok:
    for loc, rot in shots:
        setcam(unreal.Vector(*loc), unreal.Rotator(*rot))
        time.sleep(2)
        unreal.SystemLibrary.execute_console_command(
            unreal.EditorLevelLibrary.get_editor_world(),
            "HighResShot 1")
        time.sleep(6)
print("STILLS_DONE")
