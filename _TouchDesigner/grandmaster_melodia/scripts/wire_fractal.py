ft = op('/project1/learn_td/escher_fractal_tower')
cam = ft.create('cameraCOMP', 'render_cam')
cam.nodeX = 150; cam.nodeY = 200
rtop = ft.create('renderTOP', 'render_out')
rtop.nodeX = 300; rtop.nodeY = 0
rtop.par.camera = cam.path
blm = op('/project1/render/bloom_overlay')
blm.inputConnectors[0].connect(rtop)
od = op('/project1/render/out_display')
od.display = True
print('WIRED: camera->render->bloom->display')
