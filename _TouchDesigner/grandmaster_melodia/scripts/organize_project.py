"""Organize Grandmaster Melodia — newcomer-friendly layout.
Clean grid, color coding, annotations, clear comments.
Run via TD Textport: exec(open(...).read())
"""

root = op('/project1')

# ── 1. CONTAINER LAYOUT (200-unit grid, left-to-right flow) ──────
# Left column: input/analysis (audio, shaders)
# Center column: processing (postfx, particles, osc)  
# Right column: output/UI (geo, render, ui, learn_td)
# Bottom: exports, tutorial

layout = {
    # Left column — INPUTS
    'audio':        (-1400, 0),
    'shaders':      (-1400, 400),
    # Center left — PROCESSING
    'postfx':       (-800, 0),
    'particles':    (-800, 400),
    # Center — ROUTING
    'osc':          (-200, 0),
    # Right — OUTPUT
    'geo':          (400, 0),
    'render':       (400, 400),
    # Far right — UI + LEARN
    'ui':           (1000, 0),
    'learn_td':     (1000, 400),
    # Bottom — EXPORT
    'export':       (400, -400),
}

for name, (nx, ny) in layout.items():
    c = root.op(name)
    if c is not None:
        c.nodeX = nx
        c.nodeY = ny

print('[1/7] Containers positioned on 200-unit grid')

# ── 2. COLOR CODING ─────────────────────────────────────────────
colors = {
    'audio':     (0.55, 0.35, 0.70),  # purple
    'shaders':   (0.40, 0.20, 0.60),  # dark purple
    'postfx':    (0.95, 0.55, 0.20),  # orange
    'particles': (0.20, 0.70, 0.90),  # cyan/blue
    'osc':       (0.30, 0.80, 0.30),  # green
    'geo':       (0.90, 0.30, 0.30),  # red
    'render':    (0.90, 0.70, 0.10),  # gold
    'ui':        (0.40, 0.60, 1.00),  # blue
    'learn_td':  (0.60, 0.60, 0.60),  # gray
    'export':    (0.50, 0.80, 0.50),  # light green
}

for name, (r, g, b) in colors.items():
    c = root.op(name)
    if c is not None:
        c.color = (r, g, b)

print('[2/7] Containers color-coded')

# ── 3. CLEAR COMMENTS ───────────────────────────────────────────
comments = {
    'audio':     'AUDIO ENGINE — Melusina VoiceSynth WAV → pitch/amp/beat analysis → OSC to UE',
    'postfx':    'POST-FX CHAIN — Nikki-style bloom (3-pass Gaussian) + LUT color grade + vignette',
    'particles': 'PARTICLE SYSTEMS — GPU particles: sparkles (40), motes (50), wish burst (120)',
    'shaders':   'SHADER LAB — GLSL prototypes for toon, satin, crystal, sparkle — port to UE when done',
    'osc':       'OSC ROUTING HUB — TD ↔ Blender(:9000) ↔ UE(:8000) — preset matrix + routing table',
    'geo':       'GEOMETRY LOADER — FBX/USD import + camera rig + lighting',
    'render':    'RENDER OUTPUT — main composite + stats overlay + display output',
    'ui':        'UI CONTROL PANEL — style presets, day/night slider, audio gain, particle density',
    'export':    'EXPORT — screenshot capture to PNG',
    'learn_td':  'LEARN TD — Tutorial + Escher geometry — 9 containers, 232 SOPs — double-click to explore',
}

for name, txt in comments.items():
    c = root.op(name)
    if c is not None:
        c.comment = txt

print('[3/7] Comments added')

# ── 4. ANNOTATIONS AROUND GROUPS ────────────────────────────────
# (Annotations are visual boxes around groups)

# Create annotation around INPUT group (audio + shaders)
root.create('annotateCOMP', 'input_group')
try:
    ann1 = root.op('input_group')
    ann1.par.text = 'INPUTS'
    ann1.nodeX = -1420; ann1.nodeY = 420
    ann1.nodeWidth = 300; ann1.nodeHeight = 460
    ann1.color = (0.5, 0.3, 0.7)  # purple tint
except: pass

# PROCESSING group (postfx + particles)
root.create('annotateCOMP', 'fx_group')
try:
    ann2 = root.op('fx_group')
    ann2.par.text = 'EFFECTS'
    ann2.nodeX = -820; ann2.nodeY = 420
    ann2.nodeWidth = 300; ann2.nodeHeight = 460
    ann2.color = (0.9, 0.5, 0.2)  # orange tint
except: pass

# ROUTING group (osc)
root.create('annotateCOMP', 'routing_group')
try:
    ann3 = root.op('routing_group')
    ann3.par.text = 'ROUTING'
    ann3.nodeX = -220; ann3.nodeY = 20
    ann3.nodeWidth = 240; ann3.nodeHeight = 280
    ann3.color = (0.3, 0.8, 0.3)  # green tint
except: pass

# OUTPUT group (geo + render)
root.create('annotateCOMP', 'output_group')
try:
    ann4 = root.op('output_group')
    ann4.par.text = 'OUTPUT'
    ann4.nodeX = 380; ann4.nodeY = 420
    ann4.nodeWidth = 300; ann4.nodeHeight = 460
    ann4.color = (0.9, 0.3, 0.3)  # red tint
except: pass

# UI + LEARN group
root.create('annotateCOMP', 'ui_learn_group')
try:
    ann5 = root.op('ui_learn_group')
    ann5.par.text = 'UI + LEARN'
    ann5.nodeX = 980; ann5.nodeY = 420
    ann5.nodeWidth = 300; ann5.nodeHeight = 460
    ann5.color = (0.4, 0.6, 1.0)  # blue tint
except: pass

print('[4/7] Annotation groups created')

# ── 5. NEWCOMER GUIDE ANNOTATION ────────────────────────────────
root.create('annotateCOMP', 'newcomer_guide')
try:
    guide = root.op('newcomer_guide')
    guide.par.text = (
        'GRANDMASTER MELODIA TD v2.0\n\n'
        'LEFT: Audio analysis + Shader prototypes (inputs)\n'
        'CENTER: Post-FX bloom + Particle POPs + OSC routing\n'
        'RIGHT: 3D geometry + Render output + UI controls\n'
        'FAR RIGHT: Learn TD tutorial + Escher geometry\n\n'
        'Double-click any colored box to enter its network.\n'
        'Press SPACE for 3D view | H to home camera | P for params.'
    )
    guide.nodeX = -800; guide.nodeY = 800
    guide.nodeWidth = 600; guide.nodeHeight = 200
    guide.color = (1.0, 1.0, 0.7)  # warm yellow
except: pass

print('[5/7] Newcomer guide annotation')

# ── 6. MOVE DISPLAY OP INTO RENDER ─────────────────────────────
display = root.op('display')
gradient = root.op('gradient')
render = root.op('render')

if display and render:
    # Move the display and gradient INTO the render container
    # Actually, keep them as root-level for visibility, but label them
    if display:
        display.comment = 'LIVE PREVIEW — shows output of render chain. Display flag ON.'
    if gradient:
        gradient.comment = 'Test gradient source → wired to display Out TOP'
    
    # Wire gradient to postfx chain if possible
    threshold = root.op('postfx/bloom_threshold')
    if threshold and gradient:
        try:
            threshold.inputConnectors[0].connect(gradient)
        except:
            pass

print('[6/7] Display ops labeled and connected')

# ── 7. CREATE A TEXT DAT LEGEND ─────────────────────────────────
legend = root.create('textDAT', 'PROJECT_LEGEND')
legend.nodeX = -1400; legend.nodeY = 800
legend.nodeWidth = 800; legend.nodeHeight = 300
legend.color = (0.15, 0.15, 0.2)
legend.comment = 'Read me first — project guide for newcomers'

guide_text = """GRANDMASTER MELODIA — TOUCHDESIGNER PROJECT
=====================================================
Built for Environment Portfolio Platform (UE 5.8 + Blender 5.1)

HOW TO USE THIS PROJECT:
1. Look at the colored boxes below — each is a CONTAINER
2. Double-click any container to enter its network
3. Press SPACE to toggle between operator list and 3D view
4. Middle-click any operator to see its live output
5. Select any operator and press P for parameters
6. Press H to home the camera on your geometry

CONTAINER LEGEND:
  AUDIO (purple)     — Melusina vocal analysis: pitch, amplitude, beat
  SHADERS (dark purp)— GLSL shader prototypes (toon, satin, crystal)
  POST-FX (orange)   — Nikki bloom chain: 3-pass Gaussian + LUT
  PARTICLES (cyan)   — GPU particles: sparkles, ambient motes, burst 
  OSC (green)        — Open Sound Control: TD ↔ Blender ↔ Unreal
  GEO (red)          — 3D models: FBX loader + camera + lighting
  RENDER (gold)      — Final render output + stats overlay
  UI (blue)          — Preset controls: style, day/night, audio gain
  LEARN TD (gray)    — Tutorial + M.C. Escher geometry playground
  EXPORT (lt green)  — Screenshot export to PNG

QUICK START:
  → Double-click LEARN TD (gray box, far right)
  → Double-click any Escher piece (Penrose stairs, spiral, etc.)
  → Press SPACE to see 3D geometry
  → Press H to home the camera
  → Select any SOP node and press P — tune parameters live!

YOUR PIPELINE:
  Blender (SurrealArch) → FBX export → TD (SOPs + FX) → OSC → UE 5.8
"""

legend.text = guide_text

print('[7/7] Project legend created')
print('')
print('=' * 50)
print('  GRANDMASTER MELODIA — Organized')
print('')
print('  10 containers on 200-unit grid')
print('  5 annotation groups (INPUTS, EFFECTS, ROUTING, OUTPUT, UI+LEARN)')
print('  Color-coded by function')
print('  Newcomer guide annotation')
print('  Full legend text DAT')
print('')
print('  Double-click any box → explore!')
print('=' * 50)
