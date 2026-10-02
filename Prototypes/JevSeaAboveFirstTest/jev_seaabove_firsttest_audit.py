"""Jev Sea Above first-test audit — isolated prototype (2026-09-25).

ISOLATION (per Prototypes/JevMorningRenderPlan precedent):
- Everything lives in Prototypes/JevSeaAboveFirstTest/. Delete this folder to remove it.
- NO .uasset/.umap writes. NO editor mutations. NO ledger writes.
- Jev selects ONLY among the authored option sets below. It never generates
  content, commands, or parameters beyond the closed sets.
- Provenance: source="jev-live" or "classical-fallback" plus reason. Fallback
  runs without TYPESAFE_API_KEY and is NOT Jev evidence.

Skill: typesafe-ai. Choice + Noul + Score go in ONE system_one call over the
same state; code owns the log. Full distributions preserved per evaluation.

Question: first Higgsfield pipeline test for Monolith 01 The Sea Above,
beat A (Calm littoral) — what to generate first and what is riskiest.
Facts from disk audit 2026-09-25 (no editor mutations; map NOT opened):
LV_SeaAbove_Prototype.umap 14.5KB mtime 09-04, no __ExternalActors__;
Reef kit staged (~35 textures, ~30 meshes, 24 MIs, 2 jelly BPs,
8 water MIs, 1 Niagara, Gaea terrain set, 4 DataLayers, 3 VDBs);
NO pulse-writer BP on disk; NO membrane mesh/material placed;
Chapter 02 route drafted, allowlist delta NOT in DA yet.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

OUT = Path(__file__).parent / "audit_log.json"

STATE = {
    "objective": "First Higgsfield pipeline test: Monolith 01 The Sea Above, "
                 "beat A (Calm littoral) — 2 environment stills + optional "
                 "motion test, then UE blockout inside the existing prototype.",
    "map": "LV_SeaAbove_Prototype.umap 14.5KB, mtime 2026-09-04, "
            "no __ExternalActors__ (small embedded-actor map, NOT opened).",
    "kit_staged": "Reef kit on disk: ~35 textures, ~30 mesh uassets, 24 MIs "
                   "(CoralSkin/2S, Kelp, Sand, WetRock, Jelly Bell/Arms, "
                   "Leviathan, Organ Pipe, Banner/Shroud), 2 jelly holder BPs, "
                   "8 water MIs (FalseOcean/SurfaceOcean), 1 Niagara "
                   "(UpwardDroplets prototype), Gaea terrain set, 4 DataLayers, "
                   "3 VDB volumes.",
    "pulse_writer": "ABSENT from disk: no BP_SeaAbove_PrototypeDirector, no "
                     "BP_SeaAbovePulseDriver, no membrane mesh/material placed. "
                     "Chapter 02 'membrane pulse 16s live' claim UNVERIFIED.",
    "route": "Chapter 02 Shorewake Calling drafts KaleidoNave -> prototype "
              "travel; allowlist delta in encounters.json, NOT authored into "
              "DA_MelodiaIntegrationConfig yet.",
    "guards": "Prototype map only; no saves to L_MelusinaMorning; no new "
               "subsystem; one editor (PID 6396 live); Higgsfield CLI 1.1.26 "
               "authed; 8 skills installed.",
}

QUESTIONS = {
    "first_test": {"type": "choice",
        "instructions": (
            "Melodia Melusina — first Higgsfield pipeline test for Sea Above "
            "beat A. Disk truth: the Reef kit is staged but nothing proves "
            "placement; the pulse-writer BP is absent so no live pulse answers "
            "anything yet; the map file is small and untouched since 09-04. "
            "Which FIRST TEST buys the most blockout value at least cost?"
        ),
        "criteria": {
            "STILLS_ONLY": "Generate 2 environment stills (calm littoral + "
                            "split-horizon coast) and stop. Cheapest; proves "
                            "art direction against the toon/Nikki palette "
                            "before any motion spend.",
            "STILLS_PLUS_VIDEO": "2 stills, then one short image-to-video "
                                  "motion test off the winner (membrane "
                                  "breath, hesitating rain). Proves the full "
                                  "image->video->blockout loop in one pass.",
            "FULL_LOOP_WITH_BLOCKOUT": "Stills + video + audio bed + UE "
                                        "blockout in the same session. "
                                        "Fastest to a placed cell; risks "
                                        "blockout rework if refs drift.",
            "HOLD_FOR_PULSE_WRITER": "Do not generate yet: land the missing "
                                      "pulse-writer BP first, since generated "
                                      "refs of a 'living pulse' cannot be "
                                      "judged against a system that is absent.",
        }},
    "riskiest": {"type": "choice",
        "instructions": "Which single assumption is most likely to break the Sea Above beat-A first test?",
        "criteria": {
            "PULSE_WRITER_ABSENT": "The plan assumes a live membrane pulse the "
                                    "song answers; no writer BP exists on "
                                    "disk, so motion refs and blockout timing "
                                    "have no live counterpart.",
            "MAP_STATE_UNKNOWN": "The umap is 14.5KB untouched since 09-04 and "
                                  "was not opened; the beat-A cell may not "
                                  "exist and blockout may start from near-empty.",
            "KIT_NOT_PLACED": "The Reef kit is staged files only; placement "
                               "density, composition, and palette fit in the "
                               "prototype are unproven.",
            "HIGGSFIELD_STYLE_DRIFT": "Generated stills/video may fight the "
                                       "toon/Nikki lookdev (iridescence, "
                                       "pastel bands) and mislead blockout.",
            "NONE_MATERIAL": "No assumption is materially risky; proceed as written.",
        }},
    "needs_owner": {"type": "noul",
        "instructions": "Does the Sea Above first test need owner decisions before agents generate, or can it run agent-side with the owner only eyeballing the result?",
        "criteria": {
            "true": "Owner-load-bearing: generated refs set the Monolith's "
                     "visual identity and the beat-A framing is a taste call; "
                     "agents generate, owner approves before blockout.",
            "false": "Agent-runnable; the owner only eyeballs the result.",
        }},
    "readiness": {"type": "score",
        "instructions": "Readiness 0-4 for the Sea Above beat-A first test (refs generated, blockout placed in prototype, no Morning touched).",
        "criteria": [
            "Nothing: no refs, kit unstaged.",
            "Kit staged on disk; no refs generated; map state unverified.",
            "Refs generated and owner-approved; kit staged; pulse writer still absent.",
            "Blockout cell placed in prototype from approved refs; pulse writer landed.",
            "Beat-A cell dressed and PIE-proven; playlist for beats B-E sequenced.",
        ]},
}


def main() -> None:
    key = os.environ.get("TYPESAFE_API_KEY")
    log = {"schema": "melodia.jev_seaabove_firsttest_audit.v1",
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
