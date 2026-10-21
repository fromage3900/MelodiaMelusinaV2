import numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from scipy.ndimage import gaussian_filter, distance_transform_edt
N=1024; S=1000.0  # metres, 1 px ~0.98 m
y,x=np.mgrid[0:N,0:N]*(S/N); # x east, y north
def poly(pts):
    return Path(pts).contains_points(np.c_[x.ravel(),y.ravel()]).reshape(N,N)
def polyline_dist(pts):
    d=np.full((N,N),1e9)
    for (x0,y0),(x1,y1) in zip(pts[:-1],pts[1:]):
        dx,dy=x1-x0,y1-y0; t=np.clip(((x-x0)*dx+(y-y0)*dy)/(dx*dx+dy*dy),0,1)
        d=np.minimum(d,np.hypot(x-x0-t*dx,y-y0-t*dy))
    return d
# canals: (polyline, width m)
canals=[([(0,430),(250,440),(420,470),(600,455),(1000,470)],18,"Bief (main, 18 m)"),
 ([(380,0),(390,200),(400,460)],7,"Conche"),
 ([(600,455),(610,700),(640,1000)],6,"Conche"),
 ([(0,250),(380,230)],5,"Conche"),([(390,200),(1000,180)],5,"Conche"),
 ([(610,700),(1000,720)],5,"Conche"),([(150,437),(140,1000)],4,"Fosse"),
 ([(800,463),(820,180)],4,"Fosse"),([(250,440),(260,0)],4,"Fosse")]
water=np.zeros((N,N),bool); cd=np.full((N,N),1e9)
for p,w,_ in canals:
    d=polyline_dist(p); water|=d<w/2; cd=np.minimum(cd,d)
# fine ditches grid in meadows (every ~70 m)
ditch=(np.abs((x%70)-35)<1.2)&(y<420)
route=[(80,60),(330,320),(470,500),(560,600),(700,560),(800,820),(900,930)]
pathd=polyline_dist(route); path=pathd<2.0
village=poly([(380,480),(620,480),(640,640),(520,700),(400,650)])
rise=np.hypot(x-830,y-860)<140
mist=(x<200)|(y>900)&~rise; mist=mist|((x+y)<300)
meadow=(y<425)&~mist
poplar_zone=~village&~rise
church=(520,580); ruin=(830,870)
excl=water|path|(pathd<4)
def save(name,a):
    a=np.clip(a,0,1); a[excl]=0
    plt.imsave(f"heatmaps/{name}.png",np.flipud(a),cmap="gray",vmin=0,vmax=1); return a
rng=np.random.default_rng(1); noise=gaussian_filter(rng.random((N,N)),25); noise=(noise-noise.min())/np.ptp(noise)
H={}
H["village_buildings"]=save("village_buildings",np.where(village,0.6+0.4*np.exp(-np.hypot(x-church[0],y-church[1])/90)*(cd>6),0)*(cd>4))
H["canal_banks"]=save("canal_banks",np.exp(-np.maximum(cd-3,0)/6)*(0.6+0.4*noise))
H["wet_meadow_grass"]=save("wet_meadow_grass",gaussian_filter((meadow|(~village&~rise&~mist)).astype(float),6)*(0.5+0.5*noise)*(~ditch))
H["tree_rows_poplar_ash"]=save("tree_rows_poplar_ash",((cd>4)&(cd<9)&poplar_zone)*1.0*(0.7+0.3*noise)+((np.abs((x%140)-70)<3)&meadow)*0.8)
H["ruin_rise"]=save("ruin_rise",np.clip(1-np.hypot(x-830,y-860)/140,0,1)**0.7*(0.5+0.5*noise))
H["mist_marsh_reeds"]=save("mist_marsh_reeds",gaussian_filter(mist.astype(float),15)*(0.4+0.6*noise)+0.5*np.exp(-cd/10)*mist)
H["mist_volume"]=save("mist_volume",gaussian_filter(mist.astype(float),40)*0.8+0.3*np.exp(-cd/25))
# contact sheet
f,ax=plt.subplots(2,4,figsize=(16,8.6),dpi=128)
for a,(k,v) in zip(ax.ravel(),H.items()):
    a.imshow(np.flipud(v),cmap="gray",vmin=0,vmax=1); a.set_title(k); a.axis("off")
ax.ravel()[-1].axis("off"); ax.ravel()[-1].text(0,.5,"white = max density\nblack = none / excluded\n(water, paths, 4 m path buffer)\n1 px ≈ 0.98 m, north up",fontsize=12)
plt.tight_layout(); plt.savefig("heatmaps_sheet.png"); plt.close()
# map
col=np.ones((N,N,3))*np.array([.78,.88,.62])
col[meadow]=[.70,.85,.55]; col[mist]=[.75,.80,.80]; col[village]=[.93,.90,.80]; col[rise]=[.85,.80,.65]
col[H["tree_rows_poplar_ash"]>0.5]=[.25,.50,.25]; col[ditch&meadow]=[.55,.70,.85]; col[water]=[.25,.50,.80]
f=plt.figure(figsize=(16,16),dpi=128); a=f.add_axes([0.04,0.04,0.72,0.9])
a.imshow(col,origin="lower",extent=[0,S,0,S])
rx,ry=zip(*route); a.plot(rx,ry,"--",c="crimson",lw=3)
beats=["Landing jetty in the mist","Meadow footbridge (first glimpse of steeple)","Grand Port & barques","Romanesque church square","Quéreux lane / balais to water","Poplar allée & lock","Lusignan-style ruin on limestone rise"]
for i,(p,b) in enumerate(zip(route,beats)):
    a.scatter(*p,s=500,c="crimson",zorder=5,edgecolor="w"); a.text(*p,str(i+1),c="w",ha="center",va="center",fontsize=14,weight="bold",zorder=6)
lm={"A Church steeple":church,"B Ruin keep":ruin,"C Grand Port crane":(470,475),"D Lock/écluse":(700,465),"E Lone ash 'têtard'":(200,330)}
for k,p in lm.items(): a.scatter(*p,marker="^",s=300,c="k",zorder=7); a.text(p[0]+12,p[1]+12,k,fontsize=11,weight="bold",zorder=7)
for s,t in [((80,60),church),((330,320),ruin),((560,600),ruin),((800,820),(470,475))]:
    a.annotate("",xy=t,xytext=s,arrowprops=dict(arrowstyle="->",color="orange",lw=2,ls=":"))
a.plot([40,240],[20,20],c="k",lw=6); a.text(140,30,"200 m",ha="center",fontsize=12,weight="bold")
a.text(960,960,"N↑",fontsize=18,weight="bold")
a.set_title("Marais Poitevin – 'Melusina's Morning' layout v0 (1 x 1 km)",fontsize=18)
from matplotlib.patches import Patch; from matplotlib.lines import Line2D
L=[Patch(color=c,label=l) for c,l in [((.93,.90,.80),"Village core"),((.25,.5,.8),"Canals (bief 18 m / conche 5-7 m / fossé 4 m)"),((.70,.85,.55),"Wet meadow parcels"),((.55,.7,.85),"Parcel ditches (~70 m grid)"),((.25,.5,.25),"Poplar & ash rows"),((.85,.8,.65),"Limestone rise + ruin"),((.75,.8,.8),"Mist marsh edge")]]
L+=[Line2D([],[],c="crimson",ls="--",lw=3,label="Player route (1-7)"),Line2D([],[],c="orange",ls=":",lw=2,label="Sightlines"),Line2D([],[],marker="^",c="k",ls="",label="Landmarks A-E")]
f.legend(handles=L,loc="upper right",bbox_to_anchor=(0.995,0.94),fontsize=11)
f.text(0.775,0.55,"\n".join(f"{i+1}. {b}" for i,b in enumerate(beats)),fontsize=11,va="top")
plt.savefig("layout_map.png"); print("ok")
