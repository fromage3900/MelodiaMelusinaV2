import json,numpy as np
from PIL import Image,ImageDraw,ImageFont
m=json.load(open('meta.json'))
F='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';FB=F.replace('Sans.','Sans-Bold.')
f=lambda s,b=0:ImageFont.truetype(FB if b else F,s)
N={
"1_jetty_dawn":("1 · Misty canal jetty at dawn","Wet marsh (marais mouillé), dead-flat; conches lined by pollard ash, duckweed","Stone/timber quays, small embarcadères (Damvix, Marans port)","Pollard ash (frêne têtard), poplar, alder, duckweed; NOTE: no true dawn/mist photo found - grade from swatches"),
"2_footbridge":("2 · Meadow footbridge over a conche","Flat meadows divided by conches/fossés","Arched timber/metal passerelles (Le Vanneau, Le Mazeau)","Willow, pollard ash, reeds, grazed pasture"),
"3_grand_port":("3 · Grand Port, Coulon – flat barques","Sèvre Niortaise riverside quay","Limestone quays, rows of barques (plates)","Poplar & plane screens, flower boxes"),
"4_church_square":("4 · Romanesque church square","Village on slight rise at marsh edge","Poitevin Romanesque façades (Maillé portal), Arçais steeple; pale limestone","Clipped planes, lawns; NOTE: few square-level photos"),
"5_lane_to_water":("5 · Lane down to the water","Village edge sloping to canal","Lime-washed houses, terracotta roofs, quays (Coulon Quai Tardy, Damvix)","Riverside meadows, poplars"),
"6_tree_avenue_lock":("6 · Tree avenue along canal + lock","Straight canals (Canal Mignon) & Sèvre locks","Masonry locks/sluices (Marans), stone arch bridge","Pollard-ash tunnel over duckweed conche, poplar second rank"),
"7A_maillezais":("7A · Maillezais Abbey ruins","Limestone promontory on east edge of marsh (former island)","Romanesque porch-tower, Gothic N transept, nave wall","Lawn, scattered trees; winter snow in 2 refs"),
"7B_lusignan":("7B · Lusignan castle site","Limestone spur over Vonne & Bourceron valleys (Vienne, ~outside the marsh)","Castle demolished 1586; only promenade + town remain; Melusine relief; 15th-c. miniature shows towers","Promenade lawns, valley woods; NOTE: Chatsam photos show town/stone houses, verify"),
}
def sw(path,k=6):
  a=np.asarray(Image.open(path).convert('RGB').resize((120,90))).reshape(-1,3).astype(float)
  rng=np.random.default_rng(0);c=a[rng.choice(len(a),k,replace=False)]
  for _ in range(25):
    l=((a[:,None]-c)**2).sum(2).argmin(1);c=np.array([a[l==i].mean(0) if (l==i).any() else c[i] for i in range(k)])
  cnt=np.bincount(l,minlength=k);return [tuple(int(v) for v in c[i]) for i in np.argsort(-cnt)]
def stopsw(L):
  a=np.concatenate([np.asarray(Image.open(g['file']).convert('RGB').resize((120,90))).reshape(-1,3) for g in L]);Image.fromarray(a.reshape(-1,120,3)).save('/tmp/s.png');return sw('/tmp/s.png')
hx=lambda c:'#%02X%02X%02X'%c
PW,PH=1900,1150;out={}
for st,L in m.items():
  P=Image.new('RGB',(PW,PH),(246,243,236));d=ImageDraw.Draw(P);t=N[st]
  d.text((30,20),t[0],font=f(52,1),fill=(30,40,35))
  big=Image.open(L[0]['file']).convert('RGB');big.thumbnail((1150,720));P.paste(big,(30,100))
  y=100
  for g in L[1:]:
    im=Image.open(g['file']).convert('RGB');im.thumbnail((680,232));P.paste(im,(1200,y));y+=240
  S=stopsw(L);out[st]=[hx(c) for c in S]
  for i,c in enumerate(S):
    d.rectangle((30+i*190,840,200+i*190,940),fill=c);d.text((30+i*190,948),hx(c),font=f(26),fill=(40,40,40))
  for j,(lab,txt) in enumerate(zip(["Land","Arch","Veg"],t[1:])):
    d.text((30,1000+j*42),f"{lab}: {txt}"[:150],font=f(24),fill=(50,50,50))
  P.save(f'stop_{st}.png')
json.dump(out,open('swatches.json','w'),indent=1)
B=Image.new('RGB',(3840,2*1150//2*0+ 4*1000+160),(30,36,33));d=ImageDraw.Draw(B)
d.text((40,40),"Melusina's Morning — Marais Poitevin (Green Venice), Poitou · environment reference board",font=f(64,1),fill=(235,230,215))
for i,st in enumerate(m):
  p=Image.open(f'stop_{st}.png').resize((1900,1000));B.paste(p,(13+(i%2)*1914,160+(i//2)*1000))
B.save('poitou_board.png');print(B.size)
