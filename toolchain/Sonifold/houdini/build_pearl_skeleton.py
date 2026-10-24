"""build_pearl_skeleton.py -- creates heartgate_pearl_skeleton.hip.

Fully-wired parts: SOP side (gate file + Sonifold live Python SOP with spare
parms), Copernicus side structure. TWO manual GUI steps are marked with
bright null nodes labelled GUI_STEP_1 / GUI_STEP_2:

  GUI_STEP_1: replace the null between sopimport and hsv with the
              geometry-layer -> image-layer conversion (inspect sopimport's
              output layers in the Copernicus editor; likely a
              bake/geometry->layer node such as 'bakegeometrytextures' or
              geotolayer+file combo).
  GUI_STEP_2: optional image filter between hsv and geoattribfromlayer
              (crystalnoise/bubblenoise blend for pearl micro-flake).
"""
import hou

ROOT = r"C:\EnvironmentPortfolio\BS_GodFile\toolchain\Sonifold"
GEO = f"{ROOT}/data/meshes/HeartGate_clean.obj"
NPZ = f"{ROOT}/data/eigen/HeartGate_clean.npz"
WAV = f"{ROOT}/data/audio/heartbeat_gate.wav"

CODE = f"""
import sys, traceback
sys.path.insert(0, r"{ROOT}\\houdini")
try:
    import sonifold_live_sop as sls
    sls.cook()
except Exception:
    traceback.print_exc()
    raise
"""

# ------------------------------------------------------------- SOP side ----
obj = hou.node("/obj")
geo = obj.createNode("geo")
geo.setName("heartgate_geo")
filsop = geo.createNode("file")
filsop.setName("gate_obj")
filsop.parm("file").set(GEO)

pysop = geo.createNode("python")
pysop.setName("sonifold_live")
pysop.setInput(0, filsop)
pysop.parm("python").set(CODE)

def add_str(n, label):
    pysop.addSpareParmTuple(hou.StringParmTemplate(n, label, 1))
def add_int(n, label):
    pysop.addSpareParmTuple(hou.IntParmTemplate(n, label, 1))
def add_flt(n, label):
    pysop.addSpareParmTuple(hou.FloatParmTemplate(n, label, 1))

add_str("eigen_npz", "Eigen NPZ"); add_str("audio_file", "Audio File")
add_str("chop_path", "CHOP Path"); add_str("strategy", "Strategy")
add_int("nmodes", "Modes"); add_int("modeoffset", "Mode Offset")
add_flt("gain", "Gain"); add_int("n_fft", "FFT Size")
pysop.parm("eigen_npz").set(NPZ)
pysop.parm("audio_file").set(WAV)
pysop.parm("strategy").set("freqmatch")
pysop.parm("nmodes").set(24); pysop.parm("modeoffset").set(1)
pysop.parm("n_fft").set(2048)

uvsop = geo.createNode("uvunwrap")   # placeholder: replace/adjust for the real HDA
uvsop.setName("UV_PLACEHOLDER")
display = geo.createNode("null")
display.setName("OUT_GATE")
display.setInput(0, pysop)
display.setDisplayFlag(True)
pysop.setDisplayFlag(False)

# --------------------------------------------------------- Copernicus side -
copnet = obj.createNode("copnet")
copnet.setName("heartgate_pearl")

imp = copnet.createNode("sopimport")
imp.setName("IMPORT_gate")
imp.parm("soppath").set(filsop.path())

gui1 = copnet.createNode("null")
gui1.setName("GUI_STEP_1_convert_geometry_layer_to_image")
gui1.setInput(0, imp)
gui1.setColor(hou.Color(1.0, 0.4, 0.1))

hue = copnet.createNode("hsv")
hue.setName("PEARL_hueshift_160")
hue.setInput(0, gui1)
hue.parm("hueshift").set(160.0)

gui2 = copnet.createNode("null")
gui2.setName("GUI_STEP_2_optional_crystalnoise_microflake")
gui2.setInput(0, hue)
gui2.setColor(hou.Color(1.0, 0.4, 0.1))

sampler = copnet.createNode("geoattribfromlayer")
sampler.setName("SAMPLE_back_to_Cd")
sampler.setInput(0, gui2)
sampler.parm("numattribs").set(1)
if sampler.parm("attrib1"):
    sampler.parm("attrib1").set("Cd")

print("built skeleton. Manual GUI steps: GUI_STEP_1 (layer conversion), GUI_STEP_2 (optional filter)")
hou.hipFile.save(f"{ROOT}/houdini/heartgate_pearl_skeleton.hip")
print("saved houdini/heartgate_pearl_skeleton.hip")
