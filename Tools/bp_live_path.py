#!/usr/bin/env python3
"""
bp_live_path.py - is this asset on the live path, or are you about to author
into something nothing runs?

NOT THE SAME AS Tools/graph_reachability.py. That one asks an INTRA-graph
question: which exec nodes inside a graph are unreachable from an event entry.
This one asks an INTER-asset question: is the graph's owner instantiated by
anything that actually runs. A Blueprint can pass graph_reachability cleanly --
every node wired, no dead islands -- and still be an asset nothing ever
constructs. Both were caused by real defects here; run both.

WHY THIS EXISTS

Every other verification tier in this project reads the INSIDE of a graph:
`get_graph_fingerprint` and `assert_graph_matches` compare one graph to itself
over time, `compile_blueprint` proves it is well-formed, and `pie_smoke_runner`
watches the log. None of them can see whether anything instantiates the graph's
owner -- and that is where this project's wiring defects have actually lived:

  * BP_BattleUI had a live ShowBattleUI exec chain that NOTHING constructed, so
    lane input, the rhythm highway, focus and teardown were all dead code.
  * A lane remap was authored into UMelodiaBattleInputComponent, which only
    AMelodiaGameMode instantiates -- but the configured mode is
    BP_MelodiaJRPGGameMode, so the component is never created. That edit
    compiled clean and moved a fingerprint and did nothing.

Note especially that a dead path passes `pie_smoke_runner`. It raises no
Blueprint Runtime Error and drops no `must_present` line; it produces silence,
and silence reads as a clean run. Reachability is not something the smoke tier
can be extended to cover -- it needs its own question, which is this one.

USAGE

  python Tools/bp_live_path.py /Game/Path/To/Asset          # one asset
  python Tools/bp_live_path.py BP_BattleUI                  # short name
  python Tools/bp_live_path.py /Game/... --json             # machine output

Exit codes: 0 = LIVE, 1 = ORPHAN, 2 = AMBIGUOUS, 3 = tool/transport error.
Branch on the exit code or on the first output line; do not parse the prose.

WHAT "ORPHAN" MEANS -- READ THIS BEFORE DELETING ANYTHING

ORPHAN means "prove this is reachable before you author into it." It does NOT
mean "safe to delete." Static reference walking is blind to:

  * TSoftObjectPtr fields, which never populate the hard-reference graph
    (Decision 049 -- five live-wired Quill assets were flagged as orphans on
    exactly this mistake).
  * Actor references living inside .umap files (Decisions 020 / 029d / 037a --
    "content references what C++ greps call dead").
  * Anything constructed by class name from C++, config, or a data asset.

So a LIVE verdict is trustworthy and an ORPHAN verdict is a question. Treating
ORPHAN as proof of deadness would recreate the incident Decision 049 exists to
prevent.
"""
import argparse
import configparser
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from mcp_client import monolith  # noqa: E402

PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_ENGINE_INI = PROJECT / "Config" / "DefaultEngine.ini"
MAX_HOPS = 8


def _strip_object_path(value):
    """'/Game/X/Y.Y_C' -> '/Game/X/Y'. Config stores object paths; the asset
    registry keys on package names."""
    if not value:
        return None
    value = value.strip()
    if "." in value:
        value = value.split(".", 1)[0]
    return value or None


def read_anchors():
    """The configured entry points a live asset must ultimately hang off.

    Read from DefaultEngine.ini rather than asked of the editor: these are the
    values that ship, and reading them from disk keeps the anchor set honest if
    someone has changed them in-session without saving.
    """
    cfg = configparser.ConfigParser(strict=False)
    cfg.optionxform = str
    try:
        cfg.read(DEFAULT_ENGINE_INI, encoding="utf-8-sig")
    except OSError as e:
        return {}, f"cannot read {DEFAULT_ENGINE_INI}: {e}"

    section = "/Script/EngineSettings.GameMapsSettings"
    if not cfg.has_section(section):
        return {}, f"{DEFAULT_ENGINE_INI} has no [{section}]"

    anchors = {}
    for key in ("GlobalDefaultGameMode", "GameDefaultMap", "EditorStartupMap"):
        pkg = _strip_object_path(cfg.get(section, key, fallback=None))
        if pkg:
            anchors[pkg] = key
    if not anchors:
        return {}, "no anchors configured in GameMapsSettings"
    return anchors, None


# The reachability walk runs inside the editor: one round trip instead of one
# per hop, and get_referencers is only available there. Returns JSON on stdout
# via a sentinel line, because run_python gives us print output, not a value.
WALK = r"""
import json, unreal

TARGETS = {targets!r}
ANCHORS = {anchors!r}
MAX_HOPS = {max_hops}

ar = unreal.AssetRegistryHelpers.get_asset_registry()
opts = unreal.AssetRegistryDependencyOptions(
    include_soft_package_references=True,
    include_hard_package_references=True,
)

def is_world(pkg):
    for a in ar.get_assets_by_package_name(pkg) or []:
        if str(a.asset_class_path.asset_name) == "World":
            return True
    return False

def exists(pkg):
    return bool(ar.get_assets_by_package_name(pkg))

out = {{}}
for target in TARGETS:
    if not exists(target):
        out[target] = {{"exists": False}}
        continue

    # Breadth-first walk UP the reference graph, recording the first path that
    # lands on a configured anchor. Parents are tracked so the reported chain is
    # the actual route, not just the fact that one exists.
    seen = {{target: None}}
    frontier = [target]
    hit = None
    worlds = []
    hops = 0

    while frontier and hit is None and hops < MAX_HOPS:
        nxt = []
        for pkg in frontier:
            for ref in (ar.get_referencers(pkg, opts) or []):
                ref = str(ref)
                if ref in seen:
                    continue
                seen[ref] = pkg
                if ref in ANCHORS:
                    hit = ref
                    break
                if is_world(ref):
                    worlds.append(ref)
                nxt.append(ref)
            if hit:
                break
        frontier = nxt
        hops += 1

    # A World that references the asset is itself an anchor-grade signal: the
    # level is content that ships. Recorded separately from config anchors so
    # the verdict can say which kind of evidence it found.
    anchor = hit or (worlds[0] if worlds else None)
    chain = []
    if anchor:
        node = anchor
        while node is not None:
            chain.append(node)
            node = seen.get(node)
        chain.reverse()

    out[target] = {{
        "exists": True,
        "anchor": anchor,
        "anchor_kind": (ANCHORS.get(hit) if hit else ("World" if worlds else None)),
        "chain": chain,
        "direct_referencers": [str(r) for r in (ar.get_referencers(target, opts) or [])],
        "worlds": worlds,
    }}

print("__REACH__" + json.dumps(out))
"""


def find_by_short_name(name):
    """Every package whose asset short name matches. Duplicate copies of a
    template are the reason this exists -- BP_BattleUI has two, each with its
    own BP_BattleController, and a substring assertion cannot tell them apart.
    """
    code = (
        "import json, unreal\n"
        "ar = unreal.AssetRegistryHelpers.get_asset_registry()\n"
        "f = unreal.ARFilter(package_paths=['/Game'], recursive_paths=True)\n"
        "hits = [str(a.package_name) for a in ar.get_assets(f)\n"
        f"        if str(a.asset_name) == {name!r}]\n"
        'print("__REACH__" + json.dumps(hits))\n'
    )
    return _run(code)


def probe_native_class(name):
    """Reachability for a C++ class, which owns no /Game asset.

    The remap that motivated this tool edited UMelodiaBattleInputComponent, a
    native class. The asset registry cannot see it at all, so the question has to
    be asked differently: does any CONTENT reach this class -- as a Blueprint
    parent, or as a reference from a live asset?

    A native class reached only from other C++ (as this component is, being added
    by AMelodiaGameMode in code) is reported UNKNOWN_NATIVE rather than ORPHAN.
    The tool genuinely cannot see C++-to-C++ construction, and saying ORPHAN
    would be asserting something it did not check.
    """
    stripped = name[1:] if name[:1] in ("U", "A", "F") and name[1:2].isupper() else name
    code = (
        "import json, unreal\n"
        "ar = unreal.AssetRegistryHelpers.get_asset_registry()\n"
        f"short = {stripped!r}\n"
        "f = unreal.ARFilter(package_paths=['/Game'], recursive_paths=True)\n"
        "children, refs = [], []\n"
        "for a in ar.get_assets(f):\n"
        "    for key in ('NativeParentClass', 'ParentClass'):\n"
        "        try:\n"
        "            v = str(a.get_tag_value(key) or '')\n"
        "        except Exception:\n"
        "            v = ''\n"
        "        if short and short in v:\n"
        "            children.append(str(a.package_name)); break\n"
        "cls = unreal.find_object(None, '/Script/BS_GodFile.' + short) or \\\n"
        "      unreal.find_object(None, '/Script/MelodiaCore.' + short)\n"
        'print("__REACH__" + json.dumps({"short": short, "children": sorted(set(children)), '
        '"class_found": bool(cls)}))\n'
    )
    return _run(code)


def _run(code):
    raw = monolith("editor_query", {"action": "run_python", "params": {"command": code}})
    if isinstance(raw, str) and raw.startswith("ERROR:"):
        raise RuntimeError(raw)
    try:
        payload = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        raise RuntimeError(f"unparseable run_python response: {str(raw)[:300]}")
    if not payload.get("ok", payload.get("success")):
        raise RuntimeError(f"run_python failed: {json.dumps(payload)[:400]}")
    for item in payload.get("output", []):
        for line in str(item.get("output", "")).splitlines():
            if line.startswith("__REACH__"):
                return json.loads(line[len("__REACH__"):])
    raise RuntimeError(f"no result marker in run_python output: {json.dumps(payload)[:400]}")


def main():
    ap = argparse.ArgumentParser(description="Report whether an asset is on the live path.")
    ap.add_argument("asset", help="/Game/... package path, or a bare asset short name")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    anchors, anchor_err = read_anchors()
    if anchor_err:
        # Fail closed. Without anchors every asset would look unreachable, and a
        # tool that reports ORPHAN for everything trains people to ignore it.
        print(f"ERROR {anchor_err}")
        return 3

    try:
        if args.asset.startswith("/"):
            targets = [args.asset.split(".", 1)[0]]
            copies = find_by_short_name(targets[0].rsplit("/", 1)[-1])
        else:
            copies = find_by_short_name(args.asset)
            targets = list(copies)
            if not targets:
                # No content asset by that name. Treat it as a native class --
                # this is the UMelodiaBattleInputComponent case.
                nat = probe_native_class(args.asset)
                if nat["children"]:
                    print(f"LIVE-VIA-CONTENT {args.asset}")
                    for c in nat["children"]:
                        print(f"  subclassed by {c}")
                    print("  Re-run against those assets to confirm they reach an entry point.")
                    return 0
                print(f"UNKNOWN_NATIVE {args.asset}")
                print("  No /Game asset and no Blueprint subclasses this class.")
                print("  Nothing in CONTENT reaches it. If it is constructed from C++, this tool")
                print("  cannot see that -- check the constructing class by hand, and check that")
                print("  the constructor itself is on the live path.")
                print("  (UMelodiaBattleInputComponent is the worked example: only AMelodiaGameMode")
                print("   adds it, and the configured mode is BP_MelodiaJRPGGameMode, so it is")
                print("   never created.)")
                return 1
        results = _run(WALK.format(targets=targets, anchors=anchors, max_hops=MAX_HOPS))
    except RuntimeError as e:
        print(f"ERROR {e}")
        return 3

    if args.json:
        print(json.dumps({"anchors": anchors, "copies": copies, "results": results}, indent=2))

    # AMBIGUOUS applies only when the caller used a bare short name. An explicit
    # /Game/... path IS the disambiguation (reconciliation doc: "resolve the n
    # entry points first") -- report that copy's verdict and list the others as
    # informational. The duplicate _ThirdParty island (retired GameMode chain,
    # Decision 029a) must not fail the canonical BP_BattleUI check.
    ambiguous = len(copies) > 1 and not args.asset.startswith("/")
    verdicts = []
    for target in targets:
        r = results.get(target, {})
        if not r.get("exists"):
            verdict = "ORPHAN"
            detail = "asset not found in the registry"
        elif r.get("anchor"):
            verdict = "LIVE"
            detail = f"{r['anchor_kind']} <- {' <- '.join(reversed(r['chain']))}"
        elif r.get("direct_referencers"):
            verdict = "ORPHAN"
            detail = (f"referenced by {len(r['direct_referencers'])} asset(s) but no route to a "
                      f"configured entry point within {MAX_HOPS} hops")
        else:
            verdict = "ORPHAN"
            detail = "nothing references it"
        verdicts.append(verdict)
        if not args.json:
            print(f"{verdict} {target}")
            print(f"  {detail}")

    if ambiguous and not args.json:
        print(f"AMBIGUOUS({len(copies)}) more than one asset shares this short name:")
        for c in copies:
            mark = "LIVE" if results.get(c, {}).get("anchor") else "orphan"
            print(f"  [{mark}] {c}")
        print("  Confirm which copy you mean before authoring -- a substring assertion "
              "passes against either.")

    if ambiguous:
        return 2
    return 0 if verdicts and all(v == "LIVE" for v in verdicts) else 1


if __name__ == "__main__":
    sys.exit(main())
