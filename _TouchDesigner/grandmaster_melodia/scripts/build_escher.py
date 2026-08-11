"""M.C. Escher Geometry — built entirely with TD SOPs.
Run via: exec(open(...).read()) in TD Textport or MCP execute_python.
"""
import math

lt = op('/project1/learn_td')

# Clean any existing escher stuff
for c in list(lt.findChildren(name='escher*')):
    c.destroy()

# ── 1. PENROSE IMPOSSIBLE STAIRS ───────────────────────────────
pen = lt.create('geometryCOMP', 'escher_penrose_stairs')
pen.nodeX = -400; pen.nodeY = -800
pen.comment = 'Penrose impossible stairs — 4 connected staircases forming a loop'

# Base: 4 staircase segments forming a square loop
for i in range(4):
    angle = (i / 4.0) * math.pi * 2
    cx = math.cos(angle) * 4
    cz = math.sin(angle) * 4
    
    # Each stair segment = 4 steps
    for j in range(4):
        bx = cx + math.cos(angle) * j * 1.2
        bz = cz + math.sin(angle) * j * 1.2
        by = j * 0.3  + i * 1.2  # Each segment rises higher than the last
        
        box = pen.create('boxSOP', f'step_{i}_{j}')
        box.nodeX = i * 300; box.nodeY = -j * 150
        try: box.par.size = (1.2, 0.15, 0.5)
        except: pass
        
        xform = pen.create('transformSOP', f'step_tx_{i}_{j}')
        xform.nodeX = i * 300 + 150; xform.nodeY = -j * 150
        try: xform.par.t = (bx, by, bz)
        except: pass
        xform.inputConnectors[0].connect(box)

# Merge all steps
merge_all = pen.create('mergeSOP', 'all_steps')
merge_all.nodeX = 1400; merge_all.nodeY = 0

# Connect each transform sequentially 
step_count = 0
for i in range(4):
    for j in range(4):
        tx_op = pen.op(f'step_tx_{i}_{j}')
        if tx_op:
            merge_all.inputConnectors[step_count].connect(tx_op)
            step_count += 1

pen.render = True; pen.display = True

# ── 2. SPIRAL STAIRCASE (ASCENDING HELIX) ──────────────────────
spiral = lt.create('geometryCOMP', 'escher_spiral_staircase')
spiral.nodeX = -400; spiral.nodeY = -1200
spiral.comment = 'Ascending spiral staircase — 60 steps wrapping a central column'

# Central column
column = spiral.create('tubeSOP', 'central_column')
column.nodeX = 0; column.nodeY = 0

# Create spiral steps
for i in range(60):
    angle = (i / 60.0) * math.pi * 6  # 3 full rotations
    height = i * 0.15 + 0.1
    radius = 1.5 + i * 0.01  # slightly expanding
    
    px = math.cos(angle) * radius
    pz = math.sin(angle) * radius
    
    step = spiral.create('boxSOP', f'spiral_step_{i:02d}')
    step.nodeX = (i % 10) * 250; step.nodeY = -(i // 10) * 150
    try: step.par.size = (0.6, 0.08, 0.3)
    except: pass
    
    tx = spiral.create('transformSOP', f'spiral_tx_{i:02d}')
    tx.nodeX = (i % 10) * 250 + 150; tx.nodeY = -(i // 10) * 150
    try: tx.par.t = (px, height, pz)
    except: pass
    try: tx.par.r = (0, math.degrees(angle) + 90, 0)
    except: pass
    tx.inputConnectors[0].connect(step)

# Merge spiral
spiral_merge = spiral.create('mergeSOP', 'spiral_merge')
spiral_merge.nodeX = 2800; spiral_merge.nodeY = -200
spiral_merge.inputConnectors[0].connect(column)
for i in range(60):
    tx = spiral.op(f'spiral_tx_{i:02d}')
    if tx:
        spiral_merge.inputConnectors[i + 1].connect(tx)

spiral.render = True; spiral.display = True

# ── 3. RECURSIVE FRACTAL TOWER ─────────────────────────────────
fractal = lt.create('geometryCOMP', 'escher_fractal_tower')
fractal.nodeX = 200; fractal.nodeY = -800
fractal.comment = 'Self-similar recursive tower — box scaled/rotated/stacked 8 times'

# Build a chain of boxes that get smaller and rotate
prev_op = None
for i in range(8):
    scale = 1.0 - (i * 0.11)
    rotate = i * 22.5
    
    box = fractal.create('boxSOP', f'fractal_box_{i}')
    box.nodeX = i * 250; box.nodeY = -i * 100

    tx = fractal.create('transformSOP', f'fractal_tx_{i}')
    tx.nodeX = i * 250 + 150; tx.nodeY = -i * 100
    try: tx.par.scale = scale
    except: pass
    try: tx.par.r = (rotate, rotate * 0.7, 0)
    except: pass
    try: tx.par.t = (0, i * 1.2, 0)  # stack upward
    except: pass
    tx.inputConnectors[0].connect(box)
    
    if prev_op:
        merge_tmp = fractal.create('mergeSOP', f'fractal_layer_{i}')
        merge_tmp.nodeX = i * 250 + 300; merge_tmp.nodeY = -i * 100
        merge_tmp.inputConnectors[0].connect(prev_op)
        merge_tmp.inputConnectors[1].connect(tx)
        prev_op = merge_tmp
    else:
        prev_op = tx

fractal.render = True; fractal.display = True

# ── 4. TESSELLATION GRID ───────────────────────────────────────
tess = lt.create('geometryCOMP', 'escher_tessellation')
tess.nodeX = 200; tess.nodeY = -1200
tess.comment = 'Geometric tessellation — interlocking diamond pattern on a grid'

# Base grid
grid = tess.create('gridSOP', 'base_grid')
grid.nodeX = 0; grid.nodeY = 0
try: grid.par.rows = 12
except: pass
try: grid.par.cols = 12
except: pass
try: grid.par.size = (12, 12)
except: pass

# Create diamond tiles
diamond = tess.create('boxSOP', 'diamond_shape')
diamond.nodeX = 0; diamond.nodeY = -200
try: diamond.par.size = (0.8, 0.1, 0.8)
except: pass

# Rotate every other tile 45 degrees to create the tessellation pattern
diamond_tx = tess.create('transformSOP', 'diamond_rotate')
diamond_tx.nodeX = 200; diamond_tx.nodeY = -200
try: diamond_tx.par.r = (0, 45, 0)
except: pass
diamond_tx.inputConnectors[0].connect(diamond)

# Noise warp for organic Escher feel
warp = tess.create('noiseSOP', 'escher_warp')
warp.nodeX = 200; warp.nodeY = 0
try: warp.par.amp = 0.1
except: pass
warp.inputConnectors[0].connect(grid)

# Instance diamonds on grid
copy_tess = tess.create('copySOP', 'tess_copy')
copy_tess.nodeX = 400; copy_tess.nodeY = -200
copy_tess.inputConnectors[0].connect(diamond_tx)
copy_tess.inputConnectors[1].connect(warp)

tess.render = True; tess.display = True

# ── 5. BELVEDERE IMPOSSIBLE ARCHES ──────────────────────────────
belv = lt.create('geometryCOMP', 'escher_belvedere')
belv.nodeX = 600; belv.nodeY = -800
belv.comment = 'Belvedere-style arches — pillars that simultaneously support upper and lower floors'

# Upper pillars (thin)
for i in range(4):
    px = i * 2.5 - 3.75
    pillar = belv.create('tubeSOP', f'upper_pillar_{i}')
    pillar.nodeX = i * 200; pillar.nodeY = 0
    try: pillar.par.radius = (0.15, 0.15)
    except: pass
    try: pillar.par.height = 4.0
    except: pass
    
    p_tx = belv.create('transformSOP', f'upper_pillar_tx_{i}')
    p_tx.nodeX = i * 200 + 100; p_tx.nodeY = 0
    try: p_tx.par.t = (px, 1.0, 0)
    except: pass
    p_tx.inputConnectors[0].connect(pillar)

# Lower pillars (thick, offset — impossible structural support)
for i in range(4):
    px = i * 2.5 - 3.75 + 1.25  # offset from upper
    pillar = belv.create('tubeSOP', f'lower_pillar_{i}')
    pillar.nodeX = i * 200; pillar.nodeY = -200
    try: pillar.par.radius = (0.25, 0.25)
    except: pass
    try: pillar.par.height = 6.0
    except: pass
    
    p_tx = belv.create('transformSOP', f'lower_pillar_tx_{i}')
    p_tx.nodeX = i * 200 + 100; p_tx.nodeY = -200
    try: p_tx.par.t = (px, -1.0, 0)
    except: pass
    p_tx.inputConnectors[0].connect(pillar)

# Floor slabs
for floor_idx, height in enumerate([3.0, -2.0]):
    slab = belv.create('boxSOP', f'floor_{floor_idx}')
    slab.nodeX = 1000; slab.nodeY = -floor_idx * 200
    try: slab.par.size = (10, 0.2, 3)
    except: pass
    
    s_tx = belv.create('transformSOP', f'floor_tx_{floor_idx}')
    s_tx.nodeX = 1200; s_tx.nodeY = -floor_idx * 200
    try: s_tx.par.t = (0, height, 0)
    except: pass
    s_tx.inputConnectors[0].connect(slab)

belv.render = True; belv.display = True

# ── SUMMARY ─────────────────────────────────────────────────────
kids = [c.name for c in lt.findChildren(name='escher*')]
print('ESCHER_DONE:' + str(len(kids)) + ':' + ','.join(kids))
for k in kids:
    geo = lt.op(k)
    if geo:
        inner = len(geo.findChildren())
        print(f'  {k}: {inner} SOPs')
