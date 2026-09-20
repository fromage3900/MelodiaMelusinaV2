import unreal, json, math
def label(a):
    try: return a.get_actor_label() or ''
    except: return ''
svc=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
islands=[]; pcgs=[]; walks=[]; cams=[]
xs=[]; ys=[]
for a in svc.get_all_level_actors():
    lab=label(a); cn=a.get_class().get_name(); loc=a.get_actor_location()
    xs.append(loc.x); ys.append(loc.y)
    if lab.startswith('BrushifyIsland_'):
        islands.append({'label':lab,'loc':[loc.x,loc.y,loc.z]})
    if cn=='PCGVolume' or 'PCG' in cn:
        # graph?
        g=None
        try:
            comp=a.get_component_by_class(unreal.PCGComponent)
            if comp:
                g=comp.get_editor_property('graph')
                g=g.get_path_name() if g else None
        except Exception as e:
            g=str(e)[:80]
        pcgs.append({'label':lab,'class':cn,'loc':[loc.x,loc.y,loc.z],'graph':g})
    if lab.startswith('WC_EscherWalk_'):
        walks.append({'label':lab,'loc':[loc.x,loc.y,loc.z]})
    if lab.startswith('WC_Lookdev_'):
        cams.append(lab)
# quadrant islands
if xs:
    cx=(min(xs)+max(xs))/2; cy=(min(ys)+max(ys))/2
else:
    cx=cy=0
quads={'NW':[],'NE':[],'SW':[],'SE':[]}
for i in islands:
    x,y=i['loc'][0],i['loc'][1]
    q=('N' if y>=cy else 'S')+('E' if x>=cx else 'W')
    # fix: N is +Y typically in UE
    key=('N' if y>=cy else 'S')+('E' if x>=cx else 'W')
    quads[key].append(i)
print('CORNERMAP', json.dumps({
 'bounds':{'min_x':min(xs),'max_x':max(xs),'min_y':min(ys),'max_y':max(ys),'cx':cx,'cy':cy},
 'islands':islands,
 'quads':{k:v for k,v in quads.items()},
 'pcgs':pcgs,
 'walk_n':len(walks),
 'cams':cams,
}, default=str)[:10000])
