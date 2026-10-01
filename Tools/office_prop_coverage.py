"""Office prop coverage manifest - the film's coverage denominator.

Reads the team brief (a .docx), splits it into the two blocks it actually
contains, and emits one row per catalog item so the GN prop kit has something
measurable to answer to.

    C:/Users/brenn/Downloads/Office Things.docx

Block 1 - the assignment list: 9 named owners -> ~85 named props. These are the
props a human is waiting on, so they set P0.

Block 2 - the master catalog: 107 rows, A-W alphabetical, a few already spoken
for (Desk Drawers / Televisions / Telephones -> Sukhbir). This is P0+P1+P2.

Why this is a script and not a CSV somebody edits. The 2026-09-25 audit is
blocked on exactly this: "Film brief is not locked ... P4-P6 target nothing
specific until that is filled." A hand-maintained coverage table drifts from the
brief on its first edit and then nobody can tell which side moved. Parse the
source, emit the table, and the drift becomes impossible.

Usage:
    python Tools/office_prop_coverage.py                 # human report
    python Tools/office_prop_coverage.py --csv OUT.csv   # machine table
    python Tools/office_prop_coverage.py --docx PATH     # override source

The docx is read as text: it is a Word file with no embedded table metadata we
can rely on across Word versions, and the item names are plain paragraphs. If
the file is missing the script says so and exits 2 - it never invents rows.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import zipfile

DEFAULT_DOCX = r"C:/Users/brenn/Downloads/Office Things.docx"

# Markers inside the catalog block that are table furniture or owner
# annotations, not items.
_CATALOG_JUNK = {"ITEM", "NAME"}
# Owner names appear as cells in the catalog table itself (someone claimed the
# row). Kept as a column, never as an item.
_OWNERS = {
    "Sukhbir", "Arianna", "Zania", "Kay", "Pearl", "Kane", "Selma", "Elif",
    "Oscar", "Emilio",
}
# The owner's own annotation: "Cabling Systems < dont need".
_DONT_NEED = re.compile(r"<\s*dont need", re.I)

# Items the owner explicitly marked as not needed. Kept in the manifest with
# status DEFER_NOT_NEEDED rather than dropped, so the exclusion is visible to
# whoever reads the coverage table later.


def docx_text(path: str) -> str:
    """Plain text out of a .docx, paragraph per line.

    WordprocessingML paragraphs are <w:p> runs. Joining runs within a paragraph
    is what makes "Office Things List" come out as one line instead of three.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", "replace")
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<w:tab[^>]*/>", " ", xml)
    xml = re.sub(r"<w:br[^>]*/>", "\n", xml)
    text = re.sub(r"<[^>]+>", "", xml)
    for a, b in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                 ("&quot;", '"'), ("&apos;", "'")):
        text = text.replace(a, b)
    return text


def parse_assignments(lines: list[str], stop: int) -> list[tuple[str, str]]:
    """Owner -> raw comma-separated prop string, from the head of the document.

    The owner cell carries a discipline suffix on one row ("Zania
    (Modeling)"), so the name is matched with a leading-token test rather than
    an equality test. Missing that dropped a whole owner and every prop they
    were waiting on.
    """
    out = []
    for raw in lines[:stop]:
        line = raw.strip()
        if not line or ":" not in line:
            continue
        owner, _, rest = line.partition(":")
        name = owner.strip().split("(")[0].strip()
        if name not in _OWNERS:
            continue
        rest = rest.strip().strip("()").strip()
        # "Decor(Books,Papers,...)" - split on commas that are not inside ( ).
        depth, buf, items = 0, [], []
        for ch in rest:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth = max(0, depth - 1)
            if ch == "," and depth == 0:
                items.append("".join(buf).strip())
                buf = []
            else:
                buf.append(ch)
        if "".join(buf).strip():
            items.append("".join(buf).strip())
        out.append((name, "; ".join(i for i in items if i)))
    return out


def parse_catalog(lines: list[str], start: int) -> list[dict]:
    """One row per catalog item, with its claiming owner when there is one.

    The source is a THREE-column Word table that .docx text extraction flattens
    to one paragraph per cell, in reading order: item, item, OWNER, item, item,
    OWNER... So an owner name is not a property of the line it sits on - it is a
    property of the PRECEDING item, and it terminates that row.

    Getting this wrong reads as "nobody claimed anything", which is exactly the
    kind of quiet wrong the film brief already suffers from.
    """
    rows = []
    for raw in lines[start + 2:]:
        line = " ".join(raw.split()).strip()
        if not line or line in _CATALOG_JUNK:
            continue
        if line in _OWNERS:
            if rows:
                rows[-1]["claimed_by"] = line
            continue
        dont_need = bool(_DONT_NEED.search(line))
        item = re.sub(r"\s*<.*$", "", line).strip()
        if not item:
            continue
        rows.append({"catalog_item": item, "claimed_by": "",
                     "dont_need": dont_need})
    return rows


def keyword_pool(assignments: list[tuple[str, str]]) -> set[str]:
    """Lowercase word pool from the assignment list, for the coverage matcher."""
    words: set[str] = set()
    for _, items in assignments:
        for chunk in items.split(";"):
            for word in re.split(r"[^A-Za-z]+", chunk):
                if len(word) >= 4:
                    words.add(word.lower())
    return words


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--docx", default=DEFAULT_DOCX)
    ap.add_argument("--csv", help="write the machine table here")
    ap.add_argument("--json", help="also write the parsed brief as JSON")
    args = ap.parse_args(argv)

    try:
        raw = docx_text(args.docx)
    except FileNotFoundError:
        print("MISSING BRIEF: %s" % args.docx)
        print("The coverage denominator is the brief. Copy it back to that path,")
        print("or pass --docx PATH. No rows are invented when it is absent.")
        return 2

    lines = [ln for ln in raw.replace("\r", "\n").split("\n")]
    lines = [ln for ln in lines if ln.strip()]
    if not lines:
        print("EMPTY BRIEF: no paragraphs parsed from %s" % args.docx)
        return 2

    try:
        start = next(i for i, ln in enumerate(lines) if ln.strip() == "ITEM")
    except StopIteration:
        print("NO CATALOG BLOCK: no 'ITEM' marker in %s" % args.docx)
        return 2

    assignments = parse_assignments(lines, start)
    catalog = parse_catalog(lines, start)
    pool = keyword_pool(assignments)

    p0 = sum(1 for c in catalog
             if any(w in c["catalog_item"].lower() for w in pool))
    deferred = sum(1 for c in catalog if c["dont_need"])

    print("source        : %s" % args.docx)
    print("owners        : %d" % len(assignments))
    for owner, items in assignments:
        print("   %-8s %s" % (owner, items))
    print("catalog rows  : %d" % len(catalog))
    print("claimed rows  : %d (%s)"
          % (sum(1 for c in catalog if c["claimed_by"]),
             ", ".join(sorted({c["claimed_by"] for c in catalog
                               if c["claimed_by"]})) or "-"))
    print("P0 candidates : %d  (catalog rows whose words appear in an assignment)"
          % p0)
    print("dont-need rows: %d" % deferred)

    if args.csv:
        os.makedirs(os.path.dirname(os.path.abspath(args.csv)), exist_ok=True)
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["catalog_item", "gn_builder_id", "status", "shot_ids",
                        "owner", "priority"])
            for c in catalog:
                item_l = c["catalog_item"].lower()
                if c["dont_need"]:
                    status, prio = "DEFER_NOT_NEEDED", "P3"
                elif c["claimed_by"]:
                    status, prio = "CLAIMED", "P0"
                elif any(x in item_l for x in pool):
                    status, prio = "TODO", "P0"
                else:
                    status, prio = "TODO", "P1"
                w.writerow([c["catalog_item"], "", status, "",
                            c["claimed_by"], prio])
        print("wrote         : %s" % args.csv)

    if args.json:
        import json
        os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"source": args.docx,
                       "assignments": dict(assignments),
                       "catalog": catalog}, fh, indent=2)
        print("wrote         : %s" % args.json)

    return 0


if __name__ == "__main__":
    sys.exit(main())