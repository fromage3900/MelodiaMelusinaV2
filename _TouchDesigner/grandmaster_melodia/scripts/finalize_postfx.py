p = op('/project1/postfx')

# Clean up numbered copies
for n in ['bloom_threshold1','bloom_threshold2','bloom_threshold3','bloom_threshold4','bloom_threshold5']:
    o = p.op(n)
    if o is not None: o.destroy()

# Recreate threshold with levelTOP
t = p.op('bloom_threshold')
if t is None:
    t = p.create('levelTOP', 'bloom_threshold')
t.nodeX = 0; t.nodeY = 0
try: t.par.blacklevel = 0.0
except: pass
try: t.par.brightness = 0.5
except: pass

# Wire bloom chain
t_path = t
b5 = p.op('bloom_blur_5')
b15 = p.op('bloom_blur_15')
b30 = p.op('bloom_blur_30')
comp = p.op('bloom_composite')

b5.inputConnectors[0].connect(t)
b15.inputConnectors[0].connect(t)
b30.inputConnectors[0].connect(t)
comp.inputConnectors[0].connect(b5)
comp.inputConnectors[1].connect(b15)
comp.inputConnectors[2].connect(b30)

ch = [c.name for c in p.findChildren()]
print('POSTFX_DONE:' + str(len(ch)) + ':' + ','.join(sorted(ch)))
