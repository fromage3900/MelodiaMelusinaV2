#!/usr/bin/env python3
"""Validate that Melodia's agent front door reflects the current production era.

This is intentionally a small, stdlib-only regression guard. It does not decide whether
an implementation is LIVE PROVEN; CURRENT_STATE.md owns that evidence. It only prevents
the repository's first-read context from regressing to the old prototype/convergence
worldview after the capability-surface refresh lands.

Run from the repository root:
    python Tools/validate_agent_frontdoor.py

A failure should normally be fixed by correcting AGENTS.md / CURRENT_STATE.md, not by
weakening this guard. If a capability genuinely stops existing, update the guard and the
canonical status in the same reviewed change.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
STATE = ROOT / "CURRENT_STATE.md"
SYSTEM_MAP = ROOT / "SYSTEM_MAP.md"
DATA_FLOW = ROOT / "DATA_FLOW.md"
PLAYBOOK = ROOT / "Docs" / "Production" / "AGENT_PRODUCTION_PLAYBOOK.md"
RIDER_RUNBOOK = ROOT / "Docs" / "Production" / "RIDER_UE58_CANONICAL_WORKFLOW.md"


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        fail(f"missing required front-door file: {path.relative_to(ROOT)}")
        return ""


def fail(message: str) -> None:
    FAILURES.append(message)


def require(text: str, pattern: str, where: str, *, flags: int = re.IGNORECASE) -> None:
    if not re.search(pattern, text, flags):
        fail(f"{where}: missing required capability signal /{pattern}/")


def forbid(text: str, phrase: str, where: str) -> None:
    if phrase.lower() in text.lower():
        fail(f"{where}: stale worldview still present: {phrase!r}")


FAILURES: list[str] = []

agents = read(AGENTS)
state = read(STATE)
system_map = read(SYSTEM_MAP)
data_flow = read(DATA_FLOW)
playbook = read(PLAYBOOK)
rider_runbook = read(RIDER_RUNBOOK)

# 1) The first-read operating mode must be content-first, not prototype archaeology.
require(agents, r"core\s+(?:already\s+)?works|working\s+core", "AGENTS.md")
require(agents, r"author(?:ing)?\s+content|content[- ]first", "AGENTS.md")
require(agents, r"Can .* be authored .* systems|before changing architecture", "AGENTS.md")
forbid(agents, "The current job is convergence, not construction.", "AGENTS.md")
forbid(agents, "Rhythm and wardrobe still have competing or prototype authorities.", "AGENTS.md")

# 2) CURRENT_STATE must expose capabilities as usable creative vocabulary near the front door.
require(state, r"Proven Creative Capability Surface|Creative Capability Surface", "CURRENT_STATE.md")
require(state, r"What to reach for|reach for", "CURRENT_STATE.md")

# 3) The capability surface must mention the production lanes agents should compose with.
# Keep these broad enough to tolerate wording changes, but specific enough to catch regressions.
required_state_signals = {
    "Quill narrative": r"QuillScript|Quill",
    "authoritative JRPG battle": r"TurnBased JRPG|Phoenix",
    "rhythm integration": r"rhythm",
    "wardrobe": r"Wardrobe",
    "UE PCG": r"\bPCG\b",
    "UE/Python authoring": r"Content/Python/pcg|Python.*PCG|PCG.*Python",
    "Houdini Engine": r"Houdini Engine",
    "Hython": r"\bHython\b|\bhython\b",
    "Copernicus": r"Copernicus",
    "cymatics/Chladni": r"cymatic|Chladni",
    "materials/shaders": r"material|shader",
    "UI skill": r"melodia-ui-artist",
}
for label, pattern in required_state_signals.items():
    if not re.search(pattern, state, re.IGNORECASE):
        fail(f"CURRENT_STATE.md: capability surface lost {label} signal /{pattern}/")

# 4) The canonical production-tool router must remain discoverable and name the current lanes.
for text, where in ((agents, "AGENTS.md"), (state, "CURRENT_STATE.md")):
    require(text, r"AGENT_PRODUCTION_PLAYBOOK\.md", where)
    require(text, r"world_compiler\.py|World Compiler", where)
    require(text, r"Hython|hython", where)
    require(text, r"Rokoko", where)
    require(text, r"Rider", where)

for pattern, label in (
    (r"world_compiler\.py", "World Compiler CLI"),
    (r"Tools/Houdini/", "Hython tool family"),
    (r"import_rokoko_mocap_batch\.py", "guarded Rokoko importer"),
    (r"RIDER_UE58_CANONICAL_WORKFLOW\.md", "Rider runbook"),
    (r"one Unreal Editor|one editor", "single-editor rule"),
):
    if not re.search(pattern, playbook, re.IGNORECASE):
        fail(f"AGENT_PRODUCTION_PLAYBOOK.md: missing {label} signal /{pattern}/")

require(rider_runbook, r"BS_GodFileEditor Win64 Development", "RIDER_UE58_CANONICAL_WORKFLOW.md")
require(rider_runbook, r"reflected|UCLASS|UFUNCTION|UPROPERTY", "RIDER_UE58_CANONICAL_WORKFLOW.md")
require(rider_runbook, r"World Compiler", "RIDER_UE58_CANONICAL_WORKFLOW.md")
require(rider_runbook, r"Rokoko", "RIDER_UE58_CANONICAL_WORKFLOW.md")

# 5) The runtime architecture must still teach renewable-content-over-stable-core.
require(system_map, r"stable runtime ownership beneath renewable authored content", "SYSTEM_MAP.md")
require(system_map, r"content integration problem", "SYSTEM_MAP.md")
require(data_flow, r"New content extends the vocabulary", "DATA_FLOW.md")

# 6) Guard the most important compositional affordance: working battle content should be
# represented as Quill -> JRPG/Phoenix -> rhythm -> result/consequence rather than a new combat system.
flow_blob = "\n".join((state, system_map, data_flow))
for pattern, label in (
    (r"Quill", "Quill"),
    (r"Phoenix|TurnBased JRPG", "JRPG/Phoenix"),
    (r"rhythm", "rhythm"),
    (r"result|consequence", "result/consequence"),
):
    if not re.search(pattern, flow_blob, re.IGNORECASE):
        fail(f"front-door flow no longer exposes {label}")

if FAILURES:
    print("AGENT FRONT-DOOR CONTRACT: FAIL")
    for item in FAILURES:
        print(f" - {item}")
    print("\nExpected after the capability refresh: fresh agents should default to composing")
    print("with the proven gameplay/procedural/art stack instead of reopening old architecture.")
    sys.exit(1)

print("AGENT FRONT-DOOR CONTRACT: PASS")
print("Fresh-agent context exposes the content-first capability surface, stable owners, and canonical production-tool router.")
