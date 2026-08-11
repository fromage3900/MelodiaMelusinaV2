#!/usr/bin/env python3
"""Fix UTF-8 mojibake in Surreal Architecture UI strings (cp1252 mis-decode)."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Unicode code points that cp1252 maps to bytes 0x80-0x9F (not valid in latin-1)
CP1252_HIGH = {
    "\u20ac": 0x80,
    "\u201a": 0x82,
    "\u0192": 0x83,
    "\u201e": 0x84,
    "\u2026": 0x85,
    "\u2020": 0x86,
    "\u2021": 0x87,
    "\u02c6": 0x88,
    "\u2030": 0x89,
    "\u0160": 0x8A,
    "\u2039": 0x8B,
    "\u0152": 0x8C,
    "\u017d": 0x8E,
    "\u0178": 0x9F,
    "\u2018": 0x91,
    "\u2019": 0x92,
    "\u201c": 0x93,
    "\u201d": 0x94,
    "\u2022": 0x95,
    "\u2013": 0x96,
    "\u2014": 0x97,
    "\u2122": 0x99,
    "\u0161": 0x9A,
    "\u203a": 0x9B,
    "\u0153": 0x9D,
    "\u017e": 0x9E,
    "\u0178": 0x9F,
}

MOJIBAKE_MARKERS = (
    "ðŸ", "â€", "Ã", "Â", "â˜", "âœ", "â™", "âš", "â›", "âŠ", "â–", "â­",
    "â¬", "âŒ", "âŸ", "Ï", "â€¢", "â€¦", "â€™", "â€œ", "â€", "â†", "â‰",
    "\u0178", "\u0152", "\u0161", "\u201c", "\u201d", "\u203a",
)


def looks_mojibake(s: str) -> bool:
    if any(m in s for m in MOJIBAKE_MARKERS):
        return True
    if "Ã" in s or "Â" in s:
        return True
    # UTF-8 lead bytes misread as cp1252 (3-byte symbols + 4-byte emoji)
    if "\u00e2" in s or "\u00f0" in s:
        return True
    if "\u00e2" in s and any(c in s for c in CP1252_HIGH):
        return True
    return False


def to_cp1252_bytes(s: str) -> bytes:
    out = bytearray()
    for c in s:
        o = ord(c)
        if o < 128:
            out.append(o)
        elif o < 256:
            out.append(o)
        elif c in CP1252_HIGH:
            out.append(CP1252_HIGH[c])
        else:
            enc = c.encode("cp1252")
            out.extend(enc)
    return bytes(out)


def try_fix_string(s: str) -> str | None:
    if not looks_mojibake(s):
        return None
    # already valid unicode with emoji — skip clean strings
    if any(0x1F300 <= ord(c) <= 0x1FAFF for c in s) and "\u00e2" not in s and "\u00f0" not in s:
        return None
    if any(0x2460 <= ord(c) <= 0x2473 for c in s):  # circled digits ①-⑳
        return None
    try:
        fixed = to_cp1252_bytes(s).decode("utf-8")
    except UnicodeDecodeError:
        return None
    if fixed == s or "\ufffd" in fixed:
        return None
    if looks_mojibake(fixed) and "\u00f0" in fixed:
        # one more pass for double-encoding
        fixed2 = try_fix_string(fixed)
        if fixed2:
            return fixed2
    return fixed


STRING_RE = re.compile(r'(["\'])([^"\\]*(?:\\.[^"\\]*)*)\1')


def fix_line(line: str) -> tuple[str, int]:
    changes = 0

    def _repl(m: re.Match) -> str:
        nonlocal changes
        quote, body = m.group(1), m.group(2)
        fixed = try_fix_string(body)
        if fixed and fixed != body:
            changes += 1
            return f"{quote}{fixed}{quote}"
        return m.group(0)

    return STRING_RE.sub(_repl, line), changes


TRIPLE_QUOTE_RE = re.compile(r'("""|\'\'\')(.*?)\1', re.DOTALL)


def fix_triple_quoted(text: str) -> tuple[str, int]:
    changes = 0

    def _repl(m: re.Match) -> str:
        nonlocal changes
        quote, body = m.group(1), m.group(2)
        fixed = try_fix_string(body)
        if fixed and fixed != body:
            changes += 1
            return f"{quote}{fixed}{quote}"
        return m.group(0)

    return TRIPLE_QUOTE_RE.sub(_repl, text), changes


def fix_comment_suffix(line: str) -> tuple[str, int]:
    if "#" not in line or not looks_mojibake(line):
        return line, 0
    idx = line.find("#")
    prefix, comment = line[: idx + 1], line[idx + 1 :]
    if not looks_mojibake(comment):
        return line, 0
    fixed = try_fix_string(comment)
    if fixed and fixed != comment:
        return prefix + fixed, 1
    return line, 0


def process_file(path: Path, dry_run: bool = False) -> int:
    text = path.read_text(encoding="utf-8", errors="surrogateescape")
    text, triple_n = fix_triple_quoted(text)
    total = triple_n
    new_lines = []
    for line in text.splitlines(keepends=True):
        fixed, n = fix_line(line)
        total += n
        fixed, cn = fix_comment_suffix(fixed)
        total += cn
        new_lines.append(fixed)
    if total and not dry_run:
        Path(path).write_text("".join(new_lines), encoding="utf-8")
    return total


def main():
    ap = argparse.ArgumentParser(description="Fix mojibake in deploy Python UI strings")
    ap.add_argument("paths", nargs="*", default=["surreal_architecture_gen.py"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-passes", type=int, default=10)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    grand = 0
    for p in args.paths:
        path = Path(p) if Path(p).is_absolute() else root / p
        if not path.exists():
            print(f"skip missing: {path}")
            continue
        print(f"scan {path}")
        for pass_n in range(1, args.max_passes + 1):
            n = process_file(path, dry_run=args.dry_run)
            print(f"  pass {pass_n}: {n} strings fixed")
            grand += n
            if n == 0:
                break
    print(f"total strings fixed: {grand}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
