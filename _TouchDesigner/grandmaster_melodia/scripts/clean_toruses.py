lt = op('/project1/learn_td')
kids = lt.findChildren()
print('TOTAL kids in learn_td: ' + str(len(kids)))

torus_killed = 0
for c in kids:
    if c.isCOMP:
        inner = c.findChildren()
        print('  ' + c.name + ': ' + str(len(inner)) + ' SOPs')
        t = c.op('torus1')
        if t is not None:
            t.destroy()
            torus_killed += 1

print('Toruses killed: ' + str(torus_killed))

# Also verify Escher pieces
for c in kids:
    if 'escher' in c.name.lower():
        sop_count = len(c.findChildren())
        print('ESCHER: ' + c.name + ' = ' + str(sop_count) + ' SOPs, render=' + str(c.render))
