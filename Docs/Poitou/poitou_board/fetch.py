import requests,json,re,os,html
S=requests.Session();S.headers['User-Agent']='PoitouBoard/1.0 (reference research)'
API='https://commons.wikimedia.org/w/api.php'
stops={
"1_jetty_dawn":["Marais poitevin brouillard","Marais poitevin aube","Marais poitevin lever de soleil","Marais poitevin conche","Marais poitevin brume","Marais poitevin matin","Marais poitevin embarcadère"],
"2_footbridge":["Marais poitevin pont","Coulon passerelle","Marais mouillé pont bois","Arçais pont","Marais poitevin passerelle","Marais poitevin pont conche","Marais poitevin footbridge"],
"3_grand_port":["Coulon barques","Arçais port","La Garette barques","Coulon Marais poitevin port"],
"4_church_square":["Église Saint-Trojan Coulon","Église Arçais","Coulon Deux-Sèvres village maisons","Maillé église Vendée"],
"5_lane_to_water":["Coulon rue","Coulon quai","Arçais","La Garette","Saint-Hilaire-la-Palud","Damvix","Coulon ruelle","Arçais rue","La Garette village","Marais poitevin village rue"],
"6_tree_avenue_lock":["Canal Mignon","Écluse de Bazoin","Marais poitevin arbres canal","Marais poitevin écluse","Marais poitevin peupliers","Sèvre niortaise écluse","Marais poitevin frênes têtards"],
"7A_maillezais":["Abbaye de Maillezais","Maillezais abbey ruins"],
"7B_lusignan":["Lusignan château","Lusignan jardins Vauclair","Lusignan Vienne remparts"],
}
OK=re.compile(r'^(cc[- ]by|cc0|public domain|pd)',re.I)
strip=lambda s:re.sub('<[^>]+>','',html.unescape(s or '')).strip()
meta={}
old=json.load(open('meta.json')) if os.path.exists('meta.json') else {}
for st,qs in stops.items():
  if len(old.get(st,[]))>=3: meta[st]=old[st];continue
  os.makedirs(f'img/{st}',exist_ok=True);got=[];seen=set()
  for q in qs:
    if len(got)>=4:break
    import time
    for _ in range(5):
      try:
        r=S.get(API,params=dict(action='query',format='json',generator='search',gsrsearch=q+' filetype:bitmap',gsrnamespace=6,gsrlimit=15,prop='imageinfo',iiprop='url|extmetadata|size',iiurlwidth=1280)).json();break
      except Exception: time.sleep(10)
    time.sleep(1)
    pages=sorted(r.get('query',{}).get('pages',{}).values(),key=lambda p:p['index'])
    for p in pages:
      if len(got)>=4:break
      if p['title'] in seen:continue
      ii=p['imageinfo'][0];m=ii['extmetadata']
      lic=strip(m.get('LicenseShortName',{}).get('value'))
      if not OK.match(lic) or ii['width']<1000 or not p['title'].lower().endswith(('.jpg','.jpeg')):continue
      seen.add(p['title'])
      fn=f"img/{st}/{len(got)+1}.jpg"
      open(fn,'wb').write(S.get(ii['thumburl']).content)
      got.append(dict(file=fn,title=p['title'],author=strip(m.get('Artist',{}).get('value'))[:120],license=lic,url=ii['descriptionurl'],desc=strip(m.get('ImageDescription',{}).get('value'))[:150],query=q))
  meta[st]=got;print(st,len(got),[g['title'] for g in got]);json.dump(meta,open('meta.json','w'),indent=1,ensure_ascii=False)
json.dump(meta,open('meta.json','w'),indent=1,ensure_ascii=False)
