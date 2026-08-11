# Imports the CC0 _AssetLibrary into /Game/Library as .uasset.
# Run in the editor Python console:  import import_library
# (requires the "Python Editor Script Plugin")
import unreal, os

SRC  = r'G:\EnvironmentPortfolio\_AssetLibrary'
DEST = '/Game/Library'
EXTS = {'png', 'jpg', 'jpeg', 'tga', 'exr', 'hdr', 'obj', 'fbx'}

tools = unreal.AssetToolsHelpers.get_asset_tools()
tasks = []
for root, _dirs, files in os.walk(SRC):
    rel = os.path.relpath(root, SRC).replace('\\', '/')
    dpath = DEST if rel == '.' else f'{DEST}/{rel}'
    for f in files:
        if f.lower().rsplit('.', 1)[-1] in EXTS:
            t = unreal.AssetImportTask()
            t.set_editor_property('filename', os.path.join(root, f))
            t.set_editor_property('destination_path', dpath)
            t.set_editor_property('automated', True)
            t.set_editor_property('save', True)
            t.set_editor_property('replace_existing', True)
            tasks.append(t)

tools.import_asset_tasks(tasks)
unreal.log(f'[Library] imported {len(tasks)} files into {DEST}')
print(f'Imported {len(tasks)} files into {DEST}')
