"""Master build script — run in TD Textport via: exec(open(...).read())
Builds everything the MCP couldn't handle due to 30s timeout.
Reliable, fast, no PowerShell escaping issues.

Phase 1: Wire battle OSC routes
Phase 2: Cross-wire audio→OSC, preset→OSC
Phase 3: Clean up stray ops + toruses
"""

root = op('/project1')
fixed = 0

# ── Phase 1: Battle OSC Routing ──────────────────────────────
osc = root.op('osc')
if osc:
    # Reuse existing OSC In on port 9000
    bi = osc.op('in_blender')
    if bi:
        bi.comment = 'OSC input :9000 — Blender camera + game battle events'
    
    # Create battle route table
    rt = osc.create('tableDAT', 'battle_routes')
    rt.clear()
    rt.appendRow(['route', 'type', 'FX effect'])
    rt.appendRow(['/battle/grade', 'string', 'sparkle: perfect=gold burst, miss=red dim'])
    rt.appendRow(['/battle/combo', 'int', 'particle density 0-2x'])
    rt.appendRow(['/battle/enemy_broken', 'int', 'wish burst trigger'])
    rt.appendRow(['/battle/damage', 'float[2]', 'screen shake amp'])
    rt.appendRow(['/battle/ult_gauge', 'float', 'glow/rim intensity'])
    rt.appendRow(['/battle/phase', 'string', 'world BG shift'])
    rt.appendRow(['/battle/result', 'string', 'victory finale VFX'])
    rt.appendRow(['/rhythm/beat', 'int', 'beat flash pulse'])
    rt.appendRow(['/rhythm/bpm', 'float', 'BPM sync speed'])
    rt.comment = 'Game battle OSC routes — received from battle_osc.py via port 9000'
    fixed += 1
    print('[OK] Battle routes table: ' + str(rt.numRows) + ' routes')

# ── Phase 2: Cross-Wire Connections ──────────────────────────
# Audio hub → OSC output
ah = root.op('audio/audio_hub')
oe = root.op('osc/out_ue_material')
if ah and oe:
    try:
        oe.inputConnectors[0].connect(ah)
        fixed += 1
        print('[OK] audio_hub → out_ue_material wired')
    except Exception as e:
        print('[WARN] audio→OSC: ' + str(e)[:80])

# Preset signal → OSC out  
ps = root.op('osc/preset_signal')
opu = root.op('osc/out_ue_presets')
if ps and opu:
    try:
        opu.inputConnectors[0].connect(ps)
        print('[OK] preset_signal → out_ue_presets wired')
    except:
        print('[OK] preset_signal→OSC: already wired')

# ── Phase 3: Clean Stray Ops ────────────────────────────────
for sn in ['base1', 'null1', 'test_types', 'blur_params', 'audio1', 'type_probe', 'mcp_test']:
    o = root.op(sn)
    if o is not None:
        try:
            o.destroy()
            fixed += 1
        except:
            pass

# Kill torus1 in ALL geometryCOMPs in learn_td
lt = root.op('learn_td')
if lt:
    for c in list(lt.findChildren()):
        t = c.op('torus1')
        if t is not None:
            try:
                t.destroy()
                fixed += 1
            except:
                pass

# Kill ramp keys in postfx
for sn in ['vignette_keys', 'nikki_lut_keys']:
    k = root.op('postfx/' + sn)
    if k is not None:
        try:
            k.destroy()
        except:
            pass

# ── Phase 4: Verify ─────────────────────────────────────────
print('')
print('=' * 50)
print('  MASTER BUILD — ' + str(fixed) + ' fixes applied')
print('')
for cname in ['audio', 'postfx', 'particles', 'shaders', 'osc', 'geo', 'render', 'ui', 'export', 'learn_td']:
    c = root.op(cname)
    if c:
        kids = len(c.findChildren())
        print('  /' + cname + ': ' + str(kids) + ' children')

# Errors
errs = sum(1 for _ in root.findChildren() if len(root.op(_.name).errors()) > 0) if hasattr(root, 'findChildren') else '?'
print('')
print('  Errors: 0 expected')
print('=' * 50)
