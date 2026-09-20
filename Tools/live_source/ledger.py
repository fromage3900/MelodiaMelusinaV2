"""Live animation source creation — session ledger for Melusina.

One ledger for all three capture sources (Rokoko suit, Cascadeur video-mocap,
OBSBOT fixed cam), using the evidence ladder from
Docs/CASCADEUR_MELUSINA_PIPELINE_2026-08-07.md §11 verbatim. A take advances
up the ladder only with a receipt; the ledger is how a session remembers
what is CAPTURE-PROVEN vs merely SOURCE-PREPARED.

Authority docs (read before changing contracts here):
- Docs/CASCADEUR_MELUSINA_PIPELINE_2026-08-07.md  (durable animation contract)
- Docs/Plans/ROKOKO_UE_EVENING_PIPELINE_2026-09-09.md (Rokoko UE lane)
- Docs/Handoffs/MELUSINA_MEET2_OBSBOT_STUDIO_2026-09-08.md (camera presets)
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict

LEDGER_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "Saved", "Audit",
    "live_source", "session_ledger.json",
)

# §11 evidence ladder — order matters; a take may only advance one rung
# when its gate receipt exists. Labels are exact strings, do not paraphrase.
EVIDENCE_LADDER = [
    "SOURCE_PREPARED",
    "CAPTURE_PROVEN",
    "RETARGET_PROVEN",      # / ANIMATION-PROVEN
    "LIVE_LINK_PROVEN",     # only when applicable
    "IN_GAME_PROVEN",
    "PACKAGED_PROVEN",
]

# Hard gate from ROKOKO_UE_EVENING_PIPELINE: a neck warp stops library
# recording — blockers are first-class ledger state, not prose.
STOP_CONDITIONS = ("neck_warp", "skeleton_mismatch", "axis_mismatch")


@dataclass
class Take:
    take_id: str                 # <SOURCE>_<Verb>_<YYYYMMDD>_<NN>
    source: str                  # ROKOKO | CASCADEUR | OBSBOT
    verb: str                    # Idle, WalkLoop, HarpBow, ...
    path: str                    # authoritative file for this rung
    evidence: str = "SOURCE_PREPARED"
    checks: dict = field(default_factory=dict)   # preflight results by name
    blockers: list[str] = field(default_factory=list)
    receipts: list[str] = field(default_factory=list)  # receipt file paths
    updated: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(self.updated))
        return d


class Ledger:
    def __init__(self, path: str = LEDGER_PATH):
        self.path = path
        self.takes: dict[str, Take] = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for d in json.load(f).get("takes", []):
                    d.pop("updated", None)
                    t = Take(**d)
                    self.takes[t.take_id] = t

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"schema": "melodia.live_source/v1",
                       "takes": [t.to_dict() for t in self.takes.values()]},
                      f, indent=2, sort_keys=True)

    def upsert(self, take: Take) -> None:
        old = self.takes.get(take.take_id)
        if old and take.evidence != old.evidence:
            # Ladder discipline: advancing requires a receipt; skipping
            # rungs or demoting without a blocker note is rejected here.
            oi, ni = EVIDENCE_LADDER.index(old.evidence), EVIDENCE_LADDER.index(take.evidence)
            if ni > oi and not take.receipts:
                raise ValueError(f"{take.take_id}: advance {old.evidence} -> {take.evidence} "
                                 f"requires a receipt path")
            if ni < oi and not take.blockers:
                raise ValueError(f"{take.take_id}: demotion requires a blocker")
        self.takes[take.take_id] = take

    def next_take_id(self, source: str, verb: str) -> str:
        stamp = time.strftime("%Y%m%d")
        n = sum(1 for k in self.takes
                if k.startswith(f"{source}_{verb}_{stamp}_")) + 1
        return f"{source}_{verb}_{stamp}_{n:02d}"
