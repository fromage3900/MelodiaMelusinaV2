import hou
hip = r'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\endless_citadel\citadel_debug.hip'
hou.hipFile.load(hip)
geo = hou.node('/obj/citadel')
fm = geo.node('citadel_final')
fm.cook()
g = fm.geometry()
# check per-prim shop_materialpath
count_with = 0
count_without = 0
sample_vals = []
for prim in g.prims():
    try:
        val = prim.attribValue('shop_materialpath')
    except Exception:
        val = None
    if val and val != '<none>' and val != '':
        count_with += 1
        if len(sample_vals) < 10:
            sample_vals.append(f'  prim {len(sample_vals)}: {val}')
    else:
        count_without += 1
print(f'prims with shop_materialpath: {count_with}')
print(f'prims without: {count_without}')
for sv in sample_vals:
    print(sv)
# check a specific known prim - the corridor
# find prims with cit_marble or cit_obsidian
marble_count = 0
obsidian_count = 0
for prim in g.prims():
    val = prim.attribValue('shop_materialpath')
    if val:
        if 'marble' in val.lower():
            marble_count += 1
        if 'obsidian' in val.lower():
            obsidian_count += 1
print(f'prims with cit_marble: {marble_count}')
print(f'prims with cit_obsidian: {obsidian_count}')