"""JEV DECISION PACKET - the house leg's authored decisions, 2026-10-22.

The owner said: "I don't really know; tbh. What does Jev think about those decisions?"
This packet is that answer. Closed candidate sets only - Jev selects, it does not
mutate Unreal, it does not place actors and it does not write the pipeline.

Per Docs/Production/JEV_CANONICAL_WORKFLOW.md sections 3-5: a closed candidate
set, explicit criteria, one judgment call at the decision boundary, the choice
recorded with its confidence and reason, and the execution left to the existing
owner lane (Monolith / PCG / the artist's own hands).

Every fact in STATE is measured, not assumed:
  - Saved/Audit/house_level_audit.json (169 actors, 0 issues)
  - specs/p0/melusina_house_p0_dressing_state.json (97 placements)
  - specs/p0/melusina_house_p0_fill.v1.json (the fill contract)
  - specs/p0/melusina_dressing_catalog.v1.json (the catalogue seed)
  - Saved/Audit/house_density_maps.json (the derived density textures)
  - the golden-walk plan (M00-M09) and the house leg M00-M05
"""
from __future__ import annotations

import json
import os
import sys

STATE = {
    "verified_at": "2026-10-22, offline audit + plan + depot evidence",
    "situation": (
        "Melodia's P0 house leg (L_MelusinaHouse_P0) is dressed and audited, and the "
        "pipeline that should make the NEXT rooms cheap does not exist yet. The house "
        "was assembled by hand: one Houdini room shell per room, PCG graphs dropped "
        "separately, 97 hand-placed props, and gameplay carriers borrowed from a Fab "
        "asset pack. The owner wants rooms that are placeable in one action, dressed "
        "in a way that knows the room it sits in, and able to carry the gameplay loop."
    ),
    "measured_state": {
        "actors_in_level": 169,
        "audit_issues": 0,
        "dressing_actors": 84,
        "dressing_base_layer": 64,
        "dressing_enchanted_interiors_layer": 20,
        "dressing_actors_that_are_movable": 82,
        "functional_interactables": 13,
        "houdini_room_shells": 13,
        "hand_placed_placements_recorded": 97,
        "placements_by_room": {"bedroom": 40, "landing": 8, "salon": 48},
        "fill_contract_species_rows": 9,
        "fill_contract_rooms": 3,
        "catalogue_seed_families": 4,
        "catalogue_seed_props": 97,
        "density_textures": "3 derived first passes exist (bedroom/landing/salon, 0.5 m/px)",
        "route_in_density_maps": "reconstructed from the carriers the artist placed, in beat order, not read from BP_PathSplineProvider",
        "runtime_proof": "the house leg has NEVER been walked in PIE",
    },
    "what_exists": [
        "Houdini room shell HDA (melodia::room_shell, 33 params) - the room's truth, 13 instances live",
        "PCGEx room graph PCG_MelusinaRoomShell_PCGex: PCGExCreateSpline + PCGExShapeBoundsSource + PCGExFilters - the room-aware plumbing",
        "the fill contract: 9 species rows, 3 rooms, the node chain, the exclusions - designed, NOT built",
        "the dressing state file: the artist's 97 placements as diffable data (label, class, mesh, location, rotation, scale, room, prop, tags)",
        "the catalogue seed: 4 families, 97 props, derived from the artist's own placements, keyed by the gameplay tags they already used",
        "the three density textures, derived from those placements with a 12 m kernel and the P0 route corridor cut back 4 m",
        "PCG<->narrative and PCG<->gameplay bridge components in C++ (not yet proven on this leg)",
    ],
    "what_is_missing": [
        "UMelodiaDressingSubsystem is a SCAFFOLD: all four functions log and return. DressHeroClutter places nothing, PhysicallyDrop enables no simulation, FindCompositionOccluders returns empty. There is no UMelodiaDressingCatalog class, so DA_MelodiaDressingCatalog has nowhere to live.",
        "BP_MelodiaRoomShell does not exist: there is no 'place a room' action. The house is hand-assembled.",
        "the fill graphs do not exist; only the contract for them does",
        "the house's beat carriers are BORROWED from a Fab pack: BP_InteractiveBook, BP_CandleFlame, BP_Crystal, BP_HiddenDoor, BP_Lantern. The project's own carriers are BP_MelodyToken_Universal and BP_SirPerch.",
    ],
    "the_house_leg_beats": {
        "M00": "Wake - bedside camera",
        "M01": "Notice - approach and inspect ONE of: the empty perch / the companion token / the desk",
        "M02": "First resonance - instrument, music-box or window chime: choose ONE existing compatible actor",
        "M03": "Threshold - the bedroom door opens to the larger house",
        "M04": "The house hums - the curved landing and one oval salon; frame the grand staircase",
        "M05": "Open the front door - the pause before the exterior reveal",
    },
    "constraints": [
        "The artist owns the editor. No agent closes, relaunches or takes it, and no second UE instance may run beside it.",
        "No script may move, replace or delete a hand-placed actor. The fill is additive only.",
        "One toon master only: everything the fill spawns uses the converted M_Master_Toon_Universal instances.",
        "The room kit's pivot, footprint and transition metrics are frozen once layout starts (a shipped-game lesson: changing them breaks every room that used the kit).",
        "The meter is fixed: 0.6 m module, 2.4 m bay, 128 BPM. One standard doorway system between room types.",
        "The C++ tree currently carries 39 dirty Source/ and Plugins/ paths from another session, so there is no clean compile window for the C++ work.",
        "The house leg has never been walked, so the walk is the gate that proves whatever is built.",
        "No more than 3 fill species legible in any one frame; cute accents stay under 5% of a frame.",
    ],
}

QUESTIONS = {
    "carrier_slot": {
        "question": (
            "In the room kit Blueprint (BP_MelodiaRoomShell), how should the room's gameplay "
            "carrier - the interactable that carries the beat - be owned?"
        ),
        "criteria": {
            "A": "The carrier is a FIXED CHILD of the kit: dropping the room brings its "
                 "interactable with it, at a transform the kit defines. One action places a "
                 "complete, playable room.",
            "B": "The carrier stays an INDEPENDENT actor that the artist placed; the kit only "
                 "references it (a slot) and never owns, parents or moves it. The artist's "
                 "arrangement of the interactables stays exactly as it is.",
            "C": "The carrier is a child, but its transform is authored IN THE LEVEL and the kit "
                 "only supplies the default: the kit proposes, the level disposes.",
            "D": "The kit owns NO carrier at all: interactables remain hand-placed actors, and "
                 "the kit is geometry plus fill only. The loop stays in the artist's hands and "
                 "the level is not 'complete' when it is dropped in.",
        },
    },
    "density_paint": {
        "question": (
            "The three room density textures now exist as a DERIVED first pass (the artist's "
            "own 97 placements splatted with a 12 m kernel, the P0 route corridor cut back "
            "4 m). What should happen to them?"
        ),
        "criteria": {
            "A": "PAINT OVER the derived pass. It is a legitimate starting field - density "
                 "gathers where the furniture already is - and it saves painting from black. "
                 "The artist's paint is what makes it authored.",
            "B": "PAINT FROM SCRATCH. The derived field encodes the BASE layer (desks, "
                 "shelves), which is not the fill's density; painting over it risks baking "
                 "the base arrangement into the scatter.",
            "C": "USE IT AS-IS for the first graph build to prove the pipeline end to end, "
                 "then repaint once the graph is visible. Proof before authorship.",
            "D": "DO NOT PAINT AT ALL: derive the field from the fill contract's per-species "
                 "densities instead (a uniform field per species, modulated by the room "
                 "bounds), and let the art direction come from the species table alone.",
        },
    },
    "mobility": {
        "question": (
            "82 of the 84 dressing actors are MOVABLE, which means no static lighting and no "
            "occlusion culling on them. Does 'game-ready level' require the static conversion, "
            "and if so, when?"
        ),
        "criteria": {
            "A": "CONVERT BEFORE the walk: make the dressing static as part of making the leg "
                 "game-ready. The artist can unlock any actor temporarily to move it. Static "
                 "lighting and occlusion are worth it for a shipping level.",
            "B": "AFTER the walk: keep them movable for the art pass, because the walk and the "
                 "art pass are exactly when things still move. Static conversion is a later, "
                 "separate pass once the composition stops changing.",
            "C": "SPLIT BY LAYER: the base layer (64 actors: desks, shelves, architecture) goes "
                 "static now - it will not move again - while the fill and hero props stay "
                 "movable. The static set is decided by the layer, not by a blanket rule.",
            "D": "NOT PART OF 'GAME-READY': mobility is a cook and performance-budget decision "
                 "taken with the perf target, not a level-status decision. The walk gate stays "
                 "free of it.",
        },
    },
    "carrier_ownership": {
        "question": (
            "The house's beat carriers are borrowed Fab-pack Blueprints (BP_InteractiveBook, "
            "BP_CandleFlame, BP_Crystal, BP_HiddenDoor, BP_Lantern). The project's own are "
            "BP_MelodyToken_Universal and BP_SirPerch. What should happen to that?"
        ),
        "criteria": {
            "A": "REPLACE ALL of them with project-owned Blueprints before the walk: the loop "
                 "the project ships must not depend on a pack's naming or a pack's roadmap.",
            "B": "KEEP the borrowed carriers for the walk - they satisfy the beat contract "
                 "today - and migrate to project-owned in a later, separate pass.",
            "C": "REPLACE ONLY the M02 resonant object with the project's token family (the "
                 "beat asks for 'one existing compatible actor'), and keep the book and the "
                 "crystal as they are for now.",
            "D": "KEEP them permanently and document the pack dependency openly: the house leg "
                 "ships with pack actors, the project's token family is used elsewhere.",
        },
    },
    "first_build": {
        "question": (
            "The plan's critical path is W1 (catalogue class + asset) -> W5 (fill graphs) -> "
            "W4 (room kit) -> W6 (carriers) -> W7 (the walk). W1 and W3 need a C++ build and "
            "the tree is dirty from another session. What should be built FIRST, tomorrow, "
            "given the editor is the artist's and the walk is the gate?"
        ),
        "criteria": {
            "A": "W5 (the fill graphs + the density paint) first: it is editor-side, needs no "
                 "C++, and it is what makes a room look dressed - the fastest visible win and "
                 "the thing that shows the artist whether the pipeline is worth continuing.",
            "B": "W1 (the catalogue class and asset) first: the art pass is entirely dark "
                 "without it, the catalogue content is already derived and ready, and it "
                 "unlocks W2 and W3 in the same build.",
            "C": "W4 (the room kit Blueprint) first: it is the single 'place a room' action "
                 "the whole pipeline is missing, and everything else hangs off it.",
            "D": "W6 (the carriers) first: the borrowed Fab-pack actors are the largest "
                 "dependency risk on the leg, and replacing them makes the loop ours before "
                 "anything else is built on top of them.",
        },
    },
}


def jev_available() -> bool:
    if not os.environ.get("TYPESAFE_API_KEY"):
        return False
    try:
        import typesafe_sdk  # noqa: F401
        return True
    except ImportError:
        return False


def main() -> int:
    print("=" * 72)
    print("JEV DECISION PACKET - the house leg's authored decisions 2026-10-22")
    print("=" * 72)
    if not jev_available():
        print("\n[!] Jev unavailable (TYPESAFE_API_KEY / typesafe_sdk).")
        print("    Fallback would be a COMPOSED GUESS, not Jev evidence.")
        return 2
    from typesafe_sdk import TypeSafeClient
    from typesafe_sdk._core.questions import Choice

    # The criteria TEXT must be sent. Passing {option: None} makes the packet
    # uninformed - the service sees four empty options and answers arbitrarily.
    # (The first run of this packet did exactly that and returned "A" for all
    # five questions with no reason.)
    questions = {qid: Choice(instructions=spec["question"],
                             criteria=dict(spec["criteria"]))
                 for qid, spec in QUESTIONS.items()}
    with TypeSafeClient() as client:
        result = client.system_one(state={"verified_state": STATE,
                                          "constraints": STATE["constraints"]},
                                   questions=questions)
    out = {
        "schema": "melodia.jev.house_dressing_decisions.v1",
        "source": "jev-live",
        "state_verified_at": STATE["verified_at"],
        "questions": {qid: spec["question"] for qid, spec in QUESTIONS.items()},
        "criteria": {qid: spec["criteria"] for qid, spec in QUESTIONS.items()},
        # The answer carries choice + confidence + a full probability
        # distribution. There is NO reason/rationale field on this model
        # (jev-1.14.0) - an earlier version of this script looked for .reason
        # and .score and recorded nulls, which looked like "no confidence"
        # when the confidence was there all along.
        "answers": {qid: {"choice": a.choice,
                          "confidence": getattr(a, "confidence", None),
                          "probabilities": getattr(a, "probabilities", None)}
                    for qid, a in result.answers.items()},
        "model": getattr(result, "model", None),
        "usage": str(getattr(result, "usage", None)),
    }
    dest = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "Saved", "Audit", "house_dressing",
        "JevHouseDressingDecisions_20261022.json"))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    print("\n=== JEV ===")
    print(json.dumps(out["answers"], indent=1, ensure_ascii=False))
    print("\nreceipt:", dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
