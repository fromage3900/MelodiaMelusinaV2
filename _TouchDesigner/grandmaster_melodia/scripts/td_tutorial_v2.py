"""TouchDesigner for Game Dev — Live Tutorial (v2).
Uses correct operator type strings for TD 2025.32460.
Run via: exec(open(...).read()) in TD Textport
"""
lt = op('/project1/learn_td')

# Clean slate
for c in list(lt.findChildren()):
    c.destroy()

# ── 1. YOUR FBX IN TD ───────────────────────────────────────
fbx_geo = lt.create('geometryCOMP', 'nikki_sanctuary')
fbx_geo.nodeX = -400; fbx_geo.nodeY = 0
fbx_geo.comment = 'Double-click me to enter 3D view. Your Blender FBX is loading inside.'

file_sop = fbx_geo.create('fileSOP', 'fbx_loader')
file_sop.nodeX = 0; file_sop.nodeY = 0
file_sop.comment = 'Loads any FBX/OBJ/USD — like Blender File > Import'
# Note: set the file path manually once you have the FBX ready
# file_sop.par.file = r"G:\...\nikki_sanctuary.fbx"

print('[1/4] FBX loader created in Geometry COMP')

# ── 2. PROCEDURAL TOWER ──────────────────────────────────────
tower = lt.create('geometryCOMP', 'procedural_tower')
tower.nodeX = 200; tower.nodeY = 0
tower.comment = 'Pure SOP chain: cylinder + noise + cone — no external files'

# Base pillar
tube = tower.create('tubeSOP', 'pillar')
tube.nodeX = 0; tube.nodeY = 0
tube.par.radius = 2.0
tube.par.height = 6.0
tube.par.rows = 8
tube.par.cols = 1

# Organic warp (ruined/weathered look)
noise = tower.create('noiseSOP', 'warp')
noise.nodeX = 250; noise.nodeY = 0
noise.par.amp = 0.15
noise.inputConnectors[0].connect(tube)

# Roof spire
cone = tower.create('tubeSOP', 'spire')
cone.nodeX = 0; cone.nodeY = -200
cone.par.radius = 2.5
cone.par.radius2 = 0.15
cone.par.height = 2.5
cone.par.rows = 16

roof_xform = tower.create('transformSOP', 'roof_pos')
roof_xform.nodeX = 250; roof_xform.nodeY = -200
roof_xform.par.tz = 3.0
roof_xform.inputConnectors[0].connect(cone)

# Merge body + roof
merge = tower.create('mergeSOP', 'full_tower')
merge.nodeX = 500; merge.nodeY = 0
merge.inputConnectors[0].connect(noise)
merge.inputConnectors[1].connect(roof_xform)

# Turn on display
tower.render = True
tower.display = True

print('[2/4] Procedural tower: tube + noise + cone spire. Click the display flag (blue ring) on the mergeSOP to see it.')

# ── 3. INSTANCED CITY ────────────────────────────────────────
city = lt.create('geometryCOMP', 'instanced_city')
city.nodeX = 200; city.nodeY = -400
city.comment = '25 towers in a 5x5 grid — like UE PCG scatter'

# Copy the merge SOP from tower
tower_template = city.copy(merge, 'tower_template')
tower_template.nodeX = 0; tower_template.nodeY = 0

# Grid of placement points
grid = city.create('gridSOP', 'city_grid')
grid.nodeX = 0; grid.nodeY = -200
grid.par.rows = 5
grid.par.cols = 5
grid.par.size = 20.0

# Instance towers on grid points
copy_inst = city.create('copySOP', 'copy_towers')
copy_inst.nodeX = 400; copy_inst.nodeY = 0
copy_inst.inputConnectors[0].connect(tower_template)
copy_inst.inputConnectors[1].connect(grid)
copy_inst.par.dorotate = True

city.render = True
city.display = True

print('[3/4] Instanced city: 25 towers in a grid')

# ── 4. YOUR PLAYGROUND ───────────────────────────────────────
playground = lt.create('geometryCOMP', 'my_playground')
playground.nodeX = 600; playground.nodeY = 0
playground.comment = 'Your sandbox — try creating your own SOPs here!'

# Some starter primitives
box = playground.create('boxSOP', 'starter_box')
box.nodeX = 0; box.nodeY = 0
box.comment = 'Right-click the geometry viewer > Add SOP to build your own chain'

playground.render = True
playground.display = True

print('[4/4] Playground ready')
print('')
print('=' * 55)
print('  TOUCHDESIGNER FOR GAME DEV')
print('')
print('  /learn_td/nikki_sanctuary    — Load your FBX')
print('  /learn_td/procedural_tower   — Tube + Noise + Cone')
print('  /learn_td/instanced_city     — 25 towers grid')
print('  /learn_td/my_playground      — Your sandbox')
print('')
print('  IN TD NOW:')
print('  - Double-click any geometryCOMP to enter 3D SOP network')
print('  - Hit Space to toggle between SOP/3D view')
print('  - Press H to home the camera on your geometry')
print('  - Middle-click a SOP node to see its 3D output')
print('  - Select node, press P for parameters')
print('')
print('  YOUR PIPELINE:')
print('  Blender(SurrealArch) -> FBX -> TD(SOPs) -> OSC -> UE5')
print('=' * 55)
