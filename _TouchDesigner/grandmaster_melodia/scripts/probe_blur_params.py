b = op('/project1/postfx/bloom_blur_5')
results = []
for p in ['filterpixels','filtersize','filterradius','kernel','size','radius','filter','filterwidth']:
    try:
        setattr(b.par, p, 5)
        results.append('OK:' + p)
    except Exception as e:
        results.append('FAIL:' + p + ':' + str(e)[:40])
print('PROBE:' + '|'.join(results))
