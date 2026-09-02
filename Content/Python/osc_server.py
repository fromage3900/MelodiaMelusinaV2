"""osc_server.py — UE OSC listener using raw UDP sockets.

Receives OSC from TD on port 8000 and routes to:
- Material Parameter Collections (MPCs) via unreal.MaterialEditingLibrary
- Post-process volumes via unreal.find_object
- Niagara parameter control via MPCs

IMPORTANT: Uses raw sockets (NO unreal.OSCManager dependency).
UE 5.8's OSCManager API changed — raw sockets are stable across versions.

Branch: feature/touchdesigner-mcp-integration
Owner: TOA (TouchDesigner Orchestrator Agent)
"""

import socket
import struct
import threading
import time
import unreal


OSC_LISTEN_PORT = 8000
BUFFER_SIZE = 65536


# ── OSC Protocol Decoder (raw socket) ──────────────────────────────────

def _decode_osc(data: bytes):
    """Decode a single OSC message from raw bytes.
    Returns (address, [values]) or None.
    """
    try:
        # Find address string (null-terminated, 4-byte padded)
        addr_end = data.index(b"\x00")
        addr = data[:addr_end].decode("utf-8")
        pos = addr_end
        while pos < len(data) and data[pos] == 0:
            pos += 1
        # Align to 4
        pos = ((pos + 3) // 4) * 4

        # Type tag string
        if pos >= len(data) or data[pos] != ord(","):
            return None
        pos += 1
        type_end = data.index(b"\x00", pos)
        types = data[pos:type_end].decode("utf-8")
        pos = type_end
        while pos < len(data) and data[pos] == 0:
            pos += 1
        pos = ((pos + 3) // 4) * 4

        # Values
        values = []
        for t in types:
            if t == "f":
                v = struct.unpack(">f", data[pos:pos+4])[0]
                pos += 4
            elif t == "i":
                v = struct.unpack(">i", data[pos:pos+4])[0]
                pos += 4
            elif t == "s":
                s_end = data.index(b"\x00", pos)
                v = data[pos:s_end].decode("utf-8")
                pos = s_end
                while pos < len(data) and data[pos] == 0:
                    pos += 1
                pos = ((pos + 3) // 4) * 4
            else:
                break
            values.append(v)
        return (addr, values)
    except Exception:
        return None


def _decode_osc_bundle(data: bytes):
    """Yield (address, values) from an OSC bundle or single message."""
    if data.startswith(b"#bundle\x00"):
        try:
            pos = 16  # skip "#bundle\0" + 8-byte timestamp
            while pos < len(data) - 4:
                size = struct.unpack(">i", data[pos:pos+4])[0]
                pos += 4
                msg = _decode_osc(data[pos:pos+size])
                if msg:
                    yield msg
                pos += size
        except Exception:
            pass
    else:
        msg = _decode_osc(data)
        if msg:
            yield msg


# ── MPC Parameter Router ──────────────────────────────────────────────

# MPC paths in UE 5.8
_MPC_PATHS = {
    "SakuraDream":      "/Game/EnvSandbox/VFX/MPC/MPC_SakuraDream",
    "Magical":          "/Game/EnvSandbox/VFX/MPC/MPC_Magical",
    "PortfolioAudio":   "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette",
}

_mpc_cache = {}

def _get_mpc(key: str):
    """Load or return cached MPC."""
    if key in _mpc_cache:
        return _mpc_cache[key]
    path = _MPC_PATHS.get(key)
    if not path:
        return None
    try:
        # load_asset, NOT find_object: find_object(None, "/Game/Foo/Bar") resolves the
        # *Package*, not the asset inside it, and every downstream call then fails with
        # "Cannot nativize 'Package'".
        mpc = unreal.load_asset(path)
        if mpc:
            _mpc_cache[key] = mpc
            unreal.log(f"[TD-Bridge] Loaded MPC: {key}")
        return mpc
    except Exception as e:
        unreal.log_warning(f"[TD-Bridge] MPC {key} not found: {e}")
        return None


def _world_context():
    """World to write MPC values into. Prefer the PIE world so the effect is visible
    while playing; fall back to the editor world so look-dev works outside PIE."""
    try:
        ue_sub = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        return ue_sub.get_game_world() or ue_sub.get_editor_world()
    except Exception:
        return None


# ── Game-thread marshalling ───────────────────────────────────────────
#
# The OSC listener runs in a daemon thread. UE's material APIs are game-thread
# only: calling set_scalar_parameter_value from the listener thread silently
# does nothing -- no exception, no log, the value simply never lands. That is
# why this bridge appeared wired for months while every MPC stayed at its
# default. Handlers therefore only ever STAGE values here; a Slate post-tick
# callback flushes them on the game thread.
#
# Coalescing is deliberate: TD sends ~57 bundles/sec and UE renders slower, so
# the dict keeps only the newest value per parameter and we do one write per
# parameter per frame instead of queueing thousands.

_pending_scalars = {}   # (mpc_key, param) -> float
_pending_vectors = {}   # (mpc_key, param) -> (r, g, b)
_tick_handle = None


def _set_mpc_scalar(mpc_key: str, param_name: str, value: float):
    """Stage a scalar for the next game-thread flush. Safe from any thread."""
    _pending_scalars[(mpc_key, param_name)] = float(value)


def _flush_pending(_delta_seconds: float = 0.0):
    """Apply staged values. MUST run on the game thread."""
    if not _pending_scalars and not _pending_vectors:
        return
    world = _world_context()
    if not world:
        return
    scalars = dict(_pending_scalars)
    _pending_scalars.clear()
    vectors = dict(_pending_vectors)
    _pending_vectors.clear()
    for (mpc_key, param), val in scalars.items():
        mpc = _get_mpc(mpc_key)
        if not mpc:
            continue
        try:
            unreal.MaterialLibrary.set_scalar_parameter_value(world, mpc, param, val)
        except Exception as e:
            unreal.log_warning(f"[TD-Bridge] MPC scalar {mpc_key}.{param}: {e}")
    for (mpc_key, param), (r, g, b) in vectors.items():
        mpc = _get_mpc(mpc_key)
        if not mpc:
            continue
        try:
            unreal.MaterialLibrary.set_vector_parameter_value(
                world, mpc, param, unreal.LinearColor(r, g, b, 1.0))
        except Exception as e:
            unreal.log_warning(f"[TD-Bridge] MPC vector {mpc_key}.{param}: {e}")


def _start_tick():
    global _tick_handle
    if _tick_handle is None:
        _tick_handle = unreal.register_slate_post_tick_callback(_flush_pending)


def _stop_tick():
    global _tick_handle
    if _tick_handle is not None:
        try:
            unreal.unregister_slate_post_tick_callback(_tick_handle)
        except Exception:
            pass
        _tick_handle = None


def _set_mpc_vector(mpc_key: str, param_name: str, r: float, g: float, b: float):
    """Stage a vector for the next game-thread flush. Safe from any thread."""
    _pending_vectors[(mpc_key, param_name)] = (float(r), float(g), float(b))


# ── OSC Route Handlers ────────────────────────────────────────────────

# Preset names for logging
_PRESET_NAMES = {0: "Nikki", 1: "Madoka", 2: "Celestial", 3: "Itto", 4: "Sakura"}

# 12-index toon param -> MPC mapping
# [0]=bloom_intensity, [1]=bloom_threshold, [2]=sparkle_pulse,
# [3]=dream_intensity, [4]=wind_strength, [5]=global_opacity,
# [6]=shadow_tint_r, [7]=shadow_tint_b, [8]=magical_transform,
# [9]=saturation, [10]=diffuse_wrap, [11]=sparkle_visibility
_TOON_MPC_TARGETS = [
    ("Magical",     "BloomIntensity"),       # 0
    (None, None),                             # 1 — PP bloom threshold
    ("SakuraDream", "SparklePulse"),          # 2
    ("SakuraDream", "DreamIntensity"),         # 3
    ("SakuraDream", "WindStrength"),           # 4
    ("SakuraDream", "GlobalOpacity"),          # 5
    (None, None),                              # 6 — shadow tint (PP)
    (None, None),                              # 7 — shadow tint (PP)
    ("Magical",     "MagicalTransform"),       # 8
    (None, None),                              # 9 — saturation (PP)
    (None, None),                              # 10 — diffuse wrap
    ("SakuraDream", "SparkleVisibility"),      # 11
]


def _handle_preset(address: str, values: list):
    """Handle /material/preset (int 0-4)."""
    preset_id = int(values[0]) if values else 0
    name = _PRESET_NAMES.get(preset_id, "Unknown")
    unreal.log(f"[TD-Bridge] Style preset: {preset_id} ({name})")
    _set_mpc_scalar("SakuraDream", "StylePreset", float(preset_id))
    _set_mpc_scalar("Magical", "MagicalTransform", float(preset_id) * 0.25)


def _handle_toon(address: str, values: list):
    """Handle /material/toon (float[12])."""
    floats = [float(v) for v in values[:12]]
    pushed = 0
    for idx, (mpc_key, param) in enumerate(_TOON_MPC_TARGETS):
        if mpc_key and param and idx < len(floats):
            _set_mpc_scalar(mpc_key, param, floats[idx])
            pushed += 1
    unreal.log(f"[TD-Bridge] Toon: {pushed}/12 MPC params (bloom={floats[0]:.1f})")


def _handle_amp(address: str, values: list):
    """Handle /melusina/amp (float 0-1)."""
    amp = float(values[0]) if values else 0.5
    _set_mpc_scalar("PortfolioAudio", "GlobalReactivity", amp)
    _set_mpc_scalar("SakuraDream", "SparklePulse", amp)


def _handle_pitch(address: str, values: list):
    """Handle /melusina/pitch (float Hz)."""
    hz = float(values[0]) if values else 440.0
    norm = max(0.0, min(1.0, (hz - 60.0) / 1940.0))
    _set_mpc_scalar("SakuraDream", "WindStrength", norm)


def _handle_formants(address: str, values: list):
    """Handle /melusina/formants (float[5])."""
    vals = [float(v) for v in values[:5]]
    if len(vals) >= 3:
        _set_mpc_scalar("PortfolioAudio", "Bass", vals[0])
        _set_mpc_scalar("PortfolioAudio", "Mid", vals[1])
        _set_mpc_scalar("PortfolioAudio", "Treble", vals[2])
    if len(vals) >= 5:
        _set_mpc_scalar("PortfolioAudio", "BeatPhase", vals[4])


# TouchDesigner's 5-band split. Verified live 2026-08-08 against the running
# project on G:\EnvironmentPortfolio\_TouchDesigner: /project1/audio band1..band5
# are audiofilterCHOPs at cutofflog 1.903/2.397/3.0/3.602/3.903 (~80/250/1k/4k/8k Hz),
# each through an analyzeCHOP(rmspower) and a lagCHOP, renamed on the way out by
# /project1/osc/audio_bands_rename. One OSC address per channel, one float each --
# oscoutCHOP sends channels individually, it does NOT bundle them into an array.
_BAND_PARAMS = {
    "sub":  "Bass",
    "low":  "BassIntensity",
    "mid":  "Mid",
    "high": "Treble",
    "air":  "TrebleIntensity",
}

_band_energy = {}


def _handle_band(address: str, values: list):
    """Handle /audio/band/{sub,low,mid,high,air} (float 0-1, RMS power)."""
    band = address.rsplit("/", 1)[-1]
    param = _BAND_PARAMS.get(band)
    if not param:
        return
    val = float(values[0]) if values else 0.0
    _set_mpc_scalar("PortfolioAudio", param, val)

    # Aggregate energy so a material can react to "loud" without picking a band.
    _band_energy[band] = val
    if len(_band_energy) == len(_BAND_PARAMS):
        _set_mpc_scalar("PortfolioAudio", "GlobalAudioReactivity",
                        sum(_band_energy.values()) / len(_band_energy))


def _handle_audio_beat(address: str, values: list):
    """Handle /audio/beat (float, spikes to 1.0 on transient then decays)."""
    _set_mpc_scalar("PortfolioAudio", "BeatIntensity", float(values[0]) if values else 0.0)


def _handle_audio_pitch(address: str, values: list):
    """Handle /audio/pitch (float, normalized across octaves)."""
    _set_mpc_scalar("PortfolioAudio", "PaletteShift", float(values[0]) if values else 0.0)


def _handle_day_night(address: str, values: list):
    """Handle /time/cycle (float 0-1)."""
    cycle = float(values[0]) if values else 0.5
    _set_mpc_scalar("SakuraDream", "DreamIntensity", 0.3 + cycle * 0.7)


def _handle_sparkle_rate(address: str, values: list):
    """Handle /niagara/sparkle/rate."""
    _set_mpc_scalar("SakuraDream", "PetalDensity", float(values[0]) if values else 0.5)


def _handle_mote_rate(address: str, values: list):
    """Handle /niagara/mote/rate."""
    _set_mpc_scalar("SakuraDream", "SparkleVisibility", float(values[0]) if values else 0.5)


def _handle_burst(address: str, values: list):
    """Handle /niagara/burst."""
    _set_mpc_scalar("Magical", "MagicalTransform", 1.0)
    unreal.log("[TD-Bridge] Wish burst!")


def _handle_wind(address: str, values: list):
    """Handle /niagara/wind (vec3)."""
    vals = [float(v) for v in values[:3]]
    if len(vals) >= 1:
        _set_mpc_scalar("SakuraDream", "WindStrength", abs(vals[0]))


def _handle_fabric(address: str, values: list):
    """Handle /material/fabric (float[4])."""
    vals = [float(v) for v in values[:4]]
    _set_mpc_scalar("SakuraDream", "PetalDensity", vals[0] * 0.01 if len(vals)>0 else 0)
    _set_mpc_scalar("Magical", "BloomIntensity", vals[3] * 0.01 if len(vals)>3 else 0)


def _handle_beat(address: str, values: list):
    """Handle /time/beat (float 0-1)."""
    beat = float(values[0]) if values else 0.5
    _set_mpc_scalar("PortfolioAudio", "BeatPhase", beat)


# ── Audio-reactive flower: TD CHOP → OSC 9000 (2026-09-02 sprint) ───────
_MEL_AUDIO_MAP = {"bass": ("PortfolioAudio","Bass"), "mid": ("PortfolioAudio","Mid"), "treble": ("PortfolioAudio","Treble")}
def _handle_melodia_audio(address: str, values: list):
    """Handle /melodia/audio/{bass,mid,treble} [0,1] from TD CHOP."""
    band = address.rsplit("/", 1)[-1]
    tgt = _MEL_AUDIO_MAP.get(band)
    if not tgt: return
    _set_mpc_scalar(tgt[0], tgt[1], max(0.0, min(1.0, float(values[0]) if values else 0.0)))
def _handle_melodia_beat_pulse(address: str, values: list):
    v = float(values[0]) if values else 0.0
    _set_mpc_scalar("PortfolioAudio","BeatPulse",v); _set_mpc_scalar("PortfolioAudio","BeatIntensity",v)
def _handle_melodia_beat_phase(address: str, values: list):
    _set_mpc_scalar("PortfolioAudio","BeatPhase", float(values[0]) if values else 0.0)
def _handle_rhythm_beat_pulse(address: str, values: list):
    v = float(values[0]) if values else 0.0
    _set_mpc_scalar("PortfolioAudio","BeatPulse",v); _set_mpc_scalar("PortfolioAudio","BeatIntensity",v)
def _handle_rhythm_beat_phase(address: str, values: list):
    _set_mpc_scalar("PortfolioAudio","BeatPhase", float(values[0]) if values else 0.0)


# Route table
_ROUTES = {
    "/material/preset":         _handle_preset,
    "/material/toon":           _handle_toon,
    "/material/fabric":         _handle_fabric,
    "/melusina/pitch":          _handle_pitch,
    "/melusina/amp":            _handle_amp,
    "/melusina/formants":       _handle_formants,
    "/audio/band/sub":          _handle_band,
    "/audio/band/low":          _handle_band,
    "/audio/band/mid":          _handle_band,
    "/audio/band/high":         _handle_band,
    "/audio/band/air":          _handle_band,
    "/audio/beat":              _handle_audio_beat,
    "/audio/pitch":             _handle_audio_pitch,
    "/niagara/sparkle/rate":    _handle_sparkle_rate,
    "/niagara/mote/rate":       _handle_mote_rate,
    "/niagara/burst":           _handle_burst,
    "/niagara/wind":            _handle_wind,
    "/time/cycle":              _handle_day_night,
    "/time/beat":               _handle_beat,
    "/melodia/audio/bass":      _handle_melodia_audio,
    "/melodia/audio/mid":       _handle_melodia_audio,
    "/melodia/audio/treble":    _handle_melodia_audio,
    "/melodia/audio/beat/pulse": _handle_melodia_beat_pulse,
    "/melodia/audio/beat/phase": _handle_melodia_beat_phase,
    "/rhythm/beat_pulse":       _handle_rhythm_beat_pulse,
    "/rhythm/beat_phase":       _handle_rhythm_beat_phase,
}


# ── Server ─────────────────────────────────────────────────────────────

def _server_loop():
    """Blocking UDP server loop — runs in daemon thread."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", OSC_LISTEN_PORT))
    sock.settimeout(1.0)

    unreal.log(f"[TD-Bridge] OSC listener started on port {OSC_LISTEN_PORT} "
               f"(raw socket, {len(_ROUTES)} routes)")

    frame_count = 0
    while _server_running:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            for address, values in _decode_osc_bundle(data):
                handler = _ROUTES.get(address)
                if handler:
                    handler(address, values)
                else:
                    # Only log unknown routes every 60 frames
                    if frame_count % 60 == 0:
                        unreal.log(f"[TD-Bridge] Unknown route: {address} "
                                   f"(frame {frame_count})")
        except socket.timeout:
            pass
        except Exception as e:
            unreal.log_warning(f"[TD-Bridge] Socket error: {e}")
        frame_count += 1

    sock.close()
    unreal.log("[TD-Bridge] OSC listener stopped.")


_server_running = False
_server_thread = None


def start_bridge(port: int = OSC_LISTEN_PORT):
    """Start the OSC bridge in a background thread."""
    global _server_running, _server_thread, OSC_LISTEN_PORT
    if _server_running:
        return True

    OSC_LISTEN_PORT = port
    _server_running = True
    _server_thread = threading.Thread(target=_server_loop, daemon=True)
    _server_thread.start()
    _start_tick()   # MPC writes only land from the game thread; see _flush_pending
    return True


def stop_bridge():
    """Stop the OSC bridge."""
    global _server_running
    _server_running = False
    _stop_tick()
    if _server_thread:
        _server_thread.join(timeout=2.0)


def get_status():
    """Return bridge status."""
    return {
        "running": _server_running,
        "port": OSC_LISTEN_PORT,
        "routes": len(_ROUTES),
        "mpcs_loaded": list(_mpc_cache.keys()),
    }
