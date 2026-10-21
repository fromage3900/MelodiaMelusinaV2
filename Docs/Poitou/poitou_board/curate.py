import requests,json,re,html,os,time,shutil
S=requests.Session();S.headers['User-Agent']='PoitouBoard/1.0 (reference research)'
strip=lambda s:re.sub('<[^>]+>','',html.unescape(s or '')).strip()
meta=json.load(open('meta.json'))
want={
"1_jetty_dawn":["Conche des cabanes - 20150810 14h26 (11049).jpg","Photo conche du marais poitevin.JPEG","Conche avec lentilles d'eau de la Venise Verte.jpg","Damvix le port 02.jpg"],
"2_footbridge":["Le Vanneau-Passerelle.jpg","Le Mazeau village.jpg","28. Damvix. A maze of canals.jpg","Canal de la Garette - 20150810 16h00 (11061).jpg"],
"5_lane_to_water":["CoulonQuaiTardy-France.jpg","Le marais poitevin à La Garette.jpg","Damvix 01.JPG","Damvix 02.JPG"],
"6_tree_avenue_lock":["Canal mignon 004.jpg","Canal Mignon 006.jpg","Marans écluse 001.jpg","Entrée du Port de Marans - Ecluse.jpg"],
}
for st,ts in want.items():
  shutil.rmtree(f'img/{st}',ignore_errors=True);os.makedirs(f'img/{st}');got=[]
  r=S.get('https://commons.wikimedia.org/w/api.php',params=dict(action='query',format='json',titles='|'.join('File:'+t for t in ts),prop='imageinfo',iiprop='url|extmetadata|size',iiurlwidth=1280)).json()
  bt={p['title']:p for p in r['query']['pages'].values()}
  norm={n['from']:n['to'] for n in r['query'].get('normalized',[])}
  for t in ts:
    p=bt.get(norm.get('File:'+t,'File:'+t))
    if not p or 'imageinfo' not in p: print('MISSING',t);continue
    ii=p['imageinfo'][0];m=ii['extmetadata'];lic=strip(m.get('LicenseShortName',{}).get('value'))
    if not re.match(r'^(cc[- ]by|cc0|public domain|pd)',lic,re.I): print('BADLIC',t,lic);continue
    fn=f"img/{st}/{len(got)+1}.jpg";open(fn,'wb').write(S.get(ii['thumburl']).content);time.sleep(1)
    got.append(dict(file=fn,title=p['title'],author=strip(m.get('Artist',{}).get('value'))[:120],license=lic,url=ii['descriptionurl'],desc=strip(m.get('ImageDescription',{}).get('value'))[:150]))
  meta[st]=got;print(st,len(got))
json.dump(meta,open('meta.json','w'),indent=1,ensure_ascii=False)
