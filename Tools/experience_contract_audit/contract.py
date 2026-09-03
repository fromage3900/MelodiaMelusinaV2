"""Target First Dream experience contract and deterministic report rendering.

This module is deliberately data-only.  It reads text/JSON inputs, produces an
immutable audit-shaped dictionary, and renders that dictionary.  It does not
import Unreal or mutate gameplay data.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


AUDIT_ID = "FIRST_DREAM_EXPERIENCE_CONTRACT_AUDIT_2026-08-24"
PROOF_TIERS = (
    "source_built",
    "offline_proven",
    "live_proven",
    "design_intent",
    "LIVE_EVIDENCE_REQUIRED",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _load(path: Path) -> dict[str, Any]:
    text = _read(path)
    return json.loads(text) if text else {}


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _source(root: Path, relative_path: str, role: str) -> dict[str, Any]:
    path = root / relative_path
    text = _read(path)
    return {
        "path": relative_path.replace("\\", "/"),
        "role": role,
        "exists": bool(text),
        "sha256": _digest(text) if text else "NEED: source file missing",
    }


def _need(description: str) -> str:
    return f"NEED: {description}"


def build_target_report(source_audit: dict[str, Any], root: Path) -> dict[str, Any]:
    """Overlay the requested 20-30 minute design contract on parsed source truth."""
    progression = _load(root / "specs/progression/melodia_first_dream_progression.v1.json")
    golden = _load(root / "specs/p0/core_p0_dream_golden_run.v1.json")
    wardrobe = _load(root / "specs/wardrobe/wardrobe_catalog_manifest.v1.json")
    capability = _load(root / "specs/capability/melodia_capability_gate.v1.json")
    traversal = _load(root / "specs/traversal/melodia_traversal_capability.v1.json")
    morning_qsc = _read(root / "Content/MelodiaIntegration/Narrative/MelodiaMorningIntro.qsc")
    priestess_qsc = _read(root / "Content/MelodiaIntegration/Narrative/MelodiaQuillPetalPriestess.qsc")
    smoke_qsc = _read(root / "Content/MelodiaIntegration/Narrative/MelodiaQuillSmoke.qsc")

    first_outfit = wardrobe.get("first_outfit", {})
    wardrobe_records = first_outfit.get("records", [])
    accessory = next(
        (row for row in wardrobe_records if row.get("slot") == "Accessories"),
        {},
    )
    progression_ids = {
        value
        for key in ("beats", "quests", "objectives", "rewards", "consequences", "intent_journal")
        for row in progression.get(key, [])
        for field, value in row.items()
        if field.endswith("_id") and isinstance(value, str)
    }

    sources = [
        _source(root.parent, "PROJECT.md", "absolute authority statement"),
        _source(root, "Docs/ORCHESTRA_CONTRACT_2026-08-20.md", "seam authority"),
        _source(root, "Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md", "owner and duplicate verdicts"),
        _source(root, "_VERTICAL_SLICE_SCOPE.md", "active slice and open gates"),
        _source(root, "Docs/FIRST_DREAM_20_MINUTE_PLAYTEST_2026-08-01.md", "current timed playtest"),
        _source(root, "Docs/PERSONA_LITE_LOW_AGENCY_HANDOFF_2026-07-28.md", "Persona handoff"),
        _source(root, "Docs/Reviews/PERSONA_LITE_LOOP_DEEP_REVIEW_2026-08-08.md", "Persona deep review"),
        _source(root, "specs/progression/melodia_first_dream_progression.v1.json", "current progression model"),
        _source(root, "specs/p0/core_p0_dream_golden_run.v1.json", "current golden-run model"),
        _source(root, "Content/MelodiaIntegration/Narrative/MelodiaMorningIntro.qsc", "Morning authored source"),
        _source(root, "Content/MelodiaIntegration/Narrative/MelodiaQuillPetalPriestess.qsc", "Priestess authored source"),
        _source(root, "Content/MelodiaIntegration/Narrative/MelodiaQuillSmoke.qsc", "four-way battle reaction source"),
        _source(root, "specs/wardrobe/wardrobe_catalog_manifest.v1.json", "wardrobe vocabulary"),
        _source(root, "specs/capability/melodia_capability_gate.v1.json", "capability gate vocabulary"),
        _source(root, "specs/traversal/melodia_traversal_capability.v1.json", "Glide traversal vocabulary"),
    ]

    preparation_choices = [
        {
            "relationship": "Sir",
            "choice_id": _need("stable Sir preparation choice ID"),
            "authored_checkpoint": _need("Sir preparation Quill checkpoint"),
            "command_id": _need("stable command ID for Sir preparation"),
            "modifier_id": _need("single-encounter rhythm-grace modifier ID"),
            "evening_reaction_id": _need("Sir evening reaction ID"),
            "effect": "One visible rhythm-grace modifier scoped to the next stock encounter; it may soften degree of success but never submit or replace a JRPG command.",
            "consumption": "Clear on the first terminal encounter outcome, including unavailable; repeat commit returns AlreadyApplied.",
            "source_reuse": "Sir dialogue exists in MelodiaMorningIntro.qsc and MelodiaQuillSmoke.qsc; the preparation transaction does not.",
            "proof_tier": "design_intent",
        },
        {
            "relationship": "Priestess",
            "choice_id": _need("stable Priestess preparation choice ID"),
            "authored_checkpoint": _need("Priestess preparation Quill checkpoint"),
            "command_id": _need("stable command ID for Priestess preparation"),
            "modifier_id": _need("world-reading cue modifier ID"),
            "evening_reaction_id": _need("Priestess evening reaction ID"),
            "effect": "Commit the source-backed priestess_first_echo Harmony intent once and expose one readable world cue; the cue never grants Glide or completes the phrase.",
            "consumption": "The day slot is consumed once; the Harmony intent is idempotent per IntentId and the cue expires on EveningReturn.",
            "source_reuse": "MelodiaQuillPetalPriestess.qsc emits priestess_first_echo / melodia_harmony; no preparation slot or distinct evening reaction is authored.",
            "proof_tier": "source_built",
        },
    ]

    day_loop = {
        "duration_minutes": {"minimum": 20, "target": 30, "maximum": 30},
        "phase_order": ["MorningPreparation", "Expedition", "EveningReturn"],
        "scarcity_rule": "Exactly one preparation command may be Applied per day index; choosing Sir rejects Priestess for that day and vice versa.",
        "phases": [
            {
                "phase": "MorningPreparation",
                "window": "0:00-5:00",
                "entry": "Restore the canonical narrative checkpoint or create a fresh day record.",
                "player_contract": "Choose Sir or Priestess once, see the exact effect before confirmation, then leave with immediate feedback.",
                "choices": preparation_choices,
                "exit_invariant": "Preparation choice, modifier/cue, reaction key, and command ID are committed atomically before Expedition.",
                "proof_tier": "design_intent",
            },
            {
                "phase": "Expedition",
                "window": "5:00-22:00",
                "entry": "Show Cos_Accessories_MelusinaV2 at the wardrobe station with Glide visibly locked.",
                "player_contract": "Preview/equip one accessory, follow one motif, complete one existing Piano phrase, unlock Glide, cross the route it reveals, then play one stock JRPG encounter with rhythm grading.",
                "world_challenge": {
                    "accessory_id": accessory.get("cosmetic_id", _need("resonant accessory content ID")),
                    "resonant_form_id": accessory.get("resonant_form_id") or _need("resonant form ID that can expose Glide"),
                    "phrase_id": _need("stable ID of the existing Piano phrase selected for First Dream"),
                    "challenge_id": _need("stable First Dream world challenge ID"),
                    "command_id": _need("stable phrase-completion command ID"),
                    "capability_id": "Glide",
                    "route_payoff_id": _need("stable blocked-route payoff ID"),
                    "commit_rule": "Phrase completion applies one world result and one capability unlock atomically; replay returns AlreadyApplied.",
                    "failure_rule": "A failed phrase remains retryable and consumes no command, reward, capability, or checkpoint.",
                    "proof_tier": "design_intent",
                },
                "battle_rule": "Rhythm supplies a grade/modifier to the normal JRPG command. A miss lowers degree of success but never blocks the command or story progression.",
                "exit_invariant": "Exactly one typed battle outcome is committed and Quill resumes exactly once for victory, defeat, fled, or unavailable.",
                "proof_tier": "design_intent",
            },
            {
                "phase": "EveningReturn",
                "window": "22:00-30:00",
                "entry": "Resume Quill once at the outcome-specific evening checkpoint.",
                "player_contract": "Receive a reaction that reflects both the morning relationship and typed battle outcome; understand one reward's single purpose; save and advance the phase.",
                "reaction_cardinality": "2 preparation choices × 4 outcomes = 8 authored reaction cases; IDs are NEED until authored.",
                "reward_contract": "Use at most one reward ID. Current reward.first_resonance_echo is victory-only, so outcome-neutral versus victory-only semantics require an owner decision before implementation.",
                "exit_invariant": "Reaction, reward disposition, phase advance, checkpoint, and canonical save are replay-safe; failed reward/equip operations do not advance.",
                "proof_tier": "design_intent",
            },
        ],
    }

    battle_outcomes = [
        {
            "outcome": "victory",
            "source_state": "QSC has a distinct victory reaction; progression completes face_echo and grants reward.first_resonance_echo.",
            "target_state": "EveningReturn; resume Quill once; preserve morning choice; present victory consequence and reward once.",
            "reward": "reward.first_resonance_echo",
            "current_intent": "intent.first_dream.objective.face_echo.complete",
            "proof_tier": "offline_proven",
            "runtime_proof": "LIVE_EVIDENCE_REQUIRED: one outcome callback, one Quill resume, one reward grant.",
        },
        {
            "outcome": "defeat",
            "source_state": "QSC has a distinct defeat reaction; progression fails face_echo and records echo_unresolved without a reward.",
            "target_state": "EveningReturn; resume Quill once; no progression block; preserve defeat for the evening reaction.",
            "reward": _need("owner decision: no reward or the slice's single outcome-neutral reward"),
            "current_intent": "intent.first_dream.objective.face_echo.fail",
            "proof_tier": "offline_proven",
            "runtime_proof": "LIVE_EVIDENCE_REQUIRED: one outcome callback and one Quill resume with no victory reward leak.",
        },
        {
            "outcome": "fled",
            "source_state": "QSC has a distinct fled reaction; progression shares the defeat failure intent and echo_unresolved consequence.",
            "target_state": "EveningReturn; resume Quill once; no progression block; retain fled as a distinct typed outcome.",
            "reward": _need("owner decision: no reward or the slice's single outcome-neutral reward"),
            "current_intent": "intent.first_dream.objective.face_echo.fail (shared with defeat)",
            "proof_tier": "source_built",
            "runtime_proof": "LIVE_EVIDENCE_REQUIRED: fled remains distinguishable after save/reload.",
        },
        {
            "outcome": "unavailable",
            "source_state": "QSC contains fallback copy, but current progression has no unavailable terminal intent and the older model fails closed without resuming.",
            "target_state": "Commit a typed unavailable result once, resume Quill once into EveningReturn, grant no phantom victory state, and keep recovery authored.",
            "reward": _need("owner decision: recovery presentation only or the slice's single outcome-neutral reward"),
            "current_intent": _need("typed unavailable outcome intent/command ID"),
            "proof_tier": "design_intent",
            "runtime_proof": "LIVE_EVIDENCE_REQUIRED: unavailable starts no battle, mutates no JRPG state, resumes Quill exactly once.",
        },
    ]

    state_graph = {
        "fresh_slot_path": [
            "FreshSlot",
            "MorningPreparation.AwaitingChoice",
            "MorningPreparation.ChoiceCommitted",
            "Expedition.WardrobePreview.GlideLocked",
            "Expedition.AccessoryEquipped",
            "Expedition.PhraseChallenge",
            "Expedition.WorldResultCommitted",
            "Expedition.GlideUnlocked",
            "Expedition.VisibleRouteCrossed",
            "Expedition.EncounterRequested",
            "Expedition.BattleOutcome::<victory|defeat|fled|unavailable>",
            "EveningReturn.QuillResumedOnce",
            "EveningReturn.RelationshipOutcomeReaction",
            "EveningReturn.RewardDisposition",
            "EveningReturn.CheckpointCommitted",
            "CanonicalJRPGSaveRequested",
            "DayComplete",
        ],
        "outcome_paths": {
            item["outcome"]: [
                "Expedition.EncounterRequested",
                f"Expedition.BattleOutcome.{item['outcome']}",
                "EveningReturn.QuillResumedOnce",
                f"EveningReturn.Reaction.<choice+{item['outcome']}>",
                "EveningReturn.RewardDisposition",
                "EveningReturn.CheckpointCommitted",
                "CanonicalJRPGSaveRequested",
            ]
            for item in battle_outcomes
        },
        "continue_paths": {
            "MorningPreparation": "Restore day index and no/one committed preparation; never reopen the consumed alternative.",
            "Expedition.before_phrase": "Restore choice, equipped accessory, locked Glide, motif checkpoint, and applied command IDs.",
            "Expedition.after_phrase": "Restore world result and Glide; do not replay phrase completion or capability grant.",
            "Expedition.encounter_pending": "Restart the encounter beat from its canonical checkpoint without replaying preparation, equip, phrase, or unlock.",
            "EveningReturn.after_outcome": "Restore the exact typed outcome and choice-specific reaction checkpoint; do not invoke the battle callback again.",
            "DayComplete": "Restore reward disposition and checkpoint, then advance to the next MorningPreparation without duplicate grants.",
        },
        "continue_outcome_paths": {
            item["outcome"]: [
                "CanonicalJRPGSaveLoaded",
                f"RestoreTypedOutcome.{item['outcome']}",
                f"RestoreEveningReaction.<choice+{item['outcome']}>",
                "DoNotInvokeBattleCallbackAgain",
                "DoNotDuplicateRewardOrIntent",
            ]
            for item in battle_outcomes
        },
        "replay_path": [
            "Reissue stable command ID",
            "AppliedCommandIds contains ID",
            "Return AlreadyApplied",
            "Rebuild presentation read model only",
            "Do not re-grant, re-equip, re-unlock, re-resume, or advance checkpoint",
        ],
        "atomic_failure_path": [
            "Equipment or reward authority rejects",
            "Return Rejected",
            "Do not add command ID",
            "Do not advance narrative checkpoint or day phase",
            "Show authored recovery and allow retry",
        ],
    }

    matrix = [
        ("preparation.sir", "MorningPreparation", _need("stable command ID for Sir preparation"), "choice + grace modifier + Sir evening key", "design_intent"),
        ("preparation.priestess", "MorningPreparation", _need("stable command ID for Priestess preparation"), "choice + Harmony/world cue + Priestess evening key", "design_intent"),
        ("dialogue.advance", "MorningPreparation", _need("stable dialogue-checkpoint command ID"), "one Quill checkpoint advance", "design_intent"),
        ("wardrobe.equip", "Expedition", _need("stable accessory equip command ID"), "Cos_Accessories_MelusinaV2 loadout only", "design_intent"),
        ("phrase.complete", "Expedition", _need("stable phrase-completion command ID"), "one typed world challenge result", "design_intent"),
        ("capability.unlock.glide", "Expedition", _need("stable Glide-unlock command ID"), "Glide unlock through wardrobe capability provider", "design_intent"),
        ("route.payoff", "Expedition", _need("stable blocked-route payoff command ID"), "one visible route state", "design_intent"),
        ("encounter.request", "Expedition", _need("stable encounter request command ID"), "one request to IMelodiaJRPGPort", "design_intent"),
        ("battle.outcome.victory", "Expedition", _need("stable victory outcome command ID"), "typed victory + source completion intent", "design_intent"),
        ("battle.outcome.defeat", "Expedition", _need("stable defeat outcome command ID"), "typed defeat + source failure intent", "design_intent"),
        ("battle.outcome.fled", "Expedition", _need("stable fled outcome command ID"), "typed fled retained separately from defeat", "design_intent"),
        ("battle.outcome.unavailable", "Expedition", _need("stable unavailable outcome command ID"), "typed unavailable without JRPG mutation", "design_intent"),
        ("quill.resume", "EveningReturn", _need("stable Quill-resume command ID"), "exactly one resume for any typed outcome", "design_intent"),
        ("evening.reaction", "EveningReturn", _need("stable relationship+outcome reaction command ID"), "one of eight authored reaction checkpoints", "design_intent"),
        ("reward.present", "EveningReturn", "intent.first_dream.reward.first_resonance_echo", "one reward disposition with one stated purpose", "offline_proven"),
        ("phase.advance", "EveningReturn", _need("stable day-phase advance command ID"), "EveningReturn checkpoint then next day", "design_intent"),
        ("canonical.save", "EveningReturn", _need("stable canonical save request command ID"), "versioned Melodia fragment inside BP_JRPGSaveGame", "design_intent"),
        ("canonical.reload", "Any", _need("stable load request correlation ID"), "same phase/choice/loadout/unlock/outcome/checkpoint", "design_intent"),
        ("replay.applied_command", "Any", _need("stable replay probe command ID"), "AlreadyApplied and presentation-only refresh", "offline_proven"),
    ]
    exactly_once_matrix = [
        {
            "analysis_id": row_id,
            "intent_id": command_id,
            "command_id": command_id,
            "phase": phase,
            "type": row_id.split(".")[0],
            "atomic_effect": effect,
            "exactly_once": True,
            "applied_disposition": "Applied",
            "repeat_disposition": "AlreadyApplied",
            "failure_disposition": "Rejected",
            "consume_on_failure": False,
            "advance_on_failure": False,
            "record_field": "FMelodiaOrchestraSaveFragment.AppliedCommandIds (design contract; not implemented)",
            "replay": "no gameplay mutation; presentation may rebuild from immutable read model",
            "proof": "offline contract invariant" if proof == "offline_proven" else "requested target behavior",
            "proof_tier": proof,
        }
        for row_id, phase, command_id, effect, proof in matrix
    ]

    pacing_defs = [
        ("0:00-2:00", "MorningPreparation", "Walk, inspect the empty perch, approach preparation choice", "orientation and movement", "NPC/perch highlight and concise goal", "preparation choice becomes readable", "Resume at morning checkpoint; no command consumed", "source_built", True),
        ("2:00-5:00", "MorningPreparation", "Choose Sir or Priestess once", "one scarce relationship choice", "show exact modifier/cue, slot consumed, evening promise", "meaningful day commitment", "Rejected commit leaves both choices available; Applied commit survives reload", "design_intent", True),
        ("5:00-7:00", "Expedition", "Preview and equip the resonant accessory", "equip or back out", "Cos_Accessories_MelusinaV2 visible; Glide shown locked with reason", "outfit identity plus anticipated capability", "Failed equip consumes nothing and cannot advance", "design_intent", True),
        ("7:00-9:00", "Expedition", "Follow one audible/visible motif", "route reading; Priestess cue changes readability, not access", "motif feedback points toward Piano host", "find the phrase challenge", "Return to last expedition checkpoint", "design_intent", True),
        ("9:00-11:00", "Expedition", "Play the selected Piano phrase", "timing/input retry", "grade plus explicit retry; success commits once", "Glide unlock and world response", "Miss never consumes command or blocks retry", "design_intent", True),
        ("11:00-14:00", "Expedition", "Use Glide across the previously blocked route", "take Glide route or inspect fallback", "movement state and accessory remain visible", "visible traversal payoff within six minutes of preview", "Fall returns safely before the gate; unlock remains committed", "design_intent", True),
        ("14:00-22:00", "Expedition", "Choose Attack/Skill/Item/Flee and time rhythm inputs", "normal JRPG command choice with rhythm degree", "grade modifies command feedback; miss still resolves command", "typed victory/defeat/fled/unavailable", "Any outcome resumes Quill once; unavailable starts no phantom battle", "design_intent", True),
        ("22:00-25:00", "EveningReturn", "Read and advance the choice+outcome reaction", "dialogue pacing only", "distinct Sir/Priestess and outcome copy", "relationship consequence", "Restore exact reaction checkpoint; no battle callback replay", "design_intent", True),
        ("25:00-28:00", "EveningReturn", "Inspect one reward and confirm return", "accept presentation, not a second reward choice", "one purpose stated; disposition visible", "phase/checkpoint commit", "Rejected reward does not consume command or advance", "design_intent", True),
        ("28:00-30:00", "EveningReturn", "Save, return to menu, Continue, verify state", "Continue or replay probe", "same choice/outfit/unlock/outcome/dialogue checkpoint", "restart proof and next-day handoff", "AlreadyApplied on repeated commands; no duplicate intents/rewards", "offline_proven", True),
    ]
    pacing = []
    for index, row in enumerate(pacing_defs, 1):
        window, phase, verb, choice, feedback, payoff, recovery, proof, agency = row
        start, end = [int(part.split(":")[0]) for part in window.split("-")]
        pacing.append({
            "beat_id": f"target.{index:02d}",
            "window": window,
            "start_minute": start,
            "end_minute": end,
            "duration_minutes": end - start,
            "phase": phase,
            "verb": verb,
            "player_verb": verb,
            "control_state": "player-controlled" if agency else "non-interactive",
            "choice": choice,
            "feedback": feedback,
            "payoff": payoff,
            "failure_recovery": recovery,
            "proof_tier": proof,
            "agency_present": agency,
        })

    heuristics = {
        "more_than_four_minutes_without_agency": {
            "threshold_minutes": 4,
            "flagged": any(not row["agency_present"] and row["duration_minutes"] > 4 for row in pacing),
            "finding": "Target has no >4 minute non-interactive span; the eight-minute battle is continuous command/timing agency.",
            "proof_tier": "design_intent",
        },
        "apparently_meaningful_identical_effects": {
            "flagged": True,
            "finding": "Current Priestess HarmonyAnswer and ListeningAnswer converge to the same priestess_first_echo stat intent and melodia_q_echo_01 quest notify. Treat them as expressive until the new Sir/Priestess preparation effects are authored distinctly.",
            "evidence": "Content/MelodiaIntegration/Narrative/MelodiaQuillPetalPriestess.qsc",
            "proof_tier": "source_built",
        },
        "payoff_delayed_over_six_minutes": {
            "threshold_minutes": 6,
            "flagged": True,
            "finding": "Current source has no wardrobe-to-route payoff, so latency is unbounded. The target schedules accessory preview at minute 5 and visible route payoff at minute 11 (exactly six minutes).",
            "proof_tier": "source_built",
        },
        "absent_core_pillar": {
            "flagged": True,
            "finding": "Current playtest/progression omit the playable wardrobe and music-as-key loops. The target contract includes both, but they remain DESIGN_INTENT until live gates close.",
            "proof_tier": "source_built",
        },
    }

    persona_lens = {
        "thesis": "Persona's useful lens is opportunity cost plus relationship feedback, not a full calendar.",
        "scarce_activity_slot": "One preparation per day; atomic commit makes the alternative unavailable until the next day.",
        "expressive_choices": [
            {
                "choice": "Current Priestess HarmonyAnswer / ListeningAnswer",
                "classification": "expressive",
                "effect": "Identical stat and quest notifications after convergence.",
                "proof_tier": "source_built",
            },
            {
                "choice": "Current Morning follow / wait",
                "classification": "expressive with a local flag variation",
                "effect": "Both reach Departure; only melodia_met_melodious differs.",
                "proof_tier": "source_built",
            },
        ],
        "consequential_choices": [
            {
                "choice": "Target Sir / Priestess preparation",
                "classification": "mechanically consequential",
                "effect": "Mutually exclusive grace versus Harmony/world cue plus distinct evening reaction.",
                "proof_tier": "design_intent",
            },
            {
                "choice": "Stock Attack / Skill / Item / Flee with rhythm timing",
                "classification": "mechanically consequential",
                "effect": "Changes battle degree/outcome while stock JRPG remains authority.",
                "proof_tier": "design_intent",
            },
        ],
        "feedback_loop": "choice -> immediate effect card -> expedition expression -> outcome-specific evening reaction -> canonical save",
        "bond_scope": "No roster, ranks, weekdays, schedules, or additional activity periods in this slice.",
        "score": {"expressive_scored_separately": True, "consequential_scored_separately": True},
        "live_evidence": "LIVE_EVIDENCE_REQUIRED: slot scarcity, distinct effects, reaction fidelity, and reload persistence.",
    }

    nikki_lens = {
        "thesis": "Infinity Nikki is used only as a lens for an explicit outfit-to-world verb, never as a parity or affiliation claim.",
        "outfit_visibility": {
            "source": f"{accessory.get('cosmetic_id', _need('accessory ID'))} exists in the source manifest; resonant_form_id is null.",
            "target": "Preview the equipped accessory on the character and show Glide locked before the phrase.",
            "proof_tier": "design_intent",
            "live_evidence": "LIVE_EVIDENCE_REQUIRED: visual read at gameplay camera distance and after reload.",
        },
        "capability_preview": "Locked reason must name Glide and the phrase requirement; preview cannot grant or mutate capability state.",
        "acquisition_equip_payoff": "source-backed accessory -> atomic equip -> phrase result -> Glide unlock -> visibly blocked route -> crossing payoff",
        "traversal_expression": "Glide routes only through IMelodiaTraversalCapabilityProvider and UMelodiaTraversalComponent.",
        "payoff_latency_minutes": 6,
        "currently_playable": False,
        "current_reason": "Manifest is source-ready, its accessory has no resonant form, and the current progression/golden run contain no wardrobe or Piano challenge beat.",
        "proof_tier": "source_built",
    }

    drifts = [
        {"id": "target_day_phase_absent", "severity": "missing_contract", "finding": "Current progression has six story beats but no day index, three-phase enum, or one-slot preparation economy.", "evidence": "specs/progression/melodia_first_dream_progression.v1.json", "proof_tier": "source_built", "resolution": "Introduce the types-only contracts after owner approval; keep Narrative as command boundary."},
        {"id": "preparation_choice_effect_drift", "severity": "meaning_drift", "finding": "Current Priestess response choices are expressive and there is no Sir-versus-Priestess scarce preparation command.", "evidence": "Content/MelodiaIntegration/Narrative/MelodiaQuillPetalPriestess.qsc", "proof_tier": "source_built", "resolution": "NEED: authored stable choice/modifier/reaction IDs."},
        {"id": "wardrobe_resonance_gap", "severity": "missing_pillar", "finding": "Cos_Accessories_MelusinaV2 exists but resonant_form_id is null; current progression and golden run do not preview, equip, or query it.", "evidence": "specs/wardrobe/wardrobe_catalog_manifest.v1.json", "proof_tier": "source_built", "resolution": "Bind through the existing Wardrobe port/provider; do not add capability state to UI or narrative."},
        {"id": "piano_world_result_gap", "severity": "missing_pillar", "finding": "No selected phrase/challenge/command ID is present in First Dream content and music_world_key remains an open live gate.", "evidence": "Docs/ORCHESTRA_CONTRACT_2026-08-20.md", "proof_tier": "source_built", "resolution": "NEED: select the existing phrase and author stable challenge/command IDs."},
        {"id": "unavailable_terminal_gap", "severity": "outcome_drift", "finding": "QSC has unavailable fallback copy, but progression accepts only victory, defeat, and fled; unavailable lacks a typed terminal intent and resume-once proof.", "evidence": "Content/MelodiaIntegration/Narrative/MelodiaQuillSmoke.qsc; specs/progression/melodia_first_dream_progression.v1.json", "proof_tier": "source_built", "resolution": "Add typed unavailable routing through the existing bridge; no JRPG mutation or phantom reward."},
        {"id": "defeat_fled_collapse", "severity": "outcome_drift", "finding": "Defeat and fled have distinct QSC copy but share intent.first_dream.objective.face_echo.fail and the same saved failure flag.", "evidence": "specs/progression/melodia_first_dream_progression.v1.json", "proof_tier": "source_built", "resolution": "Preserve the typed result in the versioned fragment so evening/reload can distinguish them."},
        {"id": "reward_semantics_unresolved", "severity": "owner_decision", "finding": "The target evening promises one purposeful reward, while reward.first_resonance_echo is currently victory-only and other outcomes grant none.", "evidence": "specs/progression/melodia_first_dream_progression.v1.json", "proof_tier": "source_built", "resolution": "OWNER_DECISION_REQUIRED: victory-only reward versus one outcome-neutral completion reward."},
        {"id": "twenty_vs_thirty_minute_contract", "severity": "scope_drift", "finding": "The current playtest is a 0-20 minute route; the target day loop is a 20-30 minute three-phase slice.", "evidence": "Docs/FIRST_DREAM_20_MINUTE_PLAYTEST_2026-08-01.md", "proof_tier": "source_built", "resolution": "Use the target pacing table for implementation; retain the older playtest as baseline evidence only."},
        {"id": "proof_gates_open", "severity": "proof_gap", "finding": "wardrobe_equip_roundtrip, rhythm_grade_to_result, music_world_key, wardrobe_gameplay_hook, result matrix, and HUD single-writer proof remain open for this combined loop.", "evidence": "C:/EnvironmentPortfolio/PROJECT.md; _VERTICAL_SLICE_SCOPE.md", "proof_tier": "LIVE_EVIDENCE_REQUIRED", "resolution": "Only runtime evidence may close runtime gates."},
    ]

    references = [
        {"kind": "encounter", "value": "melodia_smoke_encounter", "resolution": "resolved", "evidence": "MelodiaQuillSmoke.qsc" if "melodia_smoke_encounter" in smoke_qsc else _need("encounter source")},
        {"kind": "stat_intent", "value": "priestess_first_echo", "resolution": "resolved", "evidence": "MelodiaQuillPetalPriestess.qsc" if "priestess_first_echo" in priestess_qsc else _need("stat source")},
        {"kind": "stat", "value": "melodia_harmony", "resolution": "resolved", "evidence": "MelodiaQuillPetalPriestess.qsc" if "melodia_harmony" in priestess_qsc else _need("stat source")},
        {"kind": "accessory", "value": accessory.get("cosmetic_id", _need("resonant accessory content ID")), "resolution": "resolved" if accessory else "NEED", "evidence": "specs/wardrobe/wardrobe_catalog_manifest.v1.json"},
        {"kind": "capability", "value": "Glide", "resolution": "resolved" if "Glide" in json.dumps([capability, traversal]) else "NEED", "evidence": "specs/traversal/melodia_traversal_capability.v1.json"},
        {"kind": "reward", "value": "reward.first_resonance_echo", "resolution": "resolved" if "reward.first_resonance_echo" in progression_ids else "NEED", "evidence": "specs/progression/melodia_first_dream_progression.v1.json"},
        {"kind": "sir_choice", "value": _need("stable Sir preparation choice ID"), "resolution": "NEED", "evidence": "No source ID found"},
        {"kind": "priestess_choice", "value": _need("stable Priestess preparation choice ID"), "resolution": "NEED", "evidence": "No source ID found"},
        {"kind": "piano_phrase", "value": _need("selected existing Piano phrase stable ID"), "resolution": "NEED", "evidence": "No First Dream binding found"},
        {"kind": "world_challenge", "value": _need("First Dream world challenge stable ID"), "resolution": "NEED", "evidence": "No First Dream binding found"},
        {"kind": "resonant_form", "value": _need("resonant form ID for the accessory"), "resolution": "NEED", "evidence": "Manifest value is null"},
        {"kind": "evening_reactions", "value": _need("eight relationship+outcome reaction IDs"), "resolution": "NEED", "evidence": "Current QSC reacts only to battle outcome"},
    ]
    all_refs_valid = all(
        ref["resolution"] == "resolved" or str(ref["value"]).startswith("NEED:")
        for ref in references
    )

    report = dict(source_audit)
    report.update({
        "meta": {
            "audit_id": AUDIT_ID,
            "schema": "melodia.first_dream.experience_contract_audit.v1",
            "deterministic": True,
            "baseline_head": "7122a391",
            "production_mutation": False,
            "proof_tiers": list(PROOF_TIERS),
            "claim_rule": "Source presence, offline proof, live proof, and design intent are distinct.",
        },
        "inputs_compared": sources,
        "three_phase_day": day_loop,
        "preparation_choices": preparation_choices,
        "battle_outcomes": battle_outcomes,
        "graph": {"battle_results": [row["outcome"] for row in battle_outcomes], "phase_order": day_loop["phase_order"]},
        "state_graph": state_graph,
        "exactly_once_matrix": exactly_once_matrix,
        "matrix": exactly_once_matrix,
        "pacing_table": pacing,
        "pacing": pacing,
        "persona_lens": persona_lens,
        "persona": persona_lens,
        "infinity_nikki_lens": nikki_lens,
        "nikki": nikki_lens,
        "drift_report": drifts,
        "drifts": drifts,
        "heuristics": heuristics,
        "warnings": [value for value in heuristics.values() if value["flagged"]],
        "id_resolution": {
            "references": references,
            "every_id_resolves_or_NEED": all_refs_valid,
            "resolved_count": sum(ref["resolution"] == "resolved" for ref in references),
            "need_count": sum(ref["resolution"] != "resolved" for ref in references),
        },
        "owner_decisions_required": [
            "Reward semantics across defeat, fled, and unavailable.",
            "Exact Sir grace modifier policy and player-facing copy.",
            "Selection of the existing Piano phrase and blocked route.",
            "Eight evening reaction IDs/checkpoints.",
        ],
        "live_only_questions": [
            "Does the accessory remain visible and equipped after process restart?",
            "Does phrase completion unlock Glide exactly once and open the visible route?",
            "Does a rhythm miss still submit the normal JRPG command and preserve progression?",
            "Do victory, defeat, fled, and unavailable each resume Quill exactly once?",
            "Does Continue restore choice, outfit, unlock, outcome, and dialogue checkpoint without duplication?",
            "Is MelodiaUIBridgeSubsystem the sole battle/rhythm presentation writer?",
        ],
        "scorecard": {
            "current_source": "HOLD: authored and source-built parts exist, but the three-phase loop is not implemented or live-proven.",
            "target_contract": "COMPLETE_OFFLINE: all required phases, outcomes, replay paths, pacing fields, and design lenses are represented deterministically.",
            "runtime_status": "LIVE_EVIDENCE_REQUIRED",
            "pillars": {"narrative": "source_built", "stock_battle": "source_built", "rhythm_modifier": "LIVE_EVIDENCE_REQUIRED", "wardrobe_loop": "design_intent", "music_world_key": "design_intent", "save_restart": "live_proven independently; combined fragment path LIVE_EVIDENCE_REQUIRED"},
        },
        "validation_summary": {
            "phase_count": len(day_loop["phases"]),
            "battle_outcome_count": len(battle_outcomes),
            "exactly_once_row_count": len(exactly_once_matrix),
            "unique_analysis_ids": len({row["analysis_id"] for row in exactly_once_matrix}) == len(exactly_once_matrix),
            "all_commands_failure_safe": all(not row["consume_on_failure"] and not row["advance_on_failure"] for row in exactly_once_matrix),
            "all_content_ids_resolved_or_need": all_refs_valid,
            "pacing_starts_at_zero": pacing[0]["start_minute"] == 0,
            "pacing_ends_at_thirty": pacing[-1]["end_minute"] == 30,
            "fresh_continue_replay_present": all(key in state_graph for key in ("fresh_slot_path", "continue_paths", "replay_path")),
        },
        "source_observations": {
            "morning_mentions_sir": "Sir" in morning_qsc,
            "priestess_choices_converge": "-> AcceptFirstEcho" in priestess_qsc and priestess_qsc.count("-> AcceptFirstEcho") == 2,
            "smoke_authors_four_reactions": all(token in smoke_qsc for token in ("victory", "defeat", "fled", "battle could not begin")),
            "golden_route_phase_count": len(golden.get("route_phases", [])),
            "wardrobe_accessory_resonant_form_is_null": bool(accessory) and accessory.get("resonant_form_id") is None,
        },
    })
    return report


def normalized_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _cell(value: Any) -> str:
    if isinstance(value, (dict, list)):
        value = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(report: dict[str, Any]) -> str:
    phases = report["three_phase_day"]["phases"]
    lines = [
        "# First Dream Persona / Infinity Nikki Experience Contract Audit - 2026-08-24",
        "",
        "**Verdict:** the requested three-phase slice is now specified as a deterministic offline contract, not claimed as implemented. Current sources contain the narrative, progression, wardrobe vocabulary, capability seam, and stock encounter pieces, but the scarce preparation slot, resonant accessory binding, phrase-to-Glide transaction, combined four-outcome evening flow, and versioned day fragment remain design intent or live-evidence work.",
        "",
        "Proof vocabulary is strict: `source_built`, `offline_proven`, `live_proven`, `design_intent`, and `LIVE_EVIDENCE_REQUIRED` are not interchangeable.",
        "",
        "## Three-phase day",
        "",
        "| Phase | Window | Player contract | Exit invariant | Proof |",
        "|---|---:|---|---|---|",
    ]
    for phase in phases:
        lines.append(f"| {_cell(phase['phase'])} | {_cell(phase['window'])} | {_cell(phase['player_contract'])} | {_cell(phase['exit_invariant'])} | {_cell(phase['proof_tier'])} |")
    lines.extend([
        "",
        "The phase order is `MorningPreparation -> Expedition -> EveningReturn`. One preparation slot is consumed per day. No calendar, weekday, NPC schedule, gacha, styling contest, second battle system, or second save system is introduced.",
        "",
        "## Preparation choice contract",
        "",
        "| Choice | Stable IDs | Distinct effect | Lifetime | Proof |",
        "|---|---|---|---|---|",
    ])
    for choice in report["preparation_choices"]:
        ids = f"{choice['choice_id']}; {choice['modifier_id']}; {choice['evening_reaction_id']}"
        lines.append(f"| {_cell(choice['relationship'])} | {_cell(ids)} | {_cell(choice['effect'])} | {_cell(choice['consumption'])} | {_cell(choice['proof_tier'])} |")
    lines.extend([
        "",
        "Current authored Priestess answers remain expressive because both converge to the same stat and quest notifications. The target Sir/Priestess selection is mechanically consequential only after the distinct effects and reaction checkpoints are authored.",
        "",
        "## Fresh, Continue, and replay state contract",
        "",
        "Fresh slot: `" + " -> ".join(report["state_graph"]["fresh_slot_path"]) + "`",
        "",
        "Continue must restore:",
        "",
    ])
    for key, value in report["state_graph"]["continue_paths"].items():
        lines.append(f"- `{key}` - {value}")
    lines.extend(["", "Continue outcome restoration:", ""])
    for outcome, path in report["state_graph"]["continue_outcome_paths"].items():
        lines.append(f"- `{outcome}` - `" + " -> ".join(path) + "`")
    lines.extend(["", "Replay: `" + " -> ".join(report["state_graph"]["replay_path"]) + "`", "", "Atomic rejection: `" + " -> ".join(report["state_graph"]["atomic_failure_path"]) + "`", "", "## Battle outcome contract", "", "| Outcome | Current source | Target continuation | Reward | Proof / open evidence |", "|---|---|---|---|---|"])
    for row in report["battle_outcomes"]:
        lines.append(f"| {_cell(row['outcome'])} | {_cell(row['source_state'])} | {_cell(row['target_state'])} | {_cell(row['reward'])} | {_cell(row['proof_tier'] + '; ' + row['runtime_proof'])} |")
    lines.extend(["", "Every outcome, including `unavailable`, enters EveningReturn and resumes Quill exactly once in the target contract. A rhythm miss changes degree of success, never access to the normal JRPG command or story progression.", "", "## Exactly-once matrix", "", "| Analysis row | Phase | Command ID | Atomic effect | Repeat | Failure | Proof |", "|---|---|---|---|---|---|---|"])
    for row in report["exactly_once_matrix"]:
        lines.append(f"| {_cell(row['analysis_id'])} | {_cell(row['phase'])} | {_cell(row['command_id'])} | {_cell(row['atomic_effect'])} | {_cell(row['repeat_disposition'])} | {_cell(row['failure_disposition'] + '; consume=false; advance=false')} | {_cell(row['proof_tier'])} |")
    lines.extend(["", "## 0-30 minute pacing", "", "| Window | Phase | Player verb | Choice | Feedback | Payoff | Failure recovery | Proof |", "|---|---|---|---|---|---|---|---|"])
    for row in report["pacing_table"]:
        lines.append(f"| {_cell(row['window'])} | {_cell(row['phase'])} | {_cell(row['player_verb'])} | {_cell(row['choice'])} | {_cell(row['feedback'])} | {_cell(row['payoff'])} | {_cell(row['failure_recovery'])} | {_cell(row['proof_tier'])} |")
    lines.extend(["", "## Persona lens", "", report["persona_lens"]["thesis"], "", f"Scarcity: {report['persona_lens']['scarce_activity_slot']}", "", "Expressive and consequential choices are scored separately. The feedback loop is: `" + report["persona_lens"]["feedback_loop"] + "`.", "", "## Infinity Nikki lens", "", report["infinity_nikki_lens"]["thesis"], "", f"Target loop: `{report['infinity_nikki_lens']['acquisition_equip_payoff']}`", "", f"Current playable verdict: **{report['infinity_nikki_lens']['currently_playable']}** - {report['infinity_nikki_lens']['current_reason']}", "", "## Drift report", "", "| ID | Severity | Finding | Resolution | Proof |", "|---|---|---|---|---|"])
    for row in report["drift_report"]:
        lines.append(f"| {_cell(row['id'])} | {_cell(row['severity'])} | {_cell(row['finding'])} | {_cell(row['resolution'])} | {_cell(row['proof_tier'])} |")
    lines.extend(["", "## Required heuristic flags", ""])
    for name, result in report["heuristics"].items():
        lines.append(f"- `{name}` - flagged `{str(result['flagged']).lower()}`: {result['finding']}")
    lines.extend(["", "## Content ID resolution", "", "| Kind | ID or NEED | Resolution | Evidence |", "|---|---|---|---|"])
    for ref in report["id_resolution"]["references"]:
        lines.append(f"| {_cell(ref['kind'])} | {_cell(ref['value'])} | {_cell(ref['resolution'])} | {_cell(ref['evidence'])} |")
    lines.extend(["", "## Owner decisions", ""])
    lines.extend(f"- {item}" for item in report["owner_decisions_required"])
    lines.extend(["", "## Live-only proof still required", ""])
    lines.extend(f"- {item}" for item in report["live_only_questions"])
    lines.extend(["", "## Offline validation summary", "", "```json", json.dumps(report["validation_summary"], indent=2, sort_keys=True), "```", "", "Generated deterministically from read-only text and JSON sources. No Unreal, binary assets, production source, canonical QSC, or progression spec was modified.", ""])
    return "\n".join(lines)


def write_outputs(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(normalized_json(report), encoding="utf-8", newline="\n")
    markdown_path.write_text(render_markdown(report), encoding="utf-8", newline="\n")
