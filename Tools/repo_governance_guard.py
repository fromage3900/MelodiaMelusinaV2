#!/usr/bin/env python3
"""Lightweight repository-governance gate.

Checks durable discovery contracts and high-value capstone references without
trying to infer runtime truth or mutate project state.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "README.md",
    "CURRENT_STATE.md",
    "AGENT_START_HERE.md",
    "CAPSTONE_NOW.md",
    "CONTRIBUTING.md",
    "REPOSITORY_AUTHORITY.md",
    "Docs/Production/CANONICAL_PROJECT_PIPELINE_2026-09-08.md",
    "Docs/Production/BRANCH_WORKSTATION_POLICY.md",
    "Docs/Art/VISUAL_REFERENCE_INDEX.md",
    "Docs/References/ChoralSheepCapstone/AGENT_CONTEXT.md",
    "Docs/References/ChoralSheepCapstone/REFERENCE_MANIFEST.md",
    "Docs/References/VisualBoards/2026-09-08/ChoralSheep/choral_sheep_creature_fleece.webp",
    "Docs/References/VisualBoards/2026-09-08/ChoralSheep/choral_sheep_chladni_fleece.webp",
    ".github/pull_request_template.md",
]

TEXT_REQUIREMENTS = {
    "AGENT_START_HERE.md": [
        "CURRENT_STATE.md",
        "only current status",
        "not a status document or task queue",
    ],
    "CAPSTONE_NOW.md": [
        "CURRENT_STATE.md",
        "not a task queue",
        "Docs/References/ChoralSheepCapstone/AGENT_CONTEXT.md",
    ],
    "CONTRIBUTING.md": [
        "unrequested cleanup",
    ],
    "Docs/Production/BRANCH_WORKSTATION_POLICY.md": [
        "collab/laptop/longterm",
        "render-queue",
        "WORKSTATION",
        "RECOVERY",
        "UNKNOWN",
    ],
    ".github/pull_request_template.md": [
        "Player / artist outcome",
        "Evidence level",
        "Authority touched",
        "Cleanup justification",
    ],
}


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED_PATHS:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"missing required governance path: {rel}")

    for rel, needles in TEXT_REQUIREMENTS.items():
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for needle in needles:
            if needle not in text:
                errors.append(f"{rel}: missing required marker: {needle!r}")

    if errors:
        print("repo_governance_guard: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("repo_governance_guard: OK")
    print(f"checked {len(REQUIRED_PATHS)} canonical paths")
    return 0


if __name__ == "__main__":
    sys.exit(main())
