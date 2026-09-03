"""Add a restrained Persona-lite objective panel to the active stock ExploreUI."""
from __future__ import annotations
import json
from monolith_mcp_client import call_tool
ASSET='/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_ExploreUI'
def dec(r):
 for b in r.get('content',[]):
  if b.get('type')=='text':
   try:return json.loads(b['text'])
   except:return b['text']
 return r
def call(action,**kwargs): return dec(call_tool('ui_query',{'action':action,**kwargs}))
existing=json.dumps(call('get_widget_tree',asset_path=ASSET))
results=[]
if 'MelodiaMinimapPanel' not in existing:
 results.append(call('add_widget',asset_path=ASSET,widget_class='Border',widget_name='MelodiaMinimapPanel',parent_name='CanvasPanel_0',anchor_preset='top_right',position={'x':-330,'y':28},size={'x':300,'y':190},compile=False))
 results.append(call('add_widget',asset_path=ASSET,widget_class='VerticalBox',widget_name='MelodiaMinimapMarkers',parent_name='MelodiaMinimapPanel',padding={'left':14,'top':10,'right':14,'bottom':10},compile=False))
 for name,text in (
  ('MelodiaMinimapTitle','RESONANCE MAP'),
  ('Marker_PetalPriestess','◆ Petal Priestess'),
  ('Marker_StarWeaver','◇ Star Weaver'),
  ('Marker_RhythmEcho','✦ Rhythm Echo'),
  ('Marker_ForestExit','→ Path Forward')):
  results.append(call('add_widget',asset_path=ASSET,widget_class='TextBlock',widget_name=name,parent_name='MelodiaMinimapMarkers',padding={'left':4,'top':3,'right':4,'bottom':3},compile=False))
  results.append(call('set_widget_property',asset_path=ASSET,widget_name=name,property_name='Text',value=text,compile=False))
results.append(call('compile_widget',asset_path=ASSET))
results.append(dec(call_tool('blueprint_query',{'action':'save_asset','asset_path':ASSET})))
results.append(call('get_widget_tree',asset_path=ASSET))
print(json.dumps(results,indent=2,default=str))
