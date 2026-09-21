"""Sheep truth probe — read-only Monolith inspection of BP_ChoralSheep.

Run when the editor/Monolith is reachable:
  python Prototypes/JevSheepConductor/sheep_truth_probe.py

Never mutates anything. Uses only the native C++ reflection path
(get_cdo_properties / get_graph_data / exports), never Python glue
loading of Blueprint classes.

Answers (and writes sheep_truth_report.json, this folder only):
1. BP_ChoralSheep CDO: movement/rotation knobs, existing overlap or
   awareness radius, any gaze/look-at variable already authored.
2. Graph census: functions/events callable from outside (the authored
   execution path for TURN_TO_PLAYER), ABP state names if visible.
3. SK_ChoralSheep bones: head/neck socket for gaze weighting.
4. Wind: any wind actor/param already staged in a candidate map.
5. Melusina pawn: which pawn class the project possesses for the proof.

If Monolith is unreachable the probe exits 2 with no output files —
same clean-stop contract as the duet.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join("C:/EnvironmentPortfolio/BS_GodFile", "Tools"))

HERE = os.path.dirname(os.path.abspath(__file__))
SHEEP_BP = "/Game/Melodia/Companions/ChoralSheep/BP_ChoralSheep"
SHEEP_SK = "/Game/Melodia/Companions/ChoralSheep/SK_ChoralSheep"
SHEEP_ABP = "/Game/Melodia/Companions/ChoralSheep/ABP_ChoralSheep"


def main() -> None:
    try:
        from mcp_client import monolith
    except Exception as exc:
        print(f"TRUTH PROBE: cannot load Tools/mcp_client ({exc}).")
        raise SystemExit(2)
    ping = monolith("editor_query", {"action": "list_dirty_packages"})
    if isinstance(ping, str) and ping.startswith("ERROR:"):
        print("TRUTH PROBE: editor unreachable — "
              "dismiss any modal dialog and re-run. Nothing written.")
        raise SystemExit(2)

    report: dict = {"sheep_bp": SHEEP_BP, "calls": []}

    def ask(tool: str, action: str, params: dict, label: str) -> None:
        try:
            out = monolith(tool, {"action": action, "params": params})
        except Exception as exc:  # noqa: BLE001 — probe must never crash
            out = f"ERROR:{exc}"
        text = out if isinstance(out, str) else json.dumps(out)[:6000]
        report["calls"].append({"label": label, "tool": tool,
                                "action": action, "head": text[:3000]})
        print(f"--- {label} ---")
        print(text[:1500])

    # 1. CDO truth (never a dump-census claim: reflection only).
    ask("blueprint_query", "get_cdo_properties",
        {"blueprint": SHEEP_BP}, "sheep-cdo")
    # 2. Callable surface: graph list + entry points.
    ask("blueprint_query", "get_graph_data",
        {"blueprint": SHEEP_BP}, "sheep-graphs")
    # 3. Skeleton bones for gaze weighting.
    ask("mesh_query", "get_bones", {"mesh": SHEEP_SK}, "sheep-bones")
    # 4. ABP states (authored execution may live here).
    ask("blueprint_query", "get_graph_data",
        {"blueprint": SHEEP_ABP}, "sheep-abp-graphs")
    # 5. Candidate staging maps: is anything sheep-ready?
    for m in ("/Game/Melodia/Levels/Opening/L_MelusinaMorning",
              "/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap"):
        ask("editor_query", "get_level_actors", {"map": m}, f"actors-{m}")

    path = os.path.join(HERE, "sheep_truth_report.json")
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
