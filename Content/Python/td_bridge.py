"""
td_bridge.py — TouchDesigner bridge script for Unreal Editor environment.

Handles OSC communication between TouchDesigner and Unreal Engine for the
Nikki-style vertical slice pipeline. Communicates with TD via Envoy MCP
(localhost:9870) or direct OSC, and with UE via built-in OSC plugin (port 8000).

Branch: feature/touchdesigner-mcp-integration
Owner: TOA (TouchDesigner Orchestrator Agent)
"""

import json
import os
import socket
import struct
import sys
import time
from datetime import datetime

# ── Constants ──────────────────────────────────────────────────────────
PROJECT_ROOT = r"G:\EnvironmentPortfolio"
TD_MCP_PORT = 9870
UE_OSC_PORT = 8000
TD_OSC_PORT = 9000
BLENDER_OSC_PORT = 9000

SENTINEL_PATH = os.path.join(PROJECT_ROOT, r"BS_GodFile\Saved\Audit\AGENT_LOOP_TICK_td_orch")
OSC_ROUTING_PATH = os.path.join(PROJECT_ROOT, r"BS_GodFile\deploy\osc_routing.json")

# ── Nikki Style Presets (MPC-mapped parameter names) ────────────────────
# Each preset is a 12-float array mapped to UE MPC parameters:
#   [0] bloom_intensity  -> MPC_Magical.BloomIntensity
#   [1] bloom_threshold  -> Post-process threshold
#   [2] sparkle_pulse    -> MPC_SakuraDream.SparklePulse
#   [3] dream_intensity  -> MPC_SakuraDream.DreamIntensity
#   [4] wind_strength    -> MPC_SakuraDream.WindStrength
#   [5] global_opacity   -> MPC_SakuraDream.GlobalOpacity
#   [6] shadow_tint_r    -> Post-process shadow tint
#   [7] shadow_tint_b    -> Post-process shadow tint
#   [8] magical_transform-> MPC_Magical.MagicalTransform
#   [9] saturation       -> Post-process saturation
#  [10] diffuse_wrap     -> Material wrap
#  [11] sparkle_vis      -> MPC_SakuraDream.SparkleVisibility
STYLE_PRESETS = {
    0: {
        "name": "Nikki",
        "description": "Soft dreamy pastel, heavy bloom, warm golden hour",
        "bloom_intensity": 5.0, "bloom_threshold": 0.75,
        "sparkle_pulse": 0.8, "dream_intensity": 0.7,
        "wind_strength": 0.4, "global_opacity": 0.9,
        "shadow_tint_r": 0.21, "shadow_tint_b": 0.25,
        "magical_transform": 0.25, "saturation": 0.9,
        "diffuse_wrap": 0.5, "sparkle_vis": 0.8,
    },
    1: {
        "name": "Madoka",
        "description": "Witch barrier surreal, saturated, collage-like",
        "bloom_intensity": 3.0, "bloom_threshold": 0.85,
        "sparkle_pulse": 1.0, "dream_intensity": 0.5,
        "wind_strength": 0.3, "global_opacity": 1.0,
        "shadow_tint_r": 0.15, "shadow_tint_b": 0.25,
        "magical_transform": 0.60, "saturation": 1.2,
        "diffuse_wrap": 0.3, "sparkle_vis": 1.0,
    },
    2: {
        "name": "Celestial",
        "description": "Space nebula, cool tones, deep astral",
        "bloom_intensity": 4.0, "bloom_threshold": 0.80,
        "sparkle_pulse": 0.5, "dream_intensity": 0.3,
        "wind_strength": 0.2, "global_opacity": 0.7,
        "shadow_tint_r": 0.08, "shadow_tint_b": 0.19,
        "magical_transform": 0.40, "saturation": 0.85,
        "diffuse_wrap": 0.4, "sparkle_vis": 0.5,
    },
    3: {
        "name": "Itto",
        "description": "Mythic carved stone, warm ochre, dramatic",
        "bloom_intensity": 2.5, "bloom_threshold": 0.90,
        "sparkle_pulse": 0.3, "dream_intensity": 0.4,
        "wind_strength": 0.5, "global_opacity": 0.6,
        "shadow_tint_r": 0.12, "shadow_tint_b": 0.06,
        "magical_transform": 0.10, "saturation": 0.75,
        "diffuse_wrap": 0.6, "sparkle_vis": 0.3,
    },
    4: {
        "name": "Sakura",
        "description": "Japanese pink, delicate, cherry blossom",
        "bloom_intensity": 4.5, "bloom_threshold": 0.78,
        "sparkle_pulse": 0.9, "dream_intensity": 0.6,
        "wind_strength": 0.5, "global_opacity": 0.95,
        "shadow_tint_r": 0.18, "shadow_tint_b": 0.20,
        "magical_transform": 0.30, "saturation": 0.95,
        "diffuse_wrap": 0.55, "sparkle_vis": 0.9,
    },
}


# ── OSC Protocol ─────────────────────────────────────────────────────────
def _pad_bytes(data):
    """Pad byte array to multiple of 4."""
    padding = 4 - (len(data) % 4)
    if padding == 4:
        return data
    return data + b"\x00" * padding


def _osc_message(address, *values):
    """Build raw OSC message bytes.
    Supports float ('f') and int ('i') types.
    """
    addr_bytes = address.encode("utf-8")
    addr_padded = _pad_bytes(addr_bytes)

    type_tags = ","
    value_bytes = b""
    for v in values:
        if isinstance(v, float):
            type_tags += "f"
            value_bytes += struct.pack(">f", v)
        elif isinstance(v, int):
            type_tags += "i"
            value_bytes += struct.pack(">i", v)
        elif isinstance(v, str):
            type_tags += "s"
            v_bytes = v.encode("utf-8")
            value_bytes += _pad_bytes(v_bytes)

    type_padded = _pad_bytes(type_tags.encode("utf-8"))
    return addr_padded + type_padded + value_bytes


def send_osc(host, port, address, *values):
    """Send a single OSC message via UDP."""
    message = _osc_message(address, *values)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(message, (host, port))


def send_osc_batch(host, port, messages):
    """Send multiple OSC messages to same host:port."""
    batch = b""
    for address, values in messages:
        msg = _osc_message(address, *values)
        batch += struct.pack(">i", len(msg)) + msg
    batch = b"#bundle\x00" + struct.pack(">Q", 0) + batch
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(batch, (host, port))


# ── OSC Routing ──────────────────────────────────────────────────────────
def load_osc_routing():
    """Load shared OSC route definitions from disk."""
    try:
        with open(OSC_ROUTING_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "version": "1.0",
            "routes": {
                "audio": {
                    "melusina_pitch": {
                        "path": "/melusina/pitch",
                        "type": "float",
                        "range": [60, 2000],
                    },
                    "melusina_amplitude": {
                        "path": "/melusina/amp",
                        "type": "float",
                        "range": [0, 1],
                    },
                    "melusina_formants": {
                        "path": "/melusina/formants",
                        "type": "float_array",
                        "size": 5,
                    },
                },
                "material": {
                    "toon_params": {
                        "path": "/material/toon",
                        "type": "float_array",
                        "size": 12,
                    },
                    "style_preset": {
                        "path": "/material/preset",
                        "type": "int",
                        "range": [0, 4],
                    },
                },
                "time": {
                    "day_night_cycle": {
                        "path": "/time/cycle",
                        "type": "float",
                        "range": [0, 1],
                    },
                    "beat_sync": {
                        "path": "/time/beat",
                        "type": "float",
                        "range": [0, 1],
                    },
                },
                "camera": {
                    "ue_camera_transform": {
                        "path": "/ue/camera",
                        "type": "float_array",
                        "size": 16,
                    },
                },
            },
        }


def save_osc_routing(routing):
    """Persist OSC routing schema to disk."""
    os.makedirs(os.path.dirname(OSC_ROUTING_PATH), exist_ok=True)
    with open(OSC_ROUTING_PATH, "w") as f:
        json.dump(routing, f, indent=2)


# ── Tick Handler ─────────────────────────────────────────────────────────
def td_tick(melusina_pitch=440.0, melusina_amp=0.5, style_preset=0, day_cycle=0.5):
    """Execute one TD orchestration tick.

    Pushes audio-reactive parameters, material preset, and time-of-day
    from TouchDesigner to Unreal Engine via OSC.

    In production, melusina_pitch and melusina_amp come from querying the
    TD audio analysis CHOPs via Envoy MCP. The daemon feeds these values.
    """
    routes = load_osc_routing()
    preset = STYLE_PRESETS.get(style_preset, STYLE_PRESETS[0])

    # Build OSC message batch for efficient single-packet push
    messages = []

    # Audio → UE material parameters
    pitch_route = routes["audio"]["melusina_pitch"]["path"]
    amp_route = routes["audio"]["melusina_amplitude"]["path"]
    messages.append((pitch_route, (float(melusina_pitch),)))
    messages.append((amp_route, (float(melusina_amp),)))

    # Material preset
    preset_route = routes["material"]["style_preset"]["path"]
    messages.append((preset_route, (int(style_preset),)))

    # Toon parameters (12 floats mapped to UE MPCs)
    toon_params = [
        preset["bloom_intensity"],
        preset["bloom_threshold"],
        preset["sparkle_pulse"],
        preset["dream_intensity"],
        preset["wind_strength"],
        preset["global_opacity"],
        preset["shadow_tint_r"],
        preset["shadow_tint_b"],
        preset["magical_transform"],
        preset["saturation"],
        preset["diffuse_wrap"],
        preset["sparkle_vis"],
    ]
    toon_route = routes["material"]["toon_params"]["path"]
    messages.append((toon_route, tuple(toon_params)))

    # Day/night cycle
    cycle_route = routes["time"]["day_night_cycle"]["path"]
    messages.append((cycle_route, (float(day_cycle),)))

    # Send to UE
    try:
        send_osc_batch("127.0.0.1", UE_OSC_PORT, messages)
    except Exception as e:
        print(f"[TOA] OSC send failed: {e}")
        return False

    # Write heartbeat sentinel
    tick_data = {
        "tick_timestamp": datetime.now().isoformat(),
        "agent": "TOA",
        "status": "ok",
        "pitch": melusina_pitch,
        "amplitude": melusina_amp,
        "preset": style_preset,
        "preset_name": preset["name"],
        "day_cycle": day_cycle,
        "osc_destinations": [
            {"host": "127.0.0.1", "port": UE_OSC_PORT, "label": "UE_OSC"},
        ],
    }
    os.makedirs(os.path.dirname(SENTINEL_PATH), exist_ok=True)
    with open(SENTINEL_PATH, "w") as f:
        json.dump(tick_data, f, indent=2)

    return True


# ── Preset Management ────────────────────────────────────────────────────
def set_preset(preset_id):
    """Push a Nikki-style material preset to UE via OSC."""
    preset = STYLE_PRESETS.get(preset_id)
    if not preset:
        print(f"[TOA] Unknown preset ID: {preset_id}")
        return False

    routes = load_osc_routing()
    send_osc(
        "127.0.0.1",
        UE_OSC_PORT,
        routes["material"]["style_preset"]["path"],
        int(preset_id),
    )
    print(f"[TOA] Preset set to #{preset_id} ({preset['name']}): {preset['description']}")
    return True


def list_presets():
    """Print all available style presets."""
    print(f"\n{'ID':<4} {'Name':<12} {'Description'}")
    print("-" * 56)
    for pid, p in STYLE_PRESETS.items():
        print(f"{pid:<4} {p['name']:<12} {p['description']}")
    print()


# ── Spout Health ─────────────────────────────────────────────────────────
def verify_spout():
    """Check Spout stream health.

    Returns a dict with stream status for each known Spout connection.
    In production, this queries Envoy MCP for Spout TOP operator status.
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "streams": [
            {
                "name": "TD_NikkiPreview",
                "direction": "TD_to_UE",
                "status": "checking",  # TODO: MCP query
            },
            {
                "name": "UE_RenderTarget",
                "direction": "UE_to_TD",
                "status": "checking",  # TODO: MCP query
            },
        ],
    }


# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if "--tick" in sys.argv:
        ok = td_tick()
        if ok:
            print("[TOA] Tick complete. OSC parameters pushed to UE.")
        else:
            print("[TOA] Tick FAILED.")
            sys.exit(1)

    elif "--preset" in sys.argv:
        try:
            idx = sys.argv.index("--preset")
            preset_id = int(sys.argv[idx + 1])
            set_preset(preset_id)
        except (ValueError, IndexError):
            list_presets()

    elif "--list-presets" in sys.argv:
        list_presets()

    elif "--verify" in sys.argv:
        result = verify_spout()
        print(json.dumps(result, indent=2))
        all_ok = all(s["status"] == "active" for s in result["streams"])
        print(f"\n[TOA] Spout health: {'ALL OK' if all_ok else 'DEGRADED'}")

    elif "--init-routing" in sys.argv:
        routing = load_osc_routing()
        save_osc_routing(routing)
        print(f"[TOA] OSC routing schema written to: {OSC_ROUTING_PATH}")

    else:
        print("TouchDesigner Bridge — Environment Portfolio Platform")
        print("Branch: feature/touchdesigner-mcp-integration")
        print()
        print("Usage:")
        print("  td_bridge.py --tick            Execute one orchestration tick")
        print("  td_bridge.py --preset N        Set style preset (0-4)")
        print("  td_bridge.py --list-presets    List available style presets")
        print("  td_bridge.py --verify          Check Spout stream health")
        print("  td_bridge.py --init-routing    Write initial OSC routing schema")
