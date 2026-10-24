"""Sonifold live audio->LB-mode bridge, shared core (no hou dependency).

Used by:
  - sonifold_live_sop.py  (Houdini Python SOP / HDA python module)
  - standalone tests      (hython or plain python)

Pipeline: WAV or live CHOP samples -> rFFT window -> Sonifold spectral
mapping (direct|mel|energy|freqmatch) -> per-mode coefficients -> per-vertex
amplitude = sum_k coef_k * eigenvector_k. Amplitudes are returned on the
eigen mesh's vertex order; the hou adapter position-matches them onto
whatever geometry the SOP cooks, so one eigen precompute can drive any
decorated variant of the same shape.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

SONIFOLD_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------- caches ----
_NPZ_CACHE: dict = {}
_WAV_CACHE: dict = {}


def load_eigen(npz_path: str) -> dict:
    key = (npz_path, os.path.getmtime(npz_path))
    if _NPZ_CACHE.get("key") != key:
        d = np.load(npz_path)
        evecs = d["eigenvectors"]
        evals = d["eigenvalues"]
        if evecs.shape[0] != len(evals):        # tolerate either orientation
            evecs = evecs.T
        _NPZ_CACHE.clear()
        _NPZ_CACHE["key"] = key
        _NPZ_CACHE["data"] = {
            "eigenvalues": np.asarray(evals, dtype=np.float64),
            "eigenvectors": np.asarray(evecs, dtype=np.float64),
            "vertices": np.asarray(d["vertices"], dtype=np.float64),
        }
    return _NPZ_CACHE["data"]


def load_wav(wav_path: str):
    """-> (samples float64 mono, sample_rate). Uses scipy, falls back to stdlib wave."""
    key = (wav_path, os.path.getmtime(wav_path))
    if _WAV_CACHE.get("key") == key:
        return _WAV_CACHE["data"]
    try:
        from scipy.io import wavfile
        sr, data = wavfile.read(wav_path)
    except ImportError:
        import wave
        with wave.open(wav_path, "rb") as w:
            sr = w.getframerate()
            raw = w.readframes(w.getnframes())
            width = w.getsampwidth()
            ch = w.getnchannels()
        dt = {1: np.int8, 2: np.int16, 4: np.int32}[width]
        data = np.frombuffer(raw, dtype=dt).reshape(-1, ch)
    data = np.asarray(data, dtype=np.float64)
    if data.ndim > 1:
        data = data.mean(axis=1)
    peak = np.max(np.abs(data)) or 1.0
    data = data / peak
    _WAV_CACHE.clear()
    _WAV_CACHE["key"] = key
    _WAV_CACHE["data"] = (data, int(sr))
    return _WAV_CACHE["data"]


# ------------------------------------------------------------- mapping ------
def fft_magnitudes(samples: np.ndarray, sr: int, t: float, n_fft: int = 2048,
                   hop_ref: int = 1024) -> np.ndarray:
    """1024-bin rFFT magnitude window centred on time t (seconds)."""
    center = int(t * sr)
    lo = center - n_fft // 2
    hi = center + n_fft // 2
    win = np.zeros(n_fft)
    src_lo, src_hi = max(lo, 0), min(hi, len(samples))
    win[src_lo - lo: src_hi - lo] = samples[src_lo:src_hi]
    if np.max(np.abs(win)) < 1e-12:
        return np.zeros(hop_ref)
    win = win * np.hanning(n_fft)
    mags = np.abs(np.fft.rfft(win, n=n_fft))[:hop_ref]
    return mags


def _mel_band_edges(n: int, n_bins: int) -> np.ndarray:
    high_mel = 2595.0 * np.log10(1.0 + (n_bins - 1) / 700.0)
    mel_pts = np.linspace(0.0, high_mel, n + 1)
    freq_pts = 700.0 * (10.0 ** (mel_pts / 2595.0) - 1.0)
    edges = np.clip(freq_pts / (n_bins - 1) * (n_bins - 1), 0, n_bins - 1)
    edges[-1] = n_bins
    return edges


def map_fft_to_coefficients(mags: np.ndarray, eigenvalues: np.ndarray,
                            strategy: str = "freqmatch", sample_rate: int = 44100,
                            n_fft: int = 2048) -> np.ndarray:
    """Sonifold spectral mapping (mirrors mapping/spectral_mapping.py)."""
    n_bins = 1024
    m = np.asarray(mags, dtype=np.float64).ravel()
    m = np.pad(m, (0, max(0, n_bins - len(m))))[:n_bins]
    n = len(eigenvalues)
    if strategy == "freqmatch":
        lam = np.sqrt(np.maximum(eigenvalues, 1e-20))
        lo, hi = float(lam.min()), float(lam.max())
        if hi <= lo:
            strategy = "direct"
        else:
            f_min, f_max = 50.0, sample_rate / 2.0
            target = np.exp(np.log(f_min) + (np.log(lam) - np.log(lo))
                            * (np.log(f_max) - np.log(f_min)) / (np.log(hi) - np.log(lo)))
            freqs = np.fft.rfftfreq(n_fft, 1.0 / sample_rate)[:n_bins]
            idx = np.clip(np.searchsorted(freqs, target), 1, n_bins - 1)
            dl = np.abs(np.log(freqs[idx - 1] + 1e-20) - np.log(target))
            dr = np.abs(np.log(freqs[idx] + 1e-20) - np.log(target))
            idx = np.where(dl < dr, idx - 1, idx)
            coef = m[idx]
            nrm = np.linalg.norm(coef)
            return coef / nrm if nrm > 1e-20 else coef
    if strategy in ("mel", "energy"):
        edges = _mel_band_edges(n, n_bins)
        coef = np.zeros(n)
        for i in range(n):
            a, b = int(edges[i]), min(int(edges[i + 1]), n_bins)
            coef[i] = (m[a:b] ** 2).sum() if strategy == "energy" and b > a else (m[a:b].mean() if b > a else 0.0)
    else:  # direct
        groups = np.array_split(m, n)
        coef = np.array([g.mean() for g in groups], dtype=np.float64)
    nrm = np.linalg.norm(coef)
    return coef / nrm if nrm > 1e-20 else coef


# -------------------------------------------------------------- driver ------
def sonifold_amp(npz_path: str, wav_path: str, t: float,
                 nmodes: int = 24, modeoffset: int = 1,
                 strategy: str = "freqmatch", n_fft: int = 2048,
                 gain: float = 1.0) -> np.ndarray:
    """Per-vertex amplitude on the eigen mesh's vertex order, at time t (s)."""
    eig = load_eigen(npz_path)
    samples, sr = load_wav(wav_path)
    evals = eig["eigenvalues"][modeoffset: modeoffset + nmodes]
    evecs = eig["eigenvectors"][modeoffset: modeoffset + nmodes]
    mags = fft_magnitudes(samples, sr, t, n_fft=n_fft)
    coef = map_fft_to_coefficients(mags, evals, strategy=strategy,
                                   sample_rate=sr, n_fft=n_fft)
    return gain * (coef @ evecs)


def position_match(src_verts: np.ndarray, dst_verts: np.ndarray) -> np.ndarray:
    """Index map: for each dst vertex, nearest src vertex. KDTree if scipy."""
    try:
        from scipy.spatial import cKDTree
        _, idx = cKDTree(src_verts).query(dst_verts)
        return idx
    except ImportError:
        idx = np.empty(len(dst_verts), dtype=np.int64)
        for i in range(0, len(dst_verts), 512):
            chunk = dst_verts[i: i + 512]
            d2 = ((chunk[:, None, :] - src_verts[None, :, :]) ** 2).sum(-1)
            idx[i: i + 512] = d2.argmin(axis=1)
        return idx


def live_samples_from_chop(chop_path: str, n_fft: int = 2048):
    """(hou-only) pull the tail of a CHOP channel as a live sample window.

    Returns (samples, sample_rate) where samples holds the most recent
    n_fft samples of the channel (zero-padded if the CHOP is shorter).
    """
    import hou  # noqa
    ch = hou.chopNode(chop_path)
    if ch is None:
        raise ValueError(f"CHOP not found: {chop_path}")
    chan = ch.chan(0)
    try:
        arr = chan.numpyArray()          # full cooked channel
        sr = int(round(1.0 / ch.sampleRate()))
    except AttributeError:
        raise RuntimeError("live CHOP needs Houdini with CHOP_Channel.numpyArray()")
    if arr is None or len(arr) == 0:
        raise RuntimeError(f"CHOP {chop_path} has no samples - cook it first")
    return np.asarray(arr, dtype=np.float64)[-n_fft:], sr
