"""Jev plan audit — Holo4 overnight eval, next bounded block (2026-10-05).

ISOLATION CONTRACT (per Prototypes/JevLanePlanAudit precedent):
- Everything lives in Prototypes/JevHolo4EvalAudit/. Delete this folder to undo it.
- NO .uasset/.umap writes. NO editor mutations. NO ledger writes. NO Perforce.
- Reads measured facts only; Jev selects among CLOSED option sets and never
  invents a command, path, or task.
- Provenance: source="jev-live" or "classical-fallback" + reason. A fallback run
  is never presented as Jev evidence.

WHY THIS AUDIT EXISTS
---------------------
The Holo4 tool-loop matrix is running overnight (lane `holo4-overnight`). The
question is not "is Holo4 clever" — it is "what is the next bounded block of
work, and which assumption is most likely to invalidate the plan". Jev is the
right instrument because that is a judgment among authored options, and because
its verdict already contains the useful kind of disagreement (it refused a
convenient shortcut once before).

Skill: system-one-conductor. All questions go in ONE system_one call over the
same state; code owns the log and the fallback.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

OUT = Path(__file__).parent / "audit_log.json"

# --- closed option sets -----------------------------------------------------

NEXT_BLOCK = {
    "LET_MATRIX_FINISH": (
        "Change nothing until the 4-task matrix completes. The open question is "
        "whether Holo4 can finish a multi-step task through tools; every other "
        "decision is downstream of that single answer."
    ),
    "FIX_TRUNCATION_FIRST": (
        "Pause the matrix and fix output truncation before spending more tokens: "
        "the verdict measured 6 of 7 responses cut off, so no other result is "
        "readable until a response completes."
    ),
    "RUN_PHASE4_BLENDER": (
        "Run the original Phase 4 Blender sandbox task through the now-working "
        "tool loop, to test the published claim rather than a UE-shaped proxy."
    ),
    "PROMOTE_TO_ROUTER": (
        "Register Holo4 in model_tiers.v1.json and give it a production lane. "
        "Fast, but commits the project to a CC BY-NC model on hardware with 12 GB "
        "VRAM shared against a live editor."
    ),
    "ARCHIVE_AND_STOP": (
        "Keep the weights on D: as a reference implementation of the tool-call "
        "format, claim nothing further, and return the 17 GB of headroom."
    ),
}

RISKIEST_ASSUMPTION = {
    "TRUNCATION_FOREVER": (
        "Truncation is a permanent property of the model at this speed, so no "
        "prompting change can produce a complete answer and the action machine "
        "is unusable regardless of harness quality."
    ),
    "THINKING_BUDGET_TUNABLE": (
        "Truncation is a tunable budget/config problem: --reasoning-budget plus a "
        "larger max_tokens gives complete answers, as the 155.7 s 'stop' result "
        "already showed once."
    ),
    "THROUGHPUT_ON_SHARED_HOST": (
        "1.36 tok/s is a property of a contended host. On a closed-editor or "
        "dedicated machine it may be several times faster, making the model "
        "practical."
    ),
    "COMPUTE_IS_THE_BOUNDING_CONSTRAINT": (
        "The real ceiling is this machine's 12 GB VRAM and 71.8 GB commit limit, "
        "not the model. Even a perfect harness yields 12-24 min per answer here."
    ),
    "GROUNDING_HOLDS_ON_LIVE_SOURCE": (
        "The 17/17 verbatim-quote result was measured on a small fixture. Real "
        "1328-line production source may produce confident false citations, which "
        "would make it unsafe even for review."
    ),
    "NONE_MATERIAL": "No assumption is materially risky; proceed as written.",
}

NEEDS_HUMAN = {
    "true": (
        "An owner decision gates the next block — licence/commercial call, "
        "closing the live editor, or accepting non-commercial dependency."
    ),
    "false": "Agents can execute the next block without any owner decision.",
}

READINESS_LEVELS = [
    "Scaffold only: a loop exists but no multi-step task has ever completed.",
    "Loop proven on safety and liveness; no verified end-to-end task yet.",
    "At least one task completed through tools with an artifact verified on disk.",
    "Multiple task classes pass with hallucination and truncation rates measured.",
    "Stable enough to carry an authored production lane under its licence terms.",
]


# --- state ------------------------------------------------------------------


@dataclass
class EvalState:
    """Measured facts. None = unknown (reads as missing, never as zero)."""

    # matrix run
    tasks_total: int = 4
    tasks_completed: int = 0
    tasks_with_verified_artifact: int = 0
    tool_loop_safety_tests_passing: int = 22
    tool_loop_safety_tests_total: int = 22
    vision_path_verified: bool = True
    server_resident_no_cold_start: bool = True

    # measured performance
    gen_tokens_per_s: float = 1.36
    prompt_tokens_per_s: float = 15.4
    reasoning_budget: int = 250
    truncated_responses_of_7: int = 6
    measured_clean_stop_result: bool = True   # 155.7s, finish_reason=stop

    # grounding
    prior_quotes_verified: int = 17
    prior_quotes_total: int = 17
    prior_fabrications: int = 0

    # host constraints
    vram_total_gb: int = 12
    commit_limit_gb: float = 71.8
    commit_available_gb: float = 15.3
    live_editor_open: bool = True
    licence_allows_commercial: bool = False

    def to_jev_state(self) -> dict[str, Any]:
        raw: dict[str, Any] = {
            "tasks_total": self.tasks_total,
            "tasks_completed": self.tasks_completed,
            "tasks_with_verified_artifact": self.tasks_with_verified_artifact,
            "tool_loop_safety_tests_passing": self.tool_loop_safety_tests_passing,
            "tool_loop_safety_tests_total": self.tool_loop_safety_tests_total,
            "vision_path_verified": self.vision_path_verified,
            "server_resident_no_cold_start": self.server_resident_no_cold_start,
            "gen_tokens_per_s": self.gen_tokens_per_s,
            "prompt_tokens_per_s": self.prompt_tokens_per_s,
            "reasoning_budget": self.reasoning_budget,
            "truncated_responses_of_7": self.truncated_responses_of_7,
            "measured_clean_stop_result": self.measured_clean_stop_result,
            "prior_quotes_verified": self.prior_quotes_verified,
            "prior_quotes_total": self.prior_quotes_total,
            "prior_fabrications": self.prior_fabrications,
            "vram_total_gb": self.vram_total_gb,
            "commit_limit_gb": self.commit_limit_gb,
            "commit_available_gb": self.commit_available_gb,
            "live_editor_open": self.live_editor_open,
            "licence_allows_commercial": self.licence_allows_commercial,
        }
        return {k: v for k, v in raw.items() if v is not None}


@dataclass
class AuditDecision:
    next_block: str
    next_block_probs: dict[str, float]
    riskiest: str
    riskiest_probs: dict[str, float]
    needs_human: bool
    needs_human_prob: float
    readiness: int
    readiness_probs: list[float]
    source: str
    reason: str
    confidence: float = 0.0


# --- classical fallback -----------------------------------------------------


def classical_fallback(state: EvalState) -> AuditDecision:
    """Deterministic rules, clearly labeled. Never Jev evidence."""
    nb = {k: 0.04 for k in NEXT_BLOCK}
    nb["LET_MATRIX_FINISH"] = 0.68
    nb["ARCHIVE_AND_STOP"] = 0.12
    nb["FIX_TRUNCATION_FIRST"] = 0.12
    reason = ("the matrix is mid-run and every other decision depends on its "
              "single open answer")

    rp = {k: 0.03 for k in RISKIEST_ASSUMPTION}
    rp["COMPUTE_IS_THE_BOUNDING_CONSTRAINT"] = 0.52
    rp["THINKING_BUDGET_TUNABLE"] = 0.21
    # Normalize: an unnormalized map is not a distribution. The contract test
    # caught this at 0.85, which is exactly the index/malformed-list defect the
    # live guard rejects - the fallback must not model it.
    rp_total = sum(rp.values())
    rp = {k: round(v / rp_total, 4) for k, v in rp.items()}

    readiness = 2  # loop proven on safety+liveness; no verified task yet
    return AuditDecision(
        next_block="LET_MATRIX_FINISH",
        next_block_probs={k: round(v, 4) for k, v in nb.items()},
        riskiest="COMPUTE_IS_THE_BOUNDING_CONSTRAINT",
        riskiest_probs={k: round(v, 4) for k, v in rp.items()},
        needs_human=False,
        needs_human_prob=0.4,
        readiness=readiness,
        readiness_probs=[0.03, 0.57, 0.31, 0.07, 0.02],
        source="classical-fallback",
        reason=reason,
        confidence=0.68,
    )


# --- live Jev ----------------------------------------------------------------


def _key_is_usable(key: str) -> bool:
    """A poisoned key fails LATE and opaquely as an illegal HTTP header.

    Per skill: it must start with apikey_ and contain no whitespace. Fail fast.
    """
    return bool(key) and key.startswith("apikey_") and not any(c.isspace() for c in key)


def _try_jev_live(state: EvalState) -> Optional[AuditDecision]:
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        return None
    if not _key_is_usable(key):
        fb = classical_fallback(state)
        fb.reason = (f"key shape invalid (not apikey_-prefixed / contains "
                     f"whitespace) - would fail late as Illegal header value; "
                     f"classical fallback. {fb.reason}")
        return fb
    # Let the import raise. A bare try/except here would relabel a live run as a
    # fallback whose reason string then lies about the cause.
    from typesafe_sdk import TypeSafeClient  # type: ignore

    try:
        with TypeSafeClient(api_key=key) as client:
            resp = client.system_one(
                state=state.to_jev_state(),
                questions={
                    "next_block": {
                        "type": "choice",
                        "instructions": (
                            "Which single next step should be taken on the Holo4 "
                            "computer-use evaluation? The 4-task tool-loop matrix "
                            "is running right now. Choose the one bounded block "
                            "of work that best advances the question 'can this "
                            "model complete a multi-step task through tools, with "
                            "output anyone verifies'."
                        ),
                        "criteria": NEXT_BLOCK,
                    },
                    "riskiest": {
                        "type": "choice",
                        "instructions": (
                            "Which assumption is most likely to invalidate every "
                            "other conclusion about this model? Choose the one "
                            "that, if wrong, changes what the whole evaluation is "
                            "for."
                        ),
                        "criteria": RISKIEST_ASSUMPTION,
                    },
                    "human": {
                        "type": "noul",
                        "instructions": (
                            "Does an owner decision gate the next block of work?"
                        ),
                        "criteria": NEEDS_HUMAN,
                    },
                    "readiness": {
                        "type": "score",
                        "instructions": (
                            "How ready is this tool-loop evaluation to carry real "
                            "authored work, given that the safety fence passes, "
                            "the vision path is verified, and no multi-step task "
                            "has yet completed with a verified artifact?"
                        ),
                        "criteria": READINESS_LEVELS,
                    },
                },
            )
        ans = resp.answers
        nb = ans["next_block"]
        ri = ans["riskiest"]
        hu = ans["human"]
        rd = ans["readiness"]

        nb_probs = {k: float(v) for k, v in (nb.probabilities or {}).items()
                    if k in NEXT_BLOCK}
        ri_probs = {k: float(v) for k, v in (ri.probabilities or {}).items()
                    if k in RISKIEST_ASSUMPTION}

        # Distributional validity: an index list is a valid list of floats, so a
        # NaN/type check never catches it. The honest test is that every value is
        # in [0,1] AND the sum is 1.
        def is_dist(p: dict[str, float]) -> bool:
            return bool(p) and all(0.0 <= v <= 1.0 for v in p.values()) \
                and abs(sum(p.values()) - 1.0) <= 1e-3

        rd_probs = [float(p) for p in (rd.probabilities or [])]
        rd_ok = len(rd_probs) == len(READINESS_LEVELS) \
            and all(0.0 <= p <= 1.0 for p in rd_probs) \
            and abs(sum(rd_probs) - 1.0) <= 1e-3

        notes: list[str] = []
        if not is_dist(nb_probs):
            notes.append("next_block distribution malformed")
            nb_probs = {}
        if not is_dist(ri_probs):
            notes.append("riskiest distribution malformed")
            ri_probs = {}
        if not rd_ok:
            notes.append("readiness distribution malformed (index list?)")
            rd_probs = []

        nb_pick = nb.choice if nb.choice in NEXT_BLOCK else "LET_MATRIX_FINISH"
        ri_pick = ri.choice if ri.choice in RISKIEST_ASSUMPTION \
            else "COMPUTE_IS_THE_BOUNDING_CONSTRAINT"
        rd_pick = int(rd.score) if isinstance(rd.score, int) \
            and 0 <= rd.score < len(READINESS_LEVELS) else 2

        return AuditDecision(
            next_block=nb_pick,
            next_block_probs=nb_probs,
            riskiest=ri_pick,
            riskiest_probs=ri_probs,
            needs_human=bool(hu.noul is not None and hu.noul > 0.5),
            needs_human_prob=float(hu.noul or 0.0),
            readiness=rd_pick,
            readiness_probs=rd_probs,
            source="jev-live",
            reason=("typesafe System One Choice+Choice+Noul+Score in one call; "
                    + ("; ".join(notes) if notes else "all distributions valid")),
            confidence=float(nb.confidence or 0.0),
        )
    except Exception as exc:  # service failure is not a decision
        fb = classical_fallback(state)
        fb.reason = f"jev-live failed ({type(exc).__name__}: {exc}); classical fallback"
        return fb


def main() -> None:
    state = EvalState()
    decision = _try_jev_live(state) or classical_fallback(state)
    log = {
        "schema": "melodia.jev_holo4_eval_audit.v1",
        "date": datetime.now().isoformat(timespec="seconds"),
        "state": state.to_jev_state(),
        "decision": {
            "next_block": decision.next_block,
            "next_block_probs": decision.next_block_probs,
            "riskiest": decision.riskiest,
            "riskiest_probs": decision.riskiest_probs,
            "needs_human": decision.needs_human,
            "needs_human_prob": decision.needs_human_prob,
            "readiness": decision.readiness,
            "readiness_label": READINESS_LEVELS[decision.readiness],
            "readiness_probs": decision.readiness_probs,
            "source": decision.source,
            "reason": decision.reason,
            "confidence": decision.confidence,
        },
    }
    OUT.write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(json.dumps(log["decision"], indent=1))
    print("log:", OUT)


if __name__ == "__main__":
    main()