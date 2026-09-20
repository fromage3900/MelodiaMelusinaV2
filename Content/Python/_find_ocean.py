
import unreal, json
from pathlib import Path

def lab(a):
    try: return a.get_actor_label() or ""
    except: return ""

def cls(a):
    try: return a.get_class().get_name()
    except: return ""

svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
hits = []
for a in svc.get_all_level_actors():
    L = lab(a); C = cls(a)
    key = (L + " " + C).lower()
    if any(k in key for k in ("ocean", "water", "sea", "lake", "river", "caustics", "wave")):
        hid = False
        try: hid = a.is_temporarily_hidden_in_editor() or a.actor_is_hidden_in_game()
        except: pass
        try:
            o,e = a.get_actor_bounds(False, False)
            ext = float(max(e.x,e.y,e.z)); loc=[o.x,o.y,o.z]
            sc=a.get_actor_scale3d(); sc=[sc.x,sc.y,sc.z]
        except:
            ext=None; loc=None; sc=None
        hits.append({"label":L,"class":C,"hidden":hid,"extent":ext,"loc":loc,"scale":sc})

# also list any actor with Water in mesh path
mesh_hits=[]
for a in svc.get_all_level_actors():
    try:
        for c in a.get_components_by_class(unreal.StaticMeshComponent) or []:
            sm=c.static_mesh
            if not sm: continue
            p=sm.get_path_name().lower()
            if any(k in p for k in ("ocean","water","sea")):
                mesh_hits.append({"label":lab(a),"mesh":sm.get_path_name(),"hidden":a.is_temporarily_hidden_in_editor()})
    except: pass

print("OCEAN_INV", json.dumps({"label_hits":hits,"mesh_hits":mesh_hits}, default=str))
