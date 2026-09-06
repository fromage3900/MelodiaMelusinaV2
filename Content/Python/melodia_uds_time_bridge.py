"""Bridge Ultra Dynamic Sky time-of-day into Melodia's semantic day model.

WHAT THIS ADDS, AND WHY IT IS NOT A DUPLICATE
---------------------------------------------
`setup_time_of_day_mpc.py` already established the authority and it stands:

    UDS writes its own MPC -- /Game/UltraDynamicSky/Materials/Weather/
    UltraDynamicWeather_Parameters -- and that is the live source of truth.
    MPC_Portfolio_TimeOfDay was deliberately NOT created because it would be a
    stale duplicate.

That script wires the *look* half: `UseUDSTimeOfDay` + `TimeOfDayMPCStrength` on
M_Master_Toon_Universal, so materials tint with the sun. It explicitly leaves
`MPC_Melodia_Palette.TimeOfDayWarmth` as "a manual scene-grade overlay".

This script adds the *semantic* half, which nothing currently owns: turning the raw
UDS clock (a float 0..2400) into the day model gameplay actually wants to reason
about -- a normalised phase, a named day part, and a warmth grade -- and publishing
that as a stable contract other systems bind to.

It does NOT create a new MPC, does NOT re-implement the sun, and does NOT touch
UltraDynamicWeather_Parameters. It reads UDS and derives.

THE SINGLE-WRITER RULE (read before extending)
----------------------------------------------
`UMelodiaAudioReactivePresentationSubsystem` is the ONLY runtime writer of
MPC_Melodia_Palette. That is a load-bearing invariant -- the beat namespace broke
once already when two systems wrote it.

So: **this script is an editor-time tool. It is not, and cannot become, the runtime
path.** Python does not exist in a packaged build. `--apply` writes the palette for
in-editor lookdev and preview only, and is refused while PIE is running.

The runtime owner is named in the emitted contract: the day lane must be published
by the existing single writer (or a read-only consumer of it), never by a second
writer bolted on later.

WHAT "WIRE IT FOR GAMEPLAY LATER" MEANS HERE
--------------------------------------------
The deliverable that survives into runtime is the contract JSON this emits:
`Saved/Audit/uds_time_bridge_contract.json`. It pins the day-part boundaries, the
parameter names, and the event ids, so the C++ subsystem, the Quill scripts and the
UI all agree on what "dusk" means without re-deriving it three times.

Consumers already on disk that this is shaped to feed:
  quests   UMelodiaNarrativeSubsystem::SetNarrativeFlag / SetQuestActive
  rhythm   UMelodiaMusicClockSubsystem::GetTempoBPM / GetSecondsToNextBeat
  world    FWorldFieldSample / MelodiaWorldFieldBus
  ui       MPC_Melodia_Palette -> DayCyclePhase / TimeOfDayWarmth / SeasonBlend

USAGE (editor open)
-------------------
    py Content/Python/melodia_uds_time_bridge.py                 # audit + emit contract
    py Content/Python/melodia_uds_time_bridge.py --scrub 1750    # derive at a given clock
    py Content/Python/melodia_uds_time_bridge.py --sweep         # every day part, table out
    py Content/Python/melodia_uds_time_bridge.py --apply         # editor preview write
    py Content/Python/melodia_uds_time_bridge.py --scrub 0530 --apply --set-uds

Companion: setup_time_of_day_mpc.py (look half) - setup_portfolio_mpc.py (palette).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

def _project_root() -> Path:
    """Resolve the project root whether run as a file or exec'd as a string.

    Monolith's editor_query.run_python execs the source, so __file__ is absent --
    fall back to the engine's own answer rather than guessing a relative path.
    """
    try:
        return Path(__file__).resolve().parents[2]
    except NameError:
        return Path(unreal.Paths.convert_relative_path_to_full(
            unreal.Paths.project_dir()))


PROJECT_ROOT = _project_root()
AUDIT_DIR = PROJECT_ROOT / "Saved" / "Audit"
REPORT = AUDIT_DIR / "uds_time_bridge.json"
CONTRACT = AUDIT_DIR / "uds_time_bridge_contract.json"

# Source of truth, per setup_time_of_day_mpc.py. Read-only here.
UDS_ROOT = "/Game/UltraDynamicSky"
UDS_MPC = f"{UDS_ROOT}/Materials/Weather/UltraDynamicWeather_Parameters"
UDS_BP = f"{UDS_ROOT}/Blueprints/Ultra_Dynamic_Sky"
UDS_TIME_SCALAR = "Time of Day"      # UDS writes this every tick, 0..2400
UDS_TIME_PROPERTY = "Time of Day"    # same value as an actor property

# Melodia palette. The grandmaster collection -- see setup_portfolio_mpc.py.
MELODIA_MPC = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"

# Palette lanes this bridge owns. All three are ALREADY DECLARED on the MPC and
# have no writer -- verified 2026-09-05 against the asset's 51 scalars. That is the
# gap this closes; none of these are new parameters.
LANE_PHASE = "DayCyclePhase"      # 0..1, midnight-to-midnight
LANE_WARMTH = "TimeOfDayWarmth"   # -1 cool .. +1 warm
LANE_SEASON = "SeasonBlend"       # 0..1, passthrough, not derived from the clock

UDS_DAY_UNITS = 2400.0

# ---------------------------------------------------------------------------
# The day model. Data, not code, so a designer can retune it without a rebuild --
# and so the emitted contract and the runtime C++ read the SAME numbers.
#
# Bounds are UDS clock units (0..2400, 1200 = noon), start-inclusive/end-exclusive.
# `warmth` is the value at the CENTRE of the band; the curve lerps between centres
# so dawn and dusk bloom warm rather than stepping.
# ---------------------------------------------------------------------------
DAY_PARTS = [
    {"id": "Night",     "start":    0.0, "end":  500.0, "warmth": -0.70, "flag": "melodia_tod_night"},
    {"id": "Dawn",      "start":  500.0, "end":  700.0, "warmth":  0.85, "flag": "melodia_tod_dawn"},
    {"id": "Morning",   "start":  700.0, "end": 1100.0, "warmth":  0.35, "flag": "melodia_tod_morning"},
    {"id": "Noon",      "start": 1100.0, "end": 1400.0, "warmth":  0.05, "flag": "melodia_tod_noon"},
    {"id": "Afternoon", "start": 1400.0, "end": 1700.0, "warmth":  0.30, "flag": "melodia_tod_afternoon"},
    {"id": "Dusk",      "start": 1700.0, "end": 1930.0, "warmth":  0.90, "flag": "melodia_tod_dusk"},
    {"id": "Nightfall", "start": 1930.0, "end": 2400.0, "warmth": -0.55, "flag": "melodia_tod_nightfall"},
]

# Transition events. A gameplay hook wants "the moment it became dusk", not a
# per-frame float. These are the edges the runtime broadcasts on.
TRANSITION_EVENTS = [
    {"id": "melodia.tod.sunrise", "at":  500.0, "uds_hook": "Bind to Sunrise"},
    {"id": "melodia.tod.morning", "at":  700.0, "uds_hook": None},
    {"id": "melodia.tod.noon",    "at": 1200.0, "uds_hook": None},
    {"id": "melodia.tod.sunset",  "at": 1700.0, "uds_hook": "Bind to Sunset"},
    {"id": "melodia.tod.night",   "at": 1930.0, "uds_hook": None},
]


# ---------------------------------------------------------------------------
# Pure derivation. No unreal calls in this block on purpose: it is unit-testable
# offline and it is the exact arithmetic the C++ side must reproduce.
# ---------------------------------------------------------------------------
def normalise_clock(uds_time: float) -> float:
    """UDS 0..2400 -> phase 0..1. Wraps, so 2500 and 100 agree."""
    return (float(uds_time) % UDS_DAY_UNITS) / UDS_DAY_UNITS


def day_part_at(uds_time: float) -> dict:
    t = float(uds_time) % UDS_DAY_UNITS
    for part in DAY_PARTS:
        if part["start"] <= t < part["end"]:
            return part
    return DAY_PARTS[0]


def _centre(part: dict) -> float:
    return (part["start"] + part["end"]) * 0.5


def warmth_at(uds_time: float) -> float:
    """Lerp between day-part warmth centres so dawn/dusk bloom instead of stepping."""
    t = float(uds_time) % UDS_DAY_UNITS
    # Build a wrapped ring of (centre, warmth) so midnight interpolates correctly.
    ring = [(_centre(p), p["warmth"]) for p in DAY_PARTS]
    ring.sort(key=lambda kv: kv[0])
    first_c, first_w = ring[0]
    last_c, last_w = ring[-1]
    if t < first_c:
        span = (first_c + UDS_DAY_UNITS) - last_c
        alpha = (t + UDS_DAY_UNITS - last_c) / span if span else 0.0
        return last_w + (first_w - last_w) * alpha
    for i in range(len(ring) - 1):
        c0, w0 = ring[i]
        c1, w1 = ring[i + 1]
        if c0 <= t < c1:
            span = c1 - c0
            alpha = (t - c0) / span if span else 0.0
            return w0 + (w1 - w0) * alpha
    span = (first_c + UDS_DAY_UNITS) - last_c
    alpha = (t - last_c) / span if span else 0.0
    return last_w + (first_w - last_w) * alpha


def derive(uds_time: float) -> dict:
    """The whole semantic model for one clock reading."""
    part = day_part_at(uds_time)
    t = float(uds_time) % UDS_DAY_UNITS
    span = part["end"] - part["start"]
    return {
        "uds_time": round(t, 3),
        "clock": f"{int(t // 100):02d}:{int((t % 100) * 0.6):02d}",
        "day_part": part["id"],
        "day_part_alpha": round((t - part["start"]) / span, 4) if span else 0.0,
        "narrative_flag": part["flag"],
        LANE_PHASE: round(normalise_clock(t), 4),
        LANE_WARMTH: round(warmth_at(t), 4),
        "is_night": part["id"] in ("Night", "Nightfall"),
    }


# ---------------------------------------------------------------------------
# Editor-side reads. All read-only against UDS.
# ---------------------------------------------------------------------------
def _asset_ok(path: str) -> bool:
    leaf = path.rsplit("/", 1)[-1]
    return unreal.EditorAssetLibrary.does_asset_exist(f"{path}.{leaf}")


def _mpc_scalar_names(path: str) -> list[str]:
    if not _asset_ok(path):
        return []
    mpc = unreal.load_asset(path)
    if not mpc:
        return []
    return [str(s.get_editor_property("parameter_name"))
            for s in mpc.get_editor_property("scalar_parameters")]


def find_uds_actor():
    """The live Ultra_Dynamic_Sky actor in the open level, or None."""
    try:
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        for actor in eas.get_all_level_actors() or []:
            if "Ultra_Dynamic_Sky" in actor.get_class().get_name():
                return actor
    except Exception:
        pass
    return None


def read_live_uds_time():
    """Live clock: prefer the actor property, fall back to the UDS MPC scalar."""
    actor = find_uds_actor()
    if actor:
        try:
            return float(actor.get_editor_property(UDS_TIME_PROPERTY)), "actor"
        except Exception:
            pass
    if _asset_ok(UDS_MPC):
        try:
            mpc = unreal.load_asset(UDS_MPC)
            world = unreal.EditorLevelLibrary.get_editor_world()
            inst = world.get_parameter_collection_instance(mpc)
            ok, val = inst.get_scalar_parameter_value(UDS_TIME_SCALAR)
            if ok:
                return float(val), "mpc"
        except Exception:
            pass
    return None, "unavailable"


def set_uds_time(uds_time: float) -> bool:
    """Editor-only scrub. Disables Animate Time of Day so the write is not fought."""
    actor = find_uds_actor()
    if not actor:
        return False
    try:
        actor.set_editor_property("Animate Time of Day", False)
    except Exception:
        pass
    try:
        actor.set_editor_property(UDS_TIME_PROPERTY, float(uds_time) % UDS_DAY_UNITS)
    except Exception:
        return False
    for fn in ("Update Active Variables", "Update Material Effect Parameters"):
        try:
            actor.call_method(fn)
        except Exception:
            pass
    return True


def _pie_running() -> bool:
    try:
        return bool(unreal.get_editor_subsystem(
            unreal.UnrealEditorSubsystem).get_game_world())
    except Exception:
        return False


def apply_preview(values: dict) -> dict:
    """EDITOR PREVIEW ONLY. Never a runtime path -- see the single-writer note above.

    Refused while PIE is live, because during PIE the audio subsystem owns the
    palette and a second writer is exactly the defect this project already ate once.
    """
    if _pie_running():
        return {"applied": False, "reason": "PIE is running - palette is owned by "
                                            "UMelodiaAudioReactivePresentationSubsystem"}
    if not _asset_ok(MELODIA_MPC):
        return {"applied": False, "reason": f"missing {MELODIA_MPC}"}
    declared = set(_mpc_scalar_names(MELODIA_MPC))
    world = unreal.EditorLevelLibrary.get_editor_world()
    mpc = unreal.load_asset(MELODIA_MPC)
    written, skipped = {}, {}
    for lane in (LANE_PHASE, LANE_WARMTH):
        if lane not in declared:
            skipped[lane] = "not declared on the collection"
            continue
        try:
            unreal.KismetMaterialLibrary.set_scalar_parameter_value(
                world, mpc, lane, float(values[lane]))
            written[lane] = round(float(values[lane]), 4)
        except Exception as exc:
            skipped[lane] = str(exc)[:120]
    return {"applied": bool(written), "written": written, "skipped": skipped,
            "scope": "editor preview only"}


# ---------------------------------------------------------------------------
# Contract emission -- the artifact that survives into runtime.
# ---------------------------------------------------------------------------
def build_contract(declared: list[str]) -> dict:
    missing = [ln for ln in (LANE_PHASE, LANE_WARMTH, LANE_SEASON) if ln not in declared]
    return {
        "schema": "melodia.uds_time_bridge.contract.v1",
        "generated": datetime.now(timezone.utc).isoformat(),
        "source_of_truth": {
            "uds_mpc": UDS_MPC,
            "uds_scalar": UDS_TIME_SCALAR,
            "range": [0.0, UDS_DAY_UNITS],
            "note": "UDS owns the clock. Nothing here writes it.",
        },
        "runtime_owner": {
            "writer": "UMelodiaAudioReactivePresentationSubsystem",
            "rule": "single writer of MPC_Melodia_Palette; the day lane must be "
                    "published by it or by a read-only consumer of it, never by a "
                    "second writer",
            "python_is_not_runtime": "this script is editor-time only; Python does "
                                     "not exist in a packaged build",
        },
        "palette_lanes": {
            LANE_PHASE: {"range": [0.0, 1.0], "meaning": "midnight-to-midnight phase",
                         "declared": LANE_PHASE in declared},
            LANE_WARMTH: {"range": [-1.0, 1.0], "meaning": "cool..warm scene grade",
                          "declared": LANE_WARMTH in declared},
            LANE_SEASON: {"range": [0.0, 1.0], "meaning": "passthrough, not clock-derived",
                          "declared": LANE_SEASON in declared},
        },
        "undeclared_lanes": missing,
        "day_parts": DAY_PARTS,
        "transition_events": TRANSITION_EVENTS,
        "consumers": {
            "quests": {
                "api": "UMelodiaNarrativeSubsystem::SetNarrativeFlag(FName, bool)",
                "pattern": "on transition, set the entering part's flag true and the "
                           "leaving part's false; quest gates read the flag, never the float",
                "flags": [p["flag"] for p in DAY_PARTS],
            },
            "rhythm": {
                "api": "UMelodiaMusicClockSubsystem::GetSecondsToNextBeat / GetTempoBPM",
                "pattern": "quantise the transition to the next beat so a day change "
                           "lands musically instead of mid-bar",
            },
            "ui": {
                "api": f"{MELODIA_MPC} -> {LANE_PHASE} / {LANE_WARMTH}",
                "pattern": "UI materials sample the collection; no widget needs a tick",
            },
            "world_field": {
                "api": "MelodiaWorldFieldBus / FWorldFieldSample",
                "pattern": "day phase is a candidate field alongside Resonance/Tension",
            },
        },
        "sample_table": [derive(p["start"] + 1.0) for p in DAY_PARTS],
    }


def main() -> int:
    apply = "--apply" in sys.argv
    sweep = "--sweep" in sys.argv
    set_uds = "--set-uds" in sys.argv

    scrub = None
    if "--scrub" in sys.argv:
        i = sys.argv.index("--scrub")
        if i + 1 < len(sys.argv):
            try:
                scrub = float(sys.argv[i + 1])
            except ValueError:
                unreal.log_error("[UDS Bridge] --scrub needs a number, e.g. --scrub 1750")
                return 2

    declared = _mpc_scalar_names(MELODIA_MPC)
    contract = build_contract(declared)

    if scrub is not None and set_uds:
        contract["uds_scrub_applied"] = set_uds_time(scrub)

    live_time, source = read_live_uds_time()
    effective = scrub if scrub is not None else live_time

    report = {
        "schema": "melodia.uds_time_bridge.v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uds_present": _asset_ok(UDS_MPC),
        "uds_blueprint": UDS_BP if _asset_ok(UDS_BP) else None,
        "uds_actor_in_level": bool(find_uds_actor()),
        "live_uds_time": live_time,
        "live_source": source,
        "melodia_mpc": MELODIA_MPC if _asset_ok(MELODIA_MPC) else None,
        "lanes_declared": {ln: (ln in declared)
                           for ln in (LANE_PHASE, LANE_WARMTH, LANE_SEASON)},
        "contract_file": str(CONTRACT),
    }

    if effective is not None:
        report["derived"] = derive(effective)
        if apply:
            report["preview_write"] = apply_preview(report["derived"])
    else:
        report["derived"] = None
        report["note"] = ("No UDS clock readable - open a level containing "
                          "Ultra_Dynamic_Sky, or pass --scrub <0..2400> to derive offline.")

    if sweep:
        report["sweep"] = [derive(p["start"] + 1.0) for p in DAY_PARTS]

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    CONTRACT.write_text(json.dumps(contract, indent=2), encoding="utf-8")
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

    return 0 if report["uds_present"] and _asset_ok(MELODIA_MPC) else 1


if __name__ == "__main__":
    raise SystemExit(main())
