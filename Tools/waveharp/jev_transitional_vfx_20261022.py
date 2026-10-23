"""JEV DECISION PACKET 2 - transitional VFX, states, FluidNinja and the next C++ step, 2026-10-22.

Closed candidate sets only. Jev selects; the existing owner lane (the waveharp
component, the audio-reactive subsystem) executes; deterministic tools prove.
"""
from __future__ import annotations

import json
import os
import sys

STATE = {
    "verified_at": "2026-10-22, disk + compiler evidence",
    "situation": (
        "C1-C6 of the WaveHarp form system are written and compile clean (MSVC 14.44, "
        "UBT's own toolchain). The overnight job is to wire the transitional VFX and "
        "the named states that make the change read like a designed transformation "
        "rather than a mesh swap, WITHOUT authoring new Niagara graphs and WITHOUT "
        "touching the editor."
    ),
    "already_in_place": [
        "the form change is one writer (SetForm), the transition is eased or curve-driven, "
        "the head swaps at the midpoint, the flourish starts on the music clock's beat "
        "boundary, an attack pressed during the flourish is buffered, the camera pushes in "
        "and returns, and the existing NS_Melusina_StarPop covers the swap",
        "the melee uses the MEASURED crescent geometry (a ~41 cm blade on a ~37 cm radius) "
        "and the ribbon follows the same measured points",
        "the offline gate Tools/waveharp/check_waveharp_form_contract.py is 15/15 green",
    ],
    "existing_surfaces_the_lane_may_use": {
        "niagara": ["/Game/Melodia/VFX/NS_Melusina_StarPop", "/Game/Melodia/VFX/NS_Melusina_SwingTrail",
                    "/Game/Melodia/VFX/NS_Melusina_ProviderSigil", "/Game/Melodia/VFX/NS_Melusina_Glint",
                    "/Game/Melodia/VFX/NS_Melusina_Dust", "/Game/Melodia/VFX/NS_Melusina_ImpactBurst",
                    "/Game/Melodia/VFX/NS_Melusina_Ripple", "/Game/Melodia/Characters/Melusina/Weapons/WaveHarp/NS_WaveHarp_ArrowTrail"],
        "meshes": ["/Game/Staging/HoudiniForge/MelusinaGNToys/SM_MEL_Ribbon_Transform_P100",
                   "Saved/Audit/waveharp/vfx/SM_Cymatic_BladeTrailRibbon (offline, built)",
                   "Saved/Audit/waveharp/vfx/T_Cymatic_HaloBloom.png (offline, built)"],
        "fluid_ninja": "Content/FluidNinjaLive is a full installed framework (Core/Assets, Core/DataChannels, "
                       "Core/Functions with NinjaInitGrids and NinjaInitHashGrid, and OutputMaterials/Base "
                       "with SURFACE, FOGVOLUME, SMOKEVOLUME, HETEROGENVOLUME, CLOUDVOLUME, FOLIAGE and DECAL "
                       "masters; 281 instances sit on M_NinjaOutput_BaseMaterial_SURFACE alone).",
        "owners_that_must_stay_the_only_writer": [
            "UMelodiaAudioReactivePresentationSubsystem - the sole MPC beat writer",
            "UMelodiaCymaticsWriterSubsystem - the sole writer of MPC_Cymatics_Driver",
            "UMelodiaExternalJRPGBridgeSubsystem - the sole damage authority",
            "UMelodiaNarrativeSubsystem - the sole save authority",
            "UMelodiaWaveHarpCombatComponent - the sole owner of the form"],
    },
    "reference_lanes": {
        "infinity_nikki": "their outfit change is a designed flourish with real-time clipping rules and "
                          "precomputed data; the effect budget follows screen size; the animation owns the motion",
        "anime_jrpg": "transformation conventions to borrow as a state vocabulary: charge, hold, release, "
                      "aftermath, and a named overdrive state",
        "constraint": "the identity canon is sunlit, reverent, grieving - not a fireworks show",
    },
}

QUESTIONS = {
    "state_vocabulary": {
        "question": (
            "Which state vocabulary should the WaveHarp form change use, so it reads as a "
            "designed transformation in the anime-JRPG register without becoming a cutscene?"
        ),
        "criteria": {
            "A": "The charge-hold-release-aftermath spine: the form change is a held state with a named "
                 "stage (PREPARE -> TRANSFORM -> SETTLE), and the flourish is the visual answer to it.",
            "B": "A persona-style hard cut: the change is instant, covered by a UI beat, and the "
                 "aftermath carries the weight. Cheapest, but it drops the authored henshin curve.",
            "C": "A limit-break slow state: the transition enters a named overdrive state where the "
                 "music clock slows and the camera takes over. Boldest, and it touches the music owner.",
            "D": "No named states at all: keep the current single transition and spend the night on the "
                 "VFX surfaces instead.",
        },
    },
    "vfx_surface": {
        "question": (
            "Which existing surface should carry the transition's visual beat? No new Niagara "
            "graphs may be authored."
        ),
        "criteria": {
            "A": "The existing NS_Melusina_* family at the head socket, driven by user parameters per "
                 "stage (StarPop at the handoff, SwingTrail during the unfurl, ProviderSigil at the seal).",
            "B": "The existing transformation ribbon (SM_MEL_Ribbon_Transform_P100) as a curtain that "
                 "unrolls across the swap - one asset, already in the project, reads as a designed wipe.",
            "C": "The offline flipbook (T_Cymatic_HaloBloom) as a card at the head, animated by the "
                 "existing flipbook system - already built by this lane.",
            "D": "FluidNinja: a mist or fog volume that unfurls with the transition and thins as the "
                 "form seals - the framework is already installed with fog and smoke outputs.",
        },
    },
    "fluid_ninja_discipline": {
        "question": (
            "How should FluidNinja be used in this build without breaking the one-writer-per-surface "
            "rule?"
        ),
        "criteria": {
            "A": "Not in the weapon lane at all: FluidNinja belongs to the world (the Poitou canal and "
                 "the marsh), it should be driven by the existing audio-reactive subsystem, and this lane "
                 "should leave it alone.",
            "B": "A thin bridge: the audio-reactive owner publishes the beat to FluidNinja's user "
                 "parameters, and the waveharp lane only reads the same clock. One writer, two readers.",
            "C": "Drive FluidNinja directly from the waveharp component - fastest, and it makes the "
                 "weapon a second writer on a world surface.",
            "D": "Defer FluidNinja entirely until the world lane asks for it.",
        },
    },
    "next_cxx_increment": {
        "question": (
            "What is the single highest-value NEXT C++ increment for the waveharp lane, now that "
            "C1-C6 are in?"
        ),
        "criteria": {
            "A": "A data-driven VFX descriptor table: per form and per stage, the existing system, "
                 "the socket and the user parameters - so the whole look of the transformation is "
                 "editable data, not code.",
            "B": "The idle shimmer (D4): drive the four shimmer morphs from the music clock instead "
                 "of frame-based sine, so the instrument is alive when it is not being fought.",
            "C": "The per-form grip offsets (C8): one hold solved per form, reusing the existing "
                 "character-space grip solver.",
            "D": "A quality tier for the flourish: scale the ribbon, the sparkle and the shimmer by "
                 "screen size and distance, the way the reference scales its fur layers.",
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
    print("JEV DECISION PACKET 2 - transitional VFX, states, FluidNinja 2026-10-22")
    print("=" * 72)
    if not jev_available():
        print("\n[!] Jev unavailable (TYPESAFE_API_KEY / typesafe_sdk).")
        return 2
    from typesafe_sdk import TypeSafeClient
    from typesafe_sdk._core.questions import Choice

    questions = {qid: Choice(instructions=spec["question"],
                             criteria={opt: None for opt in spec["criteria"]})
                 for qid, spec in QUESTIONS.items()}
    with TypeSafeClient() as client:
        result = client.system_one(state={"verified_state": STATE}, questions=questions)
    out = {
        "schema": "melodia.jev.waveharp_transitional_vfx.v1",
        "source": "jev-live",
        "state_verified_at": STATE["verified_at"],
        "answers": {qid: {"choice": a.choice, "score": getattr(a, "score", None),
                          "reason": getattr(a, "reason", None)}
                    for qid, a in result.answers.items()},
    }
    dest = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "Saved", "Audit", "waveharp",
        "JevWaveHarpTransitionalVfx_20261022.json"))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("\n=== JEV ===")
    print(json.dumps(out["answers"], indent=1))
    print("\nreceipt:", dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
