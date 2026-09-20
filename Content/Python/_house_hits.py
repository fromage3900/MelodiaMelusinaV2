import unreal, json
svc=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def lab(a):
    try: return a.get_actor_label() or ""
    except: return ""
hits=[]
for a in svc.get_all_level_actors():
    L=lab(a)
    if any(k in L for k in ("wallhi","Wall","House","room","Room","corridor","Corridor","Melusina","SM_wall","floor","Floor","PCG_Melusina")):
        t=a.get_actor_location(); s=a.get_actor_scale3d()
        try:
            o,e=a.get_actor_bounds(False,False)
            mh=max(e.x,e.y)
        except: mh=0
        hits.append({"label":L,"class":a.get_class().get_name(),"loc":[round(t.x,1),round(t.y,1),round(t.z,1)],"scale":[round(s.x,2),round(s.y,2),round(s.z,2)],"max_horiz":round(mh,1)})
hits.sort(key=lambda r: -r["max_horiz"])
print("HITS", json.dumps(hits[:40], default=str))
