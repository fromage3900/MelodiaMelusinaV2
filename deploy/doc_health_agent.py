#!/usr/bin/env python
"""Doc Health Agent — nightly scan for stale, missing, or contradictory documentation.

Scans all .md files in Docs/ and root, extracts technical claims, cross-references
against C++ source headers, and optionally uses qwen2.5-coder:7b (--ollama) for intelligent
claim extraction and Monolith MCP (--monolith) for live UE editor validation.

Usage:
    python deploy/doc_health_agent.py                          # basic scan
    python deploy/doc_health_agent.py --ollama                 # +Ollama claim extraction
    python deploy/doc_health_agent.py --monolith               # +Monolith MCP validation
    python deploy/doc_health_agent.py --ollama --monolith      # full
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "Docs"
SOURCE = ROOT / "Source"
PLUGINS = ROOT / "Plugins"
REVIEWS = DOCS / "Reviews"
OLLAMA_API = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "qwen2.5-coder:7b"
MONOLITH_URL = "http://localhost:9316"

# Claim extraction patterns
SYSTEM_NAME_RE = re.compile(r'\b(?:U|F|E|I|A)Melodia[A-Z][A-Za-z0-9]*\b')
BP_PATH_RE = re.compile(r'/Game/(?:[A-Za-z0-9_/]+)(?:\.[A-Za-z0-9_]+)?')
CPP_REF_RE = re.compile(r'\b[A-Z][a-zA-Z0-9]+\.(?:h|cpp)\b')
CONFIG_DA_RE = re.compile(r'\bDA_[A-Z][A-Za-z0-9]*\b')
CONFIG_TSET_RE = re.compile(r'(?:TravelLevelIds|EncounterIds|QuestIds|NarrativeFlagIds|SocialStatIds|DialogueRewardIds)')
STALE_DRIVE_RE = re.compile(r'[FG]:\\[A-Za-z0-9_\\]+', re.IGNORECASE)
TODO_RE = re.compile(r'(?:TODO|FIXME|HACK|XXX|WORKAROUND)', re.IGNORECASE)
DATE_RE = re.compile(r'(\d{4}-\d{2}-\d{2})')

# C++ entity patterns
CPP_CLASS_NAME_RE = re.compile(r'class\s+(U|F|A|I)[A-Z][A-Za-z0-9]*')
CPP_ENUM_RE = re.compile(r'UENUM\(.*?\)\s*\n\s*enum\s+class\s+(E[A-Z][A-Za-z0-9]*)', re.DOTALL)
CPP_UFUNC_RE = re.compile(r'UFUNCTION\(.*?\)\s*\n\s*(?:virtual\s+)?(?:static\s+)?(?:\w+\s+)*(\w+)\s*\(', re.DOTALL)

# Negation markers for contradiction detection
NEGATION_RE = re.compile(
    r'\b(?:not|no longer|does not|is not|was not|removed|deprecated|broken|blocked|'
    r'never|missing|absent|failed|incorrect|wrong|stale|dead|orphaned|corrupt)\b',
    re.IGNORECASE,
)

KNOWN_PLUGIN_PATHS = [
    "Plugins/MelodiaCore/Source/MelodiaCore",
    "Plugins/QuillScript/Source/QuillScript",
    "Plugins/Monolith/Source/MonolithEditor",
    "Plugins/Monolith/Source/MonolithRuntime",
    "Plugins/UEBlueprintMCP/Source",
]


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def discover_md_files() -> list[Path]:
    files = sorted(ROOT.glob("*.md")) + sorted(DOCS.rglob("*.md"))
    seen: set[str] = set()
    unique: list[Path] = []
    for f in files:
        s = str(f.resolve())
        if s not in seen:
            seen.add(s)
            unique.append(f.resolve())
    return unique


# ---------------------------------------------------------------------------
# C++ Source index
# ---------------------------------------------------------------------------

def _index_source_dir(base: Path, index: dict) -> None:
    """Index all C++ entities under *base*."""
    if not base.is_dir():
        return
    for h_file in sorted(base.rglob("*.h")):
        index["files"].add(h_file.name)
        try:
            text = h_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for m in CPP_CLASS_NAME_RE.finditer(text):
            index["classes"].add(m.group(0).split()[-1])
        for m in CPP_ENUM_RE.finditer(text):
            index["enums"].add(m.group(1))
        for m in CPP_UFUNC_RE.finditer(text):
            index["functions"].add(m.group(1))
        # Also pull method names inside UCLASS bodies
        body = re.search(
            r'UCLASS\(.*?\)\s*\n\s*class\s+\S+\s+:\s*public\s+.*?\n\{',
            text, re.DOTALL,
        )
        if body:
            for m in re.finditer(r'\b([A-Z][a-zA-Z0-9]+)\s*\(', text[body.start():]):
                name = m.group(1)
                if name not in {
                    "if", "for", "while", "switch", "return",
                    "class", "public", "private", "protected",
                }:
                    index["functions"].add(name)
    for cpp_file in sorted(base.rglob("*.cpp")):
        index["files"].add(cpp_file.name)


def build_source_index() -> dict:
    index: dict = {"classes": set(), "functions": set(), "enums": set(), "files": set()}
    _index_source_dir(SOURCE, index)

    # Also index plugin directories that are commonly referenced
    for rel_path in KNOWN_PLUGIN_PATHS:
        _index_source_dir(PLUGINS / rel_path, index)

    return index


# ---------------------------------------------------------------------------
# Claim extraction
# ---------------------------------------------------------------------------

def _add_claim(claims: list[dict], typ: str, value: str, line: int, context: str, file_rel: str) -> None:
    claims.append({
        "type": typ,
        "value": value.strip(),
        "line": line,
        "context": context.strip()[:200],
        "file": file_rel,
    })


def extract_claims_from_text(text: str, path: Path) -> list[dict]:
    claims: list[dict] = []
    file_rel = str(path.relative_to(ROOT))
    lines = text.split("\n")

    for i, line in enumerate(lines):
        s = line.strip()
        if not s or s.startswith("#") or s.startswith(">") or s.startswith("```"):
            continue
        if s.startswith("|") and s.endswith("|"):
            continue  # skip table rows

        # System class references (UMelodia*, FMelodia* etc.)
        for m in SYSTEM_NAME_RE.finditer(s):
            _add_claim(claims, "system_ref", m.group(0), i + 1, s, file_rel)

        # Blueprint asset paths
        for m in BP_PATH_RE.finditer(s):
            _add_claim(claims, "blueprint_path", m.group(0), i + 1, s, file_rel)

        # Config data assets
        for m in CONFIG_DA_RE.finditer(s):
            _add_claim(claims, "data_asset", m.group(0), i + 1, s, file_rel)

        # Config set names
        for m in CONFIG_TSET_RE.finditer(s):
            _add_claim(claims, "config_set", m.group(0), i + 1, s, file_rel)

        # C++ file references (name.cpp / name.h)
        for m in CPP_REF_RE.finditer(s):
            _add_claim(claims, "cpp_file", m.group(0), i + 1, s, file_rel)

        # "X implements/manages/provides Y" patterns
        impl = re.search(
            r'\b([A-Z][a-zA-Z0-9]+(?:Subsystem|Component|Library|Config|Handler|Provider|Adapter|Bridge|Portal))\b'
            r'.{0,80}?(?:implemented|handles|manages|owns|provides|routes|processes|broadcasts|wires|validates|renders|resolves)',
            s[:300], re.IGNORECASE,
        )
        if impl:
            _add_claim(claims, "impl_claim", impl.group(0).rstrip("."), i + 1, s, file_rel)

    # Deduplicate exact (type, value, file) triples
    seen_claims: set[tuple[str, str, str]] = set()
    unique: list[dict] = []
    for c in claims:
        key = (c["type"], c["value"], c["file"])
        if key not in seen_claims:
            seen_claims.add(key)
            unique.append(c)
    return unique


def extract_claims_ollama(text: str, path: Path) -> list[dict]:
    prompt = f"""You are a documentation auditor. Scan this markdown excerpt and extract ALL
technical claims it makes about the Melodia project.
A technical claim asserts that a class, function, Blueprint path, config, or file exists
and has specific behaviour or location.

Return ONLY a JSON array of objects:
[{{"type":"system_ref|blueprint_path|impl_claim|function_claim|data_asset|cpp_file",
     "value":"<identifier or claim text>",
     "line":<approx line number>}}]

File: {path.relative_to(ROOT)}
Content:
{text[:4000]}"""

    body = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.05, "num_predict": 1500},
    }).encode()

    try:
        req = urllib.request.Request(OLLAMA_API, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = json.loads(resp.read())["response"]
    except Exception as e:
        log(f"  [ollama] error for {path.name}: {e}")
        return []

    try:
        m = re.search(r'\[.*\]', raw, re.DOTALL)
        if m:
            claims = json.loads(m.group(0))
            for c in claims:
                c["file"] = str(path.relative_to(ROOT))
                c["source"] = "ollama"
            return claims
    except (json.JSONDecodeError, TypeError):
        pass
    return []


# ---------------------------------------------------------------------------
# Cross-referencing
# ---------------------------------------------------------------------------

def cross_reference_source(claims: list[dict], source_index: dict) -> list[dict]:
    findings: list[dict] = []
    for claim in claims:
        val, typ = claim.get("value", ""), claim.get("type", "")

        if typ == "system_ref":
            if val not in source_index["classes"]:
                # Check if it might be a plugin class (more info = less severe)
                findings.append({
                    "severity": "MISSING",
                    "claim": claim,
                    "detail": f"Class `{val}` not indexed in any scanned Source/ or Plugins/ header",
                })

        elif typ == "cpp_file":
            if val not in source_index["files"]:
                findings.append({
                    "severity": "MISSING",
                    "claim": claim,
                    "detail": f"File `{val}` not found under scanned Source/ or Plugins/ trees",
                })

    return findings


def cross_reference_monolith(claims: list[dict]) -> list[dict]:
    findings: list[dict] = []
    bp_claims = [c for c in claims if c.get("type") == "blueprint_path"]
    if not bp_claims:
        return findings

    seen_bps: set[str] = set()
    for claim in bp_claims:
        bp = claim.get("value", "").split(".")[0]
        if bp in seen_bps:
            continue
        seen_bps.add(bp)

        payload = json.dumps({
            "jsonrpc": "2.0", "id": 1,
            "method": "tools/call",
            "params": {
                "name": "project_query",
                "arguments": {"command": "get_asset_details", "asset_path": bp},
            },
        }).encode()

        try:
            req = urllib.request.Request(
                f"{MONOLITH_URL}/mcp", data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read())
            asset_text = result.get("result", {}).get("content", [{}])[0].get("text", "")
            if "error" in result or not asset_text or "not found" in asset_text.lower():
                findings.append({
                    "severity": "MISSING",
                    "claim": claim,
                    "detail": f"Blueprint path `{bp}` not found in live editor",
                })
        except Exception as e:
            findings.append({
                "severity": "WARN",
                "claim": claim,
                "detail": f"Monolith unreachable for `{bp}`: {e}",
            })

    return findings


# ---------------------------------------------------------------------------
# Contradiction detection
# ---------------------------------------------------------------------------

def detect_contradictions(all_claims: list[dict]) -> list[dict]:
    """Find documents making opposing claims about the same system."""
    contradictions: list[dict] = []

    # group system_ref claims by value
    by_value: dict[str, list[dict]] = defaultdict(list)
    for c in all_claims:
        if c.get("type") in ("system_ref", "impl_claim"):
            val = c.get("value", "")
            if len(val) > 5:
                by_value[val].append(c)

    for val, claimants in by_value.items():
        files = {c["file"] for c in claimants}
        if len(files) < 2:
            continue

        has_positive = False
        has_negative = False
        neg_files: set[str] = set()
        for c in claimants:
            ctx = c.get("context", "")
            if NEGATION_RE.search(ctx):
                has_negative = True
                neg_files.add(c["file"])
            else:
                has_positive = True

        if has_positive and has_negative:
            contradictions.append({
                "value": val,
                "files": sorted(files),
                "pos_files": sorted(files - neg_files),
                "neg_files": sorted(neg_files),
                "detail": f"Claimed present in {len(files - neg_files)} doc(s) and absent/broken in {len(neg_files)} doc(s)",
            })

    return contradictions


# ---------------------------------------------------------------------------
# Staleness helpers
# ---------------------------------------------------------------------------

def detect_stale_paths(text: str, path: Path) -> list[dict]:
    file_rel = str(path.relative_to(ROOT))
    findings: list[dict] = []
    for i, line in enumerate(text.split("\n"), 1):
        for m in STALE_DRIVE_RE.finditer(line):
            findings.append({
                "severity": "STALE", "file": file_rel, "line": i,
                "detail": f"Stale drive path: `{m.group(0)}`",
            })
    return findings


def check_date_freshness(text: str, path: Path) -> list[dict]:
    findings: list[dict] = []
    file_rel = str(path.relative_to(ROOT))
    dates = DATE_RE.findall(text)
    if not dates:
        return findings
    newest = max(dates)
    try:
        doc_date = datetime.strptime(newest, "%Y-%m-%d")
        age = (datetime.now() - doc_date).days
        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        mtime_age = (datetime.now() - mtime).days
        if age > 14:
            findings.append({
                "severity": "STALE", "file": file_rel,
                "detail": f"Doc date `{newest}` is {age}d old (threshold: 14d)",
            })
        if mtime_age < age - 1:
            findings.append({
                "severity": "INFO", "file": file_rel,
                "detail": f"mtime ({mtime.date()}) newer than newest date `{newest}` — doc modified without date bump",
            })
    except ValueError:
        pass
    return findings


def detect_todos(text: str, path: Path) -> list[dict]:
    todos = TODO_RE.findall(text)
    if not todos:
        return []
    return [{
        "severity": "INFO",
        "file": str(path.relative_to(ROOT)),
        "detail": f"{len(todos)} unresolved: {', '.join(sorted(set(todos)))}",
    }]


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

def write_report(
    findings: dict,
    contradictions: list[dict],
    stale_drive: list[dict],
    date_warnings: list[dict],
    todo_warnings: list[dict],
    stats: dict,
    args: argparse.Namespace,
) -> Path:
    today = date.today().isoformat()
    REVIEWS.mkdir(parents=True, exist_ok=True)
    report_path = REVIEWS / f"DOC_HEALTH_REPORT_{today}.md"

    lines: list[str] = [
        f"# Doc Health Report — {today}",
        "",
    ]
    if args.ollama:
        lines.append(f"**Extraction engine:** {OLLAMA_MODEL} (Ollama)")
    if args.monolith:
        lines.append("**Validation source:** Monolith MCP (live editor)")
    lines.append(f"**Mode:** Read-only{' + Monolith queries' if args.monolith else ''}")
    lines.append("")

    # --- Summary ---
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|---|---:|")
    lines.append(f"| .md files scanned | {stats['files_scanned']} |")
    lines.append(f"| Technical claims extracted | {stats['claims_extracted']} |")
    lines.append(f"| Source headers indexed | {stats['source_files']} |")
    lines.append(f"| C++ classes indexed | {stats['source_classes']} |")
    lines.append(f"| C++ functions indexed | {stats['source_functions']} |")
    lines.append(f"| Source mismatches (MISSING/STALE) | {stats['source_mismatches']} |")
    lines.append(f"| Monolith mismatches | {stats['monolith_mismatches']} |")
    lines.append(f"| Cross-doc contradictions | {stats['contradictions']} |")
    lines.append(f"| Stale drive paths | {stats['stale_drive_paths']} |")
    lines.append(f"| Stale docs (>14d without update) | {stats['stale_docs']} |")
    lines.append("")

    # --- Source findings (table, collapsed) ---
    src = findings.get("source", [])
    if src:
        lines.append("## Source Cross-Reference Findings")
        lines.append("")
        lines.append("Claims from docs that reference C++ names not found in scanned source trees.")
        lines.append("Scanned: `Source/` + MelodiaCore, QuillScript, Monolith, UEBlueprintMCP plugin dirs.")
        lines.append("")

        # Group by severity then by type for readability
        groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for f in src:
            sev = f["severity"]
            c = f["claim"]
            groups[(sev, c.get("type", ""))].append(f)

        for (sev, typ), items in sorted(groups.items()):
            icon = "❌" if sev == "MISSING" else "⚠️"
            plural = "" if len(items) == 1 else f" ({len(items)} occurrences)"
            lines.append(f"### {icon} {sev} — `{typ}`{plural}")
            lines.append("")
            for item in items[:20]:  # cap per group
                c = item["claim"]
                val = c.get("value", "")
                lines.append(f"- `{c['file']}:{c['line']}` — `{val}`")
                lines.append(f"  - {item['detail']}")
                ctx = c.get("context", "")[:100]
                if ctx:
                    lines.append(f"  - _{ctx}_")
            if len(items) > 20:
                lines.append(f"- *... and {len(items) - 20} more*")
            lines.append("")

    # --- Monolith ---
    mon = findings.get("monolith", [])
    if mon:
        lines.append("## Monolith Validation Findings")
        lines.append("")
        for item in mon:
            c = item["claim"]
            lines.append(f"- **{item['severity']}** `{c['file']}:{c['line']}` — `{c['value']}`")
            lines.append(f"  - {item['detail']}")
        lines.append("")

    # --- Contradictions ---
    if contradictions:
        lines.append("## Cross-Doc Contradictions")
        lines.append("")
        for cd in contradictions:
            lines.append(f"### `{cd['value']}`")
            lines.append("")
            lines.append(f"- {cd['detail']}")
            lines.append(f"- **Present-claiming docs:** {', '.join(cd['pos_files'])}")
            lines.append(f"- **Absent-claiming docs:** {', '.join(cd['neg_files'])}")
            lines.append("")
    else:
        lines.append("## Cross-Doc Contradictions")
        lines.append("")
        lines.append("None detected.")
        lines.append("")

    # --- Stale drive paths ---
    if stale_drive:
        lines.append("## Stale Drive Paths")
        lines.append("")
        for sd in stale_drive[:30]:
            lines.append(f"- `{sd['file']}:{sd['line']}` — {sd['detail']}")
        if len(stale_drive) > 30:
            lines.append(f"- *... and {len(stale_drive) - 30} more*")
        lines.append("")

    # --- Date freshness ---
    stale_docs = [dw for dw in date_warnings if dw["severity"] == "STALE"]
    info_dates = [dw for dw in date_warnings if dw["severity"] == "INFO"]
    if stale_docs:
        lines.append("## Stale Docs (>14 Days)")
        lines.append("")
        for dw in stale_docs:
            lines.append(f"- `{dw['file']}` — {dw['detail']}")
        lines.append("")
    if info_dates:
        lines.append("## Docs Modified Without Date Bump")
        lines.append("")
        for dw in info_dates[:20]:
            lines.append(f"- `{dw['file']}` — {dw['detail']}")
        if len(info_dates) > 20:
            lines.append(f"- *... and {len(info_dates) - 20} more*")
        lines.append("")

    # --- TODO markers ---
    if todo_warnings:
        lines.append("## Unresolved TODO/FIXME/HACK Markers")
        lines.append("")
        for tw in todo_warnings:
            lines.append(f"- `{tw['file']}` — {tw['detail']}")
        lines.append("")

    # --- File inventory ---
    lines.append("## File Inventory")
    lines.append("")
    lines.append(f"Scanned {stats['files_scanned']} markdown files.")
    lines.append("")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Doc Health Agent — nightly stale/contradiction scanner")
    p.add_argument("--ollama", action="store_true", help="Use the configured local Ollama model for claim extraction")
    p.add_argument("--monolith", action="store_true", help="Connect to Monolith MCP for validation")
    p.add_argument("--quiet", action="store_true", help="Minimal output")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    log(f"Doc Health Agent starting (ollama={args.ollama}, monolith={args.monolith})")

    # 1. Discover markdown files
    files = discover_md_files()
    log(f"Found {len(files)} markdown files")

    # 2. Index C++ sources (Source/ + known plugin dirs)
    source_index = build_source_index()
    log(f"Indexed C++ sources: {len(source_index['classes'])} classes, "
        f"{len(source_index['functions'])} functions, {len(source_index['files'])} files")

    # 3. Scan every markdown file
    all_claims: list[dict] = []
    all_source_findings: list[dict] = []
    all_stale_drive: list[dict] = []
    all_date_warnings: list[dict] = []
    all_todo_warnings: list[dict] = []

    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            log(f"  [skip] {f.name}: {e}")
            continue

        claims = extract_claims_from_text(text, f)
        if args.ollama:
            claims.extend(extract_claims_ollama(text, f))

        all_claims.extend(claims)
        all_source_findings.extend(cross_reference_source(claims, source_index))
        all_stale_drive.extend(detect_stale_paths(text, f))
        all_date_warnings.extend(check_date_freshness(text, f))
        all_todo_warnings.extend(detect_todos(text, f))

        if not args.quiet:
            status = f"  {f.relative_to(ROOT)}: {len(claims)} claims"
            src_count = sum(
                1 for s in all_source_findings
                if s["claim"]["file"] == str(f.relative_to(ROOT))
            )
            if src_count:
                status += f", {src_count} mismatches"
            log(status)

    # 4. Monolith
    monolith_findings: list[dict] = []
    if args.monolith:
        log("Connecting to Monolith MCP...")
        monolith_findings = cross_reference_monolith(all_claims)
        log(f"Monolith: {len(monolith_findings)} findings")

    # 5. Contradictions
    contradictions = detect_contradictions(all_claims)
    log(f"Contradictions: {len(contradictions)}")

    # 6. Stats
    stats = {
        "files_scanned": len(files),
        "claims_extracted": len(all_claims),
        "source_files": len(source_index["files"]),
        "source_classes": len(source_index["classes"]),
        "source_functions": len(source_index["functions"]),
        "source_mismatches": len(all_source_findings),
        "monolith_mismatches": len(monolith_findings),
        "contradictions": len(contradictions),
        "stale_drive_paths": len(all_stale_drive),
        "stale_docs": len([dw for dw in all_date_warnings if dw["severity"] == "STALE"]),
    }

    # 7. Report
    report_path = write_report(
        findings={"source": all_source_findings, "monolith": monolith_findings},
        contradictions=contradictions,
        stale_drive=all_stale_drive,
        date_warnings=all_date_warnings,
        todo_warnings=all_todo_warnings,
        stats=stats,
        args=args,
    )
    log(f"Report: {report_path}")
    log(f"Doc Health Agent complete (exit=1 if mismatches/contradictions)")

    return 1 if (all_source_findings or contradictions) else 0


if __name__ == "__main__":
    sys.exit(main())
