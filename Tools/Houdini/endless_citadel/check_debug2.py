import hou
hip = r'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\endless_citadel\citadel_debug.hip'
hou.hipFile.load(hip)
# check lights
for name in ("cit_key", "cit_rim", "cit_bio"):
    lg = hou.node("/obj/" + name)
    lt = lg.parm("light_type").eval()
    print(f"{name}: light_type eval={lt}")
    print(f"  intensity={lg.parm('light_intensity').eval()}")
    print(f"  enabled={lg.parm('light_enable').eval()}")
    print(f"  color={lg.parm('light_colorr').eval()} {lg.parm('light_colorg').eval()} {lg.parm('light_colorb').eval()}")

# check camera
cam = hou.node("/obj/cit_cam_hero")
print(f"\ncamera pos: {cam.parmTuple('t').eval()}")
print(f"camera rot: {cam.parmTuple('r').eval()}")
# check if it has res override
print(f"cam resx: {cam.parm('resx').eval() if cam.parm('resx') else 'N/A'}")
print(f"cam resy: {cam.parm('resy').eval() if cam.parm('resy') else 'N/A'}")

# check mantra settings from the .hip's /out/citadel_render
out = hou.node("/out")
for n in out.children():
    print(f"\n/out node: {n.name()}")
    if "citadel" in n.name():
        print(f"  vm_picture: {n.parm('vm_picture').eval()}")
        print(f"  override_camerares: {n.parm('override_camerares').eval()}")
        print(f"  res_overridex: {n.parm('res_overridex').eval()}")
        print(f"  res_overridey: {n.parm('res_overridey').eval()}")
        print(f"  vm_samplesx: {n.parm('vm_samplesx').eval()}")
        print(f"  vm_samplesy: {n.parm('vm_samplesy').eval()}")