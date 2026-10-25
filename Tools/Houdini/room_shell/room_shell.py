"""Melodia room shell: interlocking half-lap wall panels, trims, windows and the Nikki GN decorators, ported to Houdini.
Metres, Z-up, interior floor corner at the origin (room interior = [0,W] x [0,D] x [0,H]); walls grow outward.
Self-contained (no project imports) so it can be embedded in an HDA PythonModule. Faces are stored in Houdini's
clockwise-front winding (Mesh.poly reverses a right-hand outward face).

Decorator vocabulary mirrors deploy/surreal_arch/melodia_gn: paris_wall_detail (CORNICE_STYLE 0 FLAT / 1 HAUSSMANN /
2 GOTHIC: bands, panels, stepped reveals, quoins, arch medallions), nikki_decor (bead / star / heart / crystal solids,
cord strands, bead strings with parabolic droop), nikki_advanced_decorations (star void panel, heart chain),
nikki_musical_decorations (vertical wall bead strings).
"""
import math,random,json
TAU=math.tau

# --------------------------------------------------------------------------- mesh helpers
class Mesh:
    def __init__(self):self.P=[];self.F=[];self.R=[]
    def poly(self,pts,role):
        s=len(self.P);self.P.extend(pts);self.F.append(list(reversed(range(s,len(self.P)))));self.R.append(role)

def box(M,a,b,role):
    x,y,z=a;X,Y,Z=b
    p=[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)]
    for f in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):M.poly([p[i] for i in f],role)

def hexa(M,p,role):
    for f in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):M.poly([p[i] for i in f],role)

def _sub(a,b):return (a[0]-b[0],a[1]-b[1],a[2]-b[2])
def _cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def _norm(a):
    l=math.sqrt(a[0]**2+a[1]**2+a[2]**2) or 1.;return (a[0]/l,a[1]/l,a[2]/l)

def beam(M,a,b,w,d,role):
    z=_norm(_sub(b,a));ref=(0,0,1) if abs(z[2])<.95 else (1,0,0)
    x=_norm(_cross(ref,z));y=_norm(_cross(z,x))
    pts=[tuple(c[k]+x[k]*s*w/2+y[k]*t*d/2 for k in range(3)) for c in (a,b) for s,t in ((-1,-1),(1,-1),(1,1),(-1,1))]
    for f in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):M.poly([pts[i] for i in f],role)

def strip(M,p,q,w,z,role):
    dx,dy=q[0]-p[0],q[1]-p[1];L=math.hypot(dx,dy)
    if L<1e-6:return
    nx,ny=-dy/L*w/2,dx/L*w/2
    M.poly([(p[0]-nx,p[1]-ny,z),(q[0]-nx,q[1]-ny,z),(q[0]+nx,q[1]+ny,z),(p[0]+nx,p[1]+ny,z)],role)   # CCW from +z = right-hand up (Mesh.poly stores it reversed)

def ring(M,cx,cy,r,w,z,role,seg=48):
    pts=[(cx+r*math.cos(TAU*i/seg),cy+r*math.sin(TAU*i/seg)) for i in range(seg+1)]
    for a,b in zip(pts,pts[1:]):strip(M,a,b,w,z,role)

def sphere(M,c,r,role,lat=4,lon=8):
    rows=[]
    for i in range(lat+1):
        th=math.pi*i/lat;rows.append([(c[0]+r*math.sin(th)*math.cos(TAU*j/lon),c[1]+r*math.sin(th)*math.sin(TAU*j/lon),c[2]+r*math.cos(th)) for j in range(lon)])
    for i in range(lat):
        for j in range(lon):
            a,b,cc,d=rows[i][j],rows[i][(j+1)%lon],rows[i+1][(j+1)%lon],rows[i+1][j]
            if i==0:M.poly([a,cc,d],role)
            elif i==lat-1:M.poly([a,b,d],role)
            else:M.poly([a,b,cc,d],role)

def prism(M,pts2,z0,z1,role,cx=None,cy=None):
    """Extrude a star-shaped CCW polygon (about its centroid) between z0 and z1; faces outward right-hand."""
    n=len(pts2);cx=sum(p[0] for p in pts2)/n if cx is None else cx;cy=sum(p[1] for p in pts2)/n if cy is None else cy
    for i in range(n):
        a,b=pts2[i],pts2[(i+1)%n]
        M.poly([(cx,cy,z1),(a[0],a[1],z1),(b[0],b[1],z1)],role)           # top (CCW seen from +z)
        M.poly([(cx,cy,z0),(b[0],b[1],z0),(a[0],a[1],z0)],role)                          # bottom
        M.poly([(a[0],a[1],z0),(b[0],b[1],z0),(b[0],b[1],z1),(a[0],a[1],z1)],role)       # side

def octa(M,c,r,h,role):
    t=(c[0],c[1],c[2]+h);b=(c[0],c[1],c[2]-h);e=[(c[0]+r,c[1],c[2]),(c[0],c[1]+r,c[2]),(c[0]-r,c[1],c[2]),(c[0],c[1]-r,c[2])]
    for i in range(4):
        a,bb=e[i],e[(i+1)%4];M.poly([t,a,bb],role);M.poly([b,bb,a],role)

def star_pts(r_out,r_in,n=8,rot=0.,cx=0.,cy=0.):
    return [(cx+(r_out if i%2==0 else r_in)*math.cos(rot+math.pi*i/n),cy+(r_out if i%2==0 else r_in)*math.sin(rot+math.pi*i/n)) for i in range(2*n)]

def heart_pts(s,cx=0.,cy=0.,n=28):
    out=[]
    for i in range(n):
        t=TAU*i/n;x=16*math.sin(t)**3;y=13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t)
        out.append((cx+s*x/17,cy+s*(y+1.5)/17))
    return out

def pointed(half,rise,seg=14):
    c=(rise*rise-half*half)/(2*half);rad=half+c;th=math.atan2(rise,-c)
    left=[(c+rad*math.cos(math.pi+(th-math.pi)*i/seg),rad*math.sin(math.pi+(th-math.pi)*i/seg)) for i in range(seg+1)]
    return left+[(-x,z) for x,z in reversed(left[:-1])]

def chladni_segments(n,m,N=48):
    f=lambda x,y:math.cos(n*math.pi*x)*math.cos(m*math.pi*y)-math.cos(m*math.pi*x)*math.cos(n*math.pi*y)
    xs=[i/N for i in range(N+1)];v=[[f(x,y) for y in xs] for x in xs];segs=[]
    def cross(a,b,va,vb):
        t=va/(va-vb);return (a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t)
    for i in range(N):
        for j in range(N):
            p=[(xs[i],xs[j]),(xs[i+1],xs[j]),(xs[i+1],xs[j+1]),(xs[i],xs[j+1])];q=[v[i][j],v[i+1][j],v[i+1][j+1],v[i][j+1]]
            pts=[cross(p[k],p[(k+1)%4],q[k],q[(k+1)%4]) for k in range(4) if (q[k]>0)!=(q[(k+1)%4]>0)]
            if len(pts)==2:segs.append(pts)
            elif len(pts)==4:segs+=[pts[:2],pts[2:]]
    return [[(2*a[0]-1,2*a[1]-1),(2*b[0]-1,2*b[1]-1)] for a,b in segs]

# --------------------------------------------------------------------------- decor presets (the GN decorator families)
PRESETS={
 'paris_haussmann':dict(cornice_style=1,swag=0,wall_beads=0,star_pendants=0,star_panel=False,heart_chain=False,quoins=False,window_family='panel',gold=.55),
 'nikki_bead_swag':dict(cornice_style=1,swag=1,wall_beads=2,star_pendants=0,star_panel=False,heart_chain=False,quoins=False,window_family='geometric',gold=.7),
 'nikki_star_pendant':dict(cornice_style=0,swag=0,wall_beads=0,star_pendants=3,star_panel=True,heart_chain=False,quoins=False,window_family='intersecting',gold=.8),
 'gothic_reveal':dict(cornice_style=2,swag=0,wall_beads=0,star_pendants=0,star_panel=False,heart_chain=False,quoins=True,window_family='geometric',gold=.6),
 'heart_filigree':dict(cornice_style=1,swag=1,wall_beads=0,star_pendants=1,star_panel=False,heart_chain=True,quoins=False,window_family='intersecting',gold=.9),
}
DEFAULTS=dict(W=7.0,D=9.0,H=3.4,wall_t=.24,panel_w=1.5,seed=1031,decor='nikki_bead_swag',interlock='half_lap',lap=.05,gap=.002,
              windows_long=2,windows_short=1,win_w=1.0,win_h=1.9,sill=.95,door_wall='S',door_w=1.0,door_h=2.15,
              bead_count=11,droop=.22,bead_r=.028,floor_medallion=True,skirting=True,chair_rail=True,
              head='pointed',glass_mode='pane',pane_t=.014,sill_depth=.09,streamers=6,
              tuning=True,c_sound=343.0,dawn_puzzle=True,latitude=48.85)

def params(**kw):
    p=dict(DEFAULTS);p.update(kw);p.update({k:v for k,v in PRESETS[p['decor']].items() if k not in kw});return p

# --------------------------------------------------------------------------- wall geometry
def hexa_rings(M,bot,top,role,flip=False):
    """Closed solid from a bottom ring and a top ring (each 4 pts, CCW seen from +z). flip=True for axis-swapped (reflected) placement."""
    if flip:bot=[bot[0],bot[3],bot[2],bot[1]];top=[top[0],top[3],top[2],top[1]]
    p=bot+top
    for f in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):M.poly([p[i] for i in f],role)

def arch_z(half,rise,x,seg=40):
    """Height of a two-centred pointed arch (spring at 0) at lateral offset x from the axis."""
    pts=pointed(half,rise,seg);x=max(-half,min(half,x))
    for (xa,za),(xb,zb) in zip(pts,pts[1:]):
        if xa<=x<=xb:
            return za if xb==xa else za+(zb-za)*(x-xa)/(xb-xa)
    return pts[-1][1]

def slab_opening(M,s0,s1,u0,u1,z0,z1,opening,role,axis):
    """Box s0..s1 (along wall) x u0..u1 (thickness) x z0..z1 with an optional opening (os0,os1,oz0,oz1,rise).
    rise>0 => pointed head (spring at oz1-rise); the head above the arch is built from sloped solids so the cut-out is real.
    axis 'x': s is x, u is y.  axis 'y': s is y, u is x (a reflection, so ring order is flipped)."""
    def B(a0,a1,b0,b1,c0,c1):
        if a1-a0<1e-6 or c1-c0<1e-6:return
        if axis=='x':box(M,(a0,b0,c0),(a1,b1,c1),role)
        else:box(M,(b0,a0,c0),(b1,a1,c1),role)
    if not opening:B(s0,s1,u0,u1,z0,z1);return
    os0,os1,oz0,oz1=opening[:4];rise=opening[4] if len(opening)>4 else 0.
    os0=max(os0,s0);os1=min(os1,s1)
    B(s0,os0,u0,u1,z0,z1);B(os1,s1,u0,u1,z0,z1)           # jambs (full height)
    B(os0,os1,u0,u1,z0,oz0)                                   # below the opening (sill wall)
    if rise<=0:
        B(os0,os1,u0,u1,oz1,z1);return                        # flat head
    spring=oz1-rise;half=(os1-os0)/2;mid=(os0+os1)/2;N=16
    def P(s,u,z):return (s,u,z) if axis=='x' else (u,s,z)
    B(os0,os1,u0,u1,spring,spring) if False else None
    for i in range(N):
        sa=os0+(os1-os0)*i/N;sb=os0+(os1-os0)*(i+1)/N
        za=spring+arch_z(half,rise,sa-mid);zb=spring+arch_z(half,rise,sb-mid)
        bot=[P(sa,u0,za),P(sb,u0,zb),P(sb,u1,zb),P(sa,u1,za)];top=[P(sa,u0,z1),P(sb,u0,z1),P(sb,u1,z1),P(sa,u1,z1)]
        hexa_rings(M,bot,top,role,flip=(axis=='y'))

NOTE_NAMES=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
def note_of(hz):
    m=int(round(69+12*math.log2(hz/440.0)));return NOTE_NAMES[m%12]+str(m//12-1),m

def acoustics(p):
    """Axial standing-wave modes of the room: f_n = n*c/(2L). Wall panels are equal divisions of each wall, so panel
    joints fall on the pressure ANTINODES (cos(n*pi*s/L) = +-1) and panel centres (windows, doors) on the NODES.
    Real axial modes of a 7 x 9 x 3.4 m room are infrasonic, so the audible room note is the lowest mode octave-shifted into 110..220 Hz."""
    W,D,H,c,pw=p['W'],p['D'],p['H'],p['c_sound'],p['panel_w']
    nx,ny=max(1,int(round(W/pw))),max(1,int(round(D/pw)))
    modes={ax:[round(n*c/(2*L),2) for n in range(1,7)] for ax,L in (('x',W),('y',D),('z',H))}
    f_low=c/(2*max(W,D,H));shift=0;f=f_low
    while f<110:f*=2;shift+=1
    note,mid=note_of(f)
    anti={'x':[round(W*k/nx,6) for k in range(nx+1)],'y':[round(D*k/ny,6) for k in range(ny+1)]}
    node={'x':[round(W*(k+.5)/nx,6) for k in range(nx)],'y':[round(D*(k+.5)/ny,6) for k in range(ny)]}
    a,b=min(nx,6),min(ny,6)
    if a==b:
        if b<6:b+=1
        else:a-=1
    a,b=sorted((max(1,a),max(1,b)))
    return dict(c=c,axial_modes_hz=modes,f_low_hz=round(f_low,2),octave_shift=shift,room_note_hz=round(f,2),room_note=note,room_midi=mid,
                panels=dict(nx=nx,ny=ny),antinodes=anti,nodes=node,chladni_mode=[a,b],chladni_hz=round(55*(a*a+b*b)/2,1),
                note='octave-shifted; real axial modes are infrasonic')

def project_patch(pts,C,target):
    """Sunlight through the planar pane polygon onto z=0, with the ray that sends the pane's vertex-average C to target."""
    d=_norm(_sub(target,C));out=[]
    for q in pts:
        t=-q[2]/d[2];out.append((q[0]+d[0]*t,q[1]+d[1]*t,0.))
    return d,out

def validate_openings(records,W,D,H):
    """Named floor-level portals, in native metres; no random/panel-relative positions."""
    if not isinstance(records,list):raise ValueError('explicit openings must be an array')
    result=[];ids=set()
    for record in records:
        if not isinstance(record,dict):raise ValueError('each opening must be an object')
        name=record.get('id');wall=record.get('wall')
        if not isinstance(name,str) or not name.strip() or name in ids:raise ValueError('opening ids must be unique nonempty strings')
        if wall not in ('S','N','W','E'):raise ValueError('opening wall must be S, N, W or E')
        if record.get('kind','door')!='door':raise ValueError('explicit openings currently support floor-level doors only')
        values=[]
        for key in ('s','width','height'):
            value=record.get(key)
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):raise ValueError('opening %s must be a finite number'%key)
            values.append(float(value))
        s,width,height=values;length=W if wall in ('S','N') else D
        if width<=0 or height<=0 or height>H-.6:raise ValueError('opening size must be positive with 0.6 m of wall above')
        s0,s1=s-width/2,s+width/2
        if s0<.3 or s1>length-.3:raise ValueError('opening must retain 0.3 m corner clearance')
        if any(q['wall']==wall and min(s1,q['s1'])>max(s0,q['s0'])-1e-6 for q in result):raise ValueError('openings on the same wall overlap or touch')
        result.append(dict(id=name,wall=wall,s=s,s0=s0,s1=s1,h=height,width=width,height=height,panel=None));ids.add(name)
    return result

def opening_socket(q,W,D):
    wall,s=q['wall'],q['s']
    center={'S':(s,0.,0.),'N':(s,D,0.),'W':(0.,s,0.),'E':(W,s,0.)}[wall]
    inward={'S':(0.,1.,0.),'N':(0.,-1.,0.),'W':(1.,0.,0.),'E':(-1.,0.,0.)}[wall]
    return dict(id=q['id'],wall=wall,center_local_m=center,inward=inward,up=(0.,0.,1.),clear_width_m=q['width'],clear_height_m=q['height'],floor_z_m=0.,s0=q['s0'],s1=q['s1'],kind='door',native_cut=True)

def slab_openings(M,s0,s1,u0,u1,z0,z1,apertures,role,axis):
    """Cut every non-overlapping aperture from this panel, including across seams."""
    cursor=s0
    for op in sorted(apertures,key=lambda q:q[0]):
        lo,hi=max(s0,op[0]),min(s1,op[1])
        if hi<=lo+1e-8:continue
        if lo>cursor:slab_opening(M,cursor,lo,u0,u1,z0,z1,None,role,axis)
        slab_opening(M,lo,hi,u0,u1,z0,z1,op,role,axis);cursor=hi
    if cursor<s1:slab_opening(M,cursor,s1,u0,u1,z0,z1,None,role,axis)

def build(**kw):
    p=params(**kw);r=random.Random('room:%s:%s'%(p['seed'],p['decor']))
    W,D,H,t=p['W'],p['D'],p['H'],p['wall_t'];pw=p['panel_w'];lap=p['lap'];g=p['gap']
    M=Mesh();joints=[];windows=[];sockets=[];report=dict(solids=0)
    explicit=validate_openings(p.get('explicit_openings',[]),W,D,H)
    ac=acoustics(p) if p['tuning'] else None
    # floor + ceiling slabs
    box(M,(-t,-t,-.2),(W+t,D+t,0),'floor_stone');box(M,(-t,-t,H),(W+t,D+t,H+.2),'wall_plaster')
    half=t/2
    # corner posts
    for (x0,y0) in ((-t,-t),(W,-t),(W,D),(-t,D)):box(M,(x0,y0,0),(x0+t,y0+t,H),'stone')
    walls=[('S','x',0.,W,-t,0.,+1),('N','x',0.,W,D,D+t,-1),('W','y',0.,D,-t,0.,+1),('E','y',0.,D,W,W+t,-1)]
    door=explicit[0] if explicit else None;skip={};openings={}
    def portal_overlaps(wall,a,b,pad=0.):
        return any(q['wall']==wall and q['s0']-pad<b and q['s1']+pad>a for q in explicit)
    for name,axis,sa,sb,u0,u1,inward in walls:
        L=sb-sa;n=max(1,int(round(L/pw)));cuts=[sa+L*i/n for i in range(n+1)]
        long_wall=(L>=max(W,D)-1e-6)
        nwin=p['windows_long'] if long_wall else p['windows_short']
        idx=list(range(n));r.shuffle(idx);wins=sorted(idx[:min(nwin,max(n-1,0))]) if n>2 else []
        if name==p['door_wall'] and not explicit:
            dpan=[i for i in range(n) if i not in wins and 0<i<n-1] or [i for i in range(n) if i not in wins]
            di=r.choice(dpan);wins=[w for w in wins if w!=di]
        else:di=None
        wall_doors=[(q['s0'],q['s1'],0.,q['h'],0.) for q in explicit if q['wall']==name]
        if explicit:wins=[i for i in wins if not portal_overlaps(name,(cuts[i]+cuts[i+1]-p['win_w'])/2,(cuts[i]+cuts[i+1]+p['win_w'])/2,.15)]
        skip[name]=[(q[0],q[1]) for q in wall_doors]
        if wall_doors:openings[name]=list(skip[name])
        uf=(u0,u0+half) if inward>0 else (u0+half,u1)     # front = exterior? keep: first half is outer for S/W, inner for N/E
        ua=(u0,u0+half);ub=(u0+half,u1)
        for i in range(n):
            a,b=cuts[i],cuts[i+1];c=(a+b)/2
            op=None
            if i in wins:
                rise=min(p['win_w']*.8,p['win_h']*.4) if p['head']=='pointed' else 0.
                op=(c-p['win_w']/2,c+p['win_w']/2,p['sill'],p['sill']+p['win_h'],rise);windows.append(dict(wall=name,panel=i,s0=op[0],s1=op[1],z0=op[2],z1=op[3],rise=rise,family=p['window_family']))
            if di==i:op=(c-p['door_w']/2,c+p['door_w']/2,0.,p['door_h'],0.);door=dict(wall=name,panel=i,s0=op[0],s1=op[1],h=op[3])
            if op:openings.setdefault(name,[]).append((op[0],op[1]))
            if di==i:skip[name].append((op[0],op[1]))
            if p['interlock']=='half_lap':
                # half A (u0..u0+half) runs a..b+lap ; half B (u0+half..u1) runs a+... : B starts at a-? complementary lap
                a_end=b+(lap if i<n-1 else 0);b_start=a-(lap if i>0 else 0)
                # A-half: [a_start_A, a_end] where a_start_A = a + (lap if i>0 else 0) ; B-half: [b_start, b - (lap if i<n-1 else 0)]
                a_start=a+(lap if i>0 else 0);b_end=b-(lap if i<n-1 else 0)
                if explicit:
                    apertures=wall_doors+([op] if op else [])
                    slab_openings(M,a_start,a_end,ua[0],ua[1],0,H,apertures,'wall_plaster',axis)
                    slab_openings(M,b_start,b_end,ub[0],ub[1],0,H,apertures,'wall_plaster',axis)
                else:
                    slab_opening(M,a_start,a_end,ua[0],ua[1],0,H,op,'wall_plaster',axis)
                    slab_opening(M,b_start,b_end,ub[0],ub[1],0,H,op,'wall_plaster',axis)
                if i<n-1:joints.append(dict(wall=name,k=i,s=b,type='half_lap',a_end=a_end,next_a_start=cuts[i+1]+lap,b_end=b_end,next_b_start=cuts[i+1]-lap,lap=lap))
            else:
                if explicit:slab_openings(M,a,b,u0,u1,0,H,wall_doors+([op] if op else []),'wall_plaster',axis)
                else:slab_opening(M,a,b,u0,u1,0,H,op,'wall_plaster',axis)
                if i<n-1:joints.append(dict(wall=name,k=i,s=b,type='butt'))
            # bow-tie key plates across the joint, on the interior face
            if i<n-1 and p['gold']>0 and not portal_overlaps(name,b-.10,b+.10):
                for zk in (1.1,H-.7):
                    kw_,kd_=.20,.012
                    if name=='S':box(M,(b-kw_/2,0,zk),(b+kw_/2,kd_,zk+.07),'trim_gold')
                    elif name=='N':box(M,(b-kw_/2,D-kd_,zk),(b+kw_/2,D,zk+.07),'trim_gold')
                    elif name=='W':box(M,(0,b-kw_/2,zk),(kd_,b+kw_/2,zk+.07),'trim_gold')
                    else:box(M,(W-kd_,b-kw_/2,zk),(W,b+kw_/2,zk+.07),'trim_gold')
                sockets.append(dict(id='joint_%s_%d'%(name,i),wall=name,s=round(b,4),type=p['interlock']))
    report['door']=door;report['windows']=windows
    if explicit:
        report['explicit_openings']=explicit
        report['opening_sockets']=[opening_socket(q,W,D) for q in explicit]
    if p['tuning']:                       # stone pilasters rise exactly on the pressure antinodes, where the gold key plates ring
        pil=[]
        for name,axis,sa,sb,u0,u1,inward in walls:
            Lw=sb-sa;n_=max(1,int(round(Lw/pw)))
            for k in range(1,n_):
                s_=sa+Lw*k/n_;hw_=.075
                if portal_overlaps(name,s_-hw_-.01,s_+hw_+.01):continue
                pil.append((name,round(s_,6)))
                def pb(a0,a1,d0,d1,z0,z1,role):
                    if name=='S':box(M,(a0,d0,z0),(a1,d1,z1),role)
                    elif name=='N':box(M,(a0,D-d1,z0),(a1,D-d0,z1),role)
                    elif name=='W':box(M,(d0,a0,z0),(d1,a1,z1),role)
                    else:box(M,(W-d1,a0,z0),(W-d0,a1,z1),role)
                pb(s_-hw_,s_+hw_,0,.035,.18,H-.3,'stone');pb(s_-hw_-.01,s_+hw_+.01,0,.045,.18,.26,'trim_gold');pb(s_-hw_-.01,s_+hw_+.01,0,.045,H-.38,H-.3,'trim_gold')
        report['pilasters']=pil
    # trims along the interior faces
    def run(wall,z0,z1,depth,role,gold=False):
        for name,axis,sa,sb,u0,u1,inward in walls:
            if name!=wall and wall!='*':continue
            segs=[(sa,sb)]
            for o0,o1 in sorted(skip.get(name,[])):
                nxt=[]
                for a,b in segs:
                    if o1<=a or o0>=b:nxt.append((a,b));continue
                    if o0>a:nxt.append((a,o0))
                    if o1<b:nxt.append((o1,b))
                segs=nxt
            for a,b in segs:
                if axis=='x':
                    y0,y1=(0.,depth) if name=='S' else (D-depth,D);box(M,(a,y0,z0),(b,y1,z1),role)
                else:
                    x0,x1=(0.,depth) if name=='W' else (W-depth,W);box(M,(x0,a,z0),(x1,b,z1),role)
    if p['skirting']:run('*',0,.16,.03,'stone');run('*',.16,.175,.036,'trim_gold')
    if p['chair_rail']:run('*',.88,.93,.04,'stone');run('*',.93,.945,.05,'trim_gold')
    cs=p['cornice_style']
    def around(z0,z1,depth,role):
        box(M,(0,0,z0),(W,depth,z1),role);box(M,(0,D-depth,z0),(W,D,z1),role);box(M,(0,depth,z0),(depth,D-depth,z1),role);box(M,(W-depth,depth,z0),(W,D-depth,z1),role)
    if cs>=1:
        around(H-.14,H,.05,'stone');around(H-.22,H-.14,.09,'wall_plaster');around(H-.25,H-.22,.115,'trim_gold')
    if cs==2:
        around(H-.45,H-.40,.07,'stone');around(H-.50,H-.45,.10,'trim_gold')              # stepped reveals
    if cs>=1:                                                                              # gold panel mouldings on blank wall panels
        for name,axis,sa,sb,u0,u1,inward in walls:
            L=sb-sa;n=max(1,int(round(L/pw)))
            for i in range(n):
                a,b=sa+L*i/n,sa+L*(i+1)/n
                if any(abs((a+b)/2-(w['s0']+w['s1'])/2)<1e-6 for w in windows if w['wall']==name) or (door and door['wall']==name and abs((a+b)/2-(door['s0']+door['s1'])/2)<1e-6) or portal_overlaps(name,a,b):continue
                x0,x1,z0,z1=a+.14,b-.14,1.05,H-.55
                for (pa,pb) in (((x0,z0),(x1,z0)),((x1,z0),(x1,z1)),((x1,z1),(x0,z1)),((x0,z1),(x0,z0))):
                    fa=(0.012);
                    if axis=='x':
                        y=fa if name=='S' else D-fa;beam(M,(pa[0],y,pa[1]),(pb[0],y,pb[1]),.025,.012,'trim_gold')
                    else:
                        x=fa if name=='W' else W-fa;beam(M,(x,pa[0],pa[1]),(x,pb[0],pb[1]),.025,.012,'trim_gold')
    if p['quoins']:
        for (cx,cy,sx,sy) in ((0,0,1,1),(W,0,-1,1),(W,D,-1,-1),(0,D,1,-1)):
            for k in range(int((H-.7)/.34)):
                z=.3+k*.34;Lq=.26 if k%2==0 else .17;Lo=.17 if k%2==0 else .26
                x0,x1=sorted((cx,cx+sx*Lq));y0,y1=sorted((cy,cy+sy*.03));box(M,(x0,y0,z),(x1,y1,z+.28),'stone')
                x0,x1=sorted((cx,cx+sx*.03));y0,y1=sorted((cy,cy+sy*Lo));box(M,(x0,y0,z),(x1,y1,z+.28),'stone')
    # window infill: frame + family tracery + glazing
    for w in windows:
        name=w['wall'];axis='x' if name in('S','N') else 'y';s0,s1,z0,z1=w['s0'],w['s1'],w['z0'],w['z1'];mid=(s0+s1)/2
        def P3(s,z,off=0.):
            if name=='S':return (s,off,z)
            if name=='N':return (s,D-off,z)
            if name=='W':return (off,s,z)
            return (W-off,s,z)
        rise=w.get('rise',0.);hw=(s1-s0)/2;spring=z1-rise;pt=p['pane_t']
        # world slab of the pane: centred in the wall thickness
        if name=='S':ulo,uhi=-t/2-pt/2,-t/2+pt/2
        elif name=='N':ulo,uhi=D+t/2-pt/2,D+t/2+pt/2
        elif name=='W':ulo,uhi=-t/2-pt/2,-t/2+pt/2
        else:ulo,uhi=W+t/2-pt/2,W+t/2+pt/2
        def wsolid(sa,sb,za0,za1,zb0,zb1,role):
            if axis=='x':
                bot=[(sa,ulo,za0),(sb,ulo,zb0),(sb,uhi,zb0),(sa,uhi,za0)];top=[(sa,ulo,za1),(sb,ulo,zb1),(sb,uhi,zb1),(sa,uhi,za1)]
            else:
                bot=[(ulo,sa,za0),(uhi,sa,za0),(uhi,sb,zb0),(ulo,sb,zb0)];top=[(ulo,sa,za1),(uhi,sa,za1),(uhi,sb,zb1),(ulo,sb,zb1)]
            hexa_rings(M,bot,top,role)
        def rbox(sa,sb,off0,off1,za,zb,role):
            if name=='S':box(M,(sa,off0,za),(sb,off1,zb),role)
            elif name=='N':box(M,(sa,D-off1,za),(sb,D-off0,zb),role)
            elif name=='W':box(M,(off0,sa,za),(off1,sb,zb),role)
            else:box(M,(W-off1,sa,za),(W-off0,sb,zb),role)
        inset=.03
        if p['glass_mode']=='pane':                                     # the glass is a thin closed solid that fills the cut-out
            ps0,ps1,pz0=s0+inset,s1-inset,z0+inset
            if rise<=0:wsolid(ps0,ps1,pz0,z1-inset,pz0,z1-inset,'crystal_glass')
            else:
                N=12
                for i in range(N):
                    sa=ps0+(ps1-ps0)*i/N;sb=ps0+(ps1-ps0)*(i+1)/N
                    ta=spring+arch_z(hw-inset,rise-inset,sa-mid)if abs(sa-mid)<=hw-inset else spring
                    tb=spring+arch_z(hw-inset,rise-inset,sb-mid)if abs(sb-mid)<=hw-inset else spring
                    wsolid(sa,sb,pz0,ta,pz0,tb,'crystal_glass')
        # sash frame on the interior face: sides, sill rail and the arch
        beam(M,P3(s0,z0,.03),P3(s0,spring,.03),.05,.06,'trim_gold');beam(M,P3(s1,z0,.03),P3(s1,spring,.03),.05,.06,'trim_gold');beam(M,P3(s0,z0,.03),P3(s1,z0,.03),.05,.06,'trim_gold')
        if rise<=0:beam(M,P3(s0,z1,.03),P3(s1,z1,.03),.05,.06,'trim_gold');beam(M,P3(s0,spring,.03),P3(s0,z1,.03),.05,.06,'trim_gold');beam(M,P3(s1,spring,.03),P3(s1,z1,.03),.05,.06,'trim_gold')
        else:
            apts=[(mid+x,spring+z) for x,z in pointed(hw,rise,14)]
            for a_,b_ in zip(apts,apts[1:]):beam(M,P3(a_[0],a_[1],.03),P3(b_[0],b_[1],.03),.05,.06,'trim_gold')
        rbox(s0-.05,s1+.05,0.,p['sill_depth'],z0-.045,z0,'stone')                  # interior stone sill
        rbox(s0-.04,s1+.04,-t-.03,-t,z0-.06,z0-.01,'stone')                          # exterior drip ledge
        fam=w['family'];sh=z1-z0
        if fam=='panel':
            for k in (1,2):beam(M,P3(s0+(s1-s0)*k/3,z0,.03),P3(s0+(s1-s0)*k/3,z1,.03),.025,.04,'trim_gold')
            beam(M,P3(s0,z0+sh*.5,.03),P3(s1,z0+sh*.5,.03),.025,.04,'trim_gold')
        elif fam=='geometric':
            beam(M,P3(mid,z0,.03),P3(mid,z1-hw*.9,.03),.03,.04,'trim_gold')
            for rr in (hw*.55,):
                pts=[(mid+rr*math.cos(TAU*i/24),z1-hw*.9+rr*math.sin(TAU*i/24)) for i in range(25)]
                for a,b in zip(pts,pts[1:]):beam(M,P3(a[0],a[1],.03),P3(b[0],b[1],.03),.02,.03,'trim_gold')
        else:   # intersecting: two crossing sine arcs + a centre mullion
            for sgn in (-1,1):
                pts=[(s0+(s1-s0)*i/16,z0+sh*.5+sgn*sh*.38*math.sin(math.pi*i/16)) for i in range(17)]
                for a_,b_ in zip(pts,pts[1:]):beam(M,P3(a_[0],a_[1],.03),P3(b_[0],b_[1],.03),.02,.03,'trim_gold')
            beam(M,P3(mid,z0,.03),P3(mid,z1,.03),.025,.04,'trim_gold')
        if cs==2:                                                                          # arch medallion above the head
            cxm=P3(mid,z1+.28,0.)
            for rr in (.18,.12):
                for i in range(24):
                    a0=TAU*i/24;a1=TAU*(i+1)/24
                    pa=P3(mid+rr*math.cos(a0),z1+.28+rr*math.sin(a0),.012);pb=P3(mid+rr*math.cos(a1),z1+.28+rr*math.sin(a1),.012)
                    beam(M,pa,pb,.018,.012,'trim_gold')
    # Nikki decorators
    rng=random.Random('nikki:%s'%p['seed'])
    def inner_point(name,s,z,off=.05):
        if name=='S':return (s,off,z)
        if name=='N':return (s,D-off,z)
        if name=='W':return (off,s,z)
        return (W-off,s,z)
    if p['swag']:
        zt=H-.30
        for name,axis,sa,sb,u0,u1,inward in walls:
            L=sb-sa;n=max(1,int(round(L/pw)))
            for i in range(n):
                a,b=sa+L*i/n+.08,sa+L*(i+1)/n-.08;mid=(a+b)/2;ln=b-a
                pts=[]
                for k in range(p['bead_count']):
                    s=a+ln*k/(p['bead_count']-1);q=(2*(s-mid)/ln)
                    z=zt-p['droop']*(1-q*q);pts.append(inner_point(name,s,z,.07))
                for k in range(len(pts)-1):beam(M,pts[k],pts[k+1],.006,.006,'trim_gold')
                for q in pts:sphere(M,q,p['bead_r'],'pearl_shell')
    if p['wall_beads']:
        for name,axis,sa,sb,u0,u1,inward in walls:
            L=sb-sa
            for k in range(p['wall_beads']):
                s=sa+L*(k+1)/(p['wall_beads']+1)
                if any(o0-.1<=s<=o1+.1 for o0,o1 in openings.get(name,[])):continue
                z=H-.5
                while z>1.2:
                    sphere(M,inner_point(name,s,z,.05),p['bead_r']*.85,'pearl_shell');z-=.11
                beam(M,inner_point(name,s,H-.5,.05),inner_point(name,s,z+.11,.05),.004,.004,'trim_gold')
    for k in range(p['star_pendants']):
        cx=W*(.3+.4*rng.random());cy=D*(.3+.4*rng.random());drop=rng.uniform(.55,1.1)
        beam(M,(cx,cy,H),(cx,cy,H-drop),.006,.006,'trim_gold')
        prism(M,star_pts(.13,.055,8,rng.uniform(0,.39),cx,cy),H-drop-.015,H-drop,'gold')
        octa(M,(cx,cy,H-drop-.12),.03,.06,'crystal_glass');beam(M,(cx,cy,H-drop-.015),(cx,cy,H-drop-.07),.004,.004,'trim_gold')
    if p['star_panel'] and not any(q['wall'] in ('S','N') and q['s0']<W/2+.36 and q['s1']>W/2-.36 for q in explicit):
        name='S' if not door or door['wall']!='S' else 'N';cx=W/2;z=1.85;off=.02
        r_out,r_in=.24,.11;sp=star_pts(r_out,r_in,8,0.,0,0)
        pl=[(cx+sp[i][0],z+sp[i][1]) for i in range(len(sp))];circ=[(cx+.34*math.cos(TAU*i/len(sp)),z+.34*math.sin(TAU*i/len(sp))) for i in range(len(sp))]
        def Q(x,zz,o):return (x,o,zz) if name=='S' else (x,D-o,zz)
        for i in range(len(sp)):
            a,b=pl[i],pl[(i+1)%len(sp)];c,d=circ[(i+1)%len(sp)],circ[i]
            M.poly([Q(a[0],a[1],off),Q(b[0],b[1],off),Q(c[0],c[1],off),Q(d[0],d[1],off)][::-1] if name=='S' else [Q(a[0],a[1],off),Q(b[0],b[1],off),Q(c[0],c[1],off),Q(d[0],d[1],off)],'stone')
        for i in range(len(sp)):
            a,b=pl[i],pl[(i+1)%len(sp)]
            beam(M,Q(a[0],a[1],off+.004),Q(b[0],b[1],off+.004),.014,.01,'trim_gold')
    if p['heart_chain']:
        for name,axis,sa,sb,u0,u1,inward in walls:
            if name not in ('N','E'):continue
            L=sb-sa;k=0;s=sa+.45
            while s<sb-.3:
                if not any(o0-.15<=s<=o1+.15 for o0,o1 in openings.get(name,[])):
                    hp=heart_pts(.11);zc=1.03
                    pts3=[inner_point(name,s+q[0],zc+q[1],.03) for q in hp]
                    for j in range(len(pts3)):beam(M,pts3[j],pts3[(j+1)%len(pts3)],.012,.012,'trim_gold')
                s+=.38
    # ribbon streamer hooks: curtain rods above windows, swag low points, star pendants (ribbons are Vellum-baked, see place_streamers)
    ssock=[]
    inward={'S':(0.,1.),'N':(0.,-1.),'W':(1.,0.),'E':(-1.,0.)}
    if p['streamers']>0:
        for w in windows:
            nm=w['wall'];s0_,s1_=w['s0'],w['s1'];zr=w['z1']+.14;mid_=(s0_+s1_)/2
            a_=inner_point(nm,s0_-.12,zr,.14);b_=inner_point(nm,s1_+.12,zr,.14)
            beam(M,a_,b_,.022,.022,'trim_gold')                                   # curtain rod
            for sgn in (-1,1):sphere(M,inner_point(nm,mid_+sgn*(s1_-s0_)/2+sgn*.12,zr,.14),.03,'trim_gold')
            for f_ in (-.36,0.,.36):
                q=inner_point(nm,mid_+f_*(s1_-s0_),zr-.012,.14);ssock.append(dict(pos=q,inward=inward[nm],kind='window'))
        if p['swag']:
            for name,axis,sa,sb,u0,u1,inw in walls:
                Lw=sb-sa;n_=max(1,int(round(Lw/pw)))
                for i in range(n_):
                    mid_=sa+Lw*(i+.5)/n_;q=inner_point(name,mid_,H-.30-p['droop']-.03,.09)
                    if not any(o0-.3<=mid_<=o1+.3 for o0,o1 in openings.get(name,[])):ssock.append(dict(pos=q,inward=inward[name],kind='swag'))
    r.shuffle(ssock)
    # floor medallion (Chladni figure of the room's own note)
    mode=None
    if p['floor_medallion']:
        pairs=[(a,b) for a in range(1,6) for b in range(a+1,7)];rr=random.Random('chl:%s'%p['seed']);rr.shuffle(pairs);mode=tuple(ac['chladni_mode']) if ac else pairs[0]
        cx,cy=W/2,D/2;R=min(W,D)/2-.55;rot=rr.uniform(0,.79)
        ring(M,cx,cy,R,.05,.004,'trim_gold');ring(M,cx,cy,R-.16,.03,.004,'trim_gold')
        c,s_=math.cos(rot),math.sin(rot);RR=R-.22
        for a,b in chladni_segments(*mode):
            if math.hypot(*a)>1 or math.hypot(*b)>1:continue
            strip(M,(cx+RR*(a[0]*c-a[1]*s_),cy+RR*(a[0]*s_+a[1]*c)),(cx+RR*(b[0]*c-b[1]*s_),cy+RR*(b[0]*s_+b[1]*c)),.035,.004,'trim_gold')
    light=None
    if p['dawn_puzzle'] and p['floor_medallion'] and windows:
        tgt=(W/2,D/2,0.);t_mid=-t/2;best=None
        for wi,w in enumerate(windows):
            name=w['wall'];s0_,s1_,z0_,z1_=w['s0'],w['s1'],w['z0'],w['z1'];rise_=w.get('rise',0.);hw_=(s1_-s0_)/2;mid_=(s0_+s1_)/2;ins=.03
            poly=[(s0_+ins,z0_+ins),(s1_-ins,z0_+ins),(s1_-ins,z1_-rise_)]
            if rise_>0:poly+=[(mid_+x,z1_-rise_+z) for x,z in pointed(hw_-ins,rise_-ins,10)[::-1][1:-1]]
            else:poly+=[(s1_-ins,z1_-ins),(s0_+ins,z1_-ins)]
            poly+=[(s0_+ins,z1_-rise_)]
            def W3(sv,zv):
                if name=='S':return (sv,t_mid,zv)
                if name=='N':return (sv,D-t_mid,zv)
                if name=='W':return (t_mid,sv,zv)
                return (W-t_mid,sv,zv)
            Q=[W3(a_,b_) for a_,b_ in poly];C=tuple(sum(q[k] for q in Q)/len(Q) for k in range(3))
            d,P=project_patch(Q,C,tgt)
            el=math.degrees(math.asin(-d[2]));inside=all(.15<=q[0]<=W-.15 and .15<=q[1]<=D-.15 for q in P)
            cen=tuple(sum(q[k] for q in P)/len(P) for k in range(3));err=math.hypot(cen[0]-tgt[0],cen[1]-tgt[1])
            if inside and 8<=el<=45 and err<1e-6 and (best is None or abs(el-24)<abs(best['el']-24)):
                best=dict(window=wi,wall=name,patch=[(round(q[0],5),round(q[1],5)) for q in P],el=el,d=d,err=err)
        if best:
            P=best['patch']
            for a_,b_ in zip(P,P[1:]+P[:1]):strip(M,a_,b_,.03,.006,'trim_gold')               # gold outline of the light patch
            S=_norm((-best['d'][0],-best['d'][1],-best['d'][2]))                                  # direction TOWARD the sun
            az=math.degrees(math.atan2(S[1],S[0]))%360
            lat=math.radians(p['latitude']);sin_el=math.sin(math.radians(best['el']))
            hr=(12-math.degrees(math.acos(min(1,sin_el/math.cos(lat))))/15.) if sin_el<=math.cos(lat) else None
            light=dict(window=best['window'],wall=best['wall'],sun_elevation_deg=round(best['el'],3),sun_azimuth_room_deg=round(az,3),
                       sun_dir_to_sun_room=[round(c,6) for c in S],patch=best['patch'],center_error_m=best['err'],
                       approx_equinox_solar_hour=None if hr is None else round(hr,2),
                       note='room frame, azimuth CCW from +x. UE sun: travel dir = -S with y mirrored, then add the room actor yaw.')
    report.update(acoustics=ac,light_puzzle=light,params=p,streamer_sockets=ssock[:max(0,p['streamers'])],joints=joints,sockets=sockets,chladni=dict(mode=list(mode),hz=round(55*(mode[0]**2+mode[1]**2)/2,1)) if mode else None)
    return M,report

def manifest(rep,anchor=(0.,0.,0.),yaw_deg=0.):
    """Room acoustics + light puzzle as data for Unreal (cm; UE y mirrored; yaw sign flipped)."""
    out=dict(acoustics=rep.get('acoustics'),light_puzzle=None,anchor_ue_cm=list(anchor),room_yaw_ue=-yaw_deg)
    lp=rep.get('light_puzzle')
    if lp:
        S=lp['sun_dir_to_sun_room'];c,s_=math.cos(math.radians(-yaw_deg)),math.sin(math.radians(-yaw_deg))
        Sx,Sy=S[0],-S[1];Sx,Sy=Sx*c-Sy*s_,Sx*s_+Sy*c
        trav=(-Sx,-Sy,-S[2])
        out['light_puzzle']=dict(lp,directional_light_ue=dict(pitch=round(math.degrees(math.atan2(trav[2],math.hypot(trav[0],trav[1]))),3),yaw=round(math.degrees(math.atan2(trav[1],trav[0])),3),roll=0.),
                                  medallion_ue_cm=[anchor[0]+rep['params']['W']*50,anchor[1]-rep['params']['D']*50,anchor[2]])
    return out

# --------------------------------------------------------------------------- ribbon streamers (Vellum-baked library)
def place_streamers(M,rep,lib,loader):
    """lib: [{variant,length_m,wind:[x,y,0],drift_xy_m}]; loader(variant) -> [(role,[pts])] in Houdini-oriented order (appended as-is).
    Each ribbon is rotated so its simulated wind-lean points into the room; placements that leave the room or touch the floor are rejected."""
    p=rep['params'];W,D=p['W'],p['D'];r=random.Random('streamers:%s'%p['seed']);placed=[]
    for k,sk in enumerate(rep.get('streamer_sockets',[])):
        x,y,z=sk['pos'];nx,ny=sk['inward'];cands=[v for v in lib if v['length_m']<=z-.12];r.shuffle(cands);done=None
        for v in cands:
            ang=math.atan2(ny,nx)-math.atan2(v['wind'][1],v['wind'][0]);c,s_=math.cos(ang),math.sin(ang)
            faces=[(role,[(x+c*q[0]-s_*q[1],y+s_*q[0]+c*q[1],z+q[2]) for q in pts]) for role,pts in loader(v['variant'])]
            if all(.03<=q[0]<=W-.03 and .03<=q[1]<=D-.03 and q[2]>=.05 for _,pts in faces for q in pts):
                for role,pts in faces:
                    st=len(M.P);M.P.extend(pts);M.F.append(list(range(st,len(M.P))));M.R.append(role)
                done=dict(socket=k,kind=sk['kind'],variant=v['variant'],yaw_deg=round(math.degrees(ang),2),length_m=v['length_m']);break
        placed.append(done or dict(socket=k,kind=sk['kind'],variant=None,skipped=True))
    rep['streamers_placed']=placed;return placed

# --------------------------------------------------------------------------- gates (pure python)
def signed_volume_righthand(M):
    v=0.
    for f in M.F:
        pts=[M.P[i] for i in reversed(f)]          # undo the storage reversal -> right-hand order
        a=pts[0]
        for i in range(1,len(pts)-1):
            b,c=pts[i],pts[i+1];n=_cross(_sub(b,a),_sub(c,a));v+=(a[0]*n[0]+a[1]*n[1]+a[2]*n[2])/6
    return v

def gate(M,rep):
    p=rep['params'];out={};W,D,H,t=p['W'],p['D'],p['H'],p['wall_t']
    out['solid_volume_positive']=signed_volume_righthand(M)>0
    xs=[q[0] for q in M.P];ys=[q[1] for q in M.P];zs=[q[2] for q in M.P]
    proj=.03 if rep['windows'] else 0.      # exterior drip ledges project 3 cm past the outer wall face
    ex=lambda lo,hi,a,b:lo>=a-proj-1e-6 and lo<=a+1e-6 and hi<=b+proj+1e-6 and hi>=b-1e-6
    out['bounds_ok']=ex(min(xs),max(xs),-t,W+t) and ex(min(ys),max(ys),-t,D+t) and min(zs)>=-.2-1e-6 and max(zs)<=H+.2+1e-6
    jf=True;maxerr=0.
    for j in rep['joints']:
        if j['type']=='half_lap':
            e1=abs(j['a_end']-(j['next_a_start']-0));# half A of panel i ends at b+lap; half A of panel i+1 starts at b+lap
            e2=abs(j['b_end']-j['next_b_start']);maxerr=max(maxerr,e1,e2)
    out['joint_max_error_mm']=round(maxerr*1000,4);out['joints']=len(rep['joints']);out['joints_fit']=maxerr<1e-6
    out['windows_in_panels']=all(w['s1']-w['s0']<=p['panel_w']-.2 and w['z1']<=H-.5 for w in rep['windows'])
    d=rep['door'];out['door_clear']=(d is None) or (d['h']<=H-.4)
    out['panes_fit']=all(w['s1']-w['s0']-.06>0 and w['z1']-w['z0']-.06>0 for w in rep['windows'])
    ups=0;tot=0
    for f,r in zip(M.F,M.R):
        if r=='trim_gold' and all(abs(M.P[i][2]-.004)<1e-9 for i in f):
            a,b,c=[M.P[i] for i in f[:3]];n=_cross(_sub(b,a),_sub(c,a));tot+=1;ups+=1 if n[2]<0 else 0   # stored clockwise: Houdini front = up when right-hand normal points down
    out['floor_inlay_up']=(tot==0) or ups==tot
    sp=rep.get('streamers_placed')
    if sp is not None:
        want=len(rep.get('streamer_sockets',[]));got=sum(1 for q in sp if q.get('variant') is not None)
        out['streamers_placed']=got;out['streamers_wanted']=want;out['streamers_ok']=(want==0) or got>=max(1,int(.7*want))
    ac=rep.get('acoustics')
    if ac:
        sx=sorted({round(q['s'],6) for q in rep['sockets'] if q['wall'] in('S','N')});sy=sorted({round(q['s'],6) for q in rep['sockets'] if q['wall'] in('W','E')})
        out['keys_on_antinodes']=all(any(abs(v-a)<1e-6 for a in ac['antinodes']['x']) for v in sx) and all(any(abs(v-a)<1e-6 for a in ac['antinodes']['y']) for v in sy)
        out['windows_on_nodes']=all(any(abs((w['s0']+w['s1'])/2-a)<1e-6 for a in ac['nodes']['x' if w['wall'] in('S','N') else 'y']) for w in rep['windows'])
        out['room_note_audible']=110<=ac['room_note_hz']<220.0001
        expected_joints=rep['joints']
        if rep.get('explicit_openings'):
            expected_joints=[j for j in expected_joints if not any(q['wall']==j['wall'] and q['s0']<j['s']+.085 and q['s1']>j['s']-.085 for q in rep['explicit_openings'])]
        out['pilasters_match_joints']=len(rep.get('pilasters',[]))==len(expected_joints)
        out['chladni_from_room']=(rep['chladni'] is None) or rep['chladni']['mode']==ac['chladni_mode']
    if rep['params'].get('dawn_puzzle') and rep['params'].get('floor_medallion') and rep['windows']:
        lp=rep.get('light_puzzle');out['dawn_puzzle_ok']=bool(lp) and lp['center_error_m']<1e-6 and 8<=lp['sun_elevation_deg']<=45
    out['all_pass']=all(v for k,v in out.items() if isinstance(v,bool))
    out['prims']=len(M.F)
    return out


# ---------------------------------------------------------------- HDA glue (runs inside Houdini / Houdini Engine)
def _uv(P,face):
    a,b,c=P[face[0]],P[face[1]],P[face[2]]
    n=_cross(_sub(b,a),_sub(c,a));ax=max(range(3),key=lambda i:abs(n[i]))
    return [((P[i][1],P[i][2]) if ax==0 else (P[i][0],P[i][2]) if ax==1 else (P[i][0],P[i][1])) for i in face]

def cook(node):
    import hou
    h=node.parent()
    kw=dict(W=h.evalParm('room_w'),D=h.evalParm('room_d'),H=h.evalParm('room_h'),wall_t=h.evalParm('wall_t'),panel_w=h.evalParm('panel_w'),
            seed=h.evalParm('seed'),decor=h.parm('decor').evalAsString(),interlock=h.parm('interlock').evalAsString(),lap=h.evalParm('lap'),
            windows_long=h.evalParm('windows_long'),windows_short=h.evalParm('windows_short'),win_w=h.evalParm('win_w'),win_h=h.evalParm('win_h'),
            sill=h.evalParm('sill'),door_wall=h.parm('door_wall').evalAsString(),door_w=h.evalParm('door_w'),door_h=h.evalParm('door_h'),
            bead_count=h.evalParm('bead_count'),droop=h.evalParm('droop'),bead_r=h.evalParm('bead_r'),
            floor_medallion=bool(h.evalParm('floor_medallion')),skirting=bool(h.evalParm('skirting')),chair_rail=bool(h.evalParm('chair_rail')),
            head=h.parm('head').evalAsString(),glass_mode=h.parm('glass_mode').evalAsString(),streamers=h.evalParm('streamers'),
            tuning=bool(h.evalParm('tuning')),dawn_puzzle=bool(h.evalParm('dawn_puzzle')),latitude=h.evalParm('latitude'))
    if h.parm('openings_json'):
        records=json.loads(h.evalParm('openings_json'))
        if records:kw['explicit_openings']=records
        elif records!=[]:raise ValueError('explicit openings must be an array')
    ov=h.evalParm('cornice_override')
    if ov>=0:kw['cornice_style']=ov
    M,rep=build(**kw)
    libdir=h.evalParm('streamer_lib')
    if kw['streamers']>0 and libdir:
        import os
        meta=os.path.join(libdir,'library.json')
        if os.path.exists(meta):
            lib=json.load(open(meta))['variants'];cache={}
            def loader(vi):
                if vi not in cache:
                    gg=hou.Geometry();gg.loadFromFile(os.path.join(libdir,'ribbon_%02d.bgeo.sc'%vi))
                    cache[vi]=[('ribbon_silk',[tuple(v.point().position()) for v in pr.vertices()]) for pr in gg.prims()]
                return cache[vi]
            place_streamers(M,rep,lib,loader)
    gt=gate(M,rep)
    g=node.geometry();g.clear()
    g.addAttrib(hou.attribType.Prim,'material_role','');g.addAttrib(hou.attribType.Prim,'shop_materialpath','')
    g.addAttrib(hou.attribType.Vertex,'uv',(0.,0.,0.))
    g.addAttrib(hou.attribType.Global,'gate_json','');g.addAttrib(hou.attribType.Global,'sockets_json','')
    yup=bool(h.evalParm('engine_y_up'))
    P=[(p[0],p[2],-p[1]) for p in M.P] if yup else M.P      # Houdini Engine swaps Y/Z: emit (x, z, -y) so UE gets (x*100, -y*100, z*100)
    pts=g.createPoints(P)
    flip=yup and bool(h.evalParm('engine_flip'))     # Houdini Engine's Y/Z swap is a reflection: reverse winding so UE front faces stay outward
    collision_enabled=bool(h.parm('simple_floor_collision') and h.evalParm('simple_floor_collision'))
    render_group=g.createPrimGroup('rendered_main_geo') if collision_enabled else None
    for face,role in zip(M.F,M.R):
        face=list(reversed(face)) if flip else face
        poly=g.createPolygon();poly.setAttribValue('material_role',role);poly.setAttribValue('shop_materialpath','/mat/Cathedral_'+role)
        if render_group is not None:render_group.add(poly)
        uvs=_uv(M.P,face)
        for i,uv in zip(face,uvs):
            v=poly.addVertex(pts[i]);v.setAttribValue('uv',(uv[0]*.5,uv[1]*.5,0.))
    # Invisible simple collision is a separate slab, never a box around the room.
    # The existing rendered floor and all portal geometry remain unchanged.
    if collision_enabled:
        collision=g.createPrimGroup('collision_geo_simple_box_main_geo')
        for face,role in zip(M.F,M.R):
            if role!='floor_stone':continue
            face=list(reversed(face)) if flip else face
            poly=g.createPolygon()
            for i in face:
                point=g.createPoint();point.setPosition(P[i]);poly.addVertex(point)
            collision.add(poly)
    payload=dict(sockets=rep['sockets'],windows=rep['windows'],door=rep['door'],chladni=rep['chladni'],streamers=rep.get('streamers_placed'),room=manifest(rep))
    if rep.get('opening_sockets'):payload['opening_sockets']=rep['opening_sockets']
    g.setGlobalAttribValue('gate_json',json.dumps(gt));g.setGlobalAttribValue('sockets_json',json.dumps(payload))
