lt = op('/project1/learn_td')
total = 0
for c in lt.findChildren():
    total += 1
    nm = c.name
    ctx = nm + ' type=' + str(c.type)
    try:
        inner = len(c.findChildren()) if hasattr(c, 'findChildren') else 0
        ctx += ' kids=' + str(inner)
    except:
        pass
    print(ctx)
    t = c.op('torus1')
    if t is not None:
        t.destroy()
        print('  killed torus1 in ' + nm)
print('TOTAL: ' + str(total))
