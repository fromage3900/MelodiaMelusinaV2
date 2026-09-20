import unreal, json
svc=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
zs=[]
for a in svc.get_all_level_actors():
    L=a.get_actor_label() or ""
    if L.startswith("WC_GreySpire_Helix"):
        zs.append((L, float(a.get_actor_location().z), bool(a.is_temporarily_hidden_in_editor())))
zs.sort(key=lambda x: x[0])
print("HELIX_BEFORE", json.dumps({"n":len(zs),"zmin":min(z[1] for z in zs) if zs else None,"zmax":max(z[1] for z in zs) if zs else None,"hidden":sum(1 for z in zs if z[2]),"sample":zs[:5]+zs[-5:]}, default=str))
