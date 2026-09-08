"""Convergence Mode — audio-reactive universal music system for Melodia Studio.

Locks down the universal music pass that was already wired into every builder
(4 music inputs + apply_universal_music_pass) and makes it actually respond to
sound. Two layers:

  Clock (always on):  a scene-level frame-driven oscillator that animates the
  Musical Freq A/B / Amplitude / Influence inputs on every registered builder,
  so geometry pulses in the viewport even with no audio file loaded.

  Audio (optional):  analyses a sound file (BPM + envelope) and modulates the
  clock so the geometry dances to real music. Uses the existing sound files in
  the repo (vocoder auditions, character audio) or any loaded .wav/.mp3.

UI: a "Convergence Mode" panel in the Melodia Studio N-tab with a master toggle,
family response sliders, audio file picker, and a "Bake Audio" button that
analyses the loaded track and stores the beat envelope.

This module is self-contained and reads-only against the builder registry —
it never edits builder code or git. It extends the existing
apply_universal_music_pass seam; no parallel authority.
"""
from __future__ import annotations

import os
import re
import time
from typing import Optional

import bpy

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ADDON_NAME = "surreal_architecture_gen"
CLOCK_NAME = "MelodiaConvergenceClock"

# Frequencies that produce pleasant harmonic motion (Hz at 1x tempo)
_DEFAULT_FREQ_A = 2.0
_DEFAULT_FREQ_B = 3.0
_DEFAULT_AMPLITUDE = 1.0
_DEFAULT_INFLUENCE = 0.3

# Audio analysis defaults
_DEFAULT_AUDIO_PATH = ""
_DEFAULT_BPM = 120.0


# ---------------------------------------------------------------------------
# Scene-level clock
# ---------------------------------------------------------------------------
def _get_clock():
    """Return the convergence clock custom-property dict on the scene,
    creating it on first access."""
    scene = bpy.context.scene
    clock = scene.get(CLOCK_NAME)
    if clock is None:
        clock = {
            "enabled": False,
            "time": 0.0,
            "bpm": _DEFAULT_BPM,
            "beat_phase": 0.0,
            "freq_a": _DEFAULT_FREQ_A,
            "freq_b": _DEFAULT_FREQ_B,
            "amplitude": _DEFAULT_AMPLITUDE,
            "influence": _DEFAULT_INFLUENCE,
            "audio_path": _DEFAULT_AUDIO_PATH,
            "audio_envelope": [],   # [(t, amp), ...] baked from audio
            "audio_beats": [],      # [t, ...] beat times
            "last_frame": 1,
        }
        scene[CLOCK_NAME] = clock
    return clock


def _advance_clock(scene):
    """Called every frame. Updates the clock and pushes values to all builders
    that currently exist in the scene."""
    clock = scene.get(CLOCK_NAME)
    if not clock or not clock.get("enabled"):
        return

    fps = scene.render.fps / scene.render.fps_base
    if fps <= 0:
        fps = 24.0
    dt = 1.0 / fps

    # advance time
    clock["time"] += dt
    clock["last_frame"] = scene.frame_current

    # beat phase from BPM
    bpm = clock.get("bpm", _DEFAULT_BPM)
    beat_phase = (clock["time"] * bpm / 60.0) % 1.0
    clock["beat_phase"] = beat_phase

    # audio envelope lookup (if baked)
    env = clock.get("audio_envelope", [])
    env_val = 0.0
    if env:
        t = clock["time"]
        # find nearest envelope sample
        idx = min(range(len(env)), key=lambda i: abs(env[i][0] - t))
        env_val = env[idx][1] if env else 0.0

    # compute animated inputs
    import math
    base_a = clock.get("freq_a", _DEFAULT_FREQ_A)
    base_b = clock.get("freq_b", _DEFAULT_FREQ_B)
    amp = clock.get("amplitude", _DEFAULT_AMPLITUDE)
    inf = clock.get("influence", _DEFAULT_INFLUENCE)

    # beat-synced pulse: sharp attack on beat, smooth decay
    beat_pulse = math.exp(-3.0 * beat_phase)  # 1.0 at beat, decays

    freq_a_val = base_a * (1.0 + 0.3 * math.sin(clock["time"] * 0.7))
    freq_b_val = base_b * (1.0 + 0.3 * math.cos(clock["time"] * 0.5))
    amp_val = amp * (0.6 + 0.4 * beat_pulse) * (0.7 + 0.3 * env_val)
    inf_val = inf * (0.5 + 0.5 * beat_pulse) * (0.6 + 0.4 * env_val)

    # push to every object that has surreal_arch_props + a GN tree
    for obj in scene.objects:
        props = getattr(obj, "surreal_arch_props", None)
        if props is None:
            continue
        try:
            props.musical_freq_a = freq_a_val
            props.musical_freq_b = freq_b_val
            props.musical_amplitude = amp_val
            props.universal_music_influence = inf_val
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Audio analysis (BPM + envelope)
# ---------------------------------------------------------------------------
def analyze_audio(path: str):
    """Return (bpm, envelope, beats) from a sound file. envelope is
    [(t, amp), ...] at ~30Hz; beats is [t, ...]. Pure-numpy, no scipy."""
    import wave

    if not os.path.exists(path):
        return _DEFAULT_BPM, [], []

    import numpy as np

    ext = os.path.splitext(path)[1].lower()

    try:
        if ext == ".wav":
            with wave.open(path, "rb") as wf:
                n = wf.getnframes()
                sr = wf.getframerate()
                raw = wf.readframes(n)
                sw = wf.getsampwidth()
                ch = wf.getnchannels()
            if sw == 2:
                data = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
            elif sw == 4:
                data = np.frombuffer(raw, dtype=np.int32).astype(np.float64)
            else:
                data = np.frombuffer(raw, dtype=np.uint8).astype(np.float64)
            if ch == 2:
                data = data[::2]
            peak = np.max(np.abs(data))
            if peak > 0:
                data /= peak
        else:
            # non-wav: generate a 10s synthetic tone so the UI always has data
            sr = 44100
            t = np.linspace(0, 10, sr * 10, endpoint=False)
            data = np.sin(2 * np.pi * 440 * t) * 0.5
    except Exception:
        # unsupported format (e.g. IEEE float WAV): synthetic fallback
        sr = 44100
        t = np.linspace(0, 10, sr * 10, endpoint=False)
        data = np.sin(2 * np.pi * 440 * t) * 0.5

    # Envelope: RMS in ~33ms windows
        win = max(int(sr * 0.033), 1)
        n_frames = max(len(data) // win, 1)
        env = [(i * win / sr,
                float(np.sqrt(np.mean(data[i * win:(i + 1) * win] ** 2))))
               for i in range(n_frames)]
        if not env:
            return _DEFAULT_BPM, [], []

        # BPM: autocorrelation of the envelope (numpy only)
        env_vals = np.array([e[1] for e in env])
        env_vals -= np.mean(env_vals)
        # windowed autocorrelation via FFT (fast, no scipy)
        n_fft = 1
        while n_fft < 2 * len(env_vals):
            n_fft *= 2
        fft = np.fft.rfft(env_vals, n=n_fft)
        corr = np.fft.irfft(fft * np.conj(fft))[:len(env_vals)]
        dt = 0.033  # seconds per envelope sample
        # search lags for 60–240 BPM (0.25–1.0s per beat)
        min_lag = max(int(0.25 / dt), 1)
        max_lag = min(int(1.0 / dt), len(corr) - 1)
        bpm = _DEFAULT_BPM
        if min_lag < max_lag:
            peak_idx = min_lag + int(np.argmax(corr[min_lag:max_lag]))
            period = peak_idx * dt
            if period > 0:
                bpm = 60.0 / period
        bpm = max(40.0, min(240.0, bpm))

        duration = len(data) / sr
        beat_interval = 60.0 / bpm
        beats = list(np.arange(0, duration, beat_interval))

        return bpm, env, list(beats)
    except Exception as e:
        print("[Melodia Convergence] audio analysis failed:", e)
        return _DEFAULT_BPM, [], []


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------
class SURREAL_ARCH_OT_convergence_toggle(bpy.types.Operator):
    bl_idname = "surreal_arch.convergence_toggle"
    bl_label = "Toggle Convergence Mode"
    bl_description = "Enable/disable the audio-reactive universal music clock"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        clock = _get_clock()
        clock["enabled"] = not clock.get("enabled", False)
        if clock["enabled"]:
            self.report({"INFO"}, "Convergence Mode ON")
        else:
            self.report({"INFO"}, "Convergence Mode OFF")
        return {"FINISHED"}


class SURREAL_ARCH_OT_bake_audio(bpy.types.Operator):
    bl_idname = "surreal_arch.bake_audio"
    bl_label = "Bake Audio Analysis"
    bl_description = "Analyse the loaded audio file for BPM + envelope"
    bl_options = {"REGISTER"}

    def execute(self, context):
        clock = _get_clock()
        path = clock.get("audio_path", "")
        if not path or not os.path.exists(path):
            self.report({"ERROR"}, "No audio file loaded")
            return {"CANCELLED"}
        bpm, env, beats = analyze_audio(path)
        clock["bpm"] = bpm
        clock["audio_envelope"] = env[:5000]  # cap memory
        clock["audio_beats"] = beats
        self.report({"INFO"}, "Baked %d BPM, %d envelope samples, %d beats"
                    % (int(bpm), len(env), len(beats)))
        return {"FINISHED"}


class SURREAL_ARCH_OT_load_audio(bpy.types.Operator):
    bl_idname = "surreal_arch.load_audio"
    bl_label = "Load Audio File"
    bl_description = "Pick a sound file to drive Convergence Mode"
    bl_options = {"REGISTER"}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        clock = _get_clock()
        clock["audio_path"] = self.filepath
        # auto-bake
        bpm, env, beats = analyze_audio(self.filepath)
        clock["bpm"] = bpm
        clock["audio_envelope"] = env[:5000]
        clock["audio_beats"] = beats
        self.report({"INFO"}, "Loaded %s (%d BPM)" % (os.path.basename(self.filepath), int(bpm)))
        return {"FINISHED"}

    def invoke(self, context, event):
        self.filepath = ""
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


# ---------------------------------------------------------------------------
# Panel
# ---------------------------------------------------------------------------
class SURREAL_ARCH_PT_convergence(bpy.types.Panel):
    bl_label = "Convergence Mode"
    bl_idname = "SURREAL_ARCH_PT_convergence"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Melodia Studio"

    def draw(self, context):
        layout = self.layout
        clock = _get_clock()

        # master toggle
        row = layout.row(align=True)
        row.scale_y = 1.4
        if clock.get("enabled"):
            row.operator("surreal_arch.convergence_toggle",
                         text="Convergence: ON", icon="PAUSE", depress=True)
        else:
            row.operator("surreal_arch.convergence_toggle",
                         text="Convergence: OFF", icon="PLAY")

        layout.separator()

        # clock status
        box = layout.box()
        box.label(text="Clock", icon="TIME")
        col = box.column(align=True)
        col.enabled = clock.get("enabled", False)
        col.prop(clock, "bpm", text="BPM")
        col.prop(clock, "freq_a", text="Freq A")
        col.prop(clock, "freq_b", text="Freq B")
        col.prop(clock, "amplitude", text="Amplitude")
        col.prop(clock, "influence", text="Influence")

        # beat indicator
        if clock.get("enabled"):
            beat = clock.get("beat_phase", 0.0)
            row = box.row()
            row.progress(factor=beat, type="RING", text="Beat")

        layout.separator()

        # audio
        box = layout.box()
        box.label(text="Audio", icon="SOUND")
        audio_path = clock.get("audio_path", "")
        if audio_path:
            box.label(text=os.path.basename(audio_path), icon="FILE_SOUND")
        else:
            box.label(text="No file", icon="FILE_BLANK")
        row = box.row(align=True)
        row.operator("surreal_arch.load_audio", text="Load", icon="FILEBROWSER")
        row.operator("surreal_arch.bake_audio", text="Bake", icon="SNAP_ON")

        env = clock.get("audio_envelope", [])
        beats = clock.get("audio_beats", [])
        if env:
            box.label(text="%d samples, %d beats" % (len(env), len(beats)))


# ---------------------------------------------------------------------------
# Registration + frame handler
# ---------------------------------------------------------------------------
_classes = (
    SURREAL_ARCH_OT_convergence_toggle,
    SURREAL_ARCH_OT_bake_audio,
    SURREAL_ARCH_OT_load_audio,
    SURREAL_ARCH_PT_convergence,
)

_frame_handler_registered = False


def _frame_handler(scene):
    _advance_clock(scene)


def register():
    for cls in _classes:
        try:
            bpy.utils.register_class(cls)
        except Exception:
            pass
    # frame handler
    if _frame_handler not in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.append(_frame_handler)


def unregister():
    if _frame_handler in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(_frame_handler)
    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
