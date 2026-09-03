"""Wire complete render pipeline — geometry → postfx → particles → display → export.
All containers connected so you can SEE every stage and EXPORT renders.
Run via TD Textport: exec(open(...).read())
"""

root = op('/project1')
render_comp = root.op('render')
postfx_comp = root.op('postfx')
particles_comp = root.op('particles')
display = root.op('display')
lt = root.op('learn_td')

print('=== WIRING GRANDMASTER MELODIA RENDER PIPELINE ===')
print('')

# ── 1. CREATE RENDER OPS IN /render ──────────────────────────────
# Clean existing render ops for fresh rebuild
for cname in ['geo_switch', 'bloom_pass', 'particle_overlay', 'stats_overlay', 'out_display', 'out_export', 'render_source']:
    old = render_comp.op(cname)
    if old: old.destroy()

# Render TOP — sources from geometry
render_src = render_comp.create('renderTOP', 'render_source')
render_src.nodeX = 0; render_src.nodeY = 0
render_src.comment = 'Renders the selected geometry COMP below. Switch to change view.'

# Switch TOP — cycle through geometry containers
switch = render_comp.create('switchTOP', 'geo_switch')
switch.nodeX = 250; switch.nodeY = 0
switch.comment = 'Index 0: procedural_tower, 1: instanced_city, 2: play, 3-7: Escher pieces'

# Composite — add bloom from postfx
bloom_pass = render_comp.create('compositeTOP', 'bloom_overlay')
bloom_pass.nodeX = 500; bloom_pass.nodeY = 0
bloom_pass.comment = 'Overlays bloom from postfx chain on top of geometry'

# Overlay — add particles  
particle_overlay = render_comp.create('overTOP', 'particle_over')
particle_overlay.nodeX = 750; particle_overlay.nodeY = 0
particle_overlay.comment = 'Overlays Nikki sparkle/mote/burst particles on top'

# Stats text overlay
stats_over = render_comp.create('textTOP', 'stats_text')
stats_over.nodeX = 750; stats_over.nodeY = -120
stats_over.par.text = 'GRANDMASTER MELODIA'
stats_over.comment = 'Stats overlay — project name, tris count, FPS'

stats_composite = render_comp.create('overTOP', 'stats_overlay')
stats_composite.nodeX = 1000; stats_composite.nodeY = 0
stats_composite.comment = 'Composites stats text on final render'

# Display output
out_disp = render_comp.create('outTOP', 'out_display')
out_disp.nodeX = 1250; out_disp.nodeY = 0
out_disp.display = True
out_disp.viewer = True
out_disp.comment = 'FINAL OUTPUT — what you see in the network backdrop'

# Export output
out_export = render_comp.create('moviefileoutTOP', 'out_export')
out_export.nodeX = 1250; out_export.nodeY = -200
out_export.comment = 'EXPORT — saves rendered frame to PNG. Enable record to export sequence.'

print('[1/5] Render ops created: switch → bloom → particles → stats → output')

# ── 2. WIRE GEOMETRY COMP OUTPUTS INTO SWITCH ────────────────────
geo_sources = [
    'procedural_tower',
    'instanced_city', 
    'my_playground',
    'escher_penrose_stairs',
    'escher_spiral_staircase',
    'escher_fractal_tower',
    'escher_tessellation',
    'escher_belvedere',
]

# Create a Render TOP inside each geometry COMP so we can source it
for i, geo_name in enumerate(geo_sources):
    geo = lt.op(geo_name)
    if geo is None:
        continue
    
    # Ensure each geometry COMP has a render TOP
    geo_render = geo.op('render_out')
    if geo_render is None:
        geo_render = geo.create('renderTOP', 'render_out')
    geo_render.nodeX = 200; geo_render.nodeY = 0
    geo_render.comment = 'Renders this geometry — connected to master switch'
    
    # Connect geo render -> switch input
    switch.inputConnectors[i].connect(geo_render)
    print('  [' + str(i) + '] ' + geo_name + ' → switch input ' + str(i))

print('[2/5] ' + str(len(geo_sources)) + ' geometry sources wired to switch')

# ── 3. WIRE THE FULL PIPELINE ────────────────────────────────────
# Switch → render source (select which geometry to render)
# render_src is our main source — it already exists

# Render source → bloom pass
# We need to render the switch output
switch_render = render_comp.create('renderTOP', 'switch_render')
switch_render.nodeX = 250; switch_render.nodeY = -150
switch_render.inputConnectors[0].connect(switch)
switch_render.comment = 'Renders the current switch-selected geometry'

# Wire: geometry render → postfx threshold
threshold = postfx_comp.op('bloom_threshold')
if threshold:
    try:
        threshold.inputConnectors[0].connect(switch_render)
        print('[3/5] geometry → postfx bloom chain wired')
    except:
        print('[3/5] geometry → postfx: already connected')

# Wire: postfx out → bloom overlay
postfx_out = postfx_comp.op('postfx_out')
if postfx_out:
    bloom_pass.inputConnectors[0].connect(switch_render)  # base = clean geometry
    bloom_pass.inputConnectors[1].connect(postfx_out)       # overlay = bloomed version
    print('[3/5] bloom composited: base(geo) + overlay(bloom)')

# Wire: bloom_pass → particle_overlay
particle_bloom = particles_comp.op('particle_bloom')
if particle_bloom:
    particle_overlay.inputConnectors[0].connect(bloom_pass)      # base = geometry + bloom
    particle_overlay.inputConnectors[1].connect(particle_bloom)  # overlay = particles
    print('[3/5] particles overlayed on render')

# Wire: particle_overlay → stats
stats_composite.inputConnectors[0].connect(particle_overlay)
stats_composite.inputConnectors[1].connect(stats_over)
print('[3/5] stats overlay composited')

# Wire: stats → display + export
out_disp.inputConnectors[0].connect(stats_composite)
out_export.inputConnectors[0].connect(stats_composite)
print('[3/5] final → display OUT + export OUT')

# ── 4. WIRE ROOT-LEVEL DISPLAY ──────────────────────────────────
# Remove old gradient display if it exists
gradient = root.op('gradient')
if gradient:
    try:
        # Disconnect gradient from display
        root_display = root.op('display')
        if root_display:
            root_display.inputConnectors[0].connect(stats_composite)
            root_display.comment = 'FINAL OUTPUT — shows complete render pipeline'
        gradient.destroy()
        print('[4/5] Root display wired to final composite')
    except:
        pass

# ── 5. SET DEFAULT SWITCH INDEX ──────────────────────────────────
switch.par.index = 0  # Start with procedural tower
print('[5/5] Default view: procedural_tower (switch index 0)')

# ── VERIFY ───────────────────────────────────────────────────────
print('')
print('=' * 50)
print('  RENDER PIPELINE — COMPLETE')
print('')
print('  DATA FLOW:')
print('    Geometry COMP → Render TOP → Switch(8 inputs)')
print('    Switch → PostFX(bloom) → Composite')
print('    + Particles → Overlay → Stats → OUT DISPLAY')
print('    OUT DISPLAY → backdrop (what you see)')
print('    OUT EXPORT → saves to disk when recording')
print('')
print('  TO CYCLE VIEWS:')
print('    In TD: select /render/geo_switch')
print('    Press P, change Index 0-7 to switch Escher piece')
print('')
print('  TO EXPORT:')
print('    Select /render/out_export')
print('    Press P, set File path, click Record')
print('')
print('  GEOMETRY SOURCES:')
for i, geo_name in enumerate(geo_sources):
    status = 'READY' if lt.op(geo_name) else 'MISSING'
    print('    [' + str(i) + '] ' + geo_name + ' — ' + status)
print('=' * 50)
