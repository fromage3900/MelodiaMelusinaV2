"""ONE-SHOT: Build complete working render pipeline from scratch.
Everything needed to see the fractal tower on screen RIGHT NOW.
"""
root = op('/project1')
render = root.op('render')
lt = root.op('learn_td')
ft = lt.op('escher_fractal_tower')

# ── 1. CLEAN SLATE ──────────────────────────────────────────────
for c in list(render.findChildren()):
    c.destroy()

# Kill old display/gradient at root level  
for sn in ['display', 'gradient', 'viewer3d', 'label']:
    o = root.op(sn)
    if o: o.destroy()

# ── 2. CAMERA INSIDE FRACTAL TOWER ──────────────────────────────
cam = ft.op('render_cam')
if cam is None:
    cam = ft.create('cameraCOMP', 'render_cam')
cam.nodeX = 150; cam.nodeY = 200
cam.comment = 'Camera for render pipeline'

# ── 3. RENDER TOP INSIDE FRACTAL TOWER ──────────────────────────
rtop = ft.op('render_out')
if rtop is None:
    rtop = ft.create('renderTOP', 'render_out')
rtop.nodeX = 350; rtop.nodeY = 0
rtop.par.camera = cam.path
rtop.comment = 'Renders fractal geometry -> display chain'

# ── 4. RENDER PIPELINE IN /render ────────────────────────────────
# Bloom overlay (geometry + postfx bloom)
blm = render.create('compositeTOP', 'bloom_overlay')
blm.nodeX = 0; blm.nodeY = 0
blm.inputConnectors[0].connect(rtop)
pfx = root.op('postfx/postfx_out')
if pfx:
    blm.inputConnectors[1].connect(pfx)
blm.comment = 'Base geometry + Nikki bloom overlay'

# Particle overlay
po = render.create('overTOP', 'particle_over')
po.nodeX = 250; po.nodeY = 0
po.inputConnectors[0].connect(blm)
pb = root.op('particles/particle_bloom')
if pb:
    po.inputConnectors[1].connect(pb)
po.comment = 'Nikki particles on top of bloomed geometry'

# Stats overlay
st = render.create('textTOP', 'stats_text')
st.nodeX = 250; st.nodeY = -120
st.par.text = 'GRANDMASTER MELODIA'

so = render.create('overTOP', 'stats_overlay')
so.nodeX = 500; so.nodeY = 0
so.inputConnectors[0].connect(po)
so.inputConnectors[1].connect(st)

# Display OUT — THIS SHOWS ON SCREEN
od = render.create('outTOP', 'out_display')
od.nodeX = 750; od.nodeY = 0
od.inputConnectors[0].connect(so)
od.display = True
od.viewer = True
od.comment = 'FINAL OUTPUT — what you see on the backdrop'

# Export OUT — SAVES TO DISK
oe = render.create('moviefileoutTOP', 'out_export')
oe.nodeX = 750; oe.nodeY = -150
oe.inputConnectors[0].connect(so)
oe.comment = 'EXPORT — set file path, click Record to save PNG'

# ── 5. SET NODE WIDTHS FOR VISIBILITY ───────────────────────────
for c in render.findChildren():
    c.nodeWidth = 120

# ── 6. VERIFY ────────────────────────────────────────────────────
kids = [c.name for c in render.findChildren()]
print('RENDER CHAIN: ' + ','.join(kids))
print('')
print('Pipeline: fractal_tower -> camera -> render_out -> bloom -> particles -> stats -> DISPLAY')
print('Check the network backdrop NOW — you should see the fractal tower')
