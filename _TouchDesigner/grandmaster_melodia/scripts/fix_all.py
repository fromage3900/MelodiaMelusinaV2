"""Final fix: kill all stray toruses + ramp keys + verify audio wiring."""
root = op('/project1')
fixed = 0

# 1. Kill auto-created torus1 in ALL geometryCOMPs across the project
for comp_name in ['procedural_tower','instanced_city','my_playground',
                   'escher_penrose_stairs','escher_spiral_staircase',
                   'escher_fractal_tower','escher_tessellation','escher_belvedere']:
    torus = op('/project1/learn_td/' + comp_name + '/torus1')
    if torus is not None and torus.valid:
        torus.destroy()
        fixed += 1
        print('killed torus in ' + comp_name)

# 2. Kill ramp key DATs (auto-created by ramp TOP)
for sn in ['vignette_keys','nikki_lut_keys']:
    k = op('/project1/postfx/' + sn)
    if k is not None and k.valid:
        k.destroy()
        fixed += 1
        print('killed ' + sn)

# 3. Verify audio engine exists — list children
audio = root.op('audio')
if audio:
    ch = [c.name for c in audio.findChildren()]
    print('AUDIO children: ' + str(len(ch)) + ' — ' + ','.join(ch))
else:
    print('AUDIO: container missing!')

# 4. Verify postfx
postfx = root.op('postfx')
if postfx:
    ch = [c.name for c in postfx.findChildren()]
    print('POSTFX children: ' + str(len(ch)) + ' — ' + ','.join(sorted(ch)))

# 5. Verify learn_td
lt = root.op('learn_td')
if lt:
    ch = [c.name for c in lt.findChildren()]
    print('LEARN_TD: ' + str(len(ch)) + ' containers')
    for cname in ch:
        c = lt.op(cname)
        inner = len(c.findChildren()) if hasattr(c, 'findChildren') else 0
        has_torus = c.op('torus1') is not None if hasattr(c, 'op') else False
        torus_note = ' (HAS TORUS!)' if has_torus else ''
        print('  ' + cname + ': ' + str(inner) + ' SOPs' + torus_note)

print('')
print('FIXED: ' + str(fixed) + ' issues')
print('VERIFY: 0 errors expected -> check get_op_errors')
