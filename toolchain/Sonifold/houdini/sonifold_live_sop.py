"""sonifold_live_sop.py - Houdini Python SOP wrapper for sonifold_live.

Use inside a Python SOP (or as the Python module of an HDA's Python SOP).
Add spare parms on the node (or promote on the HDA) named exactly:

    eigen_npz    string   path to Sonifold eigen .npz
    audio_file   string   WAV path (bake/HEU mode); empty + chop_path set = live
    chop_path    string   e.g. /obj/audio/audioin1  (live CHOP mode)
    strategy     string   direct | mel | energy | freqmatch
    nmodes       int      modes used (default 24)
    modeoffset   int      skip lowest modes (default 1 skips the constant mode)
    gain         float    output gain
    n_fft        int      FFT window (default 2048)

cook() reads the current frame time ($F/$FPS), so a frame range IS the bake.
"""
import os
import sys

import hou
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import sonifold_live as sl  # noqa: E402

_DEFAULTS = {
    "eigen_npz": "",
    "audio_file": "",
    "chop_path": "",
    "strategy": "freqmatch",
    "nmodes": 24,
    "modeoffset": 1,
    "gain": 1.0,
    "n_fft": 2048,
}


def _parm(node, name):
    p = node.parm(name)
    if p is None:
        return _DEFAULTS[name]
    if isinstance(_DEFAULTS[name], float):
        return p.eval()
    if isinstance(_DEFAULTS[name], int):
        return int(p.eval())
    return p.evalAsString()


def cook(node=None):
    node = node or hou.pwd()
    geo = node.geometry()
    opts = {k: _parm(node, k) for k in _DEFAULTS}

    eig = sl.load_eigen(opts["eigen_npz"])
    src_v = eig["vertices"]

    t = hou.frame() / hou.fps() if hasattr(hou, "frame") else float(hou.expandString("$F")) / hou.fps()

    if opts["chop_path"]:
        samples, sr = sl.live_samples_from_chop(opts["chop_path"], n_fft=opts["n_fft"])
        evals = eig["eigenvalues"][opts["modeoffset"]: opts["modeoffset"] + opts["nmodes"]]
        evecs = eig["eigenvectors"][opts["modeoffset"]: opts["modeoffset"] + opts["nmodes"]]
        mags = sl.fft_magnitudes(np_pad(samples, opts["n_fft"]), sr, t=(opts["n_fft"] / 2) / sr,
                                 n_fft=opts["n_fft"])
        coef = sl.map_fft_to_coefficients(mags, evals, strategy=opts["strategy"],
                                          sample_rate=sr, n_fft=opts["n_fft"])
        amp = opts["gain"] * (coef @ evecs)
    else:
        amp = sl.sonifold_amp(opts["eigen_npz"], opts["audio_file"], t,
                              nmodes=opts["nmodes"], modeoffset=opts["modeoffset"],
                              strategy=opts["strategy"], n_fft=opts["n_fft"],
                              gain=opts["gain"])

    # position-match onto cooked geometry (any variant of the shape)
    pts = geo.points()
    dst_v = np.array([p.position() for p in pts], dtype=np.float64)
    if len(dst_v) == len(amp):
        amp_dst = amp
    else:
        amp_dst = amp[sl.position_match(src_v, dst_v)]

    attr = geo.findPointAttrib("sonifold_amp")
    if attr is None:
        attr = geo.addAttrib(hou.attribType.Point, "sonifold_amp", 0.0)
    s = np.std(amp_dst) + 1e-12
    a_norm = np.clip(amp_dst / (2.0 * s), -1.0, 1.0)
    cd_attr = geo.findPointAttrib("Cd")
    if cd_attr is None:
        cd_attr = geo.addAttrib(hou.attribType.Point, "Cd", (1.0, 1.0, 1.0))
    for i, p in enumerate(pts):
        p.setAttribValue(attr, float(amp_dst[i]))
        p.setAttribValue(cd_attr, (0.5 + 0.5 * a_norm[i], 0.15, 0.5 - 0.5 * a_norm[i]))


def np_pad(samples, n_fft):
    import numpy as np
    out = np.zeros(n_fft)
    out[-len(samples):] = samples[-n_fft:] if len(samples) >= n_fft else samples
    return out
