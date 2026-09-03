"""Focused live validation for Persona-lite touched assets and level metadata."""
from __future__ import annotations
import json
from monolith_mcp_client import call_tool
UNIT='/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation'
UI='/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_ExploreUI'
def dec(r):
 for b in r.get('content',[]):
  if b.get('type')=='text':
   try:return json.loads(b['text'])
   except:return b['text']
 return r
def call(tool,payload): return dec(call_tool(tool,payload,timeout=180))
report={}
report['unit_compile']=call('blueprint_query',{'action':'compile_blueprint','asset_path':UNIT})
report['unit_save']=call('blueprint_query',{'action':'save_asset','asset_path':UNIT})
report['skills']=call('blueprint_query',{'action':'get_cdo_properties','asset_path':UNIT,'name_pattern':'battleSkills'})
report['ui_compile']=call('ui_query',{'action':'compile_widget','asset_path':UI})
report['ui_save']=call('blueprint_query',{'action':'save_asset','asset_path':UI})
report['ui_tree']=call('ui_query',{'action':'get_widget_tree','asset_path':UI})
report['npc_verify']=call('editor_query',{'action':'run_python','params':{'command':'C:/EnvironmentPortfolio/BS_GodFile/Content/Python/verify_melodia_npc_placeholders.py','mode':'execute_file'}})
print(json.dumps(report,indent=2,default=str))
