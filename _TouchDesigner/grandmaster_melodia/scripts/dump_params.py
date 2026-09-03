b = op('/project1/postfx/bloom_blur_5')
# Try setting filter size - the actual param name
for p in ['filterpixels','filtersize','filterradius','samples','passes','size1','size2','scale']:
    try: b.par.__setattr__(p, 5)
    except: pass

# Get ALL parameter names from the operator
all_pars = [p.name for p in b.customPars] + [p.name for p in b.builtinPars]
ta = op('/project1').create('tableDAT', 'blur_params')
ta.clear()
ta.appendRow(['name','value','label'])
for pn in sorted(all_pars):
    try:
        v = b.par[pn].eval()
        lbl = b.par[pn].label
        ta.appendRow([str(pn), str(v), str(lbl)])
    except: pass
print('PARAMS_SAVED:' + str(ta.numRows))
