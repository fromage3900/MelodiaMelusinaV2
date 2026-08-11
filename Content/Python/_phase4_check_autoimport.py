import unreal

result = {"ok": False}

# Check AutomatedAssetImportData
try:
    data = unreal.AutomatedAssetImportData()
    # Check settable properties
    for prop in ["group", "filenames", "destination_path", "destination_name", 
                 "replace_existing", "skip_read_only", "factory", "level_to_load"]:
        try:
            data.set_editor_property(prop, None if prop == "factory" else [] if prop in ["filenames"] else 
                                     "/Game/Temp" if prop == "destination_path" else "Test" if prop == "destination_name" else True)
            result[prop] = "settable"
        except Exception as e:
            result[prop] = str(e)[:60]
except Exception as e:
    result["error"] = str(e)[:200]

print(json.dumps(result))
