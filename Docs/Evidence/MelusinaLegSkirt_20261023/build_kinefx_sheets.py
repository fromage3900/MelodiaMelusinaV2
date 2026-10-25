"""Evidence-derived technical-art sheets; reads pinned data, never touches UE."""
from pathlib import Path
import os,json,hashlib,collections,textwrap
HERE=Path(__file__).resolve().parent
OUT=HERE/'Sheets';OUT.mkdir(exist_ok=True)
os.environ['MPLCONFIGDIR']=str(OUT/'.mpl_cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

BG='#101722';PANEL='#172332';FG='#f0f2fa';MUTED='#aebed0'
TEAL='#76dec8';PINK='#f09fc3';GOLD='#edbd78';BLUE='#9cafff'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':FG,
 'axes.labelcolor':MUTED,'xtick.color':MUTED,'ytick.color':MUTED,
 'axes.edgecolor':'#485970','axes.facecolor':PANEL,'figure.facecolor':BG,
 'savefig.facecolor':BG,'grid.color':'#344456','grid.alpha':.45,
 'axes.titleweight':'bold','axes.titlecolor':FG,'legend.facecolor':PANEL,
 'legend.edgecolor':'#485970'})
inputs={}
def read(rel):
 p=HERE/rel;inputs[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
 return json.loads(p.read_text())
def base(title,subtitle):
 f=plt.figure(figsize=(16,9),dpi=180)
 f.text(.045,.949,'MELUSINA  /  KINEFX & RUNTIME LAB',color=TEAL,fontsize=10,weight='bold')
 f.text(.045,.906,title,fontsize=22,weight='bold')
 f.text(.045,.873,subtitle,color=MUTED,fontsize=10)
 return f
def style(ax,x=None,y=None):
 ax.grid(True,zorder=0)
 ax.spines[['top','right']].set_visible(False)
 if x:ax.set_xlabel(x)
 if y:ax.set_ylabel(y)
def foot(f,line1,line2):
 f.text(.045,.055,line1,color=MUTED,fontsize=8.5)
 f.text(.045,.030,line2,color=GOLD,fontsize=8.5)
def save(f,name):
 p=OUT/name;f.savefig(p,dpi=180);plt.close(f);return p

baseline=read('runtime_layer_comparison.json')
before=next(x for x in baseline['samples'] if x['case']=='all_on_body' and x['view']=='front')
after=read('ground_frame_clean_boots.json')
bounds=read('baseline_skinned_bounds.json')
ground=read('A_Shin_Idle_stand_MocapConv_ground_frame.json')
codec_controls=[read(name+'_recompression_control.json') for name in [
 'A_Melusina_Walk_Mocap_RootX_SeamFix','A_Melusina_Run_Mocap_RootX_SeamFix','A_Melusina_Sprint_Mocap_RootX']]
assert all(x['passed'] and x['source_file_unchanged'] for x in codec_controls)
contact=read('KineFX/contact_summary.json')
roundtrip=read('KineFX/boots_candidate_roundtrip.json')
delta=read('KineFX/boots_weight_delta.json')
boot=read('KineFX/SK_Melusina_V2_Boots_data.json')
skirt=read('KineFX/SK_Melusina_V2_Skirt_R2_SmoothChains_data.json')
reach=read('KineFX/skirt_tip_reach.json')
native_axis=read('KineFX/native_tip_axis_verification.json')
axis_stage=read('native_skirt_axis_candidate.json')
axis_idle=read('native_axis_idle_contact.json')
assert native_axis['passed'] and axis_stage['passed']
assert roundtrip['passed'] and all(roundtrip['gate'].values())
assert len(delta['verts'])==843
for source in contact['provenance']:
 p=Path(source['file']);assert hashlib.sha256(p.read_bytes()).hexdigest()==source['sha256']

# 01: actual native idle comparison, component-space bones translated to the
# measured harness world base. Source/bind data is not substituted for this test.
f=base('01  /  Why the knees folded — and what the staged fix proves',
 'LIVE STAGED IDLE  •  same canonical body and native solvers  •  diagnostic collision floor Z = 0 cm')
gs=f.add_gridspec(2,2,left=.055,right=.96,top=.815,bottom=.145,hspace=.40,wspace=.24,height_ratios=[1.25,1])
ax=f.add_subplot(gs[:,0]);style(ax,'Sagittal depth + comparison separation (cm)','World height (cm)')
for label,pose,offset,color in [('Old target lifts',before['bones_cs'],-45,GOLD),('Ground-frame candidate',after['bones'],45,TEAL)]:
 for side,marker in [('l','o'),('r','s')]:
  v=np.array([pose[n+'_'+side] for n in ['thigh_stretch','leg_stretch','foot']])
  ax.plot(v[:,1]+offset,v[:,2]+17.15,'-',marker=marker,lw=3,ms=5,color=color)
 ax.text(offset+3,116,label,ha='center',fontsize=10,color=color,weight='bold')
ax.axhline(0,color=FG,lw=1.3);ax.text(-77,3,'collision floor',fontsize=9,color=MUTED)
ax.set_ylim(-5,132);ax.set_xlim(-83,80)
ax.set_title('Anatomical hip → knee → ankle',loc='left',pad=15)
ax.text(.04,.965,'Side projection; examples separated for comparison.',transform=ax.transAxes,va='top',fontsize=9,color=MUTED)
ax=f.add_subplot(gs[0,1]);style(ax,y='Interior knee angle (degrees)')
x=np.arange(2);b=[before['derived'][s]['knee_angle'] for s in ['l','r']];a=[after['knees'][s] for s in ['l','r']]
ax.bar(x-.18,b,.33,color=GOLD,label='old targets',zorder=3);ax.bar(x+.18,a,.33,color=TEAL,label='staged ground frame',zorder=3)
for xx,vals in [(x-.18,b),(x+.18,a)]:
 for px,v in zip(xx,vals):ax.text(px,v+4,f'{v:.2f}°',ha='center',fontsize=10)
ax.axhline(180,color=MUTED,lw=.8,ls=':');ax.set_ylim(0,211);ax.set_xticks(x,['Left','Right']);ax.legend(fontsize=8,loc='upper left');ax.set_title('Fold removed with FootPlacement + LegIK still enabled',loc='left',fontsize=11)
ax=f.add_subplot(gs[1,1]);ax.axis('off')
old=min(x['min_z'] for x in bounds['meshes'] if 'Boots' in x['name'])
feet=next(x for x in after['skin'] if 'Boots' in x['component'])['per_foot_lowest_world_z']
text=(f'BOOT SUPPORT — actual CPU-skinned render LOD0\n'
 f'Old lowest boot point: {abs(old):.2f} cm below the floor\n'
 f'Staged heel minima: L {feet["l"]:+.3f} / R {feet["r"]:+.3f} cm\n\n'
 'SOURCE POSE PRESERVATION — idle duplicate only\n'
 f'{ground["compressed_pose_preservation"]["frames"]} keys × {ground["compressed_pose_preservation"]["bones_checked"]} checked bones\n'
 'Maximum world-position delta 0.000001907 cm; quaternion Δ 0\n\n'
 'Walk / run / sprint same-codec pose controls now pass.\n'
 'OPEN: live movement/contact matrix,\n'
 'skirt motion and reload. Production references are unchanged.')
ax.text(0,1,text,va='top',linespacing=1.6,fontsize=10,color=MUTED)
foot(f,'Evidence: runtime_layer_comparison.json • ground_frame_clean_boots.json • idle ground-frame preservation receipt',
 'This is a staged flat-idle result. It does not certify walking, physical input, slopes, reset or production admission.')
outputs=[save(f,'sheet_01_runtime_leg_grounding.png')]

# 02: exact source points and changed indexed vertices, with no rendered
# pose or final runtime clearance inferred from the bind-space display.
f=base('02  /  Keep the boots on their own legs',
 'KINEFX SOURCE / BIND  •  modeled high heels are real geometry  •  weight repair is additive and duplicate-only')
gs=f.add_gridspec(1,3,left=.055,right=.965,top=.80,bottom=.19,wspace=.25,width_ratios=[1.05,1.05,1.15])
v=np.array(boot['positions_m'])*100
kilt=np.array([sum(w for n,w in pairs if 'kilt' in n) for pairs in boot['weights']])
changed=np.array(sorted(map(int,delta['verts'])))
ax=f.add_subplot(gs[0,0]);style(ax,'Depth (cm)','Bind height (cm)')
mask=v[:,0]>0
ax.scatter(v[mask,2],v[mask,1],s=4,c=MUTED,alpha=.35,rasterized=True)
bad=mask&(kilt>1e-6);ax.scatter(v[bad,2],v[bad,1],s=10,c=PINK,label='skirt-bound points',rasterized=True)
ax.axhline(contact['boots']['lowest_bind_point']['position_m'][1]*100,color=TEAL,ls='--',lw=1,label='actual heel support')
ax.set_title('Left boot: source skin leak',loc='left',fontsize=11);ax.legend(fontsize=8,loc='upper right');ax.set_aspect('equal',adjustable='box')
ax=f.add_subplot(gs[0,1]);style(ax,'Lateral position (cm)','Bind height (cm)')
ax.scatter(v[:,0],v[:,1],s=4,c=MUTED,alpha=.28,rasterized=True)
ax.scatter(v[changed,0],v[changed,1],s=6,c=TEAL,alpha=.8,label='843 repaired vertices',rasterized=True)
ax.set_title('Two boots: changed weights only',loc='left',fontsize=11);ax.legend(fontsize=8,loc='upper right');ax.set_aspect('equal',adjustable='box')
ax=f.add_subplot(gs[0,2]);ax.axis('off')
summary=(f'843 / 5,540 vertices repaired\n\n'
 f'Source skirt influences: {contact["boots"]["kilt_points_any"]} points\n'
 f'Opposite-leg influence >1%: {contact["boots"]["opposite_side_points_over_1pct"]} points\n'
 '(These cohorts overlap.)\n\n'
 'CANDIDATE ROUNDTRIP: 12 / 12 gates pass\n'
 '• No skirt or opposite-leg influences\n'
 '• All weight sums normalized; none unweighted\n'
 '• Four influences maximum\n'
 '• Geometry / topology / materials unchanged\n'
 '• All 465 joints and bind matrices unchanged\n\n'
 f'Modeled sole depth below barefoot skin:\n{contact["boots"]["bind_min_below_barefoot_cm"]:.3f} cm in bind\n\n'
 'Source candidate is imported in staging.\n'
 'Default wardrobe/catalog admission is still open.')
ax.text(0,1,summary,va='top',linespacing=1.65,fontsize=10,color=MUTED)
foot(f,'Evidence: exact fresh UE FBX → KineFX • boots_weight_delta.json • boots_candidate_roundtrip.json',
 'Bind geometry proves rig and weight preservation. Runtime support is measured separately in Sheet 01; movement remains open.')
outputs.append(save(f,'sheet_02_boot_skinning.png'))

# 03: use the same connected-triangle island definition as the KineFX audit
# to display existing layers; this computes display labels only.
sv=np.array(skirt['positions_m'])*100
parents=list(range(len(sv)))
def find(i):
 while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
 return i
for tri in skirt['primitive_ids']:
 a=find(tri[0])
 for i in tri[1:]:
  b=find(i)
  if a!=b:parents[b]=a
groups=collections.defaultdict(list)
for i in range(len(sv)):groups[find(i)].append(i)
groups=sorted(groups.values(),key=len,reverse=True)
assert [len(g) for g in groups[:3]]==[20781,6476,1440]
f=base('03  /  One skirt rig, three authored hem surfaces',
 'KINEFX SOURCE / BIND  •  preserve shared seams  •  measure proxy reach before touching Kawaii settings')
gs=f.add_gridspec(2,2,left=.055,right=.965,top=.80,bottom=.155,hspace=.36,wspace=.25,width_ratios=[1.12,1])
ax=f.add_subplot(gs[:,0]);style(ax,'Depth (cm)','Bind height (cm)')
ax.scatter(sv[:,2],sv[:,1],s=2,c=MUTED,alpha=.14,rasterized=True)
for i,color in enumerate([BLUE,TEAL,PINK]):
 pts=sv[groups[i]];ax.scatter(pts[:,2],pts[:,1],s=2,c=color,alpha=.45,label=f'hem surface {i+1}  /  {len(pts):,} points',rasterized=True)
for chain in reach['chains']:
 if chain['tip'] not in ['c_kilt_01_04_l','c_kilt_03_04_l','c_kilt_05_04_l','c_kilt_07_04_l']:continue
 h=np.array(chain['head_m'])*100;d=np.array(chain['forward_unit']);p95=chain['sets']['dominant']['all']['forward_cm']['p95']
 e=h+d*p95;short=h+d*3
 ax.plot([h[2],e[2]],[h[1],e[1]],c=TEAL,lw=1.3)
 ax.plot([h[2],short[2]],[h[1],short[1]],c=GOLD,lw=4)
 ax.scatter(h[2],h[1],c=FG,s=14)
ax.set_xlim(-25,65);ax.set_ylim(10,102);ax.set_aspect('equal',adjustable='box');ax.legend(fontsize=8,loc='upper left');ax.set_title('Shared radial deformation; no separate layer solver',loc='left',fontsize=11)
ax=f.add_subplot(gs[0,1]);style(ax,y='Forward skin reach beyond tip joint (cm)')
chains=reach['dummy_reach_measurement']['dominant_set_tip_p95_max_cm'];x=np.arange(len(chains));p95=[c[1] for c in chains];maxima=[c[2] for c in chains]
ax.bar(x,p95,color=[BLUE]*8+[TEAL]*8,width=.65,zorder=3);ax.scatter(x,maxima,s=18,c=PINK,label='maximum',zorder=4);ax.axhline(3,color=GOLD,lw=1.6,ls='--',label='current 3 cm dummy')
ax.set_xticks(x,[f'{i:02d}L' for i in range(1,9)]+[f'{i:02d}R' for i in range(1,9)],rotation=60,fontsize=8);ax.set_ylim(0,21);ax.legend(fontsize=8,loc='upper right');ax.set_title('All 16 terminal chains — dominant-weight skin p95',loc='left',fontsize=11)
ax=f.add_subplot(gs[1,1]);ax.axis('off')
msg=('720 shared seam vertices have identical weights.\n'
 'The three large hem surfaces already share 64 radial bones.\n\n'
 'Dominant skin reach: p95 up to 16.45 cm; max 17.63 cm.\n'
 'Native axis now verified: −Y follows all 16 chains (Sheet 07).\n\n'
 '226 panel points have leg influence >1%:\n'
 '146 above 75 cm; 66 at 50–75 cm; 14 below 50 cm.\n'
 'Inspect the lower 14 small-panel/seam points separately.\n'
 'The three large hem surfaces have no leg-bound cohort.')
ax.text(0,1,msg,va='top',fontsize=9.5,linespacing=1.65,color=MUTED)
foot(f,'Evidence: skirt_tip_reach.json • source FBX SHA256 40356ebc1521e542… • measured chain direction, not assumed UE axis',
 'Proxy reach is a candidate measurement, not a validated physics tune. Skirt weights, seams, bones and Kawaii settings remain unchanged.')
outputs.append(save(f,'sheet_03_skirt_layers_proxies.png'))

# 04: an ownership diagram from the observed pawn, with proposed work marked.
identity=read('runtime_identity.json')
node_snapshot=read('editor_node_baseline.json')
assert len([c for c in identity['components'] if c.get('leader')=='CharacterMesh0'])==5
f=base('04  /  A single pose authority for the layered wardrobe',
 'OBSERVED RUNTIME ARCHITECTURE  •  gameplay pose → ground contact → secondary skirt motion → shared deformation')
ax=f.add_axes([.045,.145,.91,.67]);ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
def card(ax,x,y,w,h,title,body,color=TEAL,fontsize=9.8):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.012,rounding_size=0.012',
              facecolor=PANEL,edgecolor=color,lw=1.2))
 ax.text(x+.016,y+h-.035,title,va='top',fontsize=11,weight='bold',color=color)
 ax.text(x+.016,y+h-.092,body,va='top',fontsize=fontsize,color=MUTED,linespacing=1.5)
def arrow(ax,a,b,color=MUTED):
 ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->','color':color,'lw':1.5})
card(ax,.02,.76,.37,.19,'01  ANIMATION + GAMEPLAY',
 'Canonical body / ABP_Melusina_Current\nLocomotion, slots and authored pose')
card(ax,.02,.50,.37,.19,'02  NATIVE GROUND SOLVE',
 'Foot targets → FootPlacement → LegIK\nStaged candidate: existing c_traj support plane')
card(ax,.02,.24,.37,.19,'03  BODY SKIRT KAWAII',
 'c_kilt_master_x subtree; shared radial chains\nCollision / ring constraints; one skirt simulation')
arrow(ax,(.205,.76),(.205,.69));arrow(ax,(.205,.50),(.205,.43))
card(ax,.50,.52,.47,.33,'LEADERPOSE WARDROBE',
 'Shirt • R2 skirt • boots • accessories • hat\nFollowers consume the final body bone transforms.\nThree major hem surfaces share 64 radial bones.\nNew garment joints must exist in the body RefSkeleton.',BLUE)
arrow(ax,(.39,.335),(.45,.335));arrow(ax,(.45,.335),(.45,.67));arrow(ax,(.45,.67),(.50,.67))
card(ax,.50,.12,.47,.28,'WATER HAIR: EXISTING INDEPENDENT OWNER',
 'Separate skeleton + ABP_Melusina_WaterHair\nSource mesh supplies pose; hair ABP owns its Kawaii.\nBody node publishes collision; consumption is not proven.',PINK)
arrow(ax,(.45,.335),(.50,.26),PINK)
ax.text(.02,.08,'Expansion order: contact correctness → proxy geometry → measured dynamics → optional deform additions.',
        fontsize=10,color=GOLD)
foot(f,'Evidence: runtime_identity.json • editor_node_baseline.json • WardrobeComponent and MelodiaHairComponent source',
 'Diagram shows ownership, not a new architecture. Do not place a second cloth solver on a LeaderPose follower.')
outputs.append(save(f,'sheet_04_runtime_ownership.png'))

# 05 follows an actual measured, offline proxy artifact when available.
proxy_file=HERE/'KineFX/skirt_terminal_support_proxy_candidate.json'
if proxy_file.exists():
 proxy=read('KineFX/skirt_terminal_support_proxy_candidate.json')
 proxy_gate=read('KineFX/skirt_terminal_support_proxy_gate.json')
 assert proxy_gate['passed'] and all(proxy_gate['gates'].values())
 assert proxy['canonical_joint_changes']==0 and proxy['virtual_terminal_count']==16
 for name,digest in proxy_gate['artifact_hashes'].items():
  assert hashlib.sha256((HERE/'KineFX'/name).read_bytes()).hexdigest()==digest
 f=base('05  /  Extend the measured support envelope first',
  'OFFLINE RIG EXPANSION CANDIDATE  •  16 terminal support guides  •  no production joints or weights changed')
 gs=f.add_gridspec(1,2,left=.055,right=.96,top=.80,bottom=.18,wspace=.23,width_ratios=[1.12,1])
 ax=f.add_subplot(gs[0,0]);style(ax,'Lateral position (cm)','Depth (cm)')
 ax.scatter(sv[:,0],sv[:,2],s=1.5,color=MUTED,alpha=.12,rasterized=True)
 for chain in proxy['terminals']:
  h=np.array(chain['head_m'])*100;e=np.array(chain['candidate_endpoint_m'])*100
  old=np.array(chain['current_3cm_endpoint_m'])*100
  ax.plot([h[0],e[0]],[h[2],e[2]],c=TEAL,lw=2)
  ax.plot([h[0],old[0]],[h[2],old[2]],c=GOLD,lw=4)
  ax.scatter(h[0],h[2],s=14,color=FG)
  ax.text(e[0],e[2],chain['existing_parent_tip'].replace('c_kilt_','').replace('_04_',''),color=TEAL,fontsize=7)
 ax.plot([],[],c=GOLD,lw=4,label='3 cm along measured axis (reference)');ax.plot([],[],c=TEAL,lw=2,label='measured p95 support guide')
 ax.set_aspect('equal',adjustable='box');ax.legend(fontsize=8,loc='upper left');ax.set_title('Top projection of existing tip → measured reach',loc='left',fontsize=11)
 ax=f.add_subplot(gs[0,1]);ax.axis('off')
 msg=('A  /  SUPPORT GUIDES — built offline\n'
  'Each guide follows its measured parent→tip direction.\n'
  'Length: max p95 of dominant and >0.25-weight cohorts.\n'
  'These are inspection geometry, not weighted joints.\n\n'
  'B  /  KAWAII INTEGRATION — pending runtime test\n'
  'Native axis verified: −Y; staged axis-only graph compiles.\n'
  'Tune one proxy / collision setting and compare motion.\n'
  'Axial endpoint may miss cloth laterally by up to 7.81 cm.\n\n'
  'C  /  DEFORM EXPANSION — only if motion requires it\n'
  'Paired body + garment skeleton change on duplicates.\n'
  'Preserve seam weights, bind pose and clip compatibility.\n'
  'Shirt hem / independent layers need separate acceptance.\n\n'
  'Promotion requires movement, reset, LOD and reload proof.\n'
  'The existing 465-joint production hierarchy is unchanged.')
 ax.text(0,1,msg,va='top',fontsize=10,linespacing=1.65,color=MUTED)
 foot(f,'Evidence: skirt_terminal_support_proxy_candidate.json • 10/10 preservation gates • measured p95; no collision radius inferred',
  'Candidate guides are not a runtime physics tune or a delivered extra garment layer. Dynamic coverage and movement tests remain open.')
 outputs.append(save(f,'sheet_05_rig_expansion.png'))

# 06: production acceptance and a portfolio edit, with no invented timing data.
f=base('06  /  Show the engineering — earn the gameplay claim',
 'PRODUCTION ACCEPTANCE + PORTFOLIO EDIT  •  test targets are proposed  •  no frame-time or packaged certification is claimed')
gs=f.add_gridspec(1,2,left=.055,right=.96,top=.80,bottom=.17,wspace=.23,width_ratios=[1.05,1])
ax=f.add_subplot(gs[0,0]);ax.axis('off')
rows=[['Source / bind','PASS','Boot bind + locomotion pose controls'],
 ['Native staged idle','PASS','Knees + actual skinned boot contact'],
 ['Walk / run / turn / stop','OPEN','Plant drift, penetration, knee plane'],
 ['Skirt dynamics / layers','OPEN','Bend, turn, wind, off/on A/B'],
 ['Reset / equip / reload','OPEN','Warm-up, teleport, reinitialization'],
 ['Performance / LOD','UNMEASURED','CPU p50/p95, skinning, draw calls'],
 ['Packaged target build','NOT TESTED','Same equipped pawn + controls']]
table=ax.table(cellText=rows,colLabels=['Gate','Evidence','Acceptance capture'],cellLoc='left',colLoc='left',
               colWidths=[.32,.22,.46],bbox=[0,.18,1,.82])
table.auto_set_font_size(False);table.set_fontsize(8.8)
for (r,c),cell in table.get_celld().items():
 cell.set_facecolor(PANEL if r else '#273950');cell.set_edgecolor('#344456')
 cell.get_text().set_color(TEAL if r in [1,2] and c==1 else GOLD if c==1 and r else FG if not r else MUTED)
 cell.PAD=.08
ax.text(0,.11,'Profile the dressed hero on the chosen target hardware.',fontsize=10,color=TEAL,weight='bold')
ax.text(0,.045,'Compare body-only / full outfit / Kawaii off-on at 30, 60, 120 fps.\nRecord hardware, build, scene, capture duration and active LOD.',fontsize=9.5,color=MUTED,linespacing=1.6)
ax=f.add_subplot(gs[0,1]);ax.axis('off')
msg=('PROPOSED 75-SECOND PORTFOLIO SEQUENCE\n\n'
 '00–08   Hero silhouette + in-engine presentation\n'
 '08–20   Matched old / candidate leg-contact comparison\n'
 '20–32   Boot weight isolation + unchanged bind overlay\n'
 '32–44   Three skirt surfaces / shared chain ownership\n'
 '44–57   Kawaii off/on through turn, stop and bend*\n'
 '57–67   LOD transition + measured cost overlay*\n'
 '67–75   Reset / reload, role, tools and proof scope*\n\n'
 '* Capture only after those tests pass.\n'
 'Current publishable claim: measured source repair\n'
 'and staged native idle contact; gameplay completion open.\n\n'
 'Label every shot: source • staged live • real input • package.\n'
 'Use matched camera, outfit, animation time and lighting.\n'
 'State your contribution and credit third-party tools/assets.')
ax.text(0,1,msg,va='top',fontsize=10,linespacing=1.7,color=MUTED)
foot(f,'Measured evidence: Sheets 01–03 and their receipts. Sequence, test matrix and profiling fields are a proposed production brief.',
 'AAA use is a quality and performance gate on a named target; a polished still or high joint count does not certify it.')
outputs.append(save(f,'sheet_06_gameplay_portfolio.png'))

# 07: direct native mesh reference-pose readback, not an FBX-axis inference.
f=base('07  /  The native tip axis was ninety degrees off',
 'NATIVE BODY MESH REFERENCE POSE + STAGED IDLE  •  one enum corrected  •  3 cm dummy length retained')
gs=f.add_gridspec(2,2,left=.055,right=.96,top=.80,bottom=.17,wspace=.25,hspace=.40,height_ratios=[1.05,1])
ax=f.add_subplot(gs[:,0]);style(ax,'Native local X direction (schematic cm)','Native local −Y chain direction (schematic cm)')
ax.plot([0,0],[8,0],c=MUTED,lw=3,label='existing last chain segment')
ax.plot([0,3],[0,0],c=GOLD,lw=4,label='old X+ / 3 cm dummy')
ax.plot([0,0],[0,-3],c=TEAL,lw=4,label='staged −Y / 3 cm dummy')
ax.scatter(0,0,s=50,c=FG,zorder=4);ax.text(.4,.5,'terminal joint',fontsize=10,color=FG)
theta=np.linspace(0,-np.pi/2,40);ax.plot(.9*np.cos(theta),.9*np.sin(theta),ls=':',c=FG)
ax.text(1.1,-1.1,'90°',fontsize=12,color=GOLD)
ax.text(-.45,8.2,'toward parent',ha='right',fontsize=9,color=MUTED)
ax.text(.6,-3.1,'measured continuation',fontsize=10,color=TEAL)
ax.set_xlim(-3,7);ax.set_ylim(-6,10);ax.set_aspect('equal',adjustable='box')
ax.set_title('Direction only: actual reference axis, schematic segment',loc='left',fontsize=11)
ax.legend(loc='upper right',fontsize=8)
ax=f.add_subplot(gs[0,1]);style(ax,y='Angle to parent→tip direction (degrees)')
x=np.arange(16);rs=native_axis['terminals']
ax.bar(x,[r['axis_angle_degrees']['X_Positive'] for r in rs],color=GOLD,label='current production X+',zorder=3)
ax.scatter(x,[r['axis_angle_degrees']['Y_Negative'] for r in rs],c=TEAL,s=20,label='native −Y',zorder=4)
ax.set_xticks(x,[f'{i:02d}L' for i in range(1,9)]+[f'{i:02d}R' for i in range(1,9)],rotation=60,fontsize=8)
ax.set_ylim(-6,115);ax.legend(loc='upper right',fontsize=8);ax.set_title('All sixteen tips from the body RefSkeleton',loc='left',fontsize=11)
ax=f.add_subplot(gs[1,1]);ax.axis('off')
msg=('READBACK → ONE-PROPERTY STAGED EDIT\n'
 f'−Y maximum alignment error: {native_axis["native_minus_y_angle_max_degrees"]:.8f}°\n'
 'X+ is transverse: 89.99999–90.00002° on all tips.\n'
 'KineFX +Y converts to native UE −Y for these joints.\n\n'
 'ABP_LegSkirt_Axis_Candidate: X_Positive → Y_Negative\n'
 'Compile: 0 errors / 0 warnings; graph assertion matches.\n'
 '28 nodes / 25 connections; explicit native enum readback.\n'
 f'Live idle knees: {axis_idle["knees"]["l"]:.2f}° / {axis_idle["knees"]["r"]:.2f}°.\n'
 'Original equipped boot contact remains about 0 / +0.739 cm.\n\n'
 'No extra deform bones or longer dummy admitted.\n'
 'Dynamics, retained candidate wardrobe equip and gait OPEN.')
ax.text(0,1,msg,va='top',fontsize=9.6,linespacing=1.6,color=MUTED)
foot(f,'Evidence: native_body_tip_reference.json • native_tip_axis_verification.json • native_skirt_axis_candidate.json • native_axis_idle_contact.json',
 'Native axis and staged idle are verified. This does not certify fabric collision coverage, candidate footwear persistence or moving gameplay.')
outputs.append(save(f,'sheet_07_native_axis_correction.png'))

# 08: unmodified engine captures in a labelled comparison figure.
neck_fix=read('necklace_persisted_fix.json');neck_pie=read('necklace_fresh_pie.json')
neck_capture=read('necklace_final_capture.json')
assert neck_fix['passed'] and neck_fix['other_component_defaults_unchanged']
assert neck_pie['fresh_spawn']['socket']==neck_pie['after_construction_reentry']['socket']=='spine_03_x'
assert neck_capture['finished'] and not neck_capture['errors']
f=base('08  /  Return the necklace to its authored chest frame',
 'SAVED CANONICAL CHARACTER FIX  •  fresh PIE + construction re-entry pass  •  fixed diagnostic cameras; different idle phases')
gs=f.add_gridspec(1,2,left=.045,right=.955,top=.805,bottom=.28,wspace=.025)
for i,(name,title,color) in enumerate([
 ('neck_static_before_all_on_outfit_front.png','BEFORE  /  neck_x attachment',GOLD),
 ('neck_saved_all_on_outfit_front.png','AFTER  /  authored spine_03_x attachment',TEAL)]):
 p=HERE/name;inputs[name]=hashlib.sha256(p.read_bytes()).hexdigest()
 ax=f.add_subplot(gs[0,i]);ax.imshow(plt.imread(p));ax.axis('off');ax.set_title(title,loc='left',fontsize=12,color=color,pad=12)
f.text(.055,.225,'One construction pin + one component bind transform',fontsize=13,color=TEAL,weight='bold')
f.text(.055,.18,'Existing static mesh and materials retained. Full rotation, translation and scale derived from native bind pose.\n'
 'Compile: 0 errors / 0 warnings. Exact graph assertion: 14 nodes / 16 connections. Other component defaults unchanged.',
 fontsize=10,color=MUTED,linespacing=1.6)
f.text(.055,.108,'This is attachment proof. Necklace dynamics, target-build profiling and final beauty lighting are separate work.',fontsize=10,color=GOLD)
foot(f,'Evidence: necklace_persisted_fix.json • necklace_fresh_pie.json • necklace_final_capture.json • rollback .uasset preserved',
 'The diagnostic capture helper now uses native static cameras without editing SpringArm properties that reconstruct the pawn.')
outputs.append(save(f,'sheet_08_necklace_attachment.png'))

# 09: recorded dynamic localization; separate runs, not synchronized A/B.
waist_runs=[read(n+'.json') for n in ['waist_duplicate_baseline','waist_constraint_clean','waist_kawaii_off']]
for run in waist_runs:
 assert run['finished'] and not run['errors'] and run['samples']
 assert all(len(s['waist_ring_deviation_cm'])==16 for s in run['samples'])
f=base('09  /  Locate the crunchy waist before changing the surface',
 'INJECTED WALK / TURN / STOP  •  16 first-ring joints  •  separate runs and frame samples; no synchronized beauty comparison')
gs=f.add_gridspec(1,2,left=.06,right=.96,top=.79,bottom=.19,wspace=.27,width_ratios=[1.05,1])
ax=f.add_subplot(gs[0,0]);style(ax,'Recorded phase','Maximum first-ring deviation per sample (cm)')
labels=['Duplicate constraints','Single constraint set','Kawaii disabled']
colors=[GOLD,PINK,TEAL];phases=['idle','walk','turn','stop']
peaks=[]
for j,(run,label,color) in enumerate(zip(waist_runs,labels,colors)):
 vals=[max(s['waist_ring_deviation_cm'].values()) for s in run['samples']];peaks.append(max(vals))
 for i,phase in enumerate(phases):
  ys=[v for s,v in zip(run['samples'],vals) if s['phase']==phase]
  xs=i+(j-1)*.20+np.linspace(-.035,.035,len(ys))
  ax.scatter(xs,ys,c=color,s=18,alpha=.8,label=label if i==0 else None,zorder=3)
ax.set_xticks(range(4),phases);ax.set_ylim(-.4,14);ax.legend(fontsize=8,loc='upper left')
ax.set_title('Deviation from native bind-local position in master frame',loc='left',fontsize=10)
ax=f.add_subplot(gs[0,1]);ax.axis('off')
msg=('OBSERVED — NOT YET A WAIST REPAIR\n\n'
 f'Duplicate constraints: {peaks[0]:.3f} cm maximum\n'
 f'Clean constraint set:   {peaks[1]:.3f} cm maximum\n'
 f'Kawaii disabled:       {peaks[2]:.8f} cm maximum\n\n'
 'Removing duplicated constraints did not remove the shift.\n'
 'Current root is c_kilt_master_x; the first radial ring moves.\n'
 'The sampled source walk first-joint track is constant.\n\n'
 'SAVED CANDIDATE — 17 existing branch roots; P0 test pending.\n'
 'Keep authored master motion and lower-chain dynamics.\n'
 'Check rotation and skinned surface, not only root positions.\n\n'
 'LAYER GATE — map real free panels, lining and trim.\n'
 'Coincident hem islands share bones and seam weights;\n'
 'they do not prove independent fabric-layer collision.\n\n'
 'MOVING FOOT CONTACT STILL FAILS: −1.03 to +11.16 cm.\n'
 'No production leg/skirt admission from idle evidence.')
ax.text(0,1,msg,va='top',fontsize=10,linespacing=1.55,color=MUTED)
foot(f,'Evidence: waist_duplicate_baseline.json • waist_constraint_clean.json • waist_kawaii_off.json • injected_locomotion_summary.json',
 'Local positional deviation localizes simulation behavior; it is not a measurement of perceived surface quality or independent layer clearance.')
read('injected_locomotion_summary.json')
outputs.append(save(f,'sheet_09_waist_simulation_localization.png'))

# 10: explicit proposed cue design, tied to inspected existing event owners.
for name in ['MelodiaWaveHarpCombatComponent.h','MelodiaWaveHarpCombatComponent.cpp','MelodiaWaterChorus.cpp']:
 p=HERE.parents[2]/'Source/BS_GodFile/MelodiaIntegration'/name
 inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
f=base('10  /  Water and glints punctuate the action',
 'PROPOSED FONTAINE-INSPIRED PRESENTATION  •  no HoYoverse frame measurements or private implementation claims')
ax=f.add_axes([.055,.29,.90,.49]);ax.axis('off')
rows=[['Anticipation','Small droplets / hand curl','Authored draw or gesture; cancel on interrupt'],
 ['Release','Crisp glint + readable water arc','ReleaseDraw / authored pose marker: one owner'],
 ['Actual contact','Compact crown + expanding ripple','ResolveProjectileHit, after projectile travel'],
 ['Follow-through','Softer droplets / ribbon dispersal','Authored envelope; validate socket vs world space'],
 ['Recovery','Few fading glints → quiet silhouette','Existing recovery, interruption and cleanup']]
t=ax.table(cellText=rows,colLabels=['Action beat','Visual treatment','Deterministic timing authority'],
 colWidths=[.16,.32,.52],cellLoc='left',colLoc='left',bbox=[0,0,1,1])
t.auto_set_font_size(False);t.set_fontsize(10)
for (r,c),cell in t.get_celld().items():
 cell.set_facecolor(PANEL if r else '#273950');cell.set_edgecolor('#344456');cell.PAD=.09
 cell.get_text().set_color(TEAL if c==0 and r else FG if not r else MUTED)
f.text(.06,.82,'A cue sequence, not a measured time axis. Release and contact may be separated by travel.',fontsize=11,color=TEAL)
f.text(.06,.23,'EXISTING SOURCE GAP',fontsize=11,color=GOLD,weight='bold')
f.text(.06,.185,'PlayFormVfxBeats currently spawns at stage change. Declared Offset / float / color maps are not consumed.\n'
 'ResolveProjectileHit uses the target actor location; surface-fitted rings require verified contact position and normal.',fontsize=10,color=MUTED,linespacing=1.6)
f.text(.06,.11,'Gate: one cue per event • interruption cleanup • playback-speed / frame-rate checks • preload / pool / cull proof.\n'
 'Jev may choose an approved variant before the event. Existing combat, animation and music owners retain exact onset.',fontsize=10,color=MUTED,linespacing=1.6)
foot(f,'Source: MelodiaWaveHarpCombatComponent.h/.cpp + MelodiaWaterChorus.cpp; reference links and bounded integration in CURRENT_STATE.md.',
 'Implementation is planned after waist/layer acceptance. No new VFX timing code, performance result or Furina effect reproduction is claimed.')
outputs.append(save(f,'sheet_10_water_sparkle_beat_plan.png'))

# 11: exact source geometry and retained shared-chain weights, prepared offline.
shirt_data=read('KineFX/ShirtOverlap/SK_Melusina_V2_Shirt_Flared_data.json')
shirt_overlap=read('KineFX/ShirtOverlap/shirt_skirt_overlap.json')
shirt_intake=read('KineFX/ShirtOverlap/shirt_skeleton_intake.json')
shirt_import=read('KineFX/ShirtOverlap/contact_geometry.json')['files'][0]
assert shirt_import['points']==861 and shirt_import['joints']==465 and shirt_import['unweighted_points']==0
for rel,digest in shirt_overlap['input_hashes'].items():
 assert hashlib.sha256((HERE/rel).read_bytes()).hexdigest()==digest
 inputs[rel]=digest
assert not shirt_overlap['source_geometry_or_weights_changed']
sp=np.array(shirt_data['positions_m'])*100;kp=np.array(skirt['positions_m'])*100
kw=np.array([sum(w for n,w in ws if n.startswith('c_kilt_')) for ws in shirt_data['weights']])
f=base('11  /  Keep the shirt outside — keep its physics chains',
 'OFFLINE KINEFX BIND GEOMETRY  •  original 465 joints and all weights retained  •  P0 movement acceptance remains open')
gs=f.add_gridspec(1,3,left=.055,right=.96,top=.79,bottom=.19,wspace=.34,width_ratios=[1,1,1.22])
for j,(axis,label) in enumerate([(0,'Lateral X (cm)'),(2,'Depth Z (cm)')]):
 ax=f.add_subplot(gs[0,j]);style(ax,label,'KineFX height Y (cm)')
 mask=(kp[:,1]>=65)&(kp[:,1]<=108)
 ax.scatter(kp[mask,axis],kp[mask,1],s=5,c=GOLD,alpha=.35,label='skirt source points',zorder=2)
 mask=(sp[:,1]>=65)&(sp[:,1]<=108)
 pts=ax.scatter(sp[mask,axis],sp[mask,1],s=22,c=kw[mask],cmap='cool',vmin=0,vmax=1,edgecolors='none',zorder=3)
 ax.set_ylim(65,108);ax.set_xlim((-29,29) if axis==0 else (-10,51))
 ax.set_title('Front projection' if axis==0 else 'Side projection',loc='left',fontsize=11)
 ax.legend(fontsize=7,loc='upper right')
 if j==1:
  cb=f.colorbar(pts,ax=ax,orientation='horizontal',pad=.14,fraction=.045)
  cb.set_label('Existing shirt kilt-chain influence (0–1)',fontsize=8)
ax=f.add_subplot(gs[0,2]);ax.axis('off')
summary=shirt_overlap['summary'];clear=summary['same_height_radial_clearance_cm']
msg=('WHAT THE SOURCE PROVES\n\n'
 '861 shirt points / 465 joints / 3 topology islands\n'
 '278 shirt points have >1% skirt-chain influence.\n'
 '167 shirt points have >1% thigh influence.\n'
 'No weight stripping, bind edit or garment translation.\n\n'
 'FBX wrapper name differs; export intake gate stays open.\n\n'
 f"167 same-height radial sections hit skirt surfaces.\n"
 f"Shirt is outside along those rays: min {clear['min']:.3f} cm.\n"
 f"Median radial clearance: {clear['median']:.2f} cm.\n"
 'Nine brute-force checks confirm nearest-face search.\n\n'
 'WHAT THE SOURCE CANNOT PROVE\n\n'
 'Open/gapped sections are not solid-body tests.\n'
 'Rest clearance does not certify seam coverage in motion.\n'
 'The 12.54 cm simulated first-ring shift can dominate\n'
 'the tightest 2.4 mm source clearance.\n\n'
 'NEXT: saved waist-root candidate on House P0.\n'
 'Compare shirt/waist off-on through walk, turn, bend.\n'
 'Keep shared chains; inspect rotations and skinned hem.')
ax.text(0,1,msg,va='top',fontsize=9.8,linespacing=1.55,color=MUTED)
foot(f,'Evidence: ShirtOverlap/shirt_skirt_overlap.json • shirt KineFX import • exact nearest-face distances + horizontal radial ray intersections',
 'Radial sections measure the source overlap only; cloth-layer contact, P0 movement, re-equip and reload remain unverified.')
outputs.append(save(f,'sheet_11_shirt_hem_shared_chains.png'))

manifest={'schema':'melodia.kinefx_working_sheets.v1','bounded_goal':'CURRENT_STATE.md / Melusina legs, footwear and layered skirt — 2026-10-23',
 'proof_tiers':{'sheet_01':'staged live flat idle only','sheet_02':'KineFX bind / weight roundtrip with separate staged idle test','sheet_03':'KineFX source geometry / hierarchy / influence measurements',
 'sheet_04':'observed runtime ownership plus local source contract','sheet_05':'offline measured proxy candidate only, if generated','sheet_06':'measured evidence summary plus proposed acceptance and portfolio sequence',
 'sheet_07':'native body reference axes, guarded staged graph edit, and staged idle with original equipped boots',
 'sheet_08':'saved canonical necklace attachment; clean compile, exact graph assertion, fresh PIE and construction re-entry',
 'sheet_09':'recorded injected movement; waist localization, not repaired surface or synchronized quality comparison',
 'sheet_10':'proposed water and sparkle cue treatment tied to inspected existing source owners; implementation open',
 'sheet_11':'offline shirt/skirt bind clearance and shared chain weights; no shape edit or P0 garment acceptance'},
 'inputs_sha256':inputs,'outputs':[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in outputs],
 'open':['gait and transition contact FAIL in injected probe','saved waist-root candidate awaits House P0 acceptance','Kawaii proxy / collision and layer motion','shirt seam coverage in P0 motion','water / sparkle cue implementation','production admission','reload / reset / re-equip','target hardware profiling','packaged proof'],
 'production_references_changed':{'necklace_attachment_on_character_blueprint':True,'body_animation_skeleton_wardrobe_catalog':False}}
(OUT/'sheets_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest['outputs'],indent=2))
