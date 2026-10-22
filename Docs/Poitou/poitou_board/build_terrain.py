from PIL import Image,ImageDraw,ImageFont
import json,textwrap
F='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';FB=F.replace('Sans.','Sans-Bold.')
f=lambda s,b=0:ImageFont.truetype(FB if b else F,s)
M={d['file']:d for d in json.load(open('terrain_meta.json'))}
T=[
("A","t01","Historical map 1762 — mouillé vs desséché layout","Plan view: wet marsh (irregular, tree-lined plot mesh) vs drained marsh (big rectilinear blocks). HEIGHT: flat, not readable from map. MASK: use as region/zoning guide for 'mouillé' vs 'desséché' masks. Historical; layout has changed since."),
("B","t02","1839 plan, Société des Marais desséchés de Vix/Maillé/Maillezais","Plan view of drained marsh: long straight ditches & canals cutting large fields. HEIGHT: flat. BANK: not shown. MASK: straight-line ditch mask (thin, long, grid-ish). Historical map."),
("C","t03","1648 plan, Marais desséchés du Petit Poitou","Plan view: dikes and parallel drainage cuts. MASK: linear channel + dike-ridge masks. HEIGHT: dikes implied as raised lines (uncertain from engraving)."),
("D","t04","Marais desséché, Esnandes (cattle pasture)","Ground view: open, treeless, dead-flat grazed field to horizon. HEIGHT: ~0 relief; noise only. MASK: grass/pasture; few trees. Bank profile not visible."),
("E","t05","Narrow conche, Venise Verte","Ground view: narrow channel, water near bank top, tree-lined. BANK: low, vegetated, near-vertical lip (uncertain). MASK: water ribbon + tree-row mask both sides."),
("F","t06","Canal near Sèvre Niortaise","Ground view: wide calm water, low grassy bank with gentle slumped slope. BANK: low levee, est. well under 1 m above water (visual estimate, uncertain). MASK: water / grass bank / tree line."),
("G","t07","Fossé with pollard ash (frênes têtards)","Ground view: ditch along plot edge with pollard ash row. HEIGHT: plot ~flat, ditch a shallow cut. MASK: ditch + tree-row mask at plot borders — key mouillé signature."),
("H","t08","Duckweed canal, Venise Verte","Ground view: duckweed-covered canal under closed canopy. BANK: low, soft, vegetated. MASK: duckweed water material; canopy shading. Height read: flat."),
("I","t09","Canal at Maillezais","Ground view: tree-lined canal, bank rising slightly above water, trunks on bank edge. BANK: low slumped berm (uncertain). MASK: water/bank/trees."),
("J","t10","Maillezais canal with barques & jetty","Ground view: duckweed canal, timber landing, moored barques. BANK: edited hard edge where jetty is; soft elsewhere. MASK: duckweed + jetty prop placement."),
("K","t11","Abbey seen from canal de la Jeune Autise","Ground view: abbey ruins standing above water/meadow level beyond trees. HEIGHT: abbey on slight rise vs. marsh (exact elevation not verified). MASK: water fg, meadow, rise."),
("L","t12","Vue plongeante, Abbaye de Maillezais","High view from ruins: lawn & village on the island, flat land beyond. HEIGHT: gentle plateau, no cliff. MASK: lawn/ruin footprint. Rise magnitude: not measured here."),
("M","t13","Abbey ruins overview, July 2024","Ground view: open mown ground around ruins, near-flat locally. HEIGHT: island top reads flat; slope to marsh not visible. MASK: grass/gravel paths."),
]
CW,PAD=940,16;W=3840;IH=600;CH=330
tiles=[]
def tile(img,lab,title,body,credit):
  t=Image.new('RGB',(CW,IH+CH),(245,242,232));d=ImageDraw.Draw(t)
  if img:
    im=img.copy();im.thumbnail((CW,IH));t.paste(im,((CW-im.width)//2,(IH-im.height)//2))
  d.rectangle((0,0,64,56),fill=(30,50,40));d.text((14,6),lab,font=f(40,1),fill='white')
  y=IH+10
  for l in textwrap.wrap(title,52):d.text((14,y),l,font=f(26,1),fill=(25,35,30));y+=32
  for l in textwrap.wrap(body,80):d.text((14,y),l,font=f(19),fill=(50,50,50));y+=24
  d.text((14,IH+CH-28),credit[:110],font=f(15),fill=(110,110,110))
  return t
for lab,k,ti,bo in T:
  m=M[f'img/terrain/{k}.jpg'];a=m['author'] or 'unknown author'
  tiles.append(tile(Image.open(m['file']).convert('RGB'),lab,ti,bo,f"{m['title'][5:60]}… · {a[:35]} · {m['license']} · Wikimedia Commons"))
# diagram
D=Image.new('RGB',(CW,IH),(252,250,244));d=ImageDraw.Draw(D)
X=lambda m:60+m*80; Y=lambda h:380-h*150   # 80px/m horizontal, 150px/m vertical (VE ~1.9x)
water=-0.1
prof=[(0,0.0),(2.5,0.0),(3.5,0.6),(4.5,0.6),(5.3,0.15),(6.2,0.05),(6.8,-0.6),(9.5,-0.75)]
poly=[(X(a),Y(b)) for a,b in prof]+[(X(9.5),Y(-1.2)),(X(0),Y(-1.2))]
d.rectangle((X(6.4),Y(water),X(9.5),Y(-0.75)),fill=(150,190,200))
d.polygon(poly,fill=(150,125,90),outline=(60,45,30))
d.line([(X(6.4),Y(water)),(X(9.5),Y(water))],fill=(40,90,140),width=3)
for x,h,t in [(1.2,0.0,'field / meadow'),(4.0,0.6,'BERM (levee crest)'),(5.1,0.3,"SLOPE"),(5.8,0.1,'SHELF'),(8.2,-0.75,'BED')]:
  d.text((X(x)-50,Y(h)-34 if t!='BED' else Y(h)+10),t,font=f(18,1),fill=(20,20,20))
d.line([(X(3.0),Y(0)),(X(3.0),Y(0.6))],fill='red',width=2);d.text((X(1.0),Y(0.45)),'0.3–1 m',font=f(20,1),fill='red')
d.text((X(7.2),Y(water)-26),'water',font=f(17),fill=(40,90,140))
d.text((80,15),"Canal bank cross-section — ARTIST'S DIAGRAM",font=f(26,1),fill=(140,20,20))
d.text((80,50),"Not measured data. Illustrative proportions; vertical exaggeration ~2×.",font=f(18),fill=(140,20,20))
d.text((20,IH-60),"Levee/berm 0.3–1 m (brief target); slumped soft slope; narrow wet shelf; soft bed.",font=f(17),fill=(50,50,50))
tiles.append(tile(D,"N","Heightfield guide (diagram)","Use as a profile ramp for canal-edge SDF: field 0 → berm +0.3–1 m → slope → shelf ≈ waterline → bed. Values are artist targets, not survey data. Ground-truth with IGN RGE ALTI LiDAR if accuracy matters.","Original diagram for this panel"))
cols=4;rows=(len(tiles)+cols-1)//cols;H0=170
P=Image.new('RGB',(W,H0+rows*(IH+CH+PAD)+80),(28,34,30));d=ImageDraw.Draw(P)
d.text((40,30),"Marais Poitevin — TERRAIN REFERENCE for Houdini heightfield rebuild",font=f(60,1),fill=(235,230,215))
d.text((40,108),"READ = height · bank profile · mask type. 'uncertain' = visual estimate from photo; heights are not measured. Maps are historical (1648/1762/1839).",font=f(26),fill=(190,190,175))
gx=(W-cols*CW)//(cols+1)
for i,t in enumerate(tiles):
  P.paste(t,(gx+(i%cols)*(CW+gx),H0+(i//cols)*(IH+CH+PAD)))
d.text((40,P.height-55),"All photos/maps: Wikimedia Commons, CC BY-SA / CC0 / PD — full credits in TERRAIN_SOURCES.md",font=f(24),fill=(190,190,175))
P.save('terrain_ref_panel.png');print(P.size)
L=["# Terrain reference panel — sources\n","Wikimedia Commons, licenses read via Commons API (extmetadata LicenseShortName). Diagram tile N is original. CC BY-SA requires attribution + share-alike on derivatives.\n","| Tile | Local file | Commons title | Author | License | URL |","|---|---|---|---|---|---|"]
for lab,k,ti,bo in T:
  m=M[f'img/terrain/{k}.jpg'];L.append(f"| {lab} | {m['file']} | {m['title']} | {(m['author'] or 'not stated').replace('|','/')} | {m['license']} | {m['url']} |")
L.append("| N | (drawn) | Canal bank cross-section — artist's diagram, not measured data | — | — | — |")
L.append("\nGaps: no freely licensed aerial/oblique photo of marais mouillé plot patchwork or desséché fields found on Commons search; historical maps used for plan-view layout instead. No measured bank profiles found; 0.3–1 m is the brief's target.")
open('TERRAIN_SOURCES.md','x').write('\n'.join(L)+'\n')
