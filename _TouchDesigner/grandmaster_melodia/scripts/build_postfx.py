# Build Nikki Post-FX Chain in /project1/postfx
# Executed via Envoy MCP execute_python

p = op('/project1/postfx')
if p is None:
    p = op('/project1').create('baseCOMP', 'postfx')

# Destroy any existing children for clean rebuild
for child in list(p.findChildren()):
    child.destroy()

# Create operators
thresh = p.create('lumaLevelTOP', 'bloom_threshold')
thresh.nodeX = 0; thresh.nodeY = 0
thresh.par.threshold = 0.75

b5 = p.create('blurTOP', 'bloom_blur_5')
b5.nodeX = 250; b5.nodeY = 0
b5.par.filtertype = 'gaussian'
b5.par.filterpixels = 5
b5.inputConnectors[0].connect(thresh)

b15 = p.create('blurTOP', 'bloom_blur_15')
b15.nodeX = 250; b15.nodeY = -120
b15.par.filtertype = 'gaussian'
b15.par.filterpixels = 15
b15.inputConnectors[0].connect(thresh)

b30 = p.create('blurTOP', 'bloom_blur_30')
b30.nodeX = 250; b30.nodeY = -240
b30.par.filtertype = 'gaussian'
b30.par.filterpixels = 30
b30.inputConnectors[0].connect(thresh)

comp = p.create('compositeTOP', 'bloom_composite')
comp.nodeX = 500; comp.nodeY = 0
comp.inputConnectors[0].connect(b5)
comp.inputConnectors[1].connect(b15)
comp.inputConnectors[2].connect(b30)

lut = p.create('rampTOP', 'nikki_lut')
lut.nodeX = 0; lut.nodeY = -360

vig = p.create('rampTOP', 'vignette')
vig.nodeX = 250; vig.nodeY = -360
vig.par.type = 'radial'

vig_over = p.create('overTOP', 'vignette_over')
vig_over.nodeX = 500; vig_over.nodeY = -240

out = p.create('nullTOP', 'postfx_out')
out.nodeX = 750; out.nodeY = 0

children = [c.name for c in p.findChildren()]
print('POSTFX_OK:' + str(len(children)) + ':' + ','.join(children))
