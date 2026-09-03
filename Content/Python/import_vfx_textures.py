"""Import the VFX flipbook/alpha library into the project (record script).

Reads the import manifest from a local temp file and imports every texture
into /Game/_PROJECT/VFX/Textures and /Game/_PROJECT/VFX/Alphas.
Run via Monolith editor_query run_python (or the UE Python console).
"""
import json
import unreal

MANIFEST = r"C:\Users\froma\AppData\Local\Temp\opencode\import_list.json"

entries = json.load(open(MANIFEST, encoding="utf-8"))

tasks = []
for src, dest in entries:
    t = unreal.AssetImportTask()
    t.filename = src
    t.destination_path = dest
    t.automated = True
    t.save = False
    t.replace_existing = True
    tasks.append(t)

tools = unreal.AssetToolsHelpers.get_asset_tools()
tools.import_asset_tasks(tasks)

ok = 0
imported = []
failed = []
for t in tasks:
    paths = t.get_editor_property("imported_object_paths")
    if paths:
        ok += 1
        imported.append(paths[0])
    else:
        failed.append(t.filename)

print(json.dumps({"imported": ok, "total": len(tasks), "paths": imported, "failed": failed}))
