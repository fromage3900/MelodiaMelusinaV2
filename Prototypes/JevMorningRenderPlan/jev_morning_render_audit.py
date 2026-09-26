"""Jev Morning render quick-wins audit — isolated prototype (2026-09-24).

ISOLATION: everything lives in Prototypes/JevMorningRenderPlan/. No .uasset/.umap
writes, no editor mutation. Jev picks only among the closed option sets below.
Provenance: source="jev-live" or "classical-fallback" (fallback is NOT Jev evidence).
SDK typesafe_sdk 0.7.0 (TypeSafeClient + Choice/Noul/Score), same call shape as
Prototypes/JevPCGConvergenceAudit (jev-1.13.0, ran live 2026-09-24).

Question: quickest wins — creative pipeline + World Compiler integration — for
tonight's L_MelusinaMorning renders (portfolio pass, "hire this person" bar).
Facts from: CURRENT_STATE.md; Saved/Portfolio/ContactSheets_20260924/S2/ (draft v1 +
4 CAM_Hero tiles, 05:06 today); .hermes/plans/2026-09-24_184500-pcg-convergence-plan.md;
Docs/PCG/MELODIA_PCG_SCHEMA.md; Saved/Audit/Screens (09-24 WC boards).
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

OUT = Path(__file__).parent / "audit_log.json"

STATE = {
    "objective": "tonight's L_MelusinaMorning renders — portfolio pass ('hire this person' bar)",
    "s2_draft_v1": "Saved/Portfolio/ContactSheets_20260924/S2/S2_Melusina_HeroCams_DRAFT_v1.jpg (05:06 today; tiles: CAM_Hero_01 Meadow / 02 Spiral Ascent / 03 Rim Overlook / 04 House)",
    "s2_open_defects": [
        "white placeholder mannequin + black animal in frame (tiles 1/4)",
        "rock underside reads purple/incomplete (tile 3)",
        "cyan-emissive house frame overbright (tile 4)",
        "draft header: texture streaming still settling at capture",
    ],
    "new_content_since_draft": "island biome 992 inst (Massive World), crystal garden 205, WestRim art rocks 25 (greybox gone), rainbow glitter 57, golden spiral treads",
    "meadow_flowers_material": "default (no rainbow); PCGEx mesh collections (C2) are the decided fix; convergence gate = flowers spawn rainbow MIs through a collection",
    "world_compiler": "boards recaptured 2026-09-24 (Saved/Audit/Screens/wc_morning_rainbow_bloom_*_2026-09-24.png); plaza slice staged in recipe (7 slots / 15 curves / 610 samples), NOT baked or hosted in UE",
    "capture_path": "PIE capture with fill light = proven; MRQ stills untested on this box",
    "melusina": "face dark in lit shots (open; shots mostly third-person, owner option 3); doll-rig preview on island-09",
    "editor": "DOWN; another agent session live on the machine (MultiWorld probe)",
    "guards": "AAA-only in shipped sheets; owner frames finals; one editor; no new systems",
    "time_budget_hours": 4,
}

QUESTIONS = {
    "first_block": {"type": "choice",
        "instructions": (
            "Melodia Melusina — tonight's Morning renders for the portfolio pass. At 05:06 today "
            "an S2 contact-sheet draft v1 was captured from four hero cams (Meadow, Spiral Ascent, "
            "Rim Overlook, House). Since then live: island biome 992, crystal garden 205, WestRim "
            "art rocks 25 (greybox gone), glitter 57, golden spiral. The meadow's biome flowers "
            "still wear the default material — PCGEx mesh collections (C2) are the decided rainbow "
            "fix. The World Compiler plaza slice is staged but not baked or hosted. Open draft "
            "defects: placeholder pawn+animal in frame, a purple rock underside, an overbright "
            "cyan frame, unsettled streaming. Which FIRST BLOCK buys the most portfolio value at "
            "least risk?"
        ),
        "criteria": {
            "S2_V2_RECAPTURE_FIRST": "Fix the three defects and recapture the four hero cams with today's new content. Advances the owner's own sheet; lowest risk; newest content visible tonight.",
            "RAINBOW_MEADOW_C2_FIRST": "Land C2 first — PCGEx collection + per-entry rainbow MIs through the biome core, gate-proven (live A/B, no stale cache) — then recapture. Wide tiles gain the seven-band palette; the tile doubles as pipeline evidence.",
            "PLAZA_INTEGRATION_FIRST": "Bake the kit (bevel/arch/roof), GLB->Interchange, host PCG_WorldCompiler_Structures + BP_MelodiaPCGControl, live ground check, frame it. Loudest World-Compiler-integration story; the kit is a greybox shell and may not clear the AAA bar tonight.",
            "PIPELINE_STORY_FIRST": "Assemble pipeline-evidence assets (one graph -> three biomes; recipe -> compiler boards; greybox->art before/after; 09-24 boards) plus two clean hero stills. Sells the systems brain; weakest as pure beauty.",
        }},
    "riskiest": {"type": "choice",
        "instructions": "Which single assumption is most likely to break tonight's render plan?",
        "criteria": {
            "OPEN_DEFECTS_EXCEED_TONIGHT": "The draft's defects (placeholders in frame, purple material, overbright emissive, unsettled streaming) may need asset-level fixes beyond tonight; finals then ship placeholders or lose content.",
            "C2_SCRIPTING_GAPS": "Collection authoring + core rewiring hit the known scripting gap (params/pins not scriptable; save+reload, pins rebuild); C2 could eat the night.",
            "PLAZA_KIT_QUALITY": "The kit is a greybox shell and the bake pass has unproven timing; a half-built house in a portfolio render is worse than none.",
            "CHARACTER_LOOK_DARK": "Character-forward tiles depend on lit readability; the face reads dark (open) and the doll companion is a preview asset.",
            "EDITOR_STABILITY_AND_LOCK": "Today: one OOM crash + one unlogged exit; another session is live. A collision or a mid-capture death costs the render window.",
        }},
    "needs_owner": {"type": "noul",
        "instructions": "Do tonight's renders require owner decisions before anything can ship, or can it all run agent-side with the owner only eyeballing the result?",
        "criteria": {
            "true": "Owner-load-bearing: final framing is owner-framed, placeholder handling is an owner taste call, and the sheet is owner-eyeballed before upload.",
            "false": "Agent-runnable tonight; the owner only eyeballs the result.",
        }},
    "readiness": {"type": "score",
        "instructions": "Readiness 0-4 for tonight's Morning render objective (portfolio-graded S2 pass, new procedural content visible, no placeholder assets in final tiles).",
        "criteria": [
            "Nothing: no cameras, no draft.",
            "Cameras + one draft exist; new content not in any capture yet.",
            "Cameras + draft + new content live; recapture path proven; three open defects.",
            "v2 recaptured clean; one pipeline quick win (C2 or plaza) visible in tiles.",
            "Sheet final-ready: defects resolved, pipeline win visible, owner-approved.",
        ]},
}

def main() -> None:
    key = os.environ.get("TYPESAFE_API_KEY")
    log = {"schema": "melodia.jev_morning_render_audit.v1",
           "date": datetime.now().isoformat(timespec="seconds"), "state": STATE}
    if not key:
        log.update(source="classical-fallback",
                   reason="TYPESAFE_API_KEY missing — NO Jev ruling")
    else:
        from typesafe_sdk import TypeSafeClient, Choice, Noul, Score
        q = {}
        for k, v in QUESTIONS.items():
            cls = {"choice": Choice, "noul": Noul, "score": Score}[v["type"]]
            q[k] = cls(instructions=v["instructions"], criteria=v["criteria"])
        with TypeSafeClient(api_key=key) as client:
            resp = client.system_one(state=STATE, questions=q)
        ans = {}
        for k, a in resp.answers.items():
            ans[k] = a.model_dump() if hasattr(a, "model_dump") else dict(a)
        log.update(source="jev-live", model=resp.model, answers=ans)
    OUT.write_text(json.dumps(log, indent=2, default=str), encoding="utf-8")
    print("model:", log.get("model"), "| source:", log["source"])
    for k, a in log.get("answers", {}).items():
        t = a.get("type")
        if t == "choice":
            top = sorted(a["probabilities"].items(), key=lambda i: -i[1])[:3]
            print(f"{k}: {a['choice']} (conf {a['confidence']:.2f}) "
                  f"{[(n, round(p, 3)) for n, p in top]}")
        elif t == "noul":
            print(f"{k}: noul {a['noul']:.2f}")
        else:
            print(f"{k}: score {a.get('score')} (conf {a.get('confidence')})")


if __name__ == "__main__":
    main()