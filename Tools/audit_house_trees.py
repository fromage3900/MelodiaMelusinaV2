import bpy, os
blends = ["Saved/MelusinasHouse/House_Greybox.blend","Saved/MelusinasHouse/House_Detailed.blend","Saved/MelusinasHouse/House_Proper.blend","Saved/MelusinasHouse/Melusinas_House_Final_All.blend"]
for b in blends:
    if not os.path.exists(b):
        print(f"MISSING {b}")
        continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=b)
    print(f"===== {b} =====")
    print(f"  objects: {len(bpy.data.objects)} groups: {len(bpy.data.node_groups)} mats: {len(bpy.data.materials)}")
    for o in bpy.data.objects:
        mods = [m.type+':'+(m.node_group.name if m.type=='NODES' and m.node_group else '') for m in o.modifiers] if hasattr(o,'modifiers') else []
        print(f"  OBJ {o.name} mods={mods}")
    for g in bpy.data.node_groups:
        if g.type=='GEOMETRY' or 'GN_MH' in g.name or 'MEL_' in g.name:
            print(f"  TREE {g.name} nodes={len(g.nodes)} in={len(g.interface.items_tree) if hasattr(g,'interface') else '?'}")
