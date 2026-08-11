import argparse
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

MONOLITH_URL = "http://localhost:9316/mcp"

# Tracked, NOT under Saved/. Saved/ is gitignored, so a baseline kept there
# vanishes on a clean checkout -- and this script used to respond to a missing
# baseline by writing a new one and reporting OK, which turns a drift detector
# into a rubber stamp. Decision 046 recorded that failure once already
# ("prior catalogs evaporated on the next clean checkout"). Docs/T3D_Baseline/
# is where material_catalog.json lives for the same reason.
FINGERPRINT_FILE = Path(__file__).resolve().parents[1] / "Docs" / "T3D_Baseline" / "bp_fingerprints.json"
LEGACY_FINGERPRINT_FILE = Path(__file__).resolve().parents[1] / "Saved" / "bp_fingerprints.json"

DEFAULT_BPS = [
    "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController",
    "/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance",
    "/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI",
    "/Game/Melodia/UI/WBP_MainMenu",
]
SCAN_PREFIXES = ["/Game/TurnBasedJRPGTemplate", "/Game/MelodiaIntegration", "/Game/Melodia"]
PROJECT_ROOT = FINGERPRINT_FILE.parents[1]
CONTENT_ROOT = PROJECT_ROOT / "Content"
SCAN_CONTENT_ROOTS = [
    CONTENT_ROOT / "TurnBasedJRPGTemplate" / "Blueprints",
    CONTENT_ROOT / "MelodiaIntegration" / "Blueprints",
    CONTENT_ROOT / "Melodia",
]


def fetch_fingerprint(asset_path: str, mode: str = "topology") -> dict | None:
    arguments = {"action": "get_graph_fingerprint", "asset_path": asset_path, "mode": mode}
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "blueprint_query", "arguments": arguments},
    }).encode()
    req = Request(MONOLITH_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=15) as resp:
            envelope = json.loads(resp.read().decode())
        text = envelope.get("result", {}).get("content", [{}])[0].get("text", "")
        return json.loads(text)
    except URLError as e:
        print(f"  [ERROR] Monolith unreachable for {asset_path}: {e}", file=sys.stderr)
        return None
    except (json.JSONDecodeError, TypeError) as e:
        print(f"  [ERROR] Invalid JSON response for {asset_path}: {e}", file=sys.stderr)
        return None


def load_saved() -> dict | None:
    """The tracked baseline, or None when there isn't one.

    Returns None rather than {} on purpose: the caller must be able to tell
    "no baseline" from "an empty baseline", because the first is a reason to
    stop and the second is a reason to compare. A corrupt file is a hard error
    -- silently starting fresh over unreadable bytes is how a drift detector
    stops detecting drift.
    """
    if FINGERPRINT_FILE.exists():
        try:
            return json.loads(FINGERPRINT_FILE.read_text())
        except (json.JSONDecodeError, OSError) as e:
            print(f"[FAIL] Baseline at {FINGERPRINT_FILE} is unreadable: {e}", file=sys.stderr)
            print("       Restore it from git rather than regenerating -- a regenerated "
                  "baseline agrees with whatever is on disk now and proves nothing.",
                  file=sys.stderr)
            sys.exit(1)
    return None


def save_fingerprints(data: dict) -> None:
    FINGERPRINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    FINGERPRINT_FILE.write_text(json.dumps(data, indent=2))
    print(f"[OK] Fingerprints saved to {FINGERPRINT_FILE}")


def fingerprint_bp(asset_path: str) -> dict | None:
    print(f"  Fingerprinting {asset_path} ...")
    result = fetch_fingerprint(asset_path)
    if result is None:
        return None
    if result.get("status") != "ok" and "fingerprint" not in result:
        print(f"  [ERROR] API returned error for {asset_path}: {result}", file=sys.stderr)
        return None
    return result


def compare_fingerprints(current: dict, baseline: dict) -> list[str]:
    changes = []
    for path, curr_data in current.items():
        base_data = baseline.get(path)
        if base_data is None:
            changes.append(f"  [NEW] {path} has no baseline fingerprint")
            continue
        curr_fp = curr_data.get("fingerprint") if isinstance(curr_data, dict) else curr_data
        base_fp = base_data.get("fingerprint") if isinstance(base_data, dict) else base_data
        if curr_fp != base_fp:
            changes.append(f"  [CHANGED] {path}")
    for path in baseline:
        if path not in current:
            changes.append(f"  [MISSING] {path} was in baseline but not fingerprinted now")
    return changes


def _call_tool(method: str, arguments: dict) -> str | None:
    """Raw tools/call to Monolith; returns the text content or None on failure."""
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": method, "arguments": arguments},
    }).encode()
    req = Request(MONOLITH_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=15) as resp:
            envelope = json.loads(resp.read().decode())
        text = envelope.get("result", {}).get("content", [{}])[0].get("text", "")
        return text
    except (URLError, json.JSONDecodeError, TypeError) as e:
        print(f"  [ERROR] Monolith unreachable: {e}", file=sys.stderr)
        return None


def scan_via_monolith() -> list[str] | None:
    """Enumerate Blueprint assets under SCAN_PREFIXES via project_query.

    Uses project_query:find_by_type (verified contract: required param
    `asset_type`; paginated via offset/limit, capped at 100/page; assets carry
    `package_path`). Blueprint, WidgetBlueprint and AnimBlueprint classes are
    scanned; results are filtered client-side to SCAN_PREFIXES.

    Returns a sorted list of /Game/ asset paths, or None when the registry
    scan is impossible (Monolith down or unexpected response shape).
    """
    found: list[str] = []
    for asset_type in ("Blueprint", "WidgetBlueprint", "AnimBlueprint"):
        offset = 0
        while True:
            text = _call_tool("project_query", {
                "action": "find_by_type",
                "asset_type": asset_type,
                "offset": offset,
                "limit": 100,
            })
            if text is None:
                return None
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                return None
            if not isinstance(parsed, dict) or not isinstance(parsed.get("assets"), list):
                return None
            assets = parsed["assets"]
            found.extend(
                a["package_path"] for a in assets
                if isinstance(a, dict) and a.get("package_path", "").startswith(tuple(SCAN_PREFIXES))
            )
            if len(assets) < 100:
                break
            offset += len(assets)
    return sorted(set(found)) if found else None


def scan_content_disk() -> list[str]:
    """Walk the Content folders on disk for .uasset files under the scan roots.

    Excludes directories that are third-party or texture/material folders
    (matched by substring on directory segments, e.g. "_ThirdParty",
    "Textures", "04_Materials") and converts on-disk paths to /Game/ asset
    paths.
    """
    excluded = ("_thirdparty", "third party", "texture", "material")
    found = []
    for root in SCAN_CONTENT_ROOTS:
        if not root.is_dir():
            continue
        for uasset in root.rglob("*.uasset"):
            dir_parts = " ".join(p.lower() for p in uasset.parts[:-1])
            if any(seg in dir_parts for seg in excluded):
                continue
            try:
                rel = uasset.relative_to(CONTENT_ROOT)
            except ValueError:
                continue
            game_path = "/Game/" + rel.as_posix()[: -len(".uasset")]
            found.append(game_path)
    return sorted(set(found))


def filter_blueprint_class(candidates: list[str]) -> list[str]:
    """Filter candidates down to Blueprint class by attempting a fingerprint.

    Non-Blueprint assets (or unreachable Monolith) fail the fingerprint call and
    are reported as [ERROR] without crashing the scan.
    """
    kept = []
    for path in candidates:
        result = fetch_fingerprint(path)
        if result is not None and (result.get("status") == "ok" or "fingerprint" in result):
            kept.append(path)
        else:
            print(f"  [ERROR] {path} is not a fingerprintable Blueprint (skipped)", file=sys.stderr)
    return kept


def collect_all_bps() -> list[str]:
    """Enumerate Blueprint assets under SCAN_PREFIXES.

    Order: live Monolith registry scan -> on-disk Content walk (filtered to
    Blueprint class by fingerprinting) -> DEFAULT_BPS fallback.
    """
    assets = scan_via_monolith()
    if assets:
        print(f"[OK] Found {len(assets)} Blueprint(s) via Monolith registry scan", file=sys.stderr)
        return assets

    status_text = _call_tool("monolith_status", {}) or ""
    try:
        status = json.loads(status_text)
        ready = isinstance(status, dict) and "server_running" in status
    except json.JSONDecodeError:
        ready = False
    if not ready:
        print("[WARN] Monolith not ready; cannot filter candidates to Blueprint class", file=sys.stderr)
        return list(DEFAULT_BPS)

    candidates = scan_content_disk()
    if candidates:
        print(f"[OK] Found {len(candidates)} candidate .uasset(s) on disk; filtering to Blueprint class...", file=sys.stderr)
        bps = filter_blueprint_class(candidates)
        if bps:
            print(f"[OK] {len(bps)} Blueprint(s) confirmed by fingerprint", file=sys.stderr)
            return bps

    print(f"[WARN] Scan returned nothing; falling back to {len(DEFAULT_BPS)} default Blueprint(s)", file=sys.stderr)
    return list(DEFAULT_BPS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Blueprints regression checker")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--bp", type=str, help="Fingerprint a single Blueprint asset path")
    group.add_argument("--all", action="store_true", help="Scan all Melodia Blueprints")
    parser.add_argument("--update", action="store_true", help="Accept current fingerprints as new baseline")
    args = parser.parse_args()

    if args.bp:
        targets = [args.bp]
    elif args.all:
        targets = collect_all_bps()
    else:
        print("Usage: provide --bp <path> or --all")
        sys.exit(1)

    print(f"Fingerprinting {len(targets)} Blueprint(s) via Monolith...")
    current = {}
    failures = 0
    for bp in targets:
        result = fingerprint_bp(bp)
        if result is not None:
            current[bp] = result
        else:
            failures += 1

    if not current:
        print("[FAIL] No fingerprints obtained; cannot proceed.", file=sys.stderr)
        sys.exit(1)

    if failures:
        print(f"[WARN] {failures} Blueprint(s) failed to fingerprint.", file=sys.stderr)

    baseline = load_saved()

    if args.update:
        # Merge, never replace. `--bp X --update` fingerprints exactly one asset,
        # so writing `current` wholesale would drop every other entry in the
        # baseline -- silently, and the next --all run would then report those
        # assets as brand new rather than as drifted.
        merged = dict(baseline or {})
        merged.update(current)
        dropped = len(merged) - len(baseline or {})
        save_fingerprints(merged)
        print(f"[OK] Baseline updated: {len(current)} accepted, {dropped} new, "
              f"{len(merged)} total.")
        return

    if baseline is None:
        # Deliberately NOT auto-accepting. Writing a baseline here would make
        # every first run pass by construction, including the run right after a
        # clean checkout -- which is exactly when you most want to know that the
        # comparison never happened.
        print(f"[FAIL] No baseline at {FINGERPRINT_FILE}.", file=sys.stderr)
        if LEGACY_FINGERPRINT_FILE.exists():
            print(f"       A legacy baseline exists at {LEGACY_FINGERPRINT_FILE} (under the "
                  "gitignored Saved/). Move it to the tracked path above and commit it.",
                  file=sys.stderr)
        else:
            print("       Restore it from git, or run with --update to accept the current "
                  "graphs as the baseline -- but only if you have separately verified them.",
                  file=sys.stderr)
        sys.exit(1)

    if args.bp:
        baseline = {bp: v for bp, v in baseline.items() if bp == args.bp}

    changes = compare_fingerprints(current, baseline)
    if changes:
        print("--- Unexpected changes detected ---")
        for c in changes:
            print(c)
        sys.exit(1)
    else:
        print("[OK] All fingerprints match baseline — no unexpected changes.")


if __name__ == "__main__":
    main()
