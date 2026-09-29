"""Prove the flower-field wind lane chain end to end, with real traffic.

Chain under test (owner brief 2026-09-16, commit 09316fa9):

    TD / game  --UDP OSC-->  osc_server._handle_wind
              -->  MPC_Melodia_Palette.WindDirX / WindDirY / WindStrength   (source)
              -->  UMelodiaCymaticsWriterSubsystem (game tick, sole driver writer)
              -->  MPC_Cymatics_Driver.Cymatic_WindDirX / WindDirY / Strength  (derived)

Every assertion below is a read-back from the live PIE world. Nothing is
asserted from the sender's own return value, and no value is written straight
to the driver -- if the writer did not tick, the driver lanes stay at their
defaults and the gate fails.

Why two directions: the pre-2026-09-16 handler wrote `abs(vals[0])`, so +X and
-X produced identical output and Y was discarded. Direction sign and the Y
component are therefore separate assertions, not decoration.

Run:  python Tools/wind_lane_chain_proof.py [--map /Game/...] [--no-pie]
Writes: Saved/Audit/wind_lane_chain_proof.json
Exits non-zero on any failed assertion.
"""

from __future__ import annotations
from mcp_client import post_envelope

import argparse
import json
import os
import socket
import struct
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

MONOLITH = "http://localhost:9316/mcp"
PROJECT = Path(__file__).resolve().parents[1]
REPORT = PROJECT / "Saved" / "Audit" / "wind_lane_chain_proof.json"

OSC_HOST = "127.0.0.1"
OSC_PORT = 8000  # osc_server.OSC_LISTEN_PORT -- the TD bridge's real port
ADDRESS = "/melodia/wind"

PALETTE = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.MPC_Melodia_Palette"
DRIVER = "/Game/Melodia/Cymatics/MPC_Cymatics_Driver.MPC_Cymatics_Driver"


# ------------------------------------------------------------------ monolith

def rpc(method: str, params: dict | None = None, rid: int = 1):
    payload = json.dumps({"jsonrpc": "2.0", "id": rid, "method": method,
                          "params": params or {}}).encode()
    result = post_envelope(payload, timeout=180)
    if "error" in result:
        return {"_error": result["error"]}
    return result


def editor(action: str, **args):
    env = rpc("tools/call", {"name": "editor_query",
                             "arguments": {"action": action, **args}}, rid=2)
    try:
        return json.loads(env["result"]["content"][0]["text"])
    except Exception:
        return env


def run_python(source: str) -> dict:
    return editor("run_python", command=source)


def python_output(res: dict) -> str:
    if not isinstance(res, dict):
        return str(res)
    lines = [o.get("output", "") for o in res.get("output", []) or []]
    if not lines and res.get("message"):
        lines.append(str(res["message"]))
    return "".join(lines)


# ----------------------------------------------------------------------- osc

def osc_float_message(address: str, values) -> bytes:
    """Minimal OSC encoder: ',fff' with float32 args. No external deps.

    An OSC-string is NUL-terminated *and* then padded to a 4-byte boundary, so
    the type tag ',fff' is 8 bytes on the wire (',fff\\0' + 3 pad), not 4. A
    4-byte ',fff' with no terminator decodes to nothing in
    Content/Python/osc_server.py::_decode_osc, which hunts for the NUL -- the
    first zero byte it then finds is inside the float payload, the type string
    comes back as garbage, and the message is silently dropped. That is a
    sender bug, not a listener bug; real senders (TouchDesigner, python-osc)
    terminate the string.
    """
    def pad(b: bytes) -> bytes:
        return b + b"\x00" * ((4 - len(b) % 4) % 4)
    out = pad(address.encode() + b"\x00")
    out += pad(b",fff\x00")
    out += b"".join(struct.pack(">f", float(v)) for v in values)
    return out


def send_wind(vec) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(osc_float_message(ADDRESS, vec), (OSC_HOST, OSC_PORT))
    finally:
        sock.close()


# -------------------------------------------------------------------- in-editor

STAGE_BRIDGE = """
import sys, unreal
if "osc_server" not in sys.modules:
    try:
        import osc_server            # noqa: F401  (editor python path)
    except Exception as exc:
        print("OSC_IMPORT_FAIL", exc)
if "osc_server" in sys.modules:
    m = sys.modules["osc_server"]
    if getattr(m, "_server_running", False):
        print("OSC_ALREADY_RUNNING", getattr(m, "OSC_LISTEN_PORT", "?"))
    else:
        m.start_bridge()
        print("OSC_STARTED", getattr(m, "OSC_LISTEN_PORT", "?"))
else:
    print("OSC_MISSING")
"""

STAGE_READ = """
import unreal
es = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = es.get_game_world()
scope = "pie"
if not world:
    world = es.get_editor_world()
    scope = "editor"
if not world:
    print("NO_PIE_WORLD")
else:
    print("READSCOPE " + scope)
    lib = unreal.MaterialLibrary
    pal = unreal.load_asset("{palette}")
    drv = unreal.load_asset("{driver}")
    names = [("Palette.WindDirX", pal, "WindDirX"),
             ("Palette.WindDirY", pal, "WindDirY"),
             ("Palette.WindStrength", pal, "WindStrength"),
             ("Driver.Cymatic_WindDirX", drv, "Cymatic_WindDirX"),
             ("Driver.Cymatic_WindDirY", drv, "Cymatic_WindDirY"),
             ("Driver.Cymatic_WindStrength", drv, "Cymatic_WindStrength"),
             ("Driver.Cymatic_BeatPulse", drv, "Cymatic_BeatPulse"),
             ("Driver.Cymatic_BassIntensity", drv, "Cymatic_BassIntensity")]
    vals = {{}}
    for label, coll, name in names:
        try:
            vals[label] = float(lib.get_scalar_parameter_value(world, coll, name))
        except Exception as exc:
            vals[label] = "ERR:{{}}".format(exc)
    print("READBACK " + repr(vals))
"""

STAGE_STOP_BRIDGE = """
import sys
if "osc_server" in sys.modules:
    sys.modules["osc_server"].stop_bridge()
    print("OSC_STOPPED")
else:
    print("OSC_NOT_LOADED")
"""


def read_back() -> dict:
    res = run_python(STAGE_READ.format(palette=PALETTE, driver=DRIVER))
    text = python_output(res)
    for line in text.splitlines():
        if line.startswith("READBACK "):
            return json.loads(line[len("READBACK "):].replace("'", '"'))
    raise RuntimeError(f"no readback (output was: {text[:500]!r})")


def near(a, b, tol=1e-3) -> bool:
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return False


# ------------------------------------------------------------------- the gate

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", default=None, help="map for PIE; default = current level")
    ap.add_argument("--settle", type=float, default=2.5,
                    help="seconds to let the writer tick after each OSC send")
    ap.add_argument("--no-pie", action="store_true",
                    help="skip PIE; read the editor world instead (contract check only)")
    ap.add_argument("--stop-bridge", action="store_true",
                    help="call osc_server.stop_bridge() at the end. DEFAULT OFF: that "
                         "call crashed the editor on 2026-09-17 (fatal Slate assert in "
                         "unregister_slate_post_tick_callback). The bridge stays "
                         "listening on 8000 unless you pass this.")
    args = ap.parse_args()

    report = {"generated": datetime.now(timezone.utc).isoformat(),
              "chain": "OSC -> MPC_Melodia_Palette(source) -> "
                       "UMelodiaCymaticsWriterSubsystem -> MPC_Cymatics_Driver(derived)",
              "osc_address": ADDRESS, "osc_port": OSC_PORT,
              "stages": {}, "assertions": []}
    failures = []

    def check(name, ok, detail):
        report["assertions"].append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok:
            failures.append(name)

    # 1 -- bridge up (real listener, not a simulated call)
    bridge = python_output(run_python(STAGE_BRIDGE))
    report["stages"]["bridge"] = bridge.strip()
    check("osc_bridge_running",
          "OSC_STARTED" in bridge or "OSC_ALREADY_RUNNING" in bridge, bridge.strip())

    # 2 -- PIE, so the GameInstanceSubsystem writer actually ticks
    if not args.no_pie:
        started = editor("start_pie", **({"map": args.map} if args.map else {}))
        report["stages"]["start_pie"] = started
        time.sleep(12)

    # 3 -- direction A: +X-ish diagonal
    send_wind((0.6, 0.8, 0.0))
    time.sleep(args.settle)
    a = read_back()
    report["stages"]["after_+x"] = a

    check("A_palette_dirx", near(a.get("Palette.WindDirX"), 0.6),
          f"expected 0.6, got {a.get('Palette.WindDirX')}")
    check("A_palette_diry", near(a.get("Palette.WindDirY"), 0.8),
          f"expected 0.8, got {a.get('Palette.WindDirY')}")
    check("A_palette_strength", near(a.get("Palette.WindStrength"), 1.0),
          f"expected 1.0, got {a.get('Palette.WindStrength')}")

    if args.no_pie:
        # Without PIE there is no GameInstance and no writer tick, so the driver
        # lanes stay at their declared defaults. Reporting those as failures
        # would be wrong; reporting them as passes would be worse. Skip them and
        # say so in the receipt.
        report["scope"] = "sender+palette contract only (no PIE, no writer tick)"
        report["skipped"] = "driver assertions require PIE"
    else:
        report["scope"] = "full chain incl. live writer tick"

        check("A_driver_dirx", near(a.get("Driver.Cymatic_WindDirX"), 0.6),
              f"expected 0.6, got {a.get('Driver.Cymatic_WindDirX')}")
        check("A_driver_diry", near(a.get("Driver.Cymatic_WindDirY"), 0.8),
              f"expected 0.8, got {a.get('Driver.Cymatic_WindDirY')}")
        check("A_driver_strength", near(a.get("Driver.Cymatic_WindStrength"), 1.0),
              f"expected 1.0, got {a.get('Driver.Cymatic_WindStrength')}")

        # 4 -- direction B: negate X only. Kills the old abs(X) collapse if it passes.
        send_wind((-0.6, 0.8, 0.0))
        time.sleep(args.settle)
        b = read_back()
        report["stages"]["after_-x"] = b

        check("B_driver_dirx_negative", near(b.get("Driver.Cymatic_WindDirX"), -0.6),
              f"expected -0.6, got {b.get('Driver.Cymatic_WindDirX')}")
        check("B_driver_diry_unchanged", near(b.get("Driver.Cymatic_WindDirY"), 0.8),
              f"expected 0.8, got {b.get('Driver.Cymatic_WindDirY')}")
        check("B_dir_actually_changed",
              not near(a.get("Driver.Cymatic_WindDirX"), b.get("Driver.Cymatic_WindDirX"), 0.01),
              "direction must differ between +X and -X gusts")

        # 5 -- zero wind: strength 0, no NaN, direction held (not snapped)
        send_wind((0.0, 0.0, 0.0))
        time.sleep(args.settle)
        z = read_back()
        report["stages"]["after_zero"] = z

        check("Z_driver_strength_zero", near(z.get("Driver.Cymatic_WindStrength"), 0.0),
              f"expected 0.0, got {z.get('Driver.Cymatic_WindStrength')}")
        check("Z_no_nan", all(
            isinstance(v, (int, float)) and v == v
            for k, v in z.items() if k.startswith("Driver.")),
            {k: v for k, v in z.items() if k.startswith("Driver.")})
        check("Z_direction_held_not_snapped",
              near(z.get("Driver.Cymatic_WindDirX"),
                   b.get("Driver.Cymatic_WindDirX"), 0.01),
              f"held {b.get('Driver.Cymatic_WindDirX')} -> {z.get('Driver.Cymatic_WindDirX')}")

        # 6 -- the sole-writer's pre-existing contract must be untouched
        check("cym_beatpulse_present", isinstance(z.get("Driver.Cymatic_BeatPulse"), float),
              z.get("Driver.Cymatic_BeatPulse"))
        check("cym_bass_present", isinstance(z.get("Driver.Cymatic_BassIntensity"), float),
              z.get("Driver.Cymatic_BassIntensity"))

    if not args.no_pie:
        report["stages"]["stop_pie"] = editor("stop_pie")
        time.sleep(3)

    if args.stop_bridge:
        stopped = python_output(run_python(STAGE_STOP_BRIDGE))
        report["stages"]["bridge_stop"] = stopped.strip()
        if stopped.strip() != "OSC_STOPPED":
            failures.append("bridge_not_stopped")
    else:
        report["stages"]["bridge_stop"] = ("skipped (default) -- bridge left listening "
                                           "on 8000; see --stop-bridge help")

    report["ok"] = not failures
    report["failed_assertions"] = failures
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[wind-chain] {'PASS' if report['ok'] else 'FAIL'}  "
          f"({len(report['assertions']) - len(failures)}/{len(report['assertions'])} assertions)")
    for a_ in report["assertions"]:
        print(f"  {'ok  ' if a_['ok'] else 'FAIL'} {a_['name']}: {a_['detail']}")
    print(f"[wind-chain] receipt: {REPORT}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
