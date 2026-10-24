"""hython integration test: Python SOP running Sonifold live on the heart gate."""
import sys

import hou
import numpy as np

ROOT = r"C:\EnvironmentPortfolio\BS_GodFile\toolchain\Sonifold"
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

geo = hou.node("/obj").createNode("geo")
filsop = geo.createNode("file")
filsop.parm("file").set(f"{ROOT}/data/meshes/HeartGate_clean.obj")
pysop = geo.createNode("python")
pysop.setInput(0, filsop)

code_parm = next(p.name() for p in pysop.parms() if "python" in p.name().lower())
pysop.parm(code_parm).set(CODE)
print("python sop code parm:", code_parm)

# spare parms the wrapper reads
def add_str(n, label):
    pysop.addSpareParmTuple(hou.StringParmTemplate(n, label, 1))
def add_int(n, label):
    pysop.addSpareParmTuple(hou.IntParmTemplate(n, label, 1))
def add_flt(n, label):
    pysop.addSpareParmTuple(hou.FloatParmTemplate(n, label, 1))

add_str("eigen_npz", "Eigen NPZ"); add_str("audio_file", "Audio File"); add_str("chop_path", "CHOP Path")
add_str("strategy", "Strategy"); add_int("nmodes", "Modes"); add_int("modeoffset", "Mode Offset")
add_flt("gain", "Gain"); add_int("n_fft", "FFT Size")

pysop.parm("eigen_npz").set(f"{ROOT}/data/eigen/HeartGate_clean.npz")
pysop.parm("audio_file").set(f"{ROOT}/data/audio/heartbeat_gate.wav")
pysop.parm("strategy").set("freqmatch")
pysop.parm("nmodes").set(24); pysop.parm("modeoffset").set(1)
pysop.parm("gain").set(1.0); pysop.parm("n_fft").set(2048)

hou.setFps(24)
frames = [1, 12, 18, 24, 30, 36, 48, 60, 72, 84, 96]
snap = {}
for f in frames:
    hou.setFrame(f)
    try:
        pysop.cook(force=True)
    except hou.OperationFailed:
        print("COOK ERROR:", hou.hscript(f"operrors {pysop.path()}")[0])
        import traceback
        # re-run the module cook inline to surface the real traceback
        sys.path.insert(0, f"{ROOT}/houdini")
        import sonifold_live_sop as sls
        sls.cook(node=pysop)
        raise
    g = pysop.geometry()
    a = np.array(g.pointFloatAttribValues("sonifold_amp"))
    snap[f] = a
    print(f"frame {f:3d} t={f/24:5.2f}s  amp min={a.min():+.4f} max={a.max():+.4f} std={a.std():.4f}")

np.savez(f"{ROOT}/data/frames_gate_live.npz", **{f"f{f}": v for f, v in snap.items()},
         faces=np.array(g.primVertices()).astype(object) if False else np.arange(0))
print("TEST PASS - sonifold SOP live in houdini")
