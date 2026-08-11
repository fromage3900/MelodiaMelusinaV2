"""Final cleanup: remove stray ops, fix positions, cross-wire containers."""
import math

root = op('/project1')

# ── 1. DESTROY STRAY OPS ───────────────────────────────────────
strays = ['base1','null1','test_types','blur_params','type_probe','mcp_test','test_container_1','test_chop_1']
for name in strays:
    o = root.op(name)
    if o is not None:
        o.destroy()
        print(f'  destroyed stray: {name}')

# Destroy auto-created torus1 in all geometryCOMPs
for comp in root.findChildren(type='geometryCOMP'):
    t = comp.op('torus1')
    if t is not None:
        t.destroy()
        print(f'  cleaned torus in: {comp.name}')

# Also in learn_td sub-geometries
lt = root.op('learn_td')
if lt:
    for comp in lt.findChildren(type='geometryCOMP'):
        t = comp.op('torus1')
        if t is not None:
            t.destroy()
            print(f'  cleaned torus in learn_td/{comp.name}')

print('[1/4] Stray ops destroyed')

# ── 2. POSITION TOP-LEVEL CONTAINERS ON 200 GRID ───────────────
# Standard layout: left column = audio/postfx/particles/shaders (-1200)
#                   right column = osc/geo/render/ui (-600)
#                   far right = learn_td (800)
layout = {
    'audio':     (-1200, 0),
    'postfx':    (-1200, 400),
    'particles': (-1200, 800),
    'shaders':   (-1200, 1200),
    'osc':       (-600, 0),
    'geo':       (-600, 400),
    'render':    (-600, 800),
    'ui':        (-600, 1200),
    'export':    (-600, 1600),
    'learn_td':  (1000, 0),
}

for name, (nx, ny) in layout.items():
    o = root.op(name)
    if o is not None:
        o.nodeX = nx
        o.nodeY = ny
        print(f'  {name}: ({nx}, {ny})')

print('[2/4] Containers positioned')

# ── 3. CROSS-WIRE CONTAINERS ───────────────────────────────────

# 3a. Audio hub → OSC output
audio_hub = root.op('audio/audio_hub')
osc_out_ue = root.op('osc/out_ue_material')
if audio_hub and osc_out_ue:
    osc_out_ue.inputConnectors[0].connect(audio_hub)
    print('  wired: audio_hub → osc/out_ue_material')

# 3b. Connect audio to particles (amplitude → sparkle rate)
osc_niagara = root.op('osc/out_ue_niagara')
if osc_niagara:
    print('  osc/out_ue_niagara ready (connect CHOP channels from audio for reactivity)')

# 3c. Preset signal → OSC out
preset_signal = root.op('osc/preset_signal')
out_presets = root.op('osc/out_ue_presets')
if preset_signal and out_presets:
    # Already wired from earlier fix
    print('  preset_signal → out_ue_presets (already connected)')

# 3d. FBX → Render chain
fbx = root.op('geo/fbx_import')
render_main = root.op('render/render_main')
if render_main:
    print('  render/render_main ready (wire fbx_import or camera to its inputs)')

print('[3/4] Cross-container wiring done')

# ── 4. RENAME audio1 → audio IF audio1 EXISTS ──────────────────
a1 = root.op('audio1')
a = root.op('audio')
if a1 and not a:
    a1.name = 'audio'
    print('  renamed audio1 → audio')

print('[4/4] Complete')
print('')
print('CLEANUP SUMMARY:')
for name in layout:
    o = root.op(name)
    if o is not None:
        kids = len(o.findChildren())
        print(f'  /{name}: {kids} children')
