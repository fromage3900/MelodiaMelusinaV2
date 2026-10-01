"""Jev-driven showcase asset-prep conductor — isolated prototype.

ISOLATION CONTRACT:
- Everything lives in Prototypes/JevShowcasePrep/. Delete this folder to remove it.
- NO .umap/.uasset writes. NO editor mutations. NO ledger writes.
  Code READS state and RECOMMENDS the next authored prep action.
  A human (or an existing audit/fix script) executes it.
- Jev selects ONLY among the authored NEXT_ACTIONS below. It never generates
  content, commands, or parameters beyond the closed sets.
- Provenance: every Decision records source="jev-live" or
  source="classical-fallback" plus reason. Fallback runs without
  TYPESAFE_API_KEY and is NOT Jev evidence.
- Owner confirmed SIX showcase levels (not five). The authored LEVELS tuple
  is the record of that decision.

Skill: typesafe-ai. Choice + Noul + Score go in ONE system_one call over the
same state; code owns workflow, cooldown, and execution.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

# Owner decision 2026-09-21: accept six levels. Do not trim this tuple.
LEVELS = (
    "/Game/Melodia/Characters/Melusina/Portfolio/L_MelusinaPortfolioCapture",
    "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
    "/Game/EnvSandbox/Environments/L_FallenMoon",
    "/Game/EnvSandbox/Environments/L_KaleidoNave",
    "/Game/ZenForestTest",
    "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype",
)

CAPTURE_LEVEL = LEVELS[0]

NEXT_ACTIONS = (
    "AUDIT_MATERIAL_INSTANCES",
    "AUDIT_MESH_MAPS",
    "AUDIT_NIAGARA_FLIPBOOK",
    "AUDIT_HAIR_CHAIN",
    "APPLY_FIX",
    "RENDER_PROOF",
    "COOK_TO_G",
    "HOLD_FOR_OWNER",
)

MIN_HOLD_SECONDS = 60.0
SWITCH_MARGIN = 0.08
CONF_SWITCH_GATE = 0.80

# Index matches the Score answer: L0, L1, L2, L3.
RENDER_READY_LEVELS = [
    "L0 blocking defects",
    "L1 audited with open fixes",
    "L2 clean audits no proof",
    "L3 clean + render proof on disk",
]


@dataclass
class ShowcaseState:
    """Compact showcase state. None = unknown. Never invent zeros.

    Per-level counts are dicts keyed by LEVELS asset path. A missing key is
    unknown for that level. Presenter and hair fields are global because they
    describe the capture-level presenter and the Melusina hair chain.
    open_defect is the receipt's name for one open defect; None means no
    receipt has named one (unknown, not "clean").
    """

    mi_bad_parent_count: Optional[dict[str, Optional[int]]] = None
    engine_default_count: Optional[dict[str, Optional[int]]] = None
    missing_texture_count: Optional[dict[str, Optional[int]]] = None
    last_audit_age_h: Optional[dict[str, Optional[float]]] = None
    render_proof_exists: Optional[dict[str, Optional[bool]]] = None
    niagara_default_material_count: Optional[int] = None
    flipbook_authority_ok: Optional[bool] = None
    validate_errors: Optional[int] = None
    kawaii_tune_ok: Optional[bool] = None
    hair_tick_flags_ok: Optional[bool] = None
    blend_verified: Optional[bool] = None
    shp_bone_match: Optional[bool] = None
    open_defect: Optional[str] = None
    editor_up: Optional[bool] = None
    dirty_count: Optional[int] = None
    disk_gb_free_c: Optional[float] = None
    time_budget_min: float = 60.0
    focused_level: Optional[str] = None
    current_action: str = "HOLD_FOR_OWNER"
    seconds_since_last_action: float = 9999.0
    provenance: str = "assembled"

    def to_jev_state(self) -> dict[str, Any]:
        raw: dict[str, Any] = {
            "mi_bad_parent_count": self.mi_bad_parent_count,
            "engine_default_count": self.engine_default_count,
            "missing_texture_count": self.missing_texture_count,
            "last_audit_age_h": self.last_audit_age_h,
            "render_proof_exists": self.render_proof_exists,
            "niagara_default_material_count": self.niagara_default_material_count,
            "flipbook_authority_ok": self.flipbook_authority_ok,
            "validate_errors": self.validate_errors,
            "kawaii_tune_ok": self.kawaii_tune_ok,
            "hair_tick_flags_ok": self.hair_tick_flags_ok,
            "blend_verified": self.blend_verified,
            "shp_bone_match": self.shp_bone_match,
            "open_defect": self.open_defect,
            "editor_up": self.editor_up,
            "dirty_count": self.dirty_count,
            "disk_gb_free_c": self.disk_gb_free_c,
            "time_budget_min": self.time_budget_min,
            "focused_level": self.focused_level,
            "current_action": self.current_action,
            "seconds_since_last_action": round(self.seconds_since_last_action, 1),
            "levels": list(LEVELS),
        }
        return {k: v for k, v in ((k, _drop_none(val)) for k, val in raw.items()) if v is not None}


def _drop_none(value: Any) -> Any:
    """Remove None keys. An all-None dict collapses to None (still unknown)."""
    if isinstance(value, dict):
        cleaned: dict[Any, Any] = {}
        for key, item in value.items():
            if item is None:
                continue
            kept = _drop_none(item)
            if kept is None:
                continue
            cleaned[key] = kept
        return cleaned or None
    return value


NEXT_ACTION_CRITERIA: dict[str, Any] = {
    "AUDIT_MATERIAL_INSTANCES": (
        "Per level, every material interface: parent loads and is a Material, "
        "no WorldGridMaterial or <NONE> parents."
    ),
    "AUDIT_MESH_MAPS": (
        "Mesh slot to material instance to BaseColor/Normal/ORM texture params."
    ),
    "AUDIT_NIAGARA_FLIPBOOK": (
        "Presenter NS_Melusina_* flipbook authority, grid/fps, bounds, effect type, "
        "validate_system, non-black preview."
    ),
    "AUDIT_HAIR_CHAIN": (
        "UE Kawaii tune, WaterHairMesh tick flags, hair bones, plus the "
        "read-only Blender SHP/DEF bone match."
    ),
    "APPLY_FIX": (
        "Execute exactly one receipt-named fix. Owner saves. Never without a named defect."
    ),
    "RENDER_PROOF": (
        "Per-level beauty still only when that level's audits are clean and no proof is on disk (L2)."
    ),
    "COOK_TO_G": "Packaged cook to G: only when every showcase level is L3.",
    "HOLD_FOR_OWNER": "Blocked, low disk, or no authored step is justified.",
}

NEEDS_HUMAN_CRITERIA = (
    "An owner decision is required before spending editor, fix, or cook time "
    "(blocked, low disk, or a save-adjacent fix)."
)


@dataclass
class TriageDecision:
    action: str
    action_probs: dict[str, float]
    needs_human: bool
    needs_human_prob: float
    render_ready: Optional[int]
    render_ready_probs: list[float]
    source: str  # jev-live | classical-fallback
    reason: str
    confidence: float = 0.0


def _level_value(mapping: Optional[dict], level: str) -> Any:
    if not mapping or level not in mapping:
        return None
    return mapping[level]


def _named_defect(state: ShowcaseState) -> Optional[str]:
    if state.open_defect is None:
        return None
    name = state.open_defect.strip()
    return name or None


def _capture_extras_ok(state: ShowcaseState) -> Optional[bool]:
    """True when presenter+hair are known clean, False when blocking, None if incomplete."""
    numbers = (state.niagara_default_material_count, state.validate_errors)
    flags = (
        state.flipbook_authority_ok,
        state.kawaii_tune_ok,
        state.hair_tick_flags_ok,
        state.blend_verified,
        state.shp_bone_match,
    )
    if any(n is not None and n > 0 for n in numbers):
        return False
    if any(flag is False for flag in flags):
        return False
    if any(n is None for n in numbers) or any(flag is None for flag in flags):
        return None
    return True


def level_readiness(state: ShowcaseState, level: str) -> Optional[int]:
    """L0..L3 for one authored level. None when the lane is still unknown.

    L0 blocking defects. L1 audited with a receipt-named open fix.
    L2 clean audits, no proof on disk. L3 clean plus render proof on disk.
    """
    if level not in LEVELS:
        return None
    mi = _level_value(state.mi_bad_parent_count, level)
    eng = _level_value(state.engine_default_count, level)
    miss = _level_value(state.missing_texture_count, level)
    proof = _level_value(state.render_proof_exists, level)

    if any(count is not None and count > 0 for count in (mi, eng, miss)):
        return 0
    extras: Optional[bool] = True
    if level == CAPTURE_LEVEL:
        extras = _capture_extras_ok(state)
        if extras is False:
            return 0

    if _named_defect(state):
        return 1

    if any(value is None for value in (mi, eng, miss, proof)):
        return None
    if extras is None:
        return None
    return 3 if proof else 2


def showcase_render_ready(state: ShowcaseState) -> Optional[int]:
    """Worst known level. Unknown stays None — a missing lane is not L0."""
    scores = [level_readiness(state, level) for level in LEVELS]
    if any(score == 0 for score in scores):
        return 0
    if _named_defect(state):
        return 1
    if any(score is None for score in scores):
        return None
    known = [score for score in scores if score is not None]
    return min(known) if known else None


def resolve_focus(state: ShowcaseState) -> str:
    if state.focused_level in LEVELS:
        return state.focused_level
    for level in LEVELS:
        if level_readiness(state, level) != 3:
            return level
    return CAPTURE_LEVEL


def _hair_flags_unknown(state: ShowcaseState) -> bool:
    """UE hair flags. Tick flags are the 09-21 damage; Kawaii tune rides the same lane."""
    return state.hair_tick_flags_ok is None or state.kawaii_tune_ok is None


def _mi_unknown(state: ShowcaseState, level: str) -> bool:
    return (
        _level_value(state.mi_bad_parent_count, level) is None
        or _level_value(state.engine_default_count, level) is None
    )


def _mesh_unknown(state: ShowcaseState, level: str) -> bool:
    return _level_value(state.missing_texture_count, level) is None


def _niagara_unknown(state: ShowcaseState) -> bool:
    return (
        state.niagara_default_material_count is None
        or state.flipbook_authority_ok is None
        or state.validate_errors is None
    )


def _renorm(probs: dict[str, float]) -> dict[str, float]:
    total = sum(probs.values()) or 1.0
    return {key: round(value / total, 4) for key, value in probs.items()}


def _score_probs(score: Optional[int]) -> list[float]:
    if score is None:
        return [0.25, 0.25, 0.25, 0.25]
    probs = [0.05, 0.05, 0.05, 0.05]
    probs[score] = 0.85
    total = sum(probs)
    return [round(value / total, 4) for value in probs]


def _pack(action: str, reason: str, state: ShowcaseState) -> TriageDecision:
    probs = {name: 0.02 for name in NEXT_ACTIONS}
    probs[action] = 0.88
    probs = _renorm(probs)
    needs_human = action in ("HOLD_FOR_OWNER", "APPLY_FIX")
    ready = showcase_render_ready(state)
    return TriageDecision(
        action=action,
        action_probs=probs,
        needs_human=needs_human,
        needs_human_prob=0.9 if needs_human else 0.15,
        render_ready=ready,
        render_ready_probs=_score_probs(ready),
        source="classical-fallback",
        reason=reason,
        confidence=round(max(probs.values()), 3),
    )


def classical_fallback(state: ShowcaseState) -> TriageDecision:
    """Deterministic rules. source=classical-fallback. Never Jev evidence.

    Mostly-unknown order: hair flags unknown, otherwise material instances
    on the capture level. Disk under 20 GB holds. COOK_TO_G only when every
    level is L3. RENDER_PROOF only when the focused level is L2. APPLY_FIX
    only when a receipt names an open defect.
    """
    focus = resolve_focus(state)
    if state.disk_gb_free_c is not None and state.disk_gb_free_c < 20:
        return _pack("HOLD_FOR_OWNER", "C: disk low: free space under 20 GB", state)
    if all(level_readiness(state, level) == 3 for level in LEVELS):
        return _pack("COOK_TO_G", "every showcase level is L3: cook to G:", state)
    if level_readiness(state, focus) == 2:
        return _pack("RENDER_PROOF", f"focused level is L2: render proof for {focus}", state)
    defect = _named_defect(state)
    if defect:
        return _pack("APPLY_FIX", f"receipt names an open defect: {defect}", state)
    if _hair_flags_unknown(state):
        return _pack("AUDIT_HAIR_CHAIN", "hair flags unknown: audit the hair chain", state)
    if _mi_unknown(state, CAPTURE_LEVEL):
        return _pack(
            "AUDIT_MATERIAL_INSTANCES",
            f"material instances unknown on capture level: {CAPTURE_LEVEL}",
            state,
        )
    if _mesh_unknown(state, focus):
        return _pack("AUDIT_MESH_MAPS", f"mesh maps unknown on {focus}", state)
    if _niagara_unknown(state):
        return _pack("AUDIT_NIAGARA_FLIPBOOK", "presenter niagara flipbook lane unknown", state)
    if state.blend_verified is None or state.shp_bone_match is None:
        return _pack("AUDIT_HAIR_CHAIN", "blender hair chain still unknown", state)
    return _pack("HOLD_FOR_OWNER", "no authored step is justified yet", state)


def _hold_for_failure(exc: BaseException) -> TriageDecision:
    probs = _renorm({name: (0.88 if name == "HOLD_FOR_OWNER" else 0.02) for name in NEXT_ACTIONS})
    return TriageDecision(
        action="HOLD_FOR_OWNER",
        action_probs=probs,
        needs_human=True,
        needs_human_prob=0.95,
        render_ready=None,
        render_ready_probs=_score_probs(None),
        source="classical-fallback",
        reason=f"jev-live failed, holding: {type(exc).__name__}",
        confidence=0.9,
    )


def _try_jev_live(state: ShowcaseState) -> Optional[TriageDecision]:
    """One system_one call: Choice + Noul + Score. Key comes from the environment.

    Missing TYPESAFE_API_KEY returns None so the deterministic fallback can run.
    SDK or service exceptions return HOLD with source=classical-fallback and the
    exception type in the reason. The key is never printed, logged, or written.
    """
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        return None
    try:
        from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

        questions = {
            "next": Choice(
                instructions=(
                    "Pick the single best next showcase-prep step from the authored set. "
                    "Audit unknown lanes before fixes. APPLY_FIX only for a receipt-named "
                    "open defect. RENDER_PROOF only at L2. COOK_TO_G only when every level is L3."
                ),
                criteria=NEXT_ACTION_CRITERIA,
            ),
            "human": Noul(
                instructions="Should an owner decide before spending editor, fix, or cook time?",
                criteria={
                    "true": NEEDS_HUMAN_CRITERIA,
                    "false": "The state is unambiguous enough to proceed without the owner.",
                },
            ),
            "render_ready": Score(
                instructions=(
                    "How render-ready is the showcase? Missing fields are unknown, not zero. "
                    "L0 blocking defects, L1 audited with open fixes, "
                    "L2 clean audits no proof, L3 clean plus render proof on disk."
                ),
                criteria=RENDER_READY_LEVELS,
            ),
        }
        with TypeSafeClient(api_key=key) as client:
            resp = client.system_one(state=state.to_jev_state(), questions=questions)
        nxt = resp.choices["next"]
        hum = resp.nouls["human"]
        scored = resp.scores["render_ready"]
        action = nxt.choice if nxt.choice in NEXT_ACTIONS else "HOLD_FOR_OWNER"
        probs = {k: float(v) for k, v in (nxt.probabilities or {}).items() if k in NEXT_ACTIONS}
        if action not in probs:
            probs[action] = float(nxt.confidence or 0.5)
        raw_score = getattr(scored, "score", None)
        if raw_score is None:
            ready: Optional[int] = None
        else:
            ready = max(0, min(len(RENDER_READY_LEVELS) - 1, int(round(float(raw_score)))))
        cap_probs = [float(p) for p in (scored.probabilities or [])]
        if not cap_probs:
            cap_probs = _score_probs(ready)
        return TriageDecision(
            action=action,
            action_probs=probs,
            needs_human=bool(hum.noul > 0.5),
            needs_human_prob=float(hum.noul),
            render_ready=ready,
            render_ready_probs=cap_probs,
            source="jev-live",
            reason="typesafe System One Choice+Noul+Score",
            confidence=float(nxt.confidence or 0.0),
        )
    except Exception as exc:
        return _hold_for_failure(exc)


def triage(state: ShowcaseState, live_enabled: bool = True) -> TriageDecision:
    """Entry point. Cooldown/hysteresis keeps prep phrasing, not twitching."""
    raw: Optional[TriageDecision] = None
    if live_enabled:
        raw = _try_jev_live(state)
    if raw is None:
        raw = classical_fallback(state)
    if (
        state.seconds_since_last_action < MIN_HOLD_SECONDS
        and state.current_action in NEXT_ACTIONS
        and raw.action != state.current_action
    ):
        cur_p = raw.action_probs.get(state.current_action, 0.0)
        top_p = raw.action_probs.get(raw.action, 0.0)
        if not (top_p - cur_p >= SWITCH_MARGIN or raw.confidence >= CONF_SWITCH_GATE):
            return TriageDecision(
                action=state.current_action,
                action_probs=dict(raw.action_probs),
                needs_human=raw.needs_human,
                needs_human_prob=raw.needs_human_prob,
                render_ready=raw.render_ready,
                render_ready_probs=list(raw.render_ready_probs),
                source=raw.source,
                reason=raw.reason + " | held by cooldown",
                confidence=raw.confidence,
            )
    return raw


def hud(decision: TriageDecision) -> str:
    top_alt = sorted(decision.action_probs.items(), key=lambda kv: -kv[1])[:2]
    alt = f" alt {top_alt[1][0]} {top_alt[1][1]:.2f}" if len(top_alt) > 1 else ""
    if decision.render_ready is None:
        ready = "unknown"
    else:
        ready = f"L{decision.render_ready} [{RENDER_READY_LEVELS[decision.render_ready]}]"
    human = "YES" if decision.needs_human else "no"
    return (
        "JEV SHOWCASE PREP\n"
        f"Action: {decision.action} {decision.action_probs.get(decision.action, 0.0):.2f}{alt}\n"
        f"Human: {human} {decision.needs_human_prob:.2f} | Render-ready: {ready}\n"
        f"Source: {decision.source} | {decision.reason}"
    )
