#!/usr/bin/env python3
"""
echo_run.py - the Melodia Echo pipeline runner.

One entry point for the integration-layer gate chain declared in
`specs/echo_pipeline.json`. Mirrors the agent-gating shape HoYoverse's Echo
applies to AI-generated game content: a proposal may be authored by an agent or
the owner, but nothing is believed until a gate produces a ledger row.

    python Tools/echo_run.py list                     # stages + tools
    python Tools/echo_run.py status                   # ledger-backed completion gates
    python Tools/echo_run.py run static_gates         # editor-backed static chain
    python Tools/echo_run.py run runtime_gates        # editor-backed runtime tools
    python Tools/echo_run.py run --all                # static chain, then HOLD/FAIL
    python Tools/echo_run.py validate-spec spec.json  # contract check on a proposal
    python Tools/echo_run.py record <id> pass|fail --note "..."   # delegate to record_gate
    python Tools/echo_run.py record <id> pass --layer ch2_website --lane code
    python Tools/echo_run.py status --topo                        # DAG matrix + completion gates
    python Tools/echo_run.py topo schedule                        # classify eligible gates into lanes
    python Tools/echo_run.py topo check-promote ch1_gameplay.promote
    python Tools/echo_topo.py <cmd>                               # direct DAG processor

LIVENESS: stages that need the editor (static gates, pie_smoke, regression,
fingerprint, and the live allowlist query) are reported as HOLD when Monolith is
not answering on 9316. A HOLD is not a pass and never writes a ledger row.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
MANIFEST = os.path.join(PROJECT, "specs", "echo_pipeline.json")
LEDGER = os.path.join(PROJECT, "Saved", "gate_ledger.json")
TOPO_MANIFEST = os.path.join(PROJECT, "specs", "echo_topo.json")

DEFAULT_PIE_MAP = os.environ.get(
    "MELODIA_ECHO_PIE_MAP",
    "/Game/EnvSandbox/Environments/L_KaleidoNave",
)
ALLOWLIST_ASSET = os.environ.get(
    "MELODIA_ECHO_ALLOWLIST_ASSET",
    "/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig",
)

VERB_SPECS: dict[str, dict[str, Any]] = {
    "battle": {
        "parts": 3,
        "label": "EncounterId",
        "allowlist": "encounters",
    },
    "quest": {
        "parts": 3,
        "label": "QuestId",
        "allowlist": "quests",
        "consume_once": "id",
    },
    "flag": {
        "parts": 4,
        "label": "FlagId:<true|false>",
        "allowlist": "flags",
    },
    "travel": {
        "parts": 3,
        "label": "LevelId",
        "allowlist": "travel",
    },
    "reward": {
        "parts": 3,
        "label": "RewardId",
        "allowlist": "rewards",
        "consume_once": "id",
    },
    "stat": {
        "parts": 5,
        "label": "IntentId:StatId:Delta",
        "allowlist": "social_stats",
        "consume_once": "intent",
    },
    "item": {
        "parts": 5,
        "label": "give:ItemId:Count",
        "allowlist": "items",
        "consume_once": "item",
        "stub": True,
    },
}

TOKEN_RE = re.compile(
    r"melodia:(?:battle|quest|flag|travel|reward|stat|item):"
    r"[A-Za-z0-9_./+\-]+(?::[A-Za-z0-9_./+\-]+){0,3}"
    r"(?![A-Za-z0-9_./+\-:<])"
)
ID_RE = re.compile(r"^[A-Za-z0-9_./+\-]+$")
INT_RE = re.compile(r"^[+-]?\d+$")


def py(*args: str, cwd: str | None = None, timeout: int = 600) -> str:
    r = subprocess.run([sys.executable or "python"] + list(args),
                       capture_output=True, text=True, cwd=cwd or PROJECT, timeout=timeout)
    stdout = r.stdout.strip()
    stderr = r.stderr.strip()
    return "\n".join(part for part in (stdout, stderr) if part)


def run_py(*args: str, cwd: str | None = None, timeout: int = 600) -> tuple[int, str]:
    """Run a project Python tool and retain its exit code and combined output."""
    r = subprocess.run(
        [sys.executable or "python", *args],
        capture_output=True,
        text=True,
        cwd=cwd or PROJECT,
        timeout=timeout,
    )
    stdout = r.stdout.strip()
    stderr = r.stderr.strip()
    return r.returncode, "\n".join(part for part in (stdout, stderr) if part)


def editor_live() -> bool:
    """True when Monolith is answering on 9316. Editor-only stages hold otherwise."""
    try:
        import socket
        s = socket.create_connection(("127.0.0.1", 9316), timeout=1.5)
        s.close()
        return True
    except OSError:
        return False


def _ledger_latest() -> dict:
    if not os.path.exists(LEDGER):
        return {}
    try:
        with open(LEDGER, encoding="utf-8") as fh:
            ledger = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}
    latest = {}
    for g in ledger.get("gates", []):
        latest[g["id"]] = g
    return latest


def load_manifest() -> dict:
    with open(MANIFEST, encoding="utf-8") as fh:
        return json.load(fh)


def _strip_token_suffix(token: str) -> str:
    return token.rstrip(".,;:)]}\"'")


def _extract_tokens(text: str) -> list[str]:
    """Extract authored Melodia verbs without treating prose as a command."""
    return [_strip_token_suffix(match.group(0)) for match in TOKEN_RE.finditer(text)]


def _parse_token(token: str) -> tuple[str | None, list[str], str | None]:
    parts = token.split(":")
    if len(parts) < 2 or parts[0].lower() != "melodia":
        return None, parts, "token must start with melodia:"

    verb = parts[1].lower()
    spec = VERB_SPECS.get(verb)
    if spec is None:
        return verb, parts, f"unknown verb '{verb}'"
    if len(parts) != spec["parts"]:
        return verb, parts, (
            f"{verb} expects {spec['parts'] - 2} argument(s), "
            f"received {max(0, len(parts) - 2)}"
        )

    for value in parts[2:]:
        if not value or not ID_RE.fullmatch(value):
            return verb, parts, f"invalid identifier/value '{value}'"

    if verb == "flag" and parts[3].lower() not in ("true", "false"):
        return verb, parts, "flag value must be true or false"
    if verb == "stat" and not INT_RE.fullmatch(parts[4]):
        return verb, parts, "stat delta must be an integer"
    if verb == "item":
        if parts[2].lower() != "give":
            return verb, parts, "item verb must use item:give:<ItemId>:<Count>"
        if not INT_RE.fullmatch(parts[4]) or int(parts[4]) <= 0:
            return verb, parts, "item count must be a positive integer"
    return verb, parts, None


def _load_allowlist_file(path: str) -> tuple[dict[str, set[str]] | None, str | None]:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"cannot read allowlist {path}: {exc}"

    if isinstance(raw, dict) and isinstance(raw.get("allowlist"), dict):
        raw = raw["allowlist"]
    if not isinstance(raw, dict):
        return None, "allowlist must be a JSON object"

    result: dict[str, set[str]] = {}
    for key, value in raw.items():
        if isinstance(value, (list, tuple, set)):
            result[str(key)] = {str(item) for item in value}
    return result, None


def _query_live_allowlist() -> tuple[dict[str, set[str]] | None, str | None]:
    """Read the configured data asset through Monolith when the editor is live."""
    if not editor_live():
        return None, "editor is not reachable on 9316"

    try:
        sys.path.insert(0, HERE)
        from mcp_client import monolith

        command = f"""
import json, unreal
asset = unreal.load_asset({ALLOWLIST_ASSET!r})
fields = {{
    "encounters": "encounter_ids",
    "quests": "quest_ids",
    "flags": "narrative_flag_ids",
    "travel": "travel_level_ids",
    "rewards": "dialogue_reward_ids",
    "social_stats": "social_stat_ids",
}}
out = {{}}
if asset:
    for key, field in fields.items():
        try:
            values = asset.get_editor_property(field)
        except Exception:
            values = getattr(asset, field, None)
        out[key] = [str(value) for value in (values or [])]
print("__ECHO_ALLOWLIST__" + json.dumps(out))
"""
        raw = monolith(
            "editor_query",
            {"action": "run_python", "params": {"command": command}},
            timeout=15,
        )
        if isinstance(raw, str) and raw.startswith("ERROR:"):
            return None, raw
        payload = json.loads(raw) if isinstance(raw, str) else raw
        for item in payload.get("output", []) if isinstance(payload, dict) else []:
            for line in str(item.get("output", "")).splitlines():
                if line.startswith("__ECHO_ALLOWLIST__"):
                    data = json.loads(line[len("__ECHO_ALLOWLIST__"):])
                    return (
                        {key: {str(value) for value in values} for key, values in data.items()},
                        None,
                    )
        return None, "editor response did not contain an allowlist marker"
    except (ImportError, OSError, json.JSONDecodeError, RuntimeError, TypeError) as exc:
        return None, f"live allowlist query failed: {exc}"


def resolve_allowlist(
    allowlist_file: str | None = None,
    live: bool = False,
) -> tuple[dict[str, set[str]] | None, str | None, str | None]:
    """Resolve explicit, environment, local, then optional live authority."""
    candidates = [
        allowlist_file,
        os.environ.get("MELODIA_ECHO_ALLOWLIST"),
        os.path.join(PROJECT, "specs", "echo_allowlist.json"),
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            data, error = _load_allowlist_file(candidate)
            return data, candidate if data is not None else None, error
    if live:
        data, error = _query_live_allowlist()
        return data, "live:" + ALLOWLIST_ASSET if data is not None else None, error
    return None, None, "no allowlist file configured"


# ---------------------------------------------------------------- gate plugins

# The editor-backed gates are intentionally fail-closed. A missing editor,
# modal dialog, or transport failure is a HOLD and never becomes a pass.

def run_graph_reachability(timeout: int = 600) -> bool:
    code, _ = run_py("Tools/graph_reachability.py", "--all-melodia", "--ci", timeout=timeout)
    return code == 0


def run_bp_live_path(timeout: int = 600) -> bool:
    """Check configured live-path targets, failing on ORPHAN/AMBIGUOUS."""
    raw_targets = os.environ.get(
        "MELODIA_ECHO_LIVE_PATH_ASSETS",
        "/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI,BP_MelodiaJRPGGameMode",
    )
    targets = [target.strip() for target in raw_targets.split(",") if target.strip()]
    if not targets:
        return False

    for target in targets:
        code, _ = run_py("Tools/bp_live_path.py", target, "--json", timeout=timeout)
        if code != 0:
            return False
    return True


def run_bp_sweep(timeout: int = 600) -> bool:
    code, out = run_py("Tools/bp_sweep.py", "--limit", "200", timeout=timeout)
    if code != 0:
        return False
    findings: dict[str, int] = {}
    for label in ("SHADOWED", "EMPTY", "DEAD", "DUPES", "unreadable"):
        match = re.search(rf"^\s*{label}\s+(\d+)\b", out, flags=re.MULTILINE)
        if match:
            findings[label] = int(match.group(1))
    if len(findings) != 5:
        return False
    # SHADOWED/DUPES/unreadable are the shipped-defect classes that must be 0.
    # EMPTY/DEAD are noisy in stock template (167 empty stubs, 54 dead PEN nodes)
    # and are reported but do not fail the gate; the gate's value is the
    # shadowed-event and duplicate-name checks that previously reached main.
    critical = ("SHADOWED", "DUPES", "unreadable")
    return all(findings.get(k, 1) == 0 for k in critical)


def run_ui_lint(timeout: int = 600) -> bool:
    code, _ = run_py("Tools/ui_lint.py", "--all-melodia", timeout=timeout)
    return code == 0


def run_verify_baseline(timeout: int = 900) -> bool:
    r = subprocess.run([sys.executable or "python",
                        "Docs/T3D_Baseline/verify_baseline.py"],
                       capture_output=True, text=True,
                       cwd=PROJECT, timeout=timeout)
    return r.returncode == 0


STATIC = {
    "graph_reachability": run_graph_reachability,
    "bp_live_path": run_bp_live_path,
    "bp_sweep": run_bp_sweep,
    "ui_lint": run_ui_lint,
    "verify_baseline": run_verify_baseline,
}

EDITOR_ONLY = {
    "pie_smoke": [
        "Tools/pie_smoke_runner.py",
        "--map",
        DEFAULT_PIE_MAP,
        "--duration",
        os.environ.get("MELODIA_ECHO_PIE_DURATION", "10"),
    ],
    "regression": ["Tools/regression_suite.py", "--quick"],
    "fingerprint": ["Tools/bp_regression_checker.py", "--all"],
}


def validate_spec(
    path: str,
    allowlist_file: str | None = None,
    live_allowlist: bool = False,
    require_allowlist: bool = True,
) -> dict:
    """Validate a JSON/QSC/T3D proposal against the ECHO verb contract."""
    errors: list[str] = []
    warnings: list[str] = []
    verbs: list[str] = []
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        return {
            "ok": False,
            "errors": [str(exc)],
            "warnings": [],
            "verbs": [],
            "tokens": [],
        }

    data = None
    if Path(path).suffix.lower() == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            return {
                "ok": False,
                "errors": [f"not valid JSON: {exc}"],
                "warnings": [],
                "verbs": [],
                "tokens": [],
            }

    tokens = _extract_tokens(text)
    for token in tokens:
        verb, _, error = _parse_token(token)
        if error:
            errors.append(f"{token}: {error}")
            continue
        if verb not in verbs:
            verbs.append(verb)
        if VERB_SPECS[verb].get("stub"):
            errors.append(
                f"{token}: item:give is logging-only and cannot be promoted as an inventory grant"
            )

    # Scope duplicate checks to the identities the C++ authority actually
    # consumes: quest/reward/stat/item. Flags and travel are state requests,
    # not consume-once rewards.
    consumed: dict[str, str] = {}
    for token in tokens:
        verb, parts, error = _parse_token(token)
        if error or verb not in VERB_SPECS:
            continue
        consume_mode = VERB_SPECS[verb].get("consume_once")
        if consume_mode in ("id", "intent"):
            identity = parts[2]
        elif consume_mode == "item":
            identity = parts[3]
        else:
            continue
        identity_key = f"{verb}:{identity}"
        if identity_key in consumed:
            errors.append(
                f"{token}: duplicate consume-once identity; "
                f"first occurrence was {consumed[identity_key]}"
            )
        else:
            consumed[identity_key] = token

    allowlist_verbs = {
        verb
        for verb in verbs
        if VERB_SPECS[verb].get("allowlist") and not VERB_SPECS[verb].get("stub")
    }
    allowlist_source = None
    if allowlist_verbs:
        allowlist, allowlist_source, allowlist_error = resolve_allowlist(
            allowlist_file,
            live=live_allowlist,
        )
        if allowlist is None:
            message = (
                "allowlist unavailable; pass --allowlist-file or --live-allowlist "
                "to check DA_MelodiaIntegrationConfig"
            )
            if require_allowlist:
                errors.append(message + (f" ({allowlist_error})" if allowlist_error else ""))
            else:
                warnings.append(message)
        else:
            for token in tokens:
                verb, parts, error = _parse_token(token)
                if error or verb not in allowlist_verbs:
                    continue
                category = VERB_SPECS[verb]["allowlist"]
                values = allowlist.get(category)
                if values is None:
                    errors.append(f"{token}: allowlist has no '{category}' collection")
                    continue
                identifier = parts[3] if verb == "stat" else parts[2]
                if identifier not in values:
                    errors.append(
                        f"{token}: '{identifier}' is not in live allowlist '{category}'"
                    )

    if isinstance(data, dict) and data.get("ledger_id"):
        # A missing historical row is context, not proof of failure. Only
        # record_gate can create the evidence row after the gate is observed.
        claimed = data["ledger_id"]
        if claimed not in _ledger_latest():
            warnings.append(f"claimed gate '{claimed}' has no ledger baseline yet")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "verbs": verbs,
        "tokens": tokens,
        "allowlist_source": allowlist_source,
    }


# ------------------------------------------------------------------- plumbing

def cmd_list(manifest: dict) -> None:
    print("# Melodia Echo pipeline stages")
    for s in manifest["stages"]:
        impl = s.get("impl") or ",".join(s.get("impls", []))
        print(f"\n## {s['id']} ({s['label']})")
        print(f"  impl:     {impl}")
        print(f"  contract: {s.get('contract', '')}")


def cmd_status(args: argparse.Namespace | None = None) -> None:
    latest = _ledger_latest()
    print("# Completion gates (ledger-backed)")
    for gid, what in _load_manifest_completions().items():
        rec = latest.get(gid)
        if rec and rec.get("status") == "pass":
            mark = "PASS"
        elif rec and rec.get("status") == "fail":
            mark = "FAIL"
        else:
            mark = "OPEN"
        date = rec.get("date", "") if rec else ""
        print(f"  [{mark:<4}] {gid:<18} {date:<12} {what}")
    live = editor_live()
    print(f"\n  editor reachable on 9316: {'yes' if live else 'no (editor gates HOLD)'}")
    if args and getattr(args, "topo", False):
        _cmd_topo_summary()


def _load_manifest_completions() -> dict:
    m = load_manifest()
    return m.get("completion_definitions", {})


def _run_editor_stage(name: str) -> bool | None:
    if not editor_live():
        print(f"[HOLD] {name}: editor not reachable on 9316 - no ledger row written")
        return None
    try:
        code, out = run_py(*EDITOR_ONLY[name], timeout=900)
    except subprocess.TimeoutExpired:
        print(f"[HOLD] {name}: timed out against a busy editor")
        return None
    ok = code == 0
    print(f"[{'ok' if ok else 'FAIL'}] {name}\n{out[:1200]}")
    return ok


def run_runtime() -> bool | None:
    """Run the executable editor-backed portion of runtime_gates."""
    if not editor_live():
        print("[HOLD] runtime_gates: editor not reachable on 9316 - no ledger row written")
        return None

    all_ok = True
    for name in ("pie_smoke", "regression", "fingerprint"):
        result = _run_editor_stage(name)
        if result is None:
            return None
        all_ok = all_ok and result
    print(f"\n  runtime tool chain: {'ALL OK' if all_ok else 'FAILURES PRESENT'}")
    print("  Campaign evidence still requires the documented real-input/manual checks.")
    return all_ok


def cmd_run(args: argparse.Namespace) -> None:
    if args.all:
        result = run_static()
        print("\n  --all runs the static chain. editor/runtime gates (pie_smoke, regression,")
        print("  fingerprint) must be run with the editor up; no stage writes a ledger")
        print("  row automatically. Use 'record' only after reviewing evidence.")
        if result is None:
            sys.exit(2)
        if not result:
            sys.exit(1)
        return

    name = args.stage
    if name == "static_gates":
        result = run_static()
        if result is None:
            sys.exit(2)
        if not result:
            sys.exit(1)
        return
    if name == "runtime_gates":
        result = run_runtime()
        if result is None:
            sys.exit(2)
        if not result:
            sys.exit(1)
        return
    if name in EDITOR_ONLY:
        result = _run_editor_stage(name)
        if result is None:
            sys.exit(2)
        if not result:
            sys.exit(1)
        return
    names = list(STATIC) + list(EDITOR_ONLY) + ["runtime_gates"]
    print(f"unknown stage '{name}'. known: {', '.join(names)}")
    sys.exit(2)


def run_static() -> bool | None:
    print("# static gate chain (editor-gated: no ledger row without a responding editor)")
    if not editor_live():
        print("  [HOLD] editor not reachable on 9316 - run 'echo_run.py run static_gates'")
        print("         with the editor up and Monolith answering. No ledger row written.")
        return None
    all_ok = True
    for name, fn in STATIC.items():
        try:
            ok = fn()
        except subprocess.TimeoutExpired:
            ok, note = False, "timeout (tool hung against a busy editor)"
            print(f"  [HOLD] {name}: {note}")
            all_ok = False
            continue
        except Exception as e:  # noqa: BLE001 - a gate must not kill the chain
            ok, note = False, f"error: {e}"
            print(f"  [FAIL] {name}: {note}")
            all_ok = False
            continue
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        all_ok = all_ok and ok
    print(f"\n  static chain: {'ALL OK' if all_ok else 'FAILURES PRESENT'}")
    return all_ok


def _cmd_topo_summary() -> None:
    """Delegate topological DAG summary to echo_topo.py."""
    import subprocess as sp
    result = sp.run([sys.executable, os.path.join(HERE, "echo_topo.py"), "summary"],
                    capture_output=True, text=True, timeout=30)
    print("\n" + result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)


def _cmd_topo(args: argparse.Namespace) -> None:
    """Dispatch topological commands to echo_topo.py."""
    import subprocess as sp
    cmd = [sys.executable, os.path.join(HERE, "echo_topo.py"), args.topo_cmd]
    if args.topo_cmd == "check-promote":
        if not args.gate:
            print("ERROR: topo check-promote requires --gate <id>", file=sys.stderr)
            sys.exit(2)
        cmd.append(args.gate)
    if args.json:
        cmd.append("--json")
    result = sp.run(cmd, timeout=60)
    sys.exit(result.returncode)


def _cmd_topo_json() -> dict:
    """Return topo eligible gates as JSON (for programmatic consumers)."""
    import subprocess as sp
    result = sp.run(
        [sys.executable, os.path.join(HERE, "echo_topo.py"), "eligible", "--json"],
        capture_output=True, text=True, timeout=30,
    )
    return json.loads(result.stdout) if result.stdout else {}


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except (AttributeError, ValueError):
        pass

    ap = argparse.ArgumentParser(description="Melodia Echo pipeline runner")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")
    sp_status = sub.add_parser("status")
    sp_status.add_argument("--topo", action="store_true",
                          help="also show topological DAG readiness matrix")
    sp = sub.add_parser("run")
    sp.add_argument("stage", help="stage id, a gate tool name, or --all")
    sp.add_argument("--all", action="store_true")
    sv = sub.add_parser("validate-spec")
    sv.add_argument("path")
    sv.add_argument("--allowlist-file", help="JSON export of DA_MelodiaIntegrationConfig")
    sv.add_argument(
        "--live-allowlist",
        action="store_true",
        help="query DA_MelodiaIntegrationConfig through the live editor",
    )
    sv.add_argument(
        "--allowlist-optional",
        action="store_true",
        help="report missing allowlist as a warning instead of a validation error",
    )
    sr = sub.add_parser("record")
    sr.add_argument("gate_id")
    sr.add_argument("status", choices=["pass", "fail"])
    sr.add_argument("--note", default="")
    sr.add_argument("--layer", default="", help="topo layer id (e.g. ch2_environment)")
    sr.add_argument("--lane", default="", help="model lane (e.g. vision, code, audit)")

    sp_topo = sub.add_parser("topo", help="topological DAG view")
    sp_topo.add_argument("topo_cmd", nargs="?", default="summary",
                         choices=["eligible", "order", "schedule", "check-promote", "summary"])
    sp_topo.add_argument("--gate", help="gate id for check-promote")
    sp_topo.add_argument("--json", action="store_true")

    args = ap.parse_args()

    if args.cmd == "list":
        cmd_list(load_manifest())
    elif args.cmd == "status":
        cmd_status(args)
    elif args.cmd == "run":
        cmd_run(args)
    elif args.cmd == "validate-spec":
        res = validate_spec(
            args.path,
            allowlist_file=args.allowlist_file,
            live_allowlist=args.live_allowlist,
            require_allowlist=not args.allowlist_optional,
        )
        print(json.dumps(res, indent=2))
        sys.exit(0 if res["ok"] else 1)
    elif args.cmd == "record":
        record_args = ["Tools/record_gate.py", args.gate_id, args.status, "--note", args.note]
        if args.layer:
            record_args += ["--layer", args.layer]
        if args.lane:
            record_args += ["--lane", args.lane]
        code, output = run_py(*record_args)
        print(output or "recorded")
        if code != 0:
            sys.exit(code)
        # A recorded failure is intentionally non-zero so automation cannot
        # mistake an observed failure for a passing gate.
        sys.exit(0 if args.status == "pass" else 1)
    elif args.cmd == "topo":
        _cmd_topo(args)
    else:
        print("available: list | status | run | validate-spec | record | topo ; add --all to run")
        sys.exit(1)


if __name__ == "__main__":
    main()
