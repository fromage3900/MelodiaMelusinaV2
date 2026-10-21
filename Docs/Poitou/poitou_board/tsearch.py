import requests,re,html,json,time,sys
S=requests.Session();S.headers['User-Agent']='PoitouBoard/1.0 (reference research)'
API='https://commons.wikimedia.org/w/api.php'
OK=re.compile(r'^(cc[- ]by|cc0|public domain|pd)',re.I)
strip=lambda s:re.sub('<[^>]+>','',html.unescape(s or '')).strip()
out={}
for q in sys.argv[1:]:
  for _ in range(5):
   try:
    r=S.get(API,params=dict(action='query',format='json',generator='search',gsrsearch=q+' filetype:bitmap',gsrnamespace=6,gsrlimit=12,prop='imageinfo',iiprop='url|extmetadata|size',iiurlwidth=1280)).json();break
   except Exception: time.sleep(8)
  for p in sorted(r.get('query',{}).get('pages',{}).values(),key=lambda p:p['index']):
    ii=p['imageinfo'][0];m=ii['extmetadata'];lic=strip(m.get('LicenseShortName',{}).get('value'))
    if not OK.match(lic) or ii['width']<900:continue
    print(q,'|',p['title'],'|',lic,'|',strip(m.get('ImageDescription',{}).get('value'))[:90])
    out[p['title']]=dict(title=p['title'],thumb=ii['thumburl'],url=ii['descriptionurl'],license=lic,author=strip(m.get('Artist',{}).get('value'))[:100],desc=strip(m.get('ImageDescription',{}).get('value'))[:200])
  time.sleep(1)
old=json.load(open('tcand.json')) if __import__('os').path.exists('tcand.json') else {}
old.update(out);json.dump(old,open('tcand.json','w'),indent=1,ensure_ascii=False)
