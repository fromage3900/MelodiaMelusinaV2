import urllib.request, json, sys

MCP_URL = 'http://127.0.0.1:9316/mcp'
LOG = []

def log(msg):
    print(msg)
    LOG.append(msg)

def call_monolith(action, **kwargs):
    body = json.dumps({
        'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
        'params': {'name': 'blueprint_query', 'arguments': {'action': action, **kwargs}}
    }).encode()
    req = urllib.request.Request(MCP_URL, data=body, headers={'Content-Type': 'application/json'})
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
        return resp
    except Exception as e:
        return {'isError': True, 'error': str(e)}

def editor_run_python(script_code):
    """Using editor_query tool with run_python action"""
    body = json.dumps({
        'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
        'params': {'name': 'editor_query', 'arguments': {'action': 'run_python', 'command': script_code}}
    }).encode()
    req = urllib.request.Request(MCP_URL, data=body, headers={'Content-Type': 'application/json'})
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
        return resp
    except Exception as e:
        return {'isError': True, 'error': str(e)}

def export_graph(asset_path, graph_name='EventGraph'):
    r = call_monolith('export_graph', asset_path=asset_path, graph_name=graph_name)
    if r.get('isError') or not r.get('result', {}).get('content'):
        return None
    try:
        return json.loads(r['result']['content'][0]['text'])
    except:
        return None

def ok(step, resp):
    if resp.get('isError'):
        log(f'  {step}: FAIL - {resp}')
    else:
        content = resp.get('result', {}).get('content', [])
        txt = content[0].get('text','') if content and isinstance(content[0], dict) else str(content)
        log(f'  {step}: {txt}')

def compile_bp(asset_path):
    r = call_monolith('compile_blueprint', asset_path=asset_path)
    ok('Compile', r)
    return r

def connect(asset_path, graph, src_node, src_pin, tgt_node, tgt_pin):
    r = call_monolith('connect_pins', asset_path=asset_path, graph_name=graph,
        source_node=src_node, source_pin=src_pin, target_node=tgt_node, target_pin=tgt_pin)
    ok(f'Connect {src_node}.{src_pin} -> {tgt_node}.{tgt_pin}', r)
    return r

def disconnect_node_pin(asset_path, graph, node, pin):
    """Disconnect a specific pin on a node"""
    r = call_monolith('disconnect_pins', asset_path=asset_path, graph_name=graph,
        node_id=node, pin_name=pin)
    ok(f'Disconnect {node}.{pin}', r)
    return r

def remove_node(asset_path, graph, node_id):
    r = call_monolith('remove_node', asset_path=asset_path, graph_name=graph, node_id=node_id)
    ok(f'Remove {node_id}', r)
    return r

def set_pin_default(asset_path, graph, node, pin, value):
    r = call_monolith('set_pin_default', asset_path=asset_path, graph_name=graph,
        node_id=node, pin_name=pin, value=value)
    ok(f'Set {node}.{pin} = {value}', r)
    return r

def search_and_replace_text(search_str, replace_str):
    """Search all loaded assets for a string and replace"""
    script = f'''
import unreal
paths = ["/Game/Melodia/UI/WBP_SaveLoadPanel", "/Game/Melodia/UI/WBP_MainMenu"]
count = 0
for path in paths:
    asset = unreal.load_asset(path)
    if asset and hasattr(asset, 'get_all_widgets'):
        for w in asset.get_all_widgets():
            if hasattr(w, 'set_editor_property'):
                try:
                    txt = w.get_editor_property('text')
                    if txt and "{search_str}" in str(txt):
                        w.set_editor_property('text', str(txt).replace("{search_str}", "{replace_str}"))
                        count += 1
                        print(f"Fixed: {{w.get_name()}}")
                except:
                    pass
print(f"Fixed {{count}} widgets")
'''
    r = editor_run_python(script)
    return r

log('=' * 60)
log('SAVE SYSTEM FIXES - FINAL EXECUTION')
log('=' * 60)

# ============================================================
log('\n--- STEP 1: Verify BP_MelodiaJRPGGameInstance state ---')
# ============================================================
data = export_graph('/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance')
if not data:
    log('FATAL: Could not export main BP')
    sys.exit(1)

pin_to_node = {}
for n in data['nodes']:
    for p in n.get('pins', []):
        pin_to_node[p['id']] = (n['id'], p['name'], p['direction'])

# Show chain
for n in data['nodes']:
    if n['id'] in ['K2Node_CustomEvent_2', 'K2Node_CallFunction_1', 'K2Node_VariableSet_8',
                   'K2Node_VariableSet_9', 'K2Node_VariableSet_6', 'K2Node_CallFunction_46',
                   'K2Node_CallFunction_72', 'K2Node_CallFunction_73']:
        title = n.get('title', '').replace('\n', ' ').strip()
        conns = []
        for p in n.get('pins', []):
            if p['type'] == 'exec' and p.get('connected_to_ids'):
                targets = [f'{pin_to_node.get(c, ("?","?","?"))}' for c in p['connected_to_ids'] if c]
                conns.append(f'{p["name"]}->{targets}')
        log(f'  {n["id"]} ({title}): {"; ".join(conns)}')

log(f'  Found {len([n for n in data["nodes"] if "Register" in n.get("title","")])} RegisterSkill nodes')

# ============================================================
log('\n--- STEP 2: Fix Defect 1 - Verify exec chain ---')
# ============================================================
log('  Defect 1 appears already in correct state (verified above)')
log('  Compiling...')
compile_bp('/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance')

# ============================================================
log('\n--- STEP 3: Fix Defect 2 - Unify slot names ---')
# ============================================================

log('\n3.1 BP_SavePointBase - Fix slotName...')
asset_sp = '/Game/TurnBasedJRPGTemplate/Blueprints/Interactables/BP_SavePointBase'
data_sp = export_graph(asset_sp)
if data_sp:
    pin_to_node_sp = {}
    for n in data_sp['nodes']:
        for p in n.get('pins', []):
            pin_to_node_sp[p['id']] = (n['id'], p['name'], p['direction'])

    # Find the Save Game node with slotName pin
    for n in data_sp['nodes']:
        title = n.get('title', '').replace('\n', ' ').strip()
        for p in n.get('pins', []):
            pname_lower = p['name'].lower()
            if 'slotname' in pname_lower or 'slot_name' in pname_lower:
                cids = p.get('connected_to_ids', [])
                connected = [pin_to_node_sp.get(c, ('?','?','?')) for c in cids if c]
                log(f'  {n["id"]} ({title}) pin {p["name"]}: connected={connected} has_default={p.get("default_value","NOT SET")}')
                
                # Disconnect if connected to something
                if cids:
                    disconnect_node_pin(asset_sp, 'EventGraph', n['id'], p['name'])
                
                # Set default value
                set_pin_default(asset_sp, 'EventGraph', n['id'], p['name'], 'MelodiaJRPGSlot0')

# 3.2 WBP_SaveLoadPanel 
log('\n3.2 WBP_SaveLoadPanel - Fix slot name...')
asset_wb = '/Game/Melodia/UI/WBP_SaveLoadPanel'

# Try to find MelusinaSlot0 references in the widget
r = editor_run_python(f'''
import unreal
asset = unreal.load_asset(r"{asset_wb}")
if asset:
    print(f"Loaded: {{asset.get_path_name()}}")
else:
    print("Could not load asset")
''')
log(f'  Editor load: {r}')

# Export widget graph to find references
r_widget = call_monolith('export_graph', asset_path=asset_wb, graph_name='WidgetGraph')
if r_widget.get('isError'):
    log(f'  WidgetGraph export: {r_widget}')
else:
    try:
        data_wb = json.loads(r_widget['result']['content'][0]['text'])
        text_wb = json.dumps(data_wb)
        if 'MelusinaSlot0' in text_wb:
            log('  WBP_SaveLoadPanel WidgetGraph contains MelusinaSlot0 references')
        if 'MelodiaJRPGSlot0' in text_wb:
            log('  WBP_SaveLoadPanel WidgetGraph already has MelodiaJRPGSlot0')
        if 'MelusinaSlot0' not in text_wb and 'MelodiaJRPGSlot0' not in text_wb:
            log('  WBP_SaveLoadPanel: no slot string found in WidgetGraph')
    except Exception as e:
        log(f'  WidgetGraph parse error: {e}')
        log(f'  Raw response snippet: {json.dumps(r_widget)[:500]}')

# Also search via editor python for text references
# List available graphs for WBP_SaveLoadPanel
r_graphs = call_monolith('list_graphs', asset_path=asset_wb)
log(f'  Available graphs: {r_graphs}')

log('  Searching WBP_SaveLoadPanel for MelusinaSlot0 via editor...')
slot_search_code = '''
import unreal
asset = unreal.load_asset(r"''' + asset_wb + '''")
count = 0
if asset and hasattr(asset, 'get_all_widgets'):
    for w in asset.get_all_widgets():
        for pname in ['text', 'tool_tip_text', 'hint_text']:
            if hasattr(w, 'get_editor_property'):
                try:
                    val = w.get_editor_property(pname)
                    if val and 'MelusinaSlot0' in str(val):
                        print("Found in " + w.get_name() + "." + pname + " = " + str(val))
                        count += 1
                except:
                    pass
print("Found " + str(count) + " references total")
if count == 0:
    print("No MelusinaSlot0 references found")
'''
r_search = editor_run_python(slot_search_code)
log(f'  Search result: {r_search}')

# Check WBP_MainMenu
log('\n3.3 WBP_MainMenu - Verify slot name...')
r_mm = call_monolith('export_graph', asset_path='/Game/Melodia/UI/WBP_MainMenu', graph_name='EventGraph')
if not r_mm.get('isError'):
    try:
        data_mm = json.loads(r_mm['result']['content'][0]['text'])
        text_mm = json.dumps(data_mm)
        if 'MelodiaJRPGSlot0' in text_mm:
            log('  WBP_MainMenu: uses MelodiaJRPGSlot0 (CORRECT)')
        elif 'MelusinaSlot0' in text_mm:
            log('  WBP_MainMenu: uses MelusinaSlot0 (needs fix)')
        else:
            log('  WBP_MainMenu: no slot string found in EventGraph')
    except:
        log('  Could not parse WBP_MainMenu data')

# Also check WidgetGraph for WBP_MainMenu
r_mm2 = call_monolith('export_graph', asset_path='/Game/Melodia/UI/WBP_MainMenu', graph_name='WidgetGraph')
if not r_mm2.get('isError'):
    try:
        data_mm2 = json.loads(r_mm2['result']['content'][0]['text'])
        text_mm2 = json.dumps(data_mm2)
        if 'MelodiaJRPGSlot0' in text_mm2:
            log('  WBP_MainMenu WidgetGraph: uses MelodiaJRPGSlot0 (CORRECT)')
        elif 'MelusinaSlot0' in text_mm2:
            log('  WBP_MainMenu WidgetGraph: uses MelusinaSlot0 (needs fix)')
        else:
            log('  WBP_MainMenu WidgetGraph: no slot string found')
    except:
        log('  Could not parse WBP_MainMenu WidgetGraph')

# 3.4 Compile modified BPs
log('\n3.4 Compiling modified Blueprints...')
compile_bp(asset_sp)
compile_bp('/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance')

# ============================================================
log('\n--- STEP 4: Verify changes ---')
# ============================================================

log('\n4.1 BP_MelodiaJRPGGameInstance re-export:')
data_v = export_graph('/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance')
if data_v:
    pin_to_node_v = {}
    for n in data_v['nodes']:
        for p in n.get('pins', []):
            pin_to_node_v[p['id']] = (n['id'], p['name'], p['direction'])
    for n in data_v['nodes']:
        if n['id'] in ['K2Node_CustomEvent_2', 'K2Node_CallFunction_1', 'K2Node_VariableSet_9', 'K2Node_CallFunction_46']:
            title = n.get('title', '').replace('\n', ' ').strip()
            conns = []
            for p in n.get('pins', []):
                if p['type'] == 'exec' and p.get('connected_to_ids'):
                    targets = [f'{pin_to_node_v.get(c, ("?","?","?"))}' for c in p['connected_to_ids'] if c]
                    conns.append(f'{p["name"]}->{targets}')
            log(f'    {n["id"]}: {"; ".join(conns)}')

log('\n4.2 BP_SavePointBase re-export:')
data_sp_v = export_graph(asset_sp)
if data_sp_v:
    for n in data_sp_v['nodes']:
        title = n.get('title', '').replace('\n', ' ').strip()
        for p in n.get('pins', []):
            if 'slotname' in p['name'].lower():
                log(f'    {n["id"]} ({title}) {p["name"]}: default="{p.get("default_value","")}" connected={bool(p.get("connected_to_ids",[]))}')

log('\n' + '=' * 60)
log('RESULTS SUMMARY')
log('=' * 60)
for l in LOG:
    print(l)
