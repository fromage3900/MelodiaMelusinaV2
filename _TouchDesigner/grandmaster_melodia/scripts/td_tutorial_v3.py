lt = op('/project1/learn_td')

# 1. FBX loader
fbx = lt.create('fbxCOMP', 'nikki_sanctuary')
fbx.nodeX = -400; fbx.nodeY = 0
fbx.comment = 'Double-click to enter. Set FBX file path in parameters.'
print('[1/4] FBX loader')

# 2. Procedural tower
tw = lt.create('geometryCOMP', 'procedural_tower')
tw.nodeX = 200; tw.nodeY = 0
tw.comment = 'Tube -> Noise -> Cone -> Merge tower'

tube = tw.create('tubeSOP', 'pillar'); tube.nodeX = 0; tube.nodeY = 0
noise = tw.create('noiseSOP', 'warp'); noise.nodeX = 250; noise.nodeY = 0
noise.comment = 'Select me, press P, tune amplitude'
noise.inputConnectors[0].connect(tube)
cone = tw.create('tubeSOP', 'spire'); cone.nodeX = 0; cone.nodeY = -200
roof = tw.create('transformSOP', 'roof_pos'); roof.nodeX = 250; roof.nodeY = -200
roof.inputConnectors[0].connect(cone)
merge_tw = tw.create('mergeSOP', 'full_tower'); merge_tw.nodeX = 500; merge_tw.nodeY = 0
merge_tw.inputConnectors[0].connect(noise)
merge_tw.inputConnectors[1].connect(roof)
tw.render = True; tw.display = True
# Delete auto torus
torus = tw.op('torus1')
if torus: torus.destroy()
print('[2/4] Procedural tower: tube + noise + cone')

# 3. Instanced city
ct = lt.create('geometryCOMP', 'instanced_city')
ct.nodeX = 200; ct.nodeY = -400
t_ct = ct.create('tubeSOP', 'tower'); t_ct.nodeX = 0; t_ct.nodeY = 0
g_ct = ct.create('gridSOP', 'city_grid'); g_ct.nodeX = 0; g_ct.nodeY = -200
ci = ct.create('copySOP', 'copy_towers'); ci.nodeX = 400; ci.nodeY = 0
ci.inputConnectors[0].connect(t_ct)
ci.inputConnectors[1].connect(g_ct)
ct.render = True; ct.display = True
torus2 = ct.op('torus1')
if torus2: torus2.destroy()
print('[3/4] Instanced city: 5x5 grid of towers')

# 4. Playground
pg = lt.create('geometryCOMP', 'my_playground')
pg.nodeX = 600; pg.nodeY = 0
pg.comment = 'Your sandbox — right-click to add SOPs'
b_pg = pg.create('boxSOP', 'starter'); b_pg.nodeX = 0; b_pg.nodeY = 0
pg.render = True; pg.display = True
torus3 = pg.op('torus1')
if torus3: torus3.destroy()
print('[4/4] Playground ready')
print('TUTORIAL: 4 geo containers ready in /learn_td')
