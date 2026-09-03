torus_killed = 0
for cpath in [
    '/project1/learn_td/procedural_tower/torus1',
    '/project1/learn_td/instanced_city/torus1',
    '/project1/learn_td/my_playground/torus1',
    '/project1/learn_td/escher_penrose_stairs/torus1',
    '/project1/learn_td/escher_spiral_staircase/torus1',
    '/project1/learn_td/escher_fractal_tower/torus1',
    '/project1/learn_td/escher_tessellation/torus1',
    '/project1/learn_td/escher_belvedere/torus1',
    '/project1/postfx/vignette_keys',
    '/project1/postfx/nikki_lut_keys',
]:
    o = op(cpath)
    if o is not None:
        try:
            o.destroy()
            torus_killed += 1
        except:
            pass

print('CLEANED: ' + str(torus_killed))
