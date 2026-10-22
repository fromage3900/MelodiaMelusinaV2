import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Arc, Wedge
def dim(a,x0,y0,x1,y1,t,off=0.4):
    a.annotate("",(x1,y1),(x0,y0),arrowprops=dict(arrowstyle="<->",lw=1)); a.text((x0+x1)/2+off*(x0==x1),(y0+y1)/2+off*(y0==y1),t,fontsize=9,ha="center")
f,ax=plt.subplots(1,3,figsize=(18,7),dpi=128,gridspec_kw=dict(width_ratios=[1,1.2,1.2]))
# house 3 bars x 2.4 = 9.6 w, eaves 5.7, ridge 8
a=ax[0]; a.add_patch(Rectangle((0,0),9.6,5.7,fc="#E9E3D3",ec="k")); a.add_patch(Polygon([(-.3,5.7),(9.9,5.7),(4.8,8.2)],fc="#B56A4A",ec="k"))
for i in range(4): 
    a.add_patch(Rectangle((-0.0+i*0,0),0,0))
pat="-W-W"+"W-D-"[0:0]
for b in range(4):  # beats of 2.4 bays*... use 0.6 m beats per bay (4 bays)
    pass
for k,c in enumerate("-W-D--W-"):  # ground floor 8 beats over 9.6m (1.2 m each)
    x=k*1.2+0.1
    if c=="W": a.add_patch(Rectangle((x,0.9),1.0,1.8,fc="#88aacc",ec="k")); a.add_patch(Rectangle((x-0.4,0.9),0.4,1.8,fc="#8FAE9B")); a.add_patch(Rectangle((x+1,0.9),0.4,1.8,fc="#8FAE9B"))
    if c=="D": a.add_patch(Rectangle((x,0),1.1,2.3,fc="#6b5a44",ec="k"))
for k,c in enumerate("-W-W--W-"):
    x=k*1.2+0.1
    if c=="W": a.add_patch(Rectangle((x,3.6),1.0,1.6,fc="#88aacc",ec="k"))
for y in range(0,6): a.add_patch(Rectangle((0,y),0.5,0.5,fc="#D8CBAE",ec="k",lw=.5)); a.add_patch(Rectangle((9.1,y+.5 if y<5 else y),0.5,0.5,fc="#D8CBAE",ec="k",lw=.5))
a.add_patch(Rectangle((0,0),9.6,0.6,fc="#9a9480",alpha=.5))
dim(a,0,-0.8,9.6,-0.8,"W 9.6 m = 4 bays × 2.4 (4 bars)");dim(a,10.6,0,10.6,5.7,"eaves 5.7");dim(a,11.8,0,11.8,8.2,"ridge 8.2")
a.text(4.8,6.6,"pitch ~30° canal tile",ha="center",fontsize=9); a.text(4.8,-2.0,"rhythm GF: – W – D – – W – | 1F: – W – W – – W –",ha="center",fontsize=9)
a.set_title("RoomShell: maison maraîchine (2 storeys)"); a.set_xlim(-1,13); a.set_ylim(-2.5,10)
# church
a=ax[1]; a.add_patch(Rectangle((0,0),24,8,fc="#E9E3D3",ec="k")); a.add_patch(Polygon([(0,8),(24,8),(24,12),(0,12)],fc="#B56A4A",ec="k",alpha=.0))
a.add_patch(Polygon([(-.3,8),(24.3,8),(24.3,9.5),(-.3,9.5)],fc="#B56A4A",ec="k"))
a.add_patch(Rectangle((24,0),5.5,24,fc="#E9E3D3",ec="k")); a.add_patch(Polygon([(23.7,24),(29.8,24),(26.75,30)],fc="#4B5157",ec="k"))
for i in range(5):
    x=2.2+i*4.8; a.add_patch(Rectangle((x,3.5),0.9,2.4,fc="#334",ec="k")); a.add_patch(Wedge((x+.45,5.9),.45,0,180,fc="#334"))
for r in (1.2,1.6,2.0): a.add_patch(Arc((26.75,3.5),2*r,2*r,theta1=0,theta2=180,lw=1.5))
a.add_patch(Rectangle((25.55,0),2.4,3.5,fc="#6b5a44"))
for j in range(7): h=3*0.94**j; a.add_patch(Rectangle((25.0+j*0.6,18.5),0.4,h,fc="#2A2622"))
a.text(26.75,22.4,"organ-pipe louvres ×0.94",ha="center",fontsize=8)
dim(a,0,-1,24,-1,"nave 24 m (5 bays × 4.8)");dim(a,-1.5,0,-1.5,8,"8 m");dim(a,31,0,31,30,"tower 30 m");dim(a,24,-2.5,29.5,-2.5,"5.5")
a.text(12,-4,"semicircular arches only · portal = 3 archivolts ('chord') · capitals = instrument motifs",ha="center",fontsize=9)
a.set_title("Cathedral gen: squat Romanesque church"); a.set_xlim(-3,34); a.set_ylim(-5,32)
# bridge
a=ax[2]; L=6.0; a.add_patch(Rectangle((0,0),L+1.0,0.6,fc="#5aa0d0",alpha=.5)); a.text(3.5,0.15,"water (conche 6 m)",ha="center",fontsize=8)
a.add_patch(Rectangle((-0.5,1.6),L+2,0.1,fc="#A88D6A",ec="k"))
for p in [0,2.4,4.8]: a.add_patch(Rectangle((p+.2,0),0.15,2.7,fc="#6b5a44"))
a.plot([-.5,L+1.5],[2.7,2.7],c="#6b5a44",lw=3)
# plan view inset of keys
y0=4.0
for k in range(int((L+2)/0.24)):
    x=-0.5+k*0.24; a.add_patch(Rectangle((x,y0),0.23,1.4,fc="#A88D6A",ec="#7a6448",lw=.3))
import itertools
oct=[1,2,4,5,6]  # black key positions within 7
for k in range(int((L+2)/0.24)):
    if 14<=k<21 and k%7 in oct: a.add_patch(Rectangle((-0.5+k*0.24+0.17,y0+0.56),0.13,0.84,fc="#2A2622"))
dim(a,-.5,3.75,1.9,3.755,"1 bar = 10 keys = 2.4 m",off=-.32); dim(a,-.5+14*.24,3.75,-.5+21*.24,3.75,"octave 1.68 m",off=-.32); dim(a,7.8,4.0,7.8,5.4,"deck 1.4 m")
dim(a,7.0,0.6,7.0,1.6,"clear 1.0");dim(a,8.3,1.6,8.3,2.7,"rail 1.0")
a.text(4.2,6.0,"PLAN: DA_PianoWalkway_Poitou: Key Width 0.24 oak; tarred black keys ONE octave mid-span",ha="center",fontsize=8)
a.text(3.5,2.95,"ELEVATION: posts every 2.4 m (1 bar); existing PCGPianoKeyboard step/sound",ha="center",fontsize=8)
a.set_title("Piano walkway: conche footbridge"); a.set_xlim(-1,9.5); a.set_ylim(-0.5,6.9)
for a in ax: a.set_aspect("equal"); a.grid(alpha=.2)
f.suptitle("MelodiaMelusina: 'Musical but French' style contract v0 (metres)",fontsize=16)
plt.tight_layout(); plt.savefig("style_contract_sheet.png")
