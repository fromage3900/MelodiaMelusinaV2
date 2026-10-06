"""hda_audit.py - Gate 0: offline HDA inventory audit (stdlib only, no hou).

Answers "does every registered HDA file actually exist, contain a real network,
and is nothing unregistered lying around?" without starting Houdini. Cooking and
definition truth are Gate 2 (hda_verify.py); this gate is the cheap layer that
runs anywhere, including machines with no Houdini license.

    hython Tools/Houdini/hda_verify/hda_audit.py --out-dir Saved/Audit/hda_verify/<run>
    python  Tools/Houdini/hda_verify/hda_audit.py            # same, any interpreter

Checks (per registry entry, see hda_registry.v1.json):
  active  -> file exists, size > 0, has a compressed Contents.gz network, sha256
             recorded, mirrors byte-identical, DialogScript label matches.
  missing -> reported as OWED (warn, not fail): builder or recipe exists, file does not.
  stub    -> glob matches are still empty shells (no Contents.gz); drift from
             stub-ness is reported because a "backup" that silently gains a
             network is a hand edit we did not audit.
  scan    -> any *.hda under scan_roots not in the registry is WARN (unregistered);
             vendor trees are counted, never enumerated as failures.

Exit: 0 = no FAIL, 1 = at least one FAIL, 2 = environment/registry problem.
Receipt: <out-dir>/hda_inventory.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zlib
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REGISTRY = Path(__file__).with_name("hda_registry.v1.json")

SECTION_MARKERS = {
    "dialog_script": b"DialogScript",
    "create_script": b"CreateScript",
    "contents_gz": b"Contents.gz",
    "contents_plain": b"Contents",
    "internal_file_options": b"InternalFileOptions",
}
GZIP_MAGIC = b"\x1f\x8b"
# Node type references baked into the saved network, e.g. "Sop/attribwrangle".
NODE_TYPE_RE = re.compile(rb"\b(Sop|Object|Vop|Cop|Dop)/([A-Za-z0-9_][A-Za-z0-9_:.]*)")
LABEL_RE = re.compile(rb'label\s+"([^"]+)"')


# --------------------------------------------------------------------- helpers
def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_hda(path: Path) -> dict:
    """Read an HDA as bytes and report its structure. No Houdini involved.

    An HDA is a Houdini index file: a table of named sections followed by their
    data. The saved node network lives in a gzip-compressed `Contents.gz`
    section; empty shells (our hda/backup/*.hda) carry no such section at all,
    which is exactly the stub signal used below.
    """
    data = path.read_bytes()
    info = {
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "label": None,
        "sections": sorted(k for k, m in SECTION_MARKERS.items() if m in data),
        "has_network": b"Contents.gz" in data,
        "network_bytes": 0,
        "fallback_ops": [],
        "preview_error": None,
    }

    label = LABEL_RE.search(data)
    if label:
        info["label"] = label.group(1).decode("utf-8", "replace")

    idx = data.find(b"Contents.gz")
    if idx >= 0:
        start = data.find(GZIP_MAGIC, idx)
        if start < 0:
            info["preview_error"] = "Contents.gz section has no gzip stream"
        else:
            # Decompress exactly one member; trailing sections are ignored.
            try:
                d = zlib.decompressobj(16 + zlib.MAX_WBITS)
                raw = d.decompress(data[start: start + 4_000_000])
                info["network_bytes"] = len(raw)
                # Saved networks record their inlinable op defs as
                # "Sop/<type>" / "Object/<type>" references; this is a partial
                # view (fallback ops only), not the full node inventory.
                found = {t.decode() for _, t in NODE_TYPE_RE.findall(raw)}
                info["fallback_ops"] = sorted(found)
            except Exception as exc:  # corrupt section is a finding, not a crash
                info["preview_error"] = f"{type(exc).__name__}: {exc}"
    return info


def load_registry(path: Path) -> dict:
    # utf-8-sig: PowerShell's Set-Content writes a BOM and a BOM must not
    # turn into "ENVIRONMENT FAIL: JSONDecodeError".
    with path.open("r", encoding="utf-8-sig") as fh:
        reg = json.load(fh)
    if reg.get("schema") != "melodia.hda_registry.v1":
        raise ValueError(f"unexpected registry schema: {reg.get('schema')!r}")
    return reg


def _resolve(project_root: Path, rel: str) -> Path:
    return (project_root / rel).resolve()


def _rel(project_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


# ------------------------------------------------------------------ audit gates
def audit_entry(project_root: Path, entry: dict) -> dict:
    """Audit one registry entry. Never raises: failures become FAIL records."""
    status = entry.get("status", "active")
    rec = {
        "id": entry.get("id"),
        "status": status,
        "path": entry.get("path"),
        "checks": [],
        "result": "PASS",
    }

    def check(name: str, ok: bool, detail: str = "", level: str = "FAIL") -> None:
        rec["checks"].append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok and level == "FAIL" and rec["result"] != "FAIL":
            rec["result"] = "FAIL"
        elif not ok and level == "WARN" and rec["result"] == "PASS":
            rec["result"] = "WARN"

    if status == "missing":
        path = _resolve(project_root, entry["path"])
        check("file_present", False,
              f"OWED: {entry['path']} does not exist "
              f"(builder: {entry.get('builder') or 'none'})",
              level="WARN")
        return rec

    path = _resolve(project_root, entry["path"])
    if not path.is_file():
        check("file_present", False, f"missing: {entry['path']}")
        return rec
    check("file_present", True, f"{path.stat().st_size} bytes")

    info = parse_hda(path)
    rec["hda"] = info
    if status == "stub":
        # A backup is expected to be an empty shell; network presence is inverted.
        check("has_network", not info["has_network"],
              "expected empty shell (no Contents.gz) - it now holds a network, "
              "audit it before trusting it")
    else:
        check("has_network", info["has_network"],
              "compressed Contents.gz present" if info["has_network"]
              else "no Contents.gz section - empty shell / stub")
        check("decompresses", info["preview_error"] is None,
              info["preview_error"] or f"{info['network_bytes']} bytes of network, "
              f"{len(info['fallback_ops'])} inlined op defs")
    check("label_matches", entry.get("label") in (None, info["label"]),
          f"registry={entry.get('label')!r} file={info['label']!r}")

    if status == "stub":
        # Backups are expected to stay empty shells; a grown backup = unaudited edit.
        check("still_stub", not info["has_network"],
              "backup grew a real network - audit it before trusting it")

    for mirror_rel in entry.get("mirror", []) or []:
        mirror = _resolve(project_root, mirror_rel)
        if not mirror.is_file():
            check("mirror_present", False, f"missing: {mirror_rel}")
            continue
        same = sha256_of(path) == sha256_of(mirror)
        check("mirror_identical", same, mirror_rel)

    return rec


def scan_unregistered(project_root: Path, registry: dict) -> dict:
    """Find *.hda under the scan roots that the registry does not know about."""
    import fnmatch

    known = {e.get("path", "").replace("\\", "/").lower() for e in registry["entries"]}
    for e in registry["entries"]:
        for m in e.get("mirror", []) or []:
            known.add(m.replace("\\", "/").lower())
    stub_patterns = [p.lower() for p in registry.get("globs", {}).get("stub", [])]

    def covered(rel: str) -> bool:
        rel_l = rel.lower()
        return rel_l in known or any(fnmatch.fnmatch(rel_l, p) for p in stub_patterns)

    found, unregistered = [], []
    for root_rel in registry.get("scan_roots", []):
        root = _resolve(project_root, root_rel)
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*.hda")):
            rel = _rel(project_root, p)
            found.append(rel)
            if not covered(rel):
                unregistered.append(rel)

    vendor_count = 0
    for root_rel in registry.get("globs", {}).get("vendor", []):
        root = _resolve(project_root, root_rel)
        if root.is_dir():
            vendor_count += sum(1 for _ in root.rglob("*.hda"))

    return {
        "project_hda_files": found,
        "unregistered": unregistered,
        "vendor_hda_files": vendor_count,
        "stub_files": [rel for rel in found if "/backup/" in rel.lower()],
    }


def run_audit(project_root: Path, registry_path: Path, out_dir: Path) -> dict:
    registry = load_registry(registry_path)
    entries = [audit_entry(project_root, e) for e in registry["entries"]]

    stub_root = registry.get("globs", {}).get("stub", [])
    stub_files = []
    for pattern in stub_root:
        stub_files.extend(sorted(_rel(project_root, p)
                                 for p in project_root.glob(pattern)))
    for rel in stub_files:
        if any(e["path"] == rel for e in entries):
            continue
        entries.append(audit_entry(project_root, {
            "id": f"stub:{rel}", "status": "stub", "path": rel, "label": None}))

    scan = scan_unregistered(project_root, registry)
    if scan["unregistered"]:
        # Present-but-unknown is a WARN: it must be registered, not deleted.
        for rel in scan["unregistered"]:
            entries.append({
                "id": f"unregistered:{rel}", "status": "unregistered",
                "path": rel, "result": "WARN",
                "checks": [{"name": "registered", "ok": False,
                            "detail": "add it to hda_registry.v1.json"}],
            })

    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for e in entries:
        counts[e["result"]] = counts.get(e["result"], 0) + 1

    report = {
        "schema": "melodia.hda_audit_report.v1",
        "gate": 0,
        "generated": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(project_root),
        "registry": _rel(project_root, registry_path),
        "counts": counts,
        "entries": entries,
        "scan": scan,
        "overall": "FAIL" if counts.get("FAIL") else
                   ("WARN" if counts.get("WARN") else "PASS"),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "hda_inventory.json"
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, default=str)
    report["_receipt"] = str(out_path)
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="HDA Gate 0: offline inventory audit")
    ap.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    ap.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="receipt folder (default Saved/Audit/hda_verify/<timestamp>)")
    args = ap.parse_args(argv)

    out_dir = args.out_dir or (args.project_root / "Saved" / "Audit" / "hda_verify"
                               / datetime.now().strftime("%Y%m%d_%H%M%S"))
    try:
        report = run_audit(args.project_root.resolve(), args.registry, out_dir)
    except Exception as exc:  # registry missing / malformed
        print(f"[hda_audit] ENVIRONMENT FAIL: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return 2

    for e in report["entries"]:
        print(f"{e['result']:4} {e['id']}")
        for c in e["checks"]:
            if not c["ok"]:
                print(f"       - {c['name']}: {c['detail']}")
    scan = report["scan"]
    print(f"[hda_audit] {report['counts']}  |  project HDAs: "
          f"{len(scan['project_hda_files'])}, unregistered: {len(scan['unregistered'])}, "
          f"vendor: {scan['vendor_hda_files']}, stub backups: {len(scan['stub_files'])}")
    print(f"[hda_audit] receipt: {report['_receipt']}")
    return 1 if report["overall"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
