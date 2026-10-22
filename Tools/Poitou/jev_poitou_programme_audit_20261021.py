"""JEV DECISION PACKET - Poitou programme completeness audit + frontier priority, 2026-10-21.

Closed candidate sets only. Jev selects; it does not mutate Unreal. Execution
goes through the existing owner lanes; independent evidence proves the result
(Docs/Production/JEV_CANONICAL_WORKFLOW.md section 5).

This is the SECOND Jev packet of the session. The first
(jev_poitou_level_audit_20261021.py) ruled on the restore and produced
RESTORE_ALL_18_FROM_SNAPSHOT / HEADLESS_COOK_CHECK_ONLY /
NEW_ASSETS_ONLY_NO_EXISTING_MUTATION / REPAIR_AND_PROVE_LEVEL_FIRST_THEN_EXPAND.
This one audits the PROGRAMME against its original goal and the project's own
reference docs, and asks for the order a frontier model should work in.

Every fact below is verified on disk this session.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any

STATE = {
    "verified_at": "2026-10-21, disk + log + cook-check evidence",
    "original_goal": (
        "Expand the Poitsu HDA so that the canal, the house foundations and the brick are all "
        "authored IN THEME and PROCEDURALLY, on the French-Romanesque grammar, headlessly, with "
        "CAD/architecture research behind it."
    ),
    "what_is_built_and_gated": (
        "Tools/Poitou/snip/kit.vex is the shared grammar (0.6 m module and course, 2.4 m bay, "
        "0.45 m ashlar leaf over 0.9 m rubble core, a chaine/arase band every 3 courses through "
        "the full thickness, a rusticated refend base, 2 cm dry joints, semicircular arches, "
        "vertex paint R=lime-wash G=damp B=moss A=ivy). Seven generators include it: revet.vex "
        "(the canal-du-Midi section: two retaining walls and the central impermeable barrier, "
        "329,439 prims), abbey.vex (Maillezais: 7-bay nave, 1080 westwork, narthex, gallery on "
        "belt arches, splayed buttresses, apse, gable roof), found.vex (the soubassement under "
        "every house, 150,984 prims), lane.vex (2.4 m ribbons with kerbs that dodge the houses), "
        "cross.vex (lane crossings: deck, parapet, piers), roof.vex (low-pitch canal tile with "
        "per-course hue jitter), poplar_gen.vex (tapering trunk + columnar crown). 596,382 "
        "generated prims; the gate names all 18 element groups, so a generator that stops emitting "
        "is a failure. The Houdini-side gate is GREEN: 0 of 10 instanced meshes mismatched "
        "against their measured size."
    ),
    "what_the_gate_does_not_check": (
        "The gate asserts EMISSION, not PLACEMENT or APPEARANCE. It cannot tell that the abbey is "
        "where the walk sees it, and no generated geometry has been seen in Unreal by anyone, "
        "including the agent that wrote it."
    ),
    "audited_gaps_against_the_original_goal": [
        "CANALS: the revetment exists, but the canal-du-Midi system is only its retaining walls. "
        "Missing: the maison eclusiere (11-12 x 7-8 m), the quay walls, the tarred-oak jetty and "
        "pilings, the bank steps down to the water, the mooring rings, the duckweed surface. The "
        "style contract's MEL_retaining_wall wants a quay 0.6-1.5 m above the water; the "
        "generator currently runs 0.9-2.4 m.",
        "FOUNDATIONS: found.vex lays a generic 4-course ring under every house. Missing: the "
        "balais barn foundations and their half-timber walls, the per-house steps, the quereux "
        "variants, and the style contract's damp baseboard is 0.4-0.8 m where the generator "
        "lays 1.2 m. The 105 houses are still ONE instanced mesh with no generated detail.",
        "BRICK: the chaine/arase band is a plain course of boxes. There is no brick BOND - no "
        "header/stretcher alternation, no per-brick size or colour variation, and the rubble core "
        "behind the leaf is a plain box, not rubble. So 'brick generation' is a band, not a "
        "system.",
    ],
    "audited_gaps_against_the_project_reference_docs": [
        "Docs/Poitou/poitou_layout/HOUDINI_ENGINE_LIVE_CONVERGENCE_SPEC.md specifies a whole HDA "
        "SUITE with a dual-stage cook (preview_mode = lightweight proxy under 45 ms, production "
        "Nanite bake 800-1200 ms) and the attribute set unreal_nanite_enabled, "
        "unreal_collision_mode, unreal_output_name on every generated prim. The generators emit "
        "none of those attributes and have no preview mode, so the editor cannot iterate them.",
        "The same spec wants the abbey on a 105 x 32 m footprint with wall_thickness 1.8, "
        "window_style as a menu (Romanesque round / Early Gothic lancet / Rayonnant rose), "
        "buttress_tiers 3 and decay_intensity 0.45, driven by an UNREAL SPLINE input 0 and a "
        "volume brush input 1 that crumbles the ruin where the brush is. The generator has fixed "
        "geometry at a hardcoded centre and no brush.",
        "style_contract.md section 3c: the piano-walkway system ALREADY EXISTS (C++ "
        "PCGPianoKeyboard, PCG_PianoWalkway_WestRim, PCG_PianoKeyRun_2Oct, DA_PianoWalkway_*), "
        "and the contract says to REUSE it and only add a DA_PianoWalkway_Poitou variant plus "
        "MI_PianoKey_Poitou_Oak/_Tarred. cross.vex instead invented a new deck/parapet/pier "
        "generator - a parallel system where one already existed.",
        "style_contract.md section 3a also wants MEL_wall_straight/_corner/_with_door/_with_window/"
        "_multi_window/_t_join (quereux walls, enclos, gable fills), MEL_half_timber_wall for the "
        "balais barns and jetty sheds (W 4.8-9.6, H 3.0-5.0, step drop 0.6-1.2 toward the "
        "water), and round-arched openings only, never an ogive. None of these variants exist.",
        "style_contract.md section 4 (the musical motif allow/ban by distance band) is entirely "
        "unimplemented: bay spacing as the far-band metre, poplar spacing 6-7 m, bell-tower "
        "louvres reading as dark stripes, rail posts at bar spacing, archivolt chords, octave "
        "dark boards on bridges, organ-pipe louvre gradation, carved capitals, corbel musicians, "
        "ironwork shutter hinges as clef scrolls, door knockers. This is half the art direction "
        "and it is cheap, because it is detail ON the silhouette the kit already builds.",
        "style_contract.md section 5 palette and the MA palette DISAGREE by 2-4% per slot "
        "(e.g. lime wash #E9E3D3 vs #E6DFCC, limestone quoin #D8CBAE vs #D9C9A3, roof tile "
        "#B56A4A vs #C07A57, shutter green #8FAE9B vs #9DB8A5, tar #2A2622 vs #26221E, moss "
        "#5E6B3A vs #5F6B3B, oak #A88D6A vs #A58A66). The 8 MIs authored this session used the "
        "MA values; the style contract is the style authority.",
        "INFINITY_NIKKI_BRIEF_v2.md is a 20-rule contract, and two of its rules are in direct "
        "tension with what was built: rule 9 says foliage, reeds and poplars are PCG-only and "
        "HERO assets (abbey, punts, piano walkway, bridges) are hand-placed, so the GENERATED "
        "poplar may be the wrong kind of thing to generate; and rule 2 says environment lighting "
        "is PBR/Lumen and no unlit toon shaders, while the whole material programme is MIs of "
        "M_Master_Toon_Universal, whose shading model has never been checked.",
        "Other unproven Nikkie rules that are cheap to assert: a secondary landmark within 200 m of "
        "any point (rule 8), vignettes within 6 m separated by >=12 m of quiet (rules 5, 10), "
        ">=2 layered historical styles per zone (rule 18), ornament scale 1.3-1.5x (rule 13), "
        "albedo within 0.08-0.85 linear (rule 3), and the abbey readable from >=70% of the "
        "walkable area (rule 7 - the HDA's own abbey_sightline check reads 93.9%).",
        "The lookbook itself is unfinished: 6 of the 7 poitou_board plates fail the repo's own "
        "lookbook gate, and rule 16 wants a weekly benchmark against 3 locked reference frames.",
    ],
    "the_process_failures_the_next_agent_must_not_repeat": [
        "A headless cook of the HDA proves the HDA, not the LEVEL. The level's cook result is a "
        "separate fact, and Tools/Editor/poitou_he_cook_check.py now reads it.",
        "Never mutate an asset a live level depends on. Additive only: new files, new outputs, "
        "new materials left unbound until the owner approves binding.",
        "Never remove content before its replacement is live.",
        "A check that finds no evidence must FAIL, not pass.",
        "Prove one element end-to-end and LOOK at it before writing the other six.",
    ],
    "ue_side_state": (
        "The level's Poitou_Layout_v6 actor cooks a stale embedded HDA and its cook has been "
        "failing; the 18 mesh bindings it depended on have been restored to their measured "
        "pre-session state. The owner's editor must re-cook and add two output slots "
        "(output_masonry, output_generated). The Houdini Engine asset exposes no editable "
        "properties to Python, so that step cannot be done headlessly."
    ),
}

QUESTIONS: dict[str, dict[str, Any]] = {
    "canals_verdict": {
        "question": (
            "For the original goal's CANALS strand, what is the honest verdict on what exists, "
            "and what is the smallest honest next step?"
        ),
        "criteria": {
            "COMPLETE_ENOUGH_TO_MOVE_ON": 0,
            "PARTIAL_NEEDS_LOCKHOUSE_JETTY_AND_STEPS": 0,
            "SHALLOW_NEEDS_THE_WATER_EDGE_BUILT_OUT": 0,
        },
    },
    "foundations_verdict": {
        "question": (
            "For the original goal's HOUSE FOUNDATIONS strand, what is the honest verdict, and "
            "what is the smallest honest next step?"
        ),
        "criteria": {
            "COMPLETE_ENOUGH_TO_MOVE_ON": 0,
            "PARTIAL_NEEDS_HOUSE_SHELL_AND_BALAIS": 0,
            "SHALLOW_NEEDS_REAL_FOUNDATION_TYPES": 0,
        },
    },
    "brick_verdict": {
        "question": (
            "For the original goal's BRICK GENERATION strand, what is the honest verdict on the "
            "chaine/arase band versus a real brick bond, and what should the next agent build?"
        ),
        "criteria": {
            "BAND_IS_ENOUGH_FOR_SILHOUETTE": 0,
            "NEED_A_REAL_BOND_GENERATOR": 0,
            "NEED_BOND_AND_RUBBLE_CORE_PATTERN": 0,
        },
    },
    "priority_order": {
        "question": (
            "What order should a frontier model work in from here, given the level is unproven "
            "until the owner re-cooks it, the gate checks emission but not placement, and the "
            "reference docs specify a dual-stage preview/Nanite cook, a spline+brush abbey, "
            "reuse of the existing piano-walkway system, the musical-motif layer, and a palette "
            "that the MIs currently disagree with?"
        ),
        "criteria": {
            "WIRE_AND_PROVE_FIRST_THEN_SPEC_FEATURES": 0,
            "SPEC_FEATURES_FIRST_THEN_WIRE": 0,
            "PLACEMENT_ASSERTIONS_AND_ONE_SCREENSHOT_FIRST": 0,
        },
    },
    "reuse_vs_bespoke": {
        "question": (
            "For the systems the project already owns - the MEL_* wall builders, the "
            "MEL_math_gothic_cathedral kit, the piano-walkway PCG system, the existing MelodiaRoomShell "
            "HDAs - should the next agent reuse them, extend the kit, or keep generating bespoke "
            "geometry in the layout HDA?"
        ),
        "criteria": {
            "REUSE_EXISTING_SYSTEMS_FIRST": 0,
            "EXTEND_THE_SHARED_KIT": 0,
            "HYBRID_REUSE_FOR_HERO_KIT_FOR_DETAIL": 0,
        },
    },
    "poplar_and_material_conflicts": {
        "question": (
            "Two conflicts need a ruling: the Nikkie contract says poplars and foliage are PCG-only "
            "while the programme generates poplar geometry, and it says environment lighting is "
            "PBR/Lumen while the whole material programme is MIs of M_Master_Toon_Universal whose "
            "shading model was never checked. How should the next agent resolve them?"
        ),
        "criteria": {
            "GENERATE_POPLAR_AS_HERO_BUT_KEEP_PCG_FOR_FAR_BANDS": 0,
            "POPLARS_BACK_TO_PCG_ONLY": 0,
            "CHECK_THE_MASTER_SHADING_MODEL_FIRST_THEN_DECIDE": 0,
        },
    },
    "palette_authority": {
        "question": (
            "The style contract's palette and the Material Artist's palette differ by 2-4% per "
            "slot. Which is the authority for the 8 MIs that were authored?"
        ),
        "criteria": {
            "STYLE_CONTRACT_IS_AUTHORITY_REWRITE_THE_MIS": 0,
            "MA_PALETTE_IS_AUTHORITY_NO_CHANGE": 0,
            "BRING_TO_OWNER_TO_DECIDE": 0,
        },
    },
}

CONSTRAINTS = [
    "The owner's level is the deliverable and it is currently unproven until the owner re-cooks it.",
    "Additive only: new files and new outputs, no mutation of assets a live level depends on; new materials stay unbound until the owner approves the binding.",
    "No editor mutation and no touching the owner's live editor session from an agent.",
    "Jev selects only; the existing owner lane executes; independent evidence (the cook check, the in-theme gate, placement assertions, one screenshot) proves the result.",
    "Do not replace a deterministic validation rule with judgement: a placement assertion is a test, not a question.",
    "Everything the next agent ships must be additive to the HDA outputs and must earn a named group in the gate.",
]


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
    print("JEV DECISION PACKET - Poitou programme completeness audit + frontier priority")
    print("=" * 72)
    if not jev_available():
        print("\n[!] Jev unavailable (TYPESAFE_API_KEY / typesafe_sdk).")
        print("    Fallback would be a COMPOSED GUESS, not Jev evidence.")
        return 2
    from typesafe_sdk import TypeSafeClient
    from typesafe_sdk._core.questions import Choice

    questions = {qid: Choice(instructions=spec["question"],
                             criteria={opt: None for opt in spec["criteria"]})
                 for qid, spec in QUESTIONS.items()}
    with TypeSafeClient() as client:
        result = client.system_one(state={"verified_state": STATE,
                                          "constraints": CONSTRAINTS},
                                   questions=questions)
    out = {
        "schema": "melodia.jev.poitou_programme_audit.v1",
        "source": "jev-live",
        "state_verified_at": STATE["verified_at"],
        "answers": {qid: {"choice": a.choice, "score": getattr(a, "score", None),
                          "reason": getattr(a, "reason", None)}
                    for qid, a in result.answers.items()},
    }
    dest = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "Saved", "Audit",
        "PoitouConvergence_20261020", "JevPoitouProgrammeAudit_20261021.json"))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("\n=== JEV ===")
    print(json.dumps(out["answers"], indent=1))
    print("\nreceipt:", dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
