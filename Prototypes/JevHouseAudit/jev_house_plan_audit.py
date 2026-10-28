"""Jev plan-audit: melodia::house assembler track (system-one-conductor shape).

One Choice (next block) + one Choice (riskiest assumption) + one Noul
(owner gate) + one Score (readiness) in a single system_one call.
Model route "beam" with response_format json_object, per owner instruction.
Classical fallback is labeled and never presented as model evidence.
"""
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime

NEXT_BLOCK = {
    "ASSEMBLER_GREEN": "Finish house.py: joint/stair/roof pass, pure-python gate green on SALON_FIRST.",
    "PACKAGER": "Build melodia::house::1.0 subnet (arch + PCG scatter branch, full parm folders/menus).",
    "UE_STAGE": "Import refreshed salon_bay, instantiate STAGE actor, idle-editor cook + readback.",
    "COMMIT_DOCS": "Receipts, stack-pin update, force-add reviewed files, status closeout.",
}
RISKIEST = {
    "JOINT_GEOMETRY": "Snapped-room joint trim orientation/winding is wrong in UE.",
    "SOCKET_TRANSFORM": "Portal frame yaw/offset math misplaces linked rooms.",
    "UE_COOK_SCALE": "Full-house cook OOMs or signal-11s like the 2026-10-22 RoomShell cook.",
    "ROOF_PITCH": "Mansard/conical roof sweep self-intersects on some footprint.",
}
HUMAN_CRITERIA = {
    "proceed": "Owner input is required before agents run the next block.",
    "go": "Agents may proceed without waiting for the owner.",
}
READINESS_LEVELS = ["blocked", "fragile", "partial", "ready", "proven"]


@dataclass
class PlanState:
    assembler_smoke: str  # red | green
    variants_refresh: str  # e.g. 7/7 admit
    editor: str  # blocked | idle
    packager: str  # pending | done
    ue_stage: str  # blocked | done

    def to_jev_state(self):
        return dict(assembler_smoke=self.assembler_smoke,
                    variants_refresh=self.variants_refresh,
                    editor=self.editor, packager=self.packager,
                    ue_stage=self.ue_stage)


def classical_fallback(state):
    order = "ASSEMBLER_GREEN"
    return dict(
        order=order,
        order_probs={k: round(0.7 if k == order else 0.1, 4) for k in NEXT_BLOCK},
        riskiest="UE_COOK_SCALE",
        riskiest_probs={k: round(0.55 if k == "UE_COOK_SCALE" else 0.15, 4) for k in RISKIEST},
        needs_human=True, needs_human_prob=0.8, readiness=2,
        readiness_probs=[0.05, 0.15, 0.6, 0.15, 0.05],
        source="classical-fallback",
        reason="assembler gate is the only red item agents can clear without the editor",
        confidence=0.7)


def try_jev_live(state):
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        return None
    try:
        from typesafe_sdk import TypeSafeClient
    except Exception:
        return None
    try:
        with TypeSafeClient(api_key=key) as client:
            resp = client.system_one(
                state=state.to_jev_state(),
                questions={
                    "order": {"type": "choice",
                              "instructions": "Pick the single next Hython block that unblocks the working house system fastest.",
                              "criteria": NEXT_BLOCK},
                    "riskiest": {"type": "choice",
                                 "instructions": "Which plan assumption is riskiest - most likely to invalidate the build if wrong?",
                                 "criteria": RISKIEST},
                    "human": {"type": "noul",
                              "instructions": "Does an owner decision gate execution before agents run the next block?",
                              "criteria": HUMAN_CRITERIA},
                    "readiness": {"type": "score",
                                  "instructions": "How execution-ready is the house track as evidenced by the state facts?",
                                  "criteria": READINESS_LEVELS},
                },
                model="beam",
                extra_body={"response_format": {"type": "json_object"}},
                timeout=120.0,
            )
            ans = resp.answers
            o, r, h, s = ans["order"], ans["riskiest"], ans["human"], ans["readiness"]
            pick_o = o.choice if o.choice in NEXT_BLOCK else "ASSEMBLER_GREEN"
            pick_r = r.choice if r.choice in RISKIEST else "UE_COOK_SCALE"
            return dict(
                order=pick_o,
                order_probs={k: float(v) for k, v in (o.probabilities or {}).items() if k in NEXT_BLOCK},
                riskiest=pick_r,
                riskiest_probs={k: float(v) for k, v in (r.probabilities or {}).items() if k in RISKIEST},
                needs_human=bool(h.noul is not None and h.noul > 0.5),
                needs_human_prob=float(h.noul or 0.0),
                readiness=int(s.score or 0),
                readiness_probs=[float(p) for p in (s.probabilities or [])],
                source="jev-live", reason="beam system_one Choice+Choice+Noul+Score, one call",
                confidence=float(o.confidence or 0.0))
    except Exception as exc:
        fb = classical_fallback(state)
        fb["reason"] = "jev-live failed (%s), classical fallback" % type(exc).__name__
        return fb


def main():
    state = PlanState(assembler_smoke="red", variants_refresh="7/7 admit",
                      editor="blocked", packager="pending", ue_stage="blocked")
    decision = try_jev_live(state) or classical_fallback(state)
    log = dict(schema="melodia.jev_house_plan_audit.v1",
               date=datetime.now().isoformat(timespec="seconds"),
               state=state.to_jev_state(), decision=decision)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "house_audit_%s.json" % datetime.now().strftime("%Y%m%d_%H%M%S"))
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(log, fh, indent=2)
    print(json.dumps(decision, indent=2))
    print("receipt: " + out)


if __name__ == "__main__":
    main()
