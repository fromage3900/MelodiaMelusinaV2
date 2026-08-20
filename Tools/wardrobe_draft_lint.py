#!/usr/bin/env python3
"""Lint cosmetic drafts against the C++ wardrobe contract. No editor required.

WHY

`Imports/Data/Cosmetics/*.json` holds cosmetic drafts produced by
`deploy/ollama_wardrobe_catalog_daemon.py` (an LLM generator, not a designer --
see Docs/Reports/WARDROBE_CONTENT_CONTRACT_GAPS_2026-08-14.md). Several fields
cannot round-trip into the C++ model, and the failure is SILENT: an unmappable
rarity takes the enum default and looks like a deliberate `Common`.

This turns that report into an executable check, so the mismatch count is a number
anyone can reproduce rather than a claim in a document.

It reads the C++ headers for the enum values rather than hardcoding them, so it
cannot drift from the code the way a second copy of a vocabulary would -- which is
the exact mistake this file exists to catch.

USAGE

    python Tools/wardrobe_draft_lint.py            # summary + exit 1 if blocking
    python Tools/wardrobe_draft_lint.py --verbose  # per-draft detail
    python Tools/wardrobe_draft_lint.py --json     # machine-readable

EXIT CODES

    0  every draft round-trips
    1  at least one BLOCKING mismatch (data would be silently lost on import)
    2  could not read the C++ contract (do not interpret a 0 finding as clean)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_MANIFEST = ROOT / "specs" / "wardrobe" / "wardrobe_catalog_manifest.v1.json"
DRAFT_ROOTS = (
    ROOT / "Imports" / "Data" / "Cosmetics",
    ROOT / "Plugins" / "MelodiaWardrobe" / "Content" / "MelodiaWardrobe" / "Drafts",
)
# Kept as a named primary root for callers that imported this constant before the
# plugin-local definition drafts were added to the lint scope.
DRAFTS = DRAFT_ROOTS[0]

RARITY_HEADER = (ROOT / "Plugins" / "MelodiaWardrobe" / "Source" / "MelodiaWardrobe"
                 / "Public" / "MelodiaCosmeticTypes.h")
SLOT_HEADER = (ROOT / "Source" / "BS_GodFile" / "MelodiaIntegration"
               / "MelodiaNarrativeTypes.h")
ELEMENT_HEADER = (ROOT / "Plugins" / "MelodiaCore" / "Source" / "MelodiaCore"
                  / "MelodiaSpellTypes.h")

# Drafts are emitted in two shapes. The rich generator uses lower-case keys; the
# plugin definition drafts use the reflected C++ field names. Both are accepted
# only through this explicit source contract so an importer cannot silently drop
# a field when a draft moves between lanes.
SOURCE_SHAPES = {
    "rich": {
        "id": "id",
        "slot": "slot",
        "rarity": "rarity",
        "content_pack_id": "content_pack_id",
    },
    "definition": {
        "id": "CosmeticId",
        "slot": "Slot",
        "rarity": "Rarity",
        "content_pack_id": "ContentPackId",
        "source_draft_path": "SourceDraftPath",
    },
}

# Token-cost keys are ART VARIANT names, not currencies. `{"heart": 5, "swirl": 2}`
# means five Forte shards and two Arcane shards in the ONE Melody Token wallet --
# owner-confirmed 2026-08-14, and `UMelodiaTokenWalletSubsystem` implements it as
# `TMap<FName,int32> Shards` keyed by element.
#
# This mapping is NOT hardcoded below: it is read from the canonical model at
# Content/Python/gmm/game/tokens.py, which the wallet header names as the source it
# mirrors. Copying the four pairs here would be a second copy of a vocabulary that
# can drift -- the defect this linter exists to catch.
GMM_TOKENS = Path(ROOT) / "Content" / "Python"


def token_element_map() -> dict[str, str] | None:
    """{art variant -> element} from the canonical GMM token model.

    Returns None when the model cannot be read, so callers can fail closed rather
    than treat "no findings" as "the drafts are clean".
    """
    import sys as _sys
    path = str(GMM_TOKENS)
    added = path not in _sys.path
    if added:
        _sys.path.insert(0, path)
    try:
        from gmm.game.tokens import TOKEN_TYPES  # type: ignore
        return {k: v["element"] for k, v in TOKEN_TYPES.items() if "element" in v}
    except Exception:
        return None
    finally:
        if added and path in _sys.path:
            _sys.path.remove(path)


def load_catalog_manifest() -> dict | None:
    """Read the checked-in source contract used by authoring and validation."""
    try:
        value = json.loads(CATALOG_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def draft_paths() -> list[Path]:
    """Return drafts from both the generator and plugin definition lanes."""
    paths: set[Path] = set()
    for root in DRAFT_ROOTS:
        paths.update(root.glob("*.json"))
    return sorted(paths)


def source_field(draft: dict, field: str, fallback: str | None = None):
    """Read a field from either accepted draft shape."""
    if field in draft:
        return draft[field]
    if fallback and fallback in draft:
        return draft[fallback]
    return None


def read_enum(path: Path, enum_name: str) -> list[str] | None:
    """Enum value names, read from the C++ header itself.

    Deliberately not a hardcoded list: a second copy of a vocabulary drifts out of
    agreement with the enum, which is the defect this linter reports.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    match = re.search(r"enum\s+class\s+" + re.escape(enum_name) + r"\s*:\s*\w+\s*\{(.*?)\}", text, re.S)
    if not match:
        return None
    values = []
    for line in match.group(1).splitlines():
        line = line.split("//")[0].strip()
        if not line:
            continue
        name = re.match(r"([A-Za-z_]\w*)", line)
        if name:
            values.append(name.group(1))
    return values or None


def normalise_slot(raw: str, aliases: dict[str, str] | None = None) -> str:
    key = str(raw).strip().replace("-", "_").replace(" ", "_").lower()
    mapped = (aliases or {}).get(key, key)
    return mapped.replace("_", "").lower()


def resolve_slot(raw: str, slots: list[str], aliases: dict[str, str]) -> str | None:
    lookup = {slot.replace("_", "").lower(): slot for slot in slots}
    return lookup.get(normalise_slot(raw, aliases))


def lint() -> tuple[dict, int]:
    rarities = read_enum(RARITY_HEADER, "EMelodiaCosmeticRarity")
    slots = read_enum(SLOT_HEADER, "EMelodiaWardrobeSlot")
    elements = read_enum(ELEMENT_HEADER, "EMelodiaSpellElement")
    tokens = token_element_map()
    manifest = load_catalog_manifest()

    if not (rarities and slots and elements and manifest):
        missing = [n for n, v in (("EMelodiaCosmeticRarity", rarities),
                                  ("EMelodiaWardrobeSlot", slots),
                                  ("EMelodiaSpellElement", elements),
                                  ("wardrobe_catalog_manifest.v1.json", manifest)) if not v]
        return {"error": "could not read C++ contract", "missing": missing}, 2

    rarity_lookup = {r.lower(): r for r in rarities}
    element_lookup = {e.lower(): e for e in elements}
    reconciliation = manifest.get("draft_reconciliation")
    if not isinstance(reconciliation, dict):
        return {
            "error": "catalog manifest has no draft_reconciliation contract",
            "missing": ["draft_reconciliation"],
        }, 2
    slot_aliases = {
        str(key).strip().lower(): str(value)
        for key, value in dict(reconciliation.get("slot_aliases", {})).items()
    }
    rarity_aliases = {
        str(key).strip().lower(): str(value)
        for key, value in dict(reconciliation.get("rarity_aliases", {})).items()
    }
    if any(value.lower() not in rarity_lookup for value in rarity_aliases.values()):
        return {
            "error": "catalog manifest has a rarity alias outside EMelodiaCosmeticRarity",
            "missing": sorted(
                value for value in rarity_aliases.values()
                if value.lower() not in rarity_lookup
            ),
        }, 2
    deferred_rarities = {
        str(value).strip().lower()
        for value in reconciliation.get("deferred_rarity_values", [])
    }
    rarity_policy = reconciliation.get("rarity_policy")
    if not isinstance(rarity_policy, dict) or rarity_policy.get("status") != "owner_decision_required":
        return {
            "error": "catalog manifest must document unresolved rarity owner decisions",
            "missing": ["draft_reconciliation.rarity_policy"],
        }, 2
    if set(rarity_policy.get("unresolved_values", [])) != {
        value.title() for value in deferred_rarities
    } or rarity_policy.get("import_action") != "reject_until_explicit_mapping":
        return {
            "error": "rarity policy does not match deferred values or fail-closed import action",
            "missing": ["draft_reconciliation.rarity_policy"],
        }, 2
    if (
        reconciliation.get("content_pack_field") != "content_pack_id"
        or reconciliation.get("content_pack_policy")
        != "preserve_when_present_optional_until_collection_authority"
    ):
        return {
            "error": "catalog manifest must preserve content-pack identity",
            "missing": ["draft_reconciliation.content_pack_policy"],
        }, 2

    findings: list[dict] = []
    files = draft_paths()
    source_shape_counts = {name: 0 for name in SOURCE_SHAPES}
    slot_mappings: dict[str, str] = {}
    content_pack_mappings: dict[str, str] = {}
    seen_ids: dict[str, str] = {}

    for path in files:
        try:
            draft = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append({"draft": path.name, "field": "(file)", "value": str(exc),
                             "severity": "blocking", "why": "unreadable draft"})
            continue

        if not isinstance(draft, dict):
            findings.append({
                "draft": path.name,
                "field": "(shape)",
                "value": type(draft).__name__,
                "severity": "blocking",
                "why": "draft must be a JSON object",
            })
            continue

        shape_name = "definition" if "CosmeticId" in draft else "rich"
        shape = SOURCE_SHAPES[shape_name]
        source_shape_counts[shape_name] += 1
        did = source_field(draft, shape["id"]) or path.stem
        if not isinstance(did, str) or not did.strip():
            findings.append({
                "draft": path.name,
                "field": shape["id"],
                "value": did,
                "severity": "blocking",
                "why": "cosmetic id is required for catalog identity",
            })
            did = path.stem
        elif did in seen_ids:
            findings.append({
                "draft": did,
                "field": shape["id"],
                "value": did,
                "severity": "blocking",
                "why": f"duplicate cosmetic id also appears in {seen_ids[did]}",
            })
        else:
            seen_ids[did] = str(path)

        slot = source_field(draft, shape["slot"])
        if not isinstance(slot, str) or not slot.strip():
            findings.append({
                "draft": did, "field": shape["slot"], "value": slot,
                "severity": "blocking",
                "why": "slot is required and must map to EMelodiaWardrobeSlot",
            })
        else:
            resolved_slot = resolve_slot(slot, slots, slot_aliases)
            if resolved_slot is None:
                findings.append({
                    "draft": did, "field": shape["slot"], "value": slot,
                    "severity": "blocking",
                    "why": "no mapping to EMelodiaWardrobeSlot; add an explicit slot_alias",
                })
            else:
                slot_mappings[did] = resolved_slot

        rarity = source_field(draft, shape["rarity"])
        if not isinstance(rarity, str) or not rarity.strip():
            findings.append({
                "draft": did, "field": shape["rarity"], "value": rarity,
                "severity": "blocking",
                "why": "rarity is required and must map to EMelodiaCosmeticRarity",
            })
        elif (
            rarity.lower() not in rarity_lookup
            and rarity.lower() not in rarity_aliases
        ):
            why = (
                "draft value is deferred until the owner selects a canonical rarity"
                if rarity.lower() in deferred_rarities
                else "not in EMelodiaCosmeticRarity; import must not default it silently"
            )
            findings.append({
                "draft": did, "field": shape["rarity"], "value": rarity,
                "severity": (
                    "owner_decision" if rarity.lower() in deferred_rarities else "blocking"
                ),
                "why": (
                    f"{why}; importer must reject until the owner maps it explicitly"
                    if rarity.lower() in deferred_rarities else why
                )})

        if shape_name == "definition":
            source_path = source_field(draft, shape["source_draft_path"])
            if not isinstance(source_path, str) or not source_path.strip():
                findings.append({
                    "draft": did, "field": shape["source_draft_path"], "value": source_path,
                    "severity": "blocking",
                    "why": "definition drafts must retain their source path",
                })

        mood = draft.get("element_mood")
        if mood and mood.lower() not in element_lookup:
            findings.append({
                "draft": did, "field": "element_mood", "value": mood, "severity": "blocking",
                "why": "not in EMelodiaSpellElement, which is the style axis vocabulary"})

        # token_cost keys are art variants that must resolve to a wallet element.
        # An unresolvable key is BLOCKING: the price silently becomes free rather
        # than wrong-but-visible, which is worse than a bad number.
        cost = draft.get("token_cost") or {}
        if cost and tokens is None:
            findings.append({
                "draft": did, "field": "token_cost", "value": cost, "severity": "blocking",
                "why": "canonical token model unreadable; cannot verify shard elements"})
        else:
            for key, amount in cost.items():
                element = tokens.get(key) if tokens else None
                if element is None:
                    findings.append({
                        "draft": did, "field": "token_cost", "value": key, "severity": "blocking",
                        "why": "token variant not in gmm TOKEN_TYPES; cost cannot resolve to a wallet element"})
                elif element.lower() not in element_lookup:
                    findings.append({
                        "draft": did, "field": "token_cost", "value": f"{key}->{element}",
                        "severity": "blocking",
                        "why": "token maps to an element that is not in EMelodiaSpellElement"})
                elif not isinstance(amount, int) or amount < 0:
                    findings.append({
                        "draft": did, "field": "token_cost", "value": f"{key}={amount!r}",
                        "severity": "blocking", "why": "shard amount must be a non-negative integer"})
        content_pack = source_field(draft, shape["content_pack_id"])
        if content_pack is not None:
            if not isinstance(content_pack, str) or not content_pack.strip():
                findings.append({
                    "draft": did,
                    "field": shape["content_pack_id"],
                    "value": content_pack,
                    "severity": "blocking",
                    "why": "content-pack identity must be a non-empty string when present",
                })
            else:
                content_pack_mappings[did] = content_pack

    blocking = [f for f in findings if f["severity"] == "blocking"]
    owner_decisions = [f for f in findings if f["severity"] == "owner_decision"]
    unmodelled = [f for f in findings if f["severity"] == "unmodelled"]
    report = {
        "drafts_checked": len(files),
        "contract": {"rarity": rarities, "slot": slots, "element": elements,
                     "token_map": tokens or {},
                     "slot_aliases": slot_aliases,
                     "rarity_aliases": rarity_aliases,
                     "deferred_rarity_values": sorted(deferred_rarities),
                     "rarity_policy": rarity_policy,
                     "content_pack_field": reconciliation["content_pack_field"],
                     "content_pack_policy": reconciliation["content_pack_policy"]},
        "draft_roots": [str(root.relative_to(ROOT)) for root in DRAFT_ROOTS],
        "source_shapes": source_shape_counts,
        "slot_mappings": slot_mappings,
        "content_pack_mappings": content_pack_mappings,
        "blocking_count": len(blocking),
        "owner_decision_count": len(owner_decisions),
        "unmodelled_count": len(unmodelled),
        "drafts_with_blocking": sorted({f["draft"] for f in blocking}),
        "drafts_with_owner_decisions": sorted({f["draft"] for f in owner_decisions}),
        "findings": findings,
    }
    return report, (1 if blocking else 0)


def main() -> int:
    ap = argparse.ArgumentParser(description="Lint cosmetic drafts against the C++ wardrobe contract.")
    ap.add_argument("--verbose", action="store_true", help="per-finding detail")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    report, code = lint()

    if args.json:
        print(json.dumps(report, indent=2))
        return code

    if code == 2:
        print(f"[HOLD] {report['error']}: {', '.join(report['missing'])}")
        print("       A zero finding here would NOT mean the drafts are clean.")
        return code

    print(f"wardrobe draft lint - {report['drafts_checked']} drafts\n")
    print(f"  rarity  enum: {', '.join(report['contract']['rarity'])}")
    print(f"  slot    enum: {', '.join(report['contract']['slot'])}")
    print(f"  element enum: {', '.join(report['contract']['element'])}\n")

    by_field: dict[str, set] = {}
    for f in report["findings"]:
        by_field.setdefault(f"{f['severity']}:{f['field']}", set()).add(str(f["value"]))
    for key in sorted(by_field):
        sev, field = key.split(":", 1)
        vals = sorted(by_field[key])
        shown = ", ".join(vals[:6]) + (" ..." if len(vals) > 6 else "")
        print(f"  [{sev:10}] {field:16} {shown}")

    if args.verbose:
        print()
        for f in report["findings"]:
            print(f"  {f['severity']:10} {f['draft']:36} {f['field']}={f['value']}  -- {f['why']}")

    print(f"\n  {report['blocking_count']} blocking finding(s) across "
          f"{len(report['drafts_with_blocking'])} draft(s); "
          f"{report['owner_decision_count']} owner decision(s); "
          f"{report['unmodelled_count']} unmodelled-field note(s)")
    print("  blocking = data is silently lost or defaulted on import")
    print("  owner_decision = explicitly rejected until the owner maps it")
    return code


if __name__ == "__main__":
    sys.exit(main())
