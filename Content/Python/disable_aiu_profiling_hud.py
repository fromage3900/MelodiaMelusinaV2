"""Disable profiling / AI logging HUD clutter. Live editor only. No actor deletes."""
import json
import unreal

out = {"issued": [], "cvars_before": {}, "cvars_after": {}}


def issue(cmd, world=None):
    try:
        unreal.SystemLibrary.execute_console_command(world, cmd)
        out["issued"].append({"cmd": cmd, "ok": True, "world": bool(world)})
    except Exception as e:
        out["issued"].append({"cmd": cmd, "ok": False, "err": str(e), "world": bool(world)})


def read_cvar(name):
    try:
        return unreal.SystemLibrary.get_console_variable_int_value(name)
    except Exception:
        try:
            return unreal.SystemLibrary.get_console_variable_float_value(name)
        except Exception as e:
            return "err:" + str(e)


out["engine"] = unreal.SystemLibrary.get_engine_version()
w = None
try:
    w = unreal.EditorLevelLibrary.get_editor_world()
    out["level"] = str(w.get_path_name()) if w else None
except Exception as e:
    out["level_err"] = str(e)

cvars = [
    "ai.EnableAILogging",
    "gc.VerifyAssumptions",
    "gc.VerifyGC",
    "csv.Enabled",
    "fx.Niagara.DebugDrawing",
]
for name in cvars:
    out["cvars_before"][name] = read_cvar(name)

cmds = [
    "stat none",
    "stat stopfile",
    "DisableAILogging",
    "EnableAILogging 0",
    "log LogAI Off",
    "log LogVisualLogger Off",
    "csvprofiler.stop",
    "StopRecordingStats",
    "DisableAllScreenMessages",
    "fx.Niagara.DebugDrawing 0",
    "ShowFlag.Visualize 0",
    "ShowFlag.GameplayDebug 0",
    "ai.EnableAILogging 0",
    "gc.VerifyAssumptions 0",
]
for c in cmds:
    issue(c, None)
if w:
    for c in ["stat none", "stat stopfile", "DisableAILogging", "DisableAllScreenMessages"]:
        issue(c, w)

for name in cvars:
    out["cvars_after"][name] = read_cvar(name)

print("AIU_PROBE:" + json.dumps(out))
