import unreal, json
# probe line trace APIs
out = {}
sl = unreal.SystemLibrary
out["sys_trace"] = [m for m in dir(sl) if "trace" in m.lower() or "line" in m.lower()][:40]
if hasattr(unreal, "KismetSystemLibrary"):
    out["kismet_trace"] = [m for m in dir(unreal.KismetSystemLibrary) if "trace" in m.lower()][:40]
out["has_DrawDebugTrace"] = hasattr(unreal, "DrawDebugTrace")
out["has_DrawDebugType"] = hasattr(unreal, "DrawDebugType")
# EditorLoadingAndSavingUtils save_packages signature
els = unreal.EditorLoadingAndSavingUtils
out["save_methods"] = [m for m in dir(els) if "save" in m.lower()][:30]
print("TRACE " + json.dumps(out))
