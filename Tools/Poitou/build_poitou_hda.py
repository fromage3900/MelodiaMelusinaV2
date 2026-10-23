"""build_poitou.py - hython script: builds poitou_layout_v0.hip(lc) from layout_v0.json and exports UE-ready data.
Usage: hython build_poitou.py [layout_v0.json] [outdir]"""
import hou, json, os, sys, zlib, struct, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
JS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "layout_v0.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "export")
L = json.load(open(JS))
CH = ["village_buildings","canal_banks","wet_meadow_grass","tree_rows_poplar_ash","ruin_rise","mist_marsh_reeds","mist_volume"]
RES = 1009; SP = 1000.0/(RES-1)          # 1009 verts over exactly 1000 m -> 0.99206 m/px
ZSCALE = 25.0                              # UE landscape Z scale -> 1 m = 512 units, range +-64 m

hou.hipFile.clear(suppress_save_prompt=True)
obj = hou.node("/obj"); G = obj.createNode("geo", "poitou_live")
geo = G.createNode("subnet", "poitou_layout_live")
def P(x, y, h=0.0): return (x, h, y)     # layout x=east -> X, layout y=north -> Z
def add_sop(name, pts, closed=False, poly=True):
    n = geo.createNode("add", name)
    n.parm("points").set(len(pts))
    for i, (x, y) in enumerate(pts):
        n.parm("usept%d" % i).set(1); n.parmTuple("pt%d" % i).set(P(x, y))
    if poly:
        n.parm("prims").set(1); n.parm("prim0").set(" ".join(str(i) for i in range(len(pts))))
        n.parm("closed0").set(int(closed))
    return n
def wrangle(name, code, cls=1, inputs=()):
    w = geo.createNode("attribwrangle", name); w.parm("class").set(cls); w.parm("snippet").set(code)
    for i, n in enumerate(inputs): w.setInput(i, n)
    return w
def null(name, src): n = geo.createNode("null", name); n.setInput(0, src); n.setDisplayFlag(False); return n

# ---------- 1. editable input curves ----------
cm = geo.createNode("merge", "merge_canals")
for i, c in enumerate(L["canals"]):
    a = add_sop("CURVE_" + c["name"], [tuple(p) for p in c["points"]])
    for pn, v in [("width", c["width"]), ("depth", c["depth"])]:
        a.addSpareParmTuple(hou.FloatParmTemplate(pn, pn, 1, default_value=(v,)))
    a.addSpareParmTuple(hou.StringParmTemplate("ctype", "type", 1, default_value=(c["type"],)))
    t = wrangle("attr_" + c["name"], 'f@width=ch("../%s/width"); f@depth=ch("../%s/depth"); s@type=chs("../%s/ctype"); s@name="%s";'
                % (a.name(), a.name(), a.name(), c["name"]), cls=1, inputs=[a])
    cm.setInput(i, t)
CANALS = null("IN_CANALS", cm)
r = add_sop("CURVE_route", [tuple(p) for p in L["route"]["points"]])
rw = wrangle("attr_route", 's@name="route"; f@half_width=%g; f@buffer=%g;' % (L["route"]["path_half_width"], L["route"]["buffer"]), 1, [r])
ROUTE = null("IN_ROUTE", rw)
v = add_sop("CURVE_village", [tuple(p) for p in L["zones"]["village"]], closed=True)
VILLAGE = null("IN_VILLAGE", wrangle("attr_village", 's@name="village";', 1, [v]))
lm = add_sop("LANDMARKS", [tuple(p) for p in L["landmarks"].values()], poly=False)
names = list(L["landmarks"].keys())
LANDMARKS = null("IN_LANDMARKS", wrangle("attr_landmarks", 'string n[]={%s}; s@name=n[@ptnum];' % ",".join('"%s"' % s for s in names), 2, [lm]))
rs = L["rise"]
rise = add_sop("RISE_center", [tuple(rs["center"])], poly=False)
RISE_DEF=[("rise_radius", rs["radius"]), ("rise_height", rs["height"]), ("rise_plateau", 50.0)]
for pn, val in [("radius", rs["radius"]), ("height", rs["height"]), ("plateau", 50.0)]:
    rise.addSpareParmTuple(hou.FloatParmTemplate(pn, pn, 1, default_value=(val,))); rise.parm(pn).setExpression('ch("../rise_%s")' % pn)
rise.parm("pt0x").setExpression('ch("../rise_centerx")'); rise.parm("pt0z").setExpression('ch("../rise_centery")')
RISE_C=tuple(rs["center"])
RISE = null("IN_RISE", wrangle("attr_rise", 'f@radius=ch("../RISE_center/radius"); f@height=ch("../RISE_center/height"); f@plateau=ch("../RISE_center/plateau");', 2, [rise]))
zones = geo.createNode("merge", "merge_zones"); zones.setInput(0, VILLAGE); zones.setInput(1, RISE)

# ---------- 2. heightfield + layers ----------
hf = geo.createNode("heightfield", "heightfield_1km")
hf.parm("gridspacing").setExpression('1000/(if(ch("../full_res"),1009,505)-1)'); hf.parm("sizex").setExpression('ch("gridspacing")*if(ch("../full_res"),1009,505)'); hf.parm("sizey").setExpression('ch("sizex")')
hf.parm("tx").set(500); hf.parm("tz").set(500)
last = hf
LAY = CH + ["water", "route_mask", "cd", "flow", "debris", "wetness"] + ["Grass","Ground","Base","Mud","Path","Rock","Water"]
lc = geo.createNode("heightfield_copylayer", "create_mask_layers"); lc.parm("numcopy").set(len(LAY))
for i, c in enumerate(LAY):
    lc.parm("create%d" % (i+1)).set(1); lc.parm("srcname%d" % (i+1)).set("mask"); lc.parm("dstname%d" % (i+1)).set(c)
lc.setInput(0, hf); last = lc

CTRL_DEF=[]
ctrl = geo.createNode("null", "CONTROLS")
for pn, val in [("marsh_base", 0.5), ("marsh_noise", 0.45), ("village_lift", 2.5), ("village_blend", 30.0),
                ("bank_drop", 0.5), ("ditch_spacing", 17.5), ("ditch_warp", 12.0), ("abbey_len", 105.0), ("abbey_wid", 32.0), ("abbey_rot", 20.0), ("ditch_halfw", 1.2), ("ditch_ymax", 420.0), ("ditch_depth", 0.8), ("seed", 1.0)]:
    ctrl.addSpareParmTuple(hou.FloatParmTemplate(pn, pn, 1, default_value=(val,))); ctrl.parm(pn).setExpression('ch("../%s")' % pn); CTRL_DEF.append((pn,val))

VEX = r'''
// inputs: 1 canals, 2 route, 3 village+rise
float x=@P.x, y=@P.z; vector q=set(x,0,y);
float sd=ch("../CONTROLS/seed");
float n1 = fit(noise(set(x,y,sd)/60.0),0.2,0.8,0,1);
float n2 = fit(noise(set(x,y,sd+7)/25.0),0.2,0.8,0,1);
float nz = clamp(0.6*n1+0.4*n2,0,1);
// village (point-in-polygon + edge distance)
int vp = findattribval(3,"prim","name","village"); int pts[] = primpoints(3,vp);
int inside=0; int np=len(pts); float vd=1e9;
for(int i=0,j=np-1;i<np;j=i++){ vector a=point(3,"P",pts[i]), b=point(3,"P",pts[j]);
  if(((a.z>y)!=(b.z>y)) && (x < (b.x-a.x)*(y-a.z)/(b.z-a.z)+a.x)) inside=!inside;
  vector ab=b-a; float t=clamp(dot(q-a,ab)/dot(ab,ab),0,1); vd=min(vd,length(q-(a+t*ab))); }
float vsd = inside ? vd : -vd;   // >0 inside
// rise (first point with radius attr)
vector rc = point(3,"P",npoints(3)-1); float rr=point(3,"radius",npoints(3)-1), rh=point(3,"height",npoints(3)-1), rpl=point(3,"plateau",npoints(3)-1);
float rd = distance(q,set(rc.x,0,rc.z));
// canals
float carve=0, cd=1e9; int water=0; float eN=1e9, dN=0;
for(int pr=0; pr<nprimitives(1); pr++){
  int pp=-1; vector uv; float d = xyzdist(1, itoa(pr), q, pp, uv);
  float w=prim(1,"width",pr)*0.5, dep=prim(1,"depth",pr);
  cd=min(cd,d); if(d<w) water=1; if(d-w<eN){eN=d-w; dN=dep;}
  carve=max(carve, dep*(1-smooth(w*0.4, w+2.5, d)));      // soft slumped bank
}
// ditch grid
// irregular parcels: noise-warped drain lattice, 15-20 m drains, cross drains every ~4 cells, varied
float dsp=ch("../CONTROLS/ditch_spacing"), wp=ch("../CONTROLS/ditch_warp");
float xw = x + wp*(noise(set(x,y,3.1)/45.0)-0.5)*2 + 0.15*y; float yw = y + wp*(noise(set(x,y,9.7)/45.0)-0.5)*2 - 0.1*x;
float dsx = dsp*fit(noise(set(floor(yw/(dsp*4)),5.5,1.1)),0.3,0.7,0.86,1.14);
float dx=min(abs((xw%dsx)-dsx*0.5), abs((yw%(dsp*4))-dsp*2));
int ditch = (dx<ch("../CONTROLS/ditch_halfw")) && (y<ch("../CONTROLS/ditch_ymax"));
carve=max(carve, ch("../CONTROLS/ditch_depth")*(1-smooth(0.3,ch("../CONTROLS/ditch_halfw")+1.0,dx))*(y<ch("../CONTROLS/ditch_ymax")));
// route
int rpp; vector ruv; float pathd = xyzdist(2,q,rpp,ruv);
float rhw=point(2,"half_width",0), rbuf=point(2,"buffer",0);
int path = pathd<rhw;
// height
float h = ch("../CONTROLS/marsh_base") + ch("../CONTROLS/marsh_noise")*(nz-0.5);
h += ch("../CONTROLS/village_lift")*smooth(-5, ch("../CONTROLS/village_blend"), vsd);
float rmask = (1-smooth(rpl, rr, rd));                      // soft slope 140 -> 50 m
h = max(h, h + rh*rmask*(0.92+0.16*n2));
h += 3.0*exp(-pow(distance(q,set(830,0,870))/30.0,2))*rmask; // keep knoll
h -= carve*(1-0.85*rmask);
// iles: low limestone island rises (masked out of canals, village, rise)
{ int nI=chi("../iles_count"); float isd=ch("../iles_seed");
  for(int k=0;k<nI;k++){ float cx=fit01(rand(isd+k*1.37),120,880), cy=fit01(rand(isd+k*7.91+3.3),120,880);
    float r=ch("../iles_radius")*fit01(rand(isd+k*2.31),0.7,1.3); float d=distance(q,set(cx,0,cy));
    float ih=fit01(rand(isd+k*5.13),ch("../iles_hmin"),ch("../iles_hmax"));
    h += ih*(1-smooth(r*0.35,r,d))*(0.85+0.3*n2)*smooth(3,25,cd)*smooth(0,40,-vsd)*(1-rmask); } }
// Maillezais-style abbey footprint pad (105x32 m) on the rise, levelled
float ar=radians(ch("../CONTROLS/abbey_rot")); vector lq=q-set(830,0,870); float ax=abs(lq.x*cos(ar)+lq.z*sin(ar)), az=abs(-lq.x*sin(ar)+lq.z*cos(ar));
float pad = 1-smooth(0, 8, max(ax-ch("../CONTROLS/abbey_len")*0.5, az-ch("../CONTROLS/abbey_wid")*0.5));
h = lerp(h, rh+ch("../CONTROLS/marsh_base")+2.0, pad*rmask);
if(chi("../ign_calib")){
  float hw=chf("../ign_water"), hfld=chf("../ign_field")+chf("../ign_noise")*(2*nz-1);
  float h2=hfld;
  float lev=hw+fit01(nz,chf("../ign_bank_min"),chf("../ign_bank_max"));
  float bk=smooth(-0.5,1.5,eN)*(1-smooth(3.0,12.0,eN));
  h2=lerp(h2,max(h2,lev),bk);
  float dch=ch("../CONTROLS/ditch_depth")*(1-smooth(0.3,ch("../CONTROLS/ditch_halfw")+1.0,dx))*(y<ch("../CONTROLS/ditch_ymax"));
  h2-=dch*(1-rmask);
  h2+=0.4*smooth(-5,ch("../CONTROLS/village_blend"),vsd);
  float rs=smooth(0,1,rmask);
  h2=max(h2,hfld+chf("../ign_rise")*rs*(0.96+0.08*n2));
  h2=lerp(h2,hfld+chf("../ign_rise"),pad*rmask);
  h2=lerp(h2,hw-max(dN,0.6),1-smooth(-1.5,0.0,eN));
  float jet=(x>438&&x<492&&abs(y-478)<16&&eN>0&&eN<5)?1:0;
  h2=lerp(h2,hw+chf("../ign_jetty"),jet);
  h=h2;
}
@height = h;
// masks (mirror gen.py)
int village=inside, rise = rd<rr;
int mist = (x<200) || ((y>900)&&!rise) || ((x+y)<300);
int meadow = (y<425)&&!mist;
float excl = (water||path||pathd<rbuf) ? 0 : 1;
float churchd = distance(q,set(520,0,580));
@village_buildings = excl*clamp(village ? (0.6+0.4*exp(-churchd/90.0)*(cd>6)) : 0,0,1)*(cd>4);
@canal_banks = excl*clamp(exp(-max(cd-3,0)/6.0)*(0.6+0.4*nz),0,1);
@wet_meadow_grass = excl*clamp((meadow||(!village&&!rise&&!mist))*(0.5+0.5*nz)*(!ditch),0,1);
float rows = ((cd>4)&&(cd<9)&&!village&&!rise)*(0.7+0.3*nz) + ((min(abs((xw%(dsx*4))-dsx*2),abs((yw%(dsp*4))-dsp*2))<3)&&meadow&&dx>1.2)*0.8;
@tree_rows_poplar_ash = excl*clamp(rows,0,1);
@ruin_rise = (1-pad)*excl*pow(clamp(1-rd/rr,0,1),0.7)*(0.5+0.5*nz);
float misty = smooth(-30,30, max(max(200-x, (rise ? -200.0 : (y-900))), 300-(x+y)));
@mist_marsh_reeds = excl*clamp(misty*(0.4+0.6*nz)+0.5*exp(-cd/10.0)*mist,0,1);
@mist_volume = ch("../mist_strength")*excl*clamp(smooth(-120,120,max(max(200-x,(rise ? -200.0 : (y-900))),300-(x+y)))*0.8+0.3*exp(-cd/25.0),0,1);
@water = water; @route_mask = pathd<rbuf; @cd = cd;
@mask = @tree_rows_poplar_ash;
'''
vw = geo.createNode("volumewrangle", "BUILD_terrain_and_masks")
vw.parm("snippet").set(VEX)
vw.setInput(0, last); vw.setInput(1, CANALS); vw.setInput(2, ROUTE); vw.setInput(3, zones)
fdw = geo.createNode("volumewrangle", "derive_flow_debris_wetness"); fdw.parm("snippet").set(open(os.path.join(HERE,"snip","fdw.vex")).read()); fdw.setInput(0, vw)
TERRAIN = null("OUT_TERRAIN", fdw); TERRAIN.setDisplayFlag(True); TERRAIN.setRenderFlag(True)

# ---------- 3. scatter preview points ----------
rsm = geo.createNode("resample", "resample_canals_6p5m"); rsm.setInput(0, CANALS)
rsm.parm("length").set(6.5); rsm.parm("dotangentattr").set(1)
POPLAR = wrangle("SCATTER_poplar_rows", open(os.path.join(HERE,"snip","poplar.vex")).read(), 2, [rsm, TERRAIN])
GENERIC = wrangle("SCATTER_channels_preview", r'''
// stochastic jittered-grid preview per channel (keep prob = mask value); NOT final PCG density
string chans[] = {"village_buildings","canal_banks","wet_meadow_grass","ruin_rise","mist_marsh_reeds","tree_rows_poplar_ash"};
string types[] = {"building","reed_bank","meadow_grass_clump","rubble","reed_marsh","parcel_row_tree"};
float  sp[]    = {15.0, 5.0, 10.0, 6.0, 6.0, 6.5};
for(int c=0;c<len(chans);c++){
  float s=sp[c];
  for(float gx=s*0.5; gx<1000; gx+=s) for(float gy=s*0.5; gy<1000; gy+=s){
    vector p=set(gx+(rand(set(gx,gy,c))-0.5)*s*0.8,0,gy+(rand(set(gy,gx,c+5))-0.5)*s*0.8);
    float m=volumesample(1,chans[c],p);
    if(c==5 || c==0) continue;
    if(c==0 && volumesample(1,"cd",p)<6) m=0;
    if(rand(set(gx,gy,c*13))<m){
      int n=addpoint(0,p); setpointattrib(0,"type",n,types[c]);
      float yaw = c==0 ? 90*floor(rand(set(gx,gy,99))*4)+(rand(set(gx,gy,98))-0.5)*12 : rand(set(gx,gy,97))*360;
      if(c==5) yaw=0;
      vector sc = c==0 ? set(fit01(rand(set(gx,gy,1)),9,15), fit01(rand(set(gx,gy,4)),6.5,9), fit01(rand(set(gx,gy,2)),7,10)) : set(1,1,1)*fit01(rand(set(gx,gy,3)),0.8,1.2);
      setpointattrib(0,"yaw",n,yaw); setpointattrib(0,"scale",n,sc);
    }}
}
''', 0, [geo.createNode("null", "empty"), TERRAIN])
ab = wrangle("abbey_and_barques", r'''
// --- Maillezais abbey ruin ------------------------------------------------------
// The abbey is a RUIN, not a box.  The canon footprint is 105 x 32 m, rotated
// abbey_rot degrees on the rise.  The in-theme Maillezais masonry (tufa:
// broken arch, buttress stub, collapsed wall) is instanced as the ruin:
//   * one collapsed nave wall run per 12 m along both long sides,
//   * the broken westwork arch at the west end (13.21 m tall),
//   * a buttress stub every 2 bays along the nave (the bay is 2.4 m),
//   * the footprint point itself, kept so the in-theme gate can assert the
//     abbey is in the level at all.
float ar = radians(chf("../CONTROLS/abbey_rot"));
vector ac = set(830,0,870);
float AL = chf("../CONTROLS/abbey_len"), AW = chf("../CONTROLS/abbey_wid");
vector ax = set(cos(ar),0,sin(ar));   // along the nave
vector az = set(-sin(ar),0,cos(ar));  // across the nave

int n=addpoint(0,ac); setpointattrib(0,"type",n,"abbey_maillezais_footprint"); setpointattrib(0,"yaw",n,ar*180/PI);
setpointattrib(0,"scale",n,set(8.45,13.21,1.82)); setpointattrib(0,"height_m",n,13.21);

// collapsed nave walls: 12 m runs stepped along both long sides
float RUN = 12.0; int NRUN = max(1, int(AL/RUN));
for(int side=0; side<2; side++){
  float sgn = side==0 ? -1.0 : 1.0;
  for(int i=0; i<NRUN; i++){
    float u = (i+0.5)*AL/NRUN - AL*0.5;
    vector p = ac + ax*u + az*(sgn*AW*0.5);
    int w=addpoint(0,p); setpointattrib(0,"type",w,"abbey_maillezais_wall");
    setpointattrib(0,"yaw",w,ar*180/PI + (rand(set(i,side,3))-0.5)*6.0);
    setpointattrib(0,"scale",w,set(AL/NRUN,6.0,1.27)); }
}
// westwork: the broken arch at the west end, facing down the nave
int w1=addpoint(0, ac - ax*(AL*0.5));
setpointattrib(0,"type",w1,"abbey_maillezais_footprint"); setpointattrib(0,"yaw",w1,ar*180/PI);
setpointattrib(0,"scale",w1,set(8.45,13.21,1.82)); setpointattrib(0,"height_m",w1,13.21);
// buttress stubs every 2 bays along the south wall
int NB = 14; for(int i=0; i<NB; i++){
  float u = (i+0.5)*AL/NB - AL*0.5;
  vector p = ac + ax*u + az*(-AW*0.5 + 1.6);
  int bt=addpoint(0,p); setpointattrib(0,"type",bt,"abbey_maillezais_buttress");
  setpointattrib(0,"yaw",bt,ar*180/PI);
  setpointattrib(0,"scale",bt,set(1.62,9.69,2.27)); setpointattrib(0,"height_m",bt,9.69); }
// barques (4.6 x 1.55 m) moored at Grand Port along the bief
for(int i=0;i<6;i++){ vector p=set(445+i*7.5,0,470+0.17*(i*7.5-25)+8.2); int b=addpoint(0,p); setpointattrib(0,"type",b,"barque");
  setpointattrib(0,"yaw",b,10.0); setpointattrib(0,"scale",b,set(4.6,0.5,1.55)); }
''', 0, [geo.createNode("null","empty2")])
VIL = wrangle("SCATTER_village_lanes", open(os.path.join(HERE,"snip","village.vex")).read(), 0, [geo.createNode("null","empty_v"), TERRAIN, CANALS, ROUTE])
pm = geo.createNode("merge", "merge_points"); pm.setInput(0, POPLAR); pm.setInput(1, GENERIC); pm.setInput(2, ab); pm.setInput(3, VIL)
SNAP = wrangle("snap_to_terrain", '@P.y = volumesample(1,"height",@P);', 2, [pm, TERRAIN])
POINTS = null("OUT_POINTS_PCG", SNAP)

# ================= HDA wrapping =================
import time
def has_in(i): return 'hou.pwd().parent().inputs()[%d] is not None if len(hou.pwd().parent().inputs())>%d else 0' % (i, i)
# input 0 = canal curves (from UE), input 1 = route curve (from UE)
for idx, (nullname, defaults_vex) in enumerate([
    ("IN_CANALS", 'if(f@width<=0) f@width=chf("../ue_canal_width"); if(f@depth<=0) f@depth=chf("../ue_canal_depth"); if(s@type=="") s@type="bief"; if(s@name=="") s@name=sprintf("ue_canal_%d",@primnum);'),
    ("IN_ROUTE", 's@name="route"; if(f@half_width<=0) f@half_width=%g; if(f@buffer<=0) f@buffer=%g;' % (L["route"]["path_half_width"], L["route"]["buffer"]))]):
    nn = geo.node(nullname); internal = nn.inputs()[0]
    ind = geo.indirectInputs()[idx]
    ue = geo.createNode("attribwrangle", "ue_in%d_defaults" % idx); ue.parm("class").set(1); ue.parm("snippet").set(defaults_vex); ue.setInput(0, ind)
    sw = geo.createNode("switch", "SW_in%d_use_ue_curve" % idx); sw.setInput(0, internal); sw.setInput(1, ue)
    sw.parm("input").setExpression('int(ch("../use_ue_input%d") and (%s))' % (idx, has_in(idx)), hou.exprLanguage.Python if False else hou.exprLanguage.Hscript)
    sw.parm("input").setExpression('int(hou.pwd().parent().evalParm("use_ue_input%d") and (%s))' % (idx, has_in(idx)), hou.exprLanguage.Python)
    if idx == 0:
        sn = geo.createNode("attribwrangle", "snap_canal_width_2p4"); sn.parm("class").set(1); sn.parm("snippet").set('if(chi("../snap_canals")) { f@width = max(2.4, rint(f@width/2.4)*2.4); if(s@type=="bief") f@width = max(f@width, 19.2); }'); sn.setInput(0, sw); sw = sn
    nn.setInput(0, sw)

TERRAIN = geo.node("OUT_TERRAIN"); POINTS = geo.node("OUT_POINTS_PCG"); ROUTE = geo.node("IN_ROUTE")
# --- output 0: landscape heightfield (drop helper volumes) ---
bl = geo.createNode("blast", "drop_helper_layers"); bl.setInput(0, TERRAIN)
bl.parm("group").set("@name=cd @name=mask"); bl.parm("grouptype").set(4) if False else None
rmp = geo.createNode("volumewrangle", "NIKKI_layer_remap"); rmp.setInput(0, bl)
rmp.parm("snippet").set('@Grass=max(max(@wet_meadow_grass,@tree_rows_poplar_ash),@village_buildings); @Mud=max(@canal_banks,@flow); @Path=@mist_marsh_reeds; @Rock=max(@ruin_rise,@debris); @Water=@water; @Ground=1; @Base=1;')
bOld = geo.createNode("blast", "drop_old_layers"); bOld.setInput(0, rmp); bOld.parm("group").set("@name=village_buildings @name=canal_banks @name=wet_meadow_grass @name=tree_rows_poplar_ash @name=ruin_rise @name=mist_marsh_reeds @name=mist_volume @name=water @name=route_mask @name=flow @name=debris")
bNew = geo.createNode("blast", "drop_nikki_layers"); bNew.setInput(0, bl); bNew.parm("group").set("@name=Grass @name=Ground @name=Base @name=Mud @name=Path @name=Rock @name=Water")
swl = geo.createNode("switch", "SW_nikki_layers"); swl.setInput(0, bNew); swl.setInput(1, bOld); swl.parm("input").setExpression('ch("../nikki_layers")')
lscape = wrangle("landscape_tags", open(os.path.join(HERE,"snip","lscape.vex")).read(), 1, [swl])
o0 = geo.createNode("output", "output_landscape"); o0.parm("outputidx").set(0); o0.setInput(0, lscape)
# --- output 1: instancing points (placeholder engine meshes, attrs kept for PCG) ---
_S = lambda n: open(os.path.join(HERE, "snip", n)).read()
HZ = wrangle("HORIZON_bands_spires", _S("skf.vex") + _S("hz.vex"), 0, [geo.createNode("null","empty3")])
PM2 = geo.createNode("merge","merge_core_horizon"); PM2.setInput(0, POINTS); PM2.setInput(1, HZ)
inst = wrangle("unreal_instance_placeholders", _S("inst.vex"), 2, [PM2])
o1 = geo.createNode("output", "output_points"); o1.parm("outputidx").set(1); o1.setInput(0, inst)
# --- output 2: route curve ---
rr_ = geo.createNode("resample", "route_resample_5m"); rr_.setInput(0, ROUTE); rr_.parm("length").set(5.0)
dr = wrangle("route_drape", '@P.y = volumesample(1,"height",@P)+0.05; if(@ptnum==0) for(int i=0;i<nprimitives(0);i++) setprimattrib(0,"unreal_output_curve",i,1);', 2, [rr_, TERRAIN])
o2 = geo.createNode("output", "output_route_curve"); o2.parm("outputidx").set(2); o2.setInput(0, dr)
S = lambda n: open(os.path.join(HERE, "snip", n)).read()
sk = geo.createNode("grid","skirt_grid"); sk.parm("sizex").setExpression('ch("../skirt_extent")'); sk.parm("sizey").setExpression('ch("../skirt_extent")')
sk.parm("tx").set(500); sk.parm("tz").set(500); sk.parm("rows").setExpression('int(ch("../skirt_extent")/50)+1'); sk.parm("cols").setExpression('int(ch("../skirt_extent")/50)+1')
skh = wrangle("skirt_swells", S("skf.vex") + '@P.y = skirt_h(@P.x,@P.z);', 2, [sk])
skd = wrangle("skirt_cut_core", S("skcut.vex"), 1, [skh])
o3 = geo.createNode("output", "output_skirt_mesh"); o3.parm("outputidx").set(3); o3.setInput(0, skd)
wg = geo.createNode("grid","water_grid"); wg.parm("sizex").set(1000); wg.parm("sizey").set(1000); wg.parm("tx").set(500); wg.parm("tz").set(500)
wg.parm("rows").setExpression('int(1000/ch("../water_res"))+1'); wg.parm("cols").setExpression('int(1000/ch("../water_res"))+1')
ww = wrangle("water_cut", 'int pts[]=primpoints(0,@primnum); vector m={0,0,0}; foreach(int p;pts) m+=point(0,"P",p); m/=len(pts); float r=ch("../water_res"); if(volumesample(1,"cd",m)>prim(2,"width",0)*0+r*0.75+volumesample(1,"cd",m)*0 && volumesample(1,"water",m)<0.5 && volumesample(1,"cd",m)>r*0.9) removeprim(0,@primnum,1); else s@unreal_material=chs("../water_material");', 1, [wg, TERRAIN])
wl = wrangle("water_level", '@P.y = chi("../ign_calib") ? ch("../ign_water") : ch("../marsh_base") - ch("../water_drop");', 2, [ww])
o4 = geo.createNode("output", "output_water"); o4.parm("outputidx").set(4); o4.setInput(0, wl)
# --- output 5: GENERATED masonry (canal revetment, coursed ashlar) ---
# This is geometry the HDA BUILDS, not meshes it places: every stone of the
# canal revetment is generated on the French-Romanesque grammar (0.6 m
# module, 0.6 m course, staggered joints, chaine/arase band every 3
# courses, 0.45 m ashlar leaf over a 0.9 m rubble core, refend base).
rc = geo.createNode("resample", "revetment_resample"); rc.setInput(0, CANALS); rc.parm("length").set(0.6)
rv = wrangle("REVETMENT_coursed_ashlar", _S("kit.vex") + _S("revet.vex"), 0, [rc, TERRAIN])
o5 = geo.createNode("output", "output_masonry"); o5.parm("outputidx").set(5); o5.setInput(0, rv)

# --- output 6: the GENERATED element set, all off the SAME kit ------------
# snip/kit.vex is the shared masonry grammar (0.6 m module and course,
# 2.4 m bay, ashlar leaf over rubble core, chaine/arase bands, refends,
# arches, vertex paint).  Every generator includes it, so the canal
# revetment, the abbey, the foundations, the lanes, the crossings, the
# roofs and the poplars are the SAME building system, not seven styles.
#
# They ship as ONE output, not seven: the UE-side Houdini Engine asset
# would otherwise need a new output slot per generator (and the editor is
# not ours to touch), and one merged output keeps the element set as one
# assembly - which is how the level is actually dressed.  The elements are
# told apart by prim group and by their material.
_KIT = _S("kit.vex")
ab_g = wrangle("ABBEY_maillezais", _KIT + _S("abbey.vex"), 0, [geo.createNode("null", "empty_abbey"), TERRAIN])
fd_g = wrangle("FOUNDATIONS_soubassement", _KIT + _S("found.vex"), 0, [POINTS, TERRAIN])
ln_g = wrangle("LANES_ribbons", _KIT + _S("lane.vex"), 0, [POINTS, TERRAIN])
cr_res = geo.createNode("resample", "crossing_resample"); cr_res.setInput(0, CANALS); cr_res.parm("length").set(2.0)
cr_g = wrangle("CROSSINGS_bridges", _KIT + _S("cross.vex"), 0, [cr_res, TERRAIN, POINTS])
rf_g = wrangle("ROOFS_tiles", _KIT + _S("roof.vex"), 0, [POINTS, TERRAIN])
pl_g = wrangle("POPLAR_columnar", _KIT + _S("poplar_gen.vex"), 0, [POINTS, TERRAIN])
lk_g = wrangle("LOCK_chamber_steps", _KIT + _S("lock.vex"), 0, [rc, TERRAIN])
# piano numbering runs downstream: lock.vex only READS its inputs, so the
# group query must happen here, on the lock's completed output
lk_keys = wrangle("LOCK_piano_keys", r'''
{
    int keys[] = expandprimgroup(0, "lock_steps");
    int per = 6;
    int base = chi("../lock_step_note_base");
    for(int k=0;k<len(keys);k++){
        setprimattrib(0, "note", keys[k], base + k/per);
        setprimattrib(0, "piano_key", keys[k], 1);
    }
}
''', 0, [lk_g])
col_g = wrangle("COLLISION_proxies", _KIT + _S("collision.vex"), 0, [POINTS, TERRAIN])
o7 = geo.createNode("output", "output_collision"); o7.parm("outputidx").set(7); o7.setInput(0, col_g)
gen = geo.createNode("merge", "merge_generated_elements")
for _i, _n in enumerate([ab_g, fd_g, ln_g, cr_g, rf_g, pl_g, lk_keys]):
    gen.setInput(_i, _n)
o6 = geo.createNode("output", "output_generated"); o6.parm("outputidx").set(6); o6.setInput(0, gen)
los = wrangle("abbey_sightline", r"""
vector e=@P+{0,1.7,0}; vector a=set(830, volumesample(1,"height",{830,0,870})+12, 870); int ok=1;
for(float k=0.02;k<0.98;k+=0.01){ vector s=lerp(e,a,k); if(volumesample(1,"height",s)>s.y){ ok=0; break; } }
i@abbey_los=ok; """, 2, [dr, TERRAIN])
o2.setInput(0, los)

o0.setDisplayFlag(True)

geo.layoutChildren()

# --- create HDA ---
HDADIR = os.path.join(HERE, "hda"); os.makedirs(HDADIR, exist_ok=True)
ext = ".hdalc" if hou.licenseCategory() == hou.licenseCategoryType.Indie else ".hda"
hpath = os.path.join(HDADIR, "poitou_layout_live" + ext).replace("\\", "/")
hda = geo.createDigitalAsset(name="poitou_layout_live_v6", hda_file_name=hpath, description="Poitou Layout Live", min_num_inputs=0, max_num_inputs=2, version="1.0")
d = hda.type().definition()
ptg = d.parmTemplateGroup()
F = hou.FolderParmTemplate
f_live = F("f_live", "Live iteration", folder_type=hou.folderType.Tabs)
f_live.addParmTemplate(hou.ToggleParmTemplate("full_res", "Full res heightfield (1009, else 505)", default_value=False))
f_live.addParmTemplate(hou.ToggleParmTemplate("nikki_layers", "Nikki master layers (Grass/Ground/Base/Mud/Path/Rock/Water)", default_value=True))
f_live.addParmTemplate(hou.ToggleParmTemplate("ign_calib", "IGN RGE ALTI calibration", default_value=True))
for _pn,_lab,_v in [("ign_field","Field level (m)",2.05),("ign_noise","Field noise +- (m)",0.1),("ign_water","Water level (m)",1.7),("ign_bank_min","Bank min above water (m)",0.8),("ign_bank_max","Bank max above water (m)",1.4),("ign_rise","Abbey rise above fields (m)",11.0),("ign_jetty","Jetty stage above water (m)",0.45)]:
    f_live.addParmTemplate(hou.FloatParmTemplate(_pn,_lab,1,default_value=(_v,)))
f_live.addParmTemplate(hou.ToggleParmTemplate("instance_preview", "Placeholder unreal_instance meshes", default_value=True))
f_live.addParmTemplate(hou.ToggleParmTemplate("use_ue_input0", "Use UE canal curves (input 1) if connected", default_value=True))
f_live.addParmTemplate(hou.ToggleParmTemplate("use_ue_input1", "Use UE route curve (input 2) if connected", default_value=True))
f_live.addParmTemplate(hou.FloatParmTemplate("shell_cluster_radius", "Remove placeholder buildings within R of church (room shells there)", 1, default_value=(21.0,)))
f_live.addParmTemplate(hou.FloatParmTemplate("ue_canal_width", "UE canal default width (m)", 1, default_value=(6.0,)))
f_live.addParmTemplate(hou.FloatParmTemplate("ue_canal_depth", "UE canal default depth (m)", 1, default_value=(1.2,)))
f_ctl = F("f_ctl", "Terrain controls", folder_type=hou.folderType.Tabs)
for pn, val in CTRL_DEF:
    f_ctl.addParmTemplate(hou.FloatParmTemplate(pn, pn.replace("_", " ").title(), 1, default_value=(val,)))
f_rise = F("f_rise", "Rise / abbey", folder_type=hou.folderType.Tabs)
f_rise.addParmTemplate(hou.FloatParmTemplate("rise_centerx", "Rise centre X (m)", 1, default_value=(RISE_C[0],)))
f_rise.addParmTemplate(hou.FloatParmTemplate("rise_centery", "Rise centre Y/north (m)", 1, default_value=(RISE_C[1],)))
for pn, val in RISE_DEF:
    f_rise.addParmTemplate(hou.FloatParmTemplate(pn, pn.replace("_", " ").title(), 1, default_value=(val,)))
f_live.addParmTemplate(hou.ToggleParmTemplate("real_meshes", "Use project meshes (else BasicShapes)", default_value=True))
f_live.addParmTemplate(hou.StringParmTemplate("landscape_material", "Landscape material", 1, default_value=("/Game/EnvSandbox/Poitou/Materials/MI_Poitou_Landscape_Nikki.MI_Poitou_Landscape_Nikki",)))
f_live.addParmTemplate(hou.StringParmTemplate("layerinfo_dir", "LayerInfo folder", 1, default_value=("/Game/EnvSandbox/Poitou/LayerInfo",)))
f_iles = F("f_iles", "Iles", folder_type=hou.folderType.Tabs)
f_iles.addParmTemplate(hou.IntParmTemplate("iles_count", "Island count", 1, default_value=(4,), min=0, max=6))
for pn, lab, v in [("iles_seed","Island seed",3.0),("iles_radius","Island radius (m)",70.0),("iles_hmin","Island min height (m)",4.0),("iles_hmax","Island max height (m)",12.0)]:
    f_iles.addParmTemplate(hou.FloatParmTemplate(pn, lab, 1, default_value=(v,)))
f_v = F("f_v", "Village / rows / water", folder_type=hou.folderType.Tabs)
f_v.addParmTemplate(hou.FloatParmTemplate("lane_spacing", "Village lane house spacing (m)", 1, default_value=(12.0,)))
f_v.addParmTemplate(hou.IntParmTemplate("radial_lanes", "Radial lanes from church", 1, default_value=(5,), min=0, max=8))
f_v.addParmTemplate(hou.FloatParmTemplate("row_gap", "Tree row gap fraction", 1, default_value=(0.15,)))
f_v.addParmTemplate(hou.FloatParmTemplate("flow_slope_gain", "Flow mask slope gain", 1, default_value=(4.0,)))
f_v.addParmTemplate(hou.ToggleParmTemplate("snap_canals", "Snap canal widths to 2.4 m", default_value=True))
f_v.addParmTemplate(hou.FloatParmTemplate("water_res", "Water mesh cell (m)", 1, default_value=(2.0,)))
f_v.addParmTemplate(hou.FloatParmTemplate("water_drop", "Water level below marsh base (m)", 1, default_value=(0.25,)))
f_v.addParmTemplate(hou.StringParmTemplate("water_material", "Water material", 1, default_value=("/Game/EnvSandbox/Materials/Instances/Water/v10/Integrated/MI_WaterV10_Integrated_CalmPond.MI_WaterV10_Integrated_CalmPond",)))
f_hz = F("f_hz", "Horizon", folder_type=hou.folderType.Tabs)
f_hz.addParmTemplate(hou.ToggleParmTemplate("horizon_on", "Horizon ring + bands", default_value=True))
for pn, lab, v in [("skirt_extent","Skirt extent (m, square)",6000.0),("swell_amp","Swell max height (m)",10.0),("swell_ramp","Swell ramp distance (m)",1500.0),("swell_freq","Swell noise freq",0.0012),
                   ("band0_dist","Band 0 radius (m)",1300.0),("band1_dist","Band 1 radius (m)",1900.0),("band2_dist","Band 2 radius (m)",2600.0),("band_spacing","Band tree spacing (m)",9.0),("band_gap","Band gap threshold",0.45),
                   ("spire_dist","Far spire radius (m)",2300.0),("spire_angle","Far spire angle (deg)",35.0),("spire_height","Far spire height (m)",40.0),("mist_strength","Mist mask strength",1.0)]:
    f_hz.addParmTemplate(hou.FloatParmTemplate(pn, lab, 1, default_value=(v,)))
f_hz.addParmTemplate(hou.IntParmTemplate("spire_count", "Far spires", 1, default_value=(2,), min=0, max=3))
f_hz.addParmTemplate(hou.StringParmTemplate("skirt_material", "Skirt material", 1, default_value=("/Game/EnvSandbox/Poitou/Materials/MI_Poitou_FarStone.MI_Poitou_FarStone",)))
# --- generated masonry (canal revetment) ---
f_mas = F("f_mas", "Generated masonry", folder_type=hou.folderType.Tabs)
f_mas.addParmTemplate(hou.ToggleParmTemplate("revetment_on", "Generate the canal revetment", default_value=True))
f_mas.addParmTemplate(hou.FloatParmTemplate("revetment_bed_drop", "Bed below the water line (m)", 1, default_value=(0.6,)))
f_mas.addParmTemplate(hou.FloatParmTemplate("revetment_min_height", "Minimum revetment height (m)", 1, default_value=(0.9,)))
f_mas.addParmTemplate(hou.FloatParmTemplate("revetment_max_height", "Maximum revetment height (m)", 1, default_value=(2.4,)))
f_mas.addParmTemplate(hou.FloatParmTemplate("revetment_barrier_height", "Central barrier height (m)", 1, default_value=(0.45,)))
f_mas.addParmTemplate(hou.StringParmTemplate("masonry_ashlar_material", "Ashlar facing material", 1, default_value=("/Game/Melodia/Meshes/Poitou/M_Tufa_Stone_Blocks.M_Tufa_Stone_Blocks",)))
f_mas.addParmTemplate(hou.StringParmTemplate("masonry_core_material", "Rubble core material", 1, default_value=("/Game/Melodia/Meshes/Poitou/M_Limestone_Rubble_Core.M_Limestone_Rubble_Core",)))
f_mas.addParmTemplate(hou.StringParmTemplate("masonry_band_material", "Chaine / arase band material", 1, default_value=("/Game/EnvSandbox/Poitou/Materials/MI_Poitou_Arase_Brick.MI_Poitou_Arase_Brick",)))
f_mas.addParmTemplate(hou.StringParmTemplate("masonry_roof_material", "Roof tile material", 1, default_value=("/Game/EnvSandbox/Poitou/Materials/MI_Poitou_Tile.MI_Poitou_Tile",)))
f_mas.addParmTemplate(hou.StringParmTemplate("foundation_material", "Foundation / plinth material", 1, default_value=("/Game/Melodia/Meshes/Poitou/M_Poitou_Stone_Plinth.M_Poitou_Stone_Plinth",)))
f_mas.addParmTemplate(hou.StringParmTemplate("lane_material", "Lane surface material", 1, default_value=("/Game/EnvSandbox/Poitou/Materials/MI_Poitou_Ruin_Limestone.MI_Poitou_Ruin_Limestone",)))
f_mas.addParmTemplate(hou.StringParmTemplate("roof_material", "Village roof material", 1, default_value=("/Game/EnvSandbox/Poitou/Materials/MI_Poitou_Tile.MI_Poitou_Tile",)))
f_mas.addParmTemplate(hou.StringParmTemplate("poplar_bark_material", "Poplar bark material", 1, default_value=("/Game/Melodia/Meshes/Poitou/M_Ash_Bark.M_Ash_Bark",)))
f_mas.addParmTemplate(hou.StringParmTemplate("poplar_foliage_material", "Poplar foliage material", 1, default_value=("/Game/EnvSandbox/Poitou/Materials/MI_Poitou_Poplar_Band1.MI_Poitou_Poplar_Band1",)))
f_mas.addParmTemplate(hou.FloatParmTemplate("lane_length", "Village lane length (m)", 1, default_value=(160.0,)))
# --- the Maillezais abbey (the canon's landmark) ---
f_mas.addParmTemplate(hou.IntParmTemplate("abbey_bays", "Abbey nave bays", 1, default_value=(7,), min=1, max=24))
f_mas.addParmTemplate(hou.FloatParmTemplate("abbey_bay_length", "Abbey bay length (m)", 1, default_value=(2.4,)))
f_mas.addParmTemplate(hou.FloatParmTemplate("abbey_nave_width", "Abbey nave width (m)", 1, default_value=(14.4,)))
f_mas.addParmTemplate(hou.FloatParmTemplate("abbey_wall_height", "Abbey wall height (m)", 1, default_value=(13.2,)))
f_mas.addParmTemplate(hou.FloatParmTemplate("abbey_gallery_height", "Abbey gallery sill (m)", 1, default_value=(7.2,)))
f_mas.addParmTemplate(hou.FloatParmTemplate("abbey_westwork_height", "Abbey westwork height (m)", 1, default_value=(15.6,)))
f_mas.addParmTemplate(hou.FloatParmTemplate("abbey_portal_span", "Abbey portal span (m)", 1, default_value=(3.6,)))
# --- the pound lock (Jev gap: lockhouse/jetty/steps; triangle: traversal)
f_lock = F("f_lock", "Lock / jetty / steps", folder_type=hou.folderType.Tabs)
f_lock.addParmTemplate(hou.ToggleParmTemplate("lock_on", "Generate the lock", default_value=True))
f_lock.addParmTemplate(hou.FloatParmTemplate("lock_u", "Lock position along bief (0..1)", 1, default_value=(0.35,), min=0.0, max=1.0))
f_lock.addParmTemplate(hou.FloatParmTemplate("lock_chamber_l", "Lock chamber length (m)", 1, default_value=(19.2,), min=9.6, max=28.8))
f_lock.addParmTemplate(hou.FloatParmTemplate("lock_coping_h", "Coping above bank (m)", 1, default_value=(0.3,)))
f_lock.addParmTemplate(hou.MenuParmTemplate("lock_gate_style", "Gate leaves", ("Timber mitre (Marais)", "Stone slab"), default_value=0))
f_lock.addParmTemplate(hou.IntParmTemplate("lock_steps_n", "Piano steps (treads)", 1, default_value=(7,), min=1, max=12))
f_lock.addParmTemplate(hou.IntParmTemplate("lock_step_note_base", "Step scale root (degrees)", 1, default_value=(0,), min=0, max=6))
f_lock.addParmTemplate(hou.FloatParmTemplate("jetty_len", "Jetty length (m)", 1, default_value=(7.2,)))
f_lock.addParmTemplate(hou.FloatParmTemplate("jetty_wid", "Jetty width (m)", 1, default_value=(2.4,)))
f_lock.addParmTemplate(hou.MenuParmTemplate("lockhouse_style", "Lockhouse", ("Stone + tile (abbey era)", "Timber + lime (maraichin era)"), default_value=0))
f_lock.addParmTemplate(hou.FloatParmTemplate("lock_ornament", "Ornament scale (Nikki 1.3-1.5x)", 1, default_value=(1.4,), min=1.0, max=2.0))
f_lock.addParmTemplate(hou.ToggleParmTemplate("lock_lamp", "Lamp finial at mid-chamber", default_value=True))
f_lock.addParmTemplate(hou.ToggleParmTemplate("lock_bridge", "Footbridge over the lock tail", default_value=True))
for f in (f_live, f_ctl, f_rise, f_iles, f_v, f_hz, f_mas, f_lock): ptg.append(f)

d.setParmTemplateGroup(ptg)
d.save(hpath, hda)
hda.matchCurrentDefinition()
print("HDA", hpath)
# report every node error BEFORE the test cook, so a generator that fails
# to compile is named instead of surfacing as a dead output
for _n in hda.allSubChildren():
    if _n.errors():
        print("  NODE ERROR", _n.path(), _n.errors())
# --- test cook both resolutions ---
def _stat(node_name):
    n = hda.node(node_name)
    if n is None:
        return "MISSING"
    g = n.geometry()
    if g is None:
        return "NO-GEOMETRY"
    return "%d pts / %d prims" % (len(g.points()), len(g.prims()))

for fr in (0, 1):
    hda.parm("full_res").set(fr)
    t0 = time.time()
    for _o in ("output_landscape", "output_points", "output_route_curve",
               "output_skirt_mesh", "output_water", "output_masonry",
               "output_generated"):
        print("  cook[%d] %-20s %s" % (fr, _o, _stat(_o)))
    g = hda.node("output_landscape").geometry()
    if g is not None:
        hv = [p for p in g.prims() if p.attribValue("name") == "height"][0]
        print("full_res", fr, "cook %.2fs" % (time.time() - t0), "res", hv.resolution(),
              "layers", [p.attribValue("name") for p in g.prims()])
    rg = hda.node("output_route_curve").geometry()
    if rg is not None:
        los = [p.attribValue("abbey_los") for p in rg.points()]
        print("  abbey_sightline_pct %.1f" % (100.0*sum(los)/max(1,len(los))))
    cw = hda.node("IN_CANALS").geometry()
    if cw is not None:
        print("  canal widths", sorted(set(round(p.attribValue("width"),2) for p in cw.prims())))
    op = hda.node("output_points").geometry()
    if op is not None:
        from collections import Counter
        print("  types", dict(Counter(p.attribValue("type") for p in op.points())))
    # every node error, now that the graph has cooked
    for _n in hda.allSubChildren():
        if _n.errors():
            print("  NODE ERROR", _n.name(), str(_n.errors())[:300])
mg = None
_mn = hda.node("output_masonry")
if _mn is None:
    _stack=[hda]
    while _stack:
        _c=_stack.pop()
        for _ch in _c.children():
            if _ch.name()=="output_masonry": _mn=_ch; break
            _stack.append(_ch)
        if _mn: break
_rv = hda.node("REVETMENT_coursed_ashlar")
if _rv is not None:
    print("  REVETMENT errors:", _rv.errors())
    _rg = _rv.geometry()
    print("  revetment prims", (len(_rg.prims()), len(_rg.points())) if _rg is not None else "NONE")
    if _rg is not None:
        mm = Counter(pr.attribValue("unreal_material") for pr in _rg.prims()); print("  revetment materials", dict(mm))
if _mn is not None:
    mg = _mn.geometry()
    print("  masonry output prims", (len(mg.prims()), len(mg.points())) if mg is not None else "NONE")
else:
    print("  masonry output NOT FOUND")
hda.parm("full_res").set(0)
print("errors", [ (n.path(), n.errors()) for n in hda.allSubChildren() if n.errors()])
hou.hipFile.save(os.path.join(HDADIR, "poitou_layout_live_test" + (".hiplc" if ext==".hdalc" else ".hip")).replace("\\","/"))

# ---- export height + flow/debris/wetness PNGs (same frame as v0 export: row0 = north, col0 = west) ----
import numpy as np, zlib, struct
EXP = os.path.join(HERE, "export"); os.makedirs(EXP, exist_ok=True)
def _png(path, a, bits):
    h, w = a.shape
    raw = b"".join(b"\0" + (a[i].astype(">u2") if bits == 16 else a[i].astype("u1")).tobytes() for i in range(h))
    ck = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + ck(b"IHDR", struct.pack(">IIBBBBB", w, h, bits, 0, 0, 0, 0)) + ck(b"IDAT", zlib.compress(raw, 6)) + ck(b"IEND", b""))
def _vol(g, name):
    pr = [p for p in g.prims() if p.attribValue("name") == name][0]; rx, ry, rz = pr.resolution()
    a = np.array(pr.allVoxels(), dtype=np.float64).reshape(ry, rx) if rz == 1 else np.array(pr.allVoxels()).reshape(rz, ry, rx)[0]
    p00 = pr.indexToPos((0,0,0)); p10 = pr.indexToPos((1,0,0)); p01 = pr.indexToPos((0,1,0))
    if abs(p10[0]-p00[0]) < 1e-6: a = a.T; p10, p01 = p01, p10
    if p10[0] < p00[0]: a = a[:, ::-1]
    if p01[2] > p00[2]: a = a[::-1, :]
    return a
for fr, res in ((1, 1009), (0, 505)):
    hda.parm("full_res").set(fr); g = hda.node("OUT_TERRAIN").geometry()
    H = _vol(g, "height"); _png(os.path.join(EXP, "poitou_height_%d_u16.png" % res), np.clip(np.round(32768 + H*128*100/25.0), 0, 65535).astype(np.uint16), 16)
    for m in ("flow", "debris", "wetness"):
        a = _vol(g, m); _png(os.path.join(EXP, "mask_%s_%d.png" % (m, res)), np.round(np.clip(a, 0, 1)*255).astype(np.uint8), 8)
        print("export", m, res, a.shape, "mean %.3f" % a.mean())
hda.parm("full_res").set(0)
