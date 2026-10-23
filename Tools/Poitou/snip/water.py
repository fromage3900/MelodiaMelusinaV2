wg = geo.createNode("grid","water_grid"); wg.parm("sizex").set(1000); wg.parm("sizey").set(1000); wg.parm("tx").set(500); wg.parm("tz").set(500)
wg.parm("rows").setExpression('int(1000/ch("../water_res"))+1'); wg.parm("cols").setExpression('int(1000/ch("../water_res"))+1')
ww = wrangle("water_cut", 'int pts[]=primpoints(0,@primnum); vector m={0,0,0}; foreach(int p;pts) m+=point(0,"P",p); m/=len(pts); float r=ch("../water_res"); if(volumesample(1,"cd",m)>prim(2,"width",0)*0+r*0.75+volumesample(1,"cd",m)*0 && volumesample(1,"water",m)<0.5 && volumesample(1,"cd",m)>r*0.9) removeprim(0,@primnum,1); else s@unreal_material=chs("../water_material");', 1, [wg, TERRAIN])
wl = wrangle("water_level", '@P.y = ch("../marsh_base") - ch("../water_drop");', 2, [ww])
o4 = geo.createNode("output", "output_water"); o4.parm("outputidx").set(4); o4.setInput(0, wl)
los = wrangle("abbey_sightline", r"""
vector e=@P+{0,1.7,0}; vector a=set(830, volumesample(1,"height",{830,0,870})+12, 870); int ok=1;
for(float k=0.02;k<0.98;k+=0.01){ vector s=lerp(e,a,k); if(volumesample(1,"height",s)>s.y){ ok=0; break; } }
i@abbey_los=ok; """, 2, [dr, TERRAIN])
o2.setInput(0, los)
