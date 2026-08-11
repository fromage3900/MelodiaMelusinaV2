"""Validate relative Markdown links that point to local project files."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")
THREAD_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f-]{27,}$", re.IGNORECASE)


def main() -> int:
    """Validate doc links."""
    missing = []
    checked = 0

    docs = [
        ROOT / "README.md",
        ROOT / "DOC_INDEX.md",
        *sorted((ROOT / "Docs").rglob("*.md")),
    ]

    for doc in docs:
        if not doc.exists():
            continue

        for raw in LINK.findall(doc.read_text(encoding="utf-8", errors="replace")):
            target = raw.split("#", 1)[0].strip().strip("<>")

            if not target:
                continue
            if "://" in target:
                continue
            if target.startswith("mailto:"):
                continue

            if THREAD_ID.match(target):
                continue

            checked += 1

            if not (doc.parent / target).resolve().exists():
                missing.append({
                    "source": str(doc.relative_to(ROOT).as_posix()),
                    "target": target,
                })

    print({
        "checked": checked,
        "missing": len(missing),
        "examples": missing[:20],
    })

    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
