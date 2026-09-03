#!/usr/bin/env python3
"""Collect the canonical Melodia project-health claims.

Writes Saved/Audit/project_health_claims.json. Cheap by default: file parses,
ledger rows, editor ping, MATH harness eval. Does not pretend editor-backed
gates were re-run.

    python Tools/project_health.py
    python Tools/project_health.py --json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "Tools"
SAVED = ROOT / "Saved"
AUDIT = SAVED / "Audit"
SPECS = ROOT / "specs"
STATUS_SIBLING = Path(r"C:\EnvironmentPortfolio\generated\melodia\status")

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import echo_run  # noqa: E402


REQUIRED_COMPLETION = ("runtime", "save_load", "repeat_consume", "package_launch")
TRACKED_BATTLE = ("battle_encounter", "battle_integration_map")
UTF8_DIRS = ("specs", "Tools", "deploy")
UTF8_DOCS = "Docs"
UTF8_SUFFIXES = {".md", ".json", ".py", ".toml", ".yml", ".yaml"}
DOC_LINK_FAIL_AT = 200


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _claim(
    cid: str,
    label: str,
    status: str,
    evidence: str,
    *,
    required: bool = False,
    editor_backed: bool = False,
    note: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": cid,
        "label": label,
        "status": status,
        "evidence": evidence,
        "required": required,
        "editor_backed": editor_backed,
    }
    if note:
        row["note"] = note
    if extra:
        row.update(extra)
    return row


def _ledger_row(latest: dict[str, Any], gid: str) -> dict[str, Any] | None:
    rec = latest.get(gid)
    return rec if isinstance(rec, dict) else None


def _gate_status(rec: dict[str, Any] | None) -> str:
    if not rec:
        return "open"
    raw = str(rec.get("status") or "").lower()
    if raw == "pass":
        return "pass"
    if raw == "fail":
        return "fail"
    return "hold"


def _gate_evidence(rec: dict[str, Any] | None, gid: str) -> str:
    if not rec:
        return f"echo_run.py status / ledger: no row for {gid}"
    date = rec.get("date") or ""
    time = rec.get("time") or ""
    note = (rec.get("note") or "")[:180]
    return f"Saved/gate_ledger.json {gid} {date} {time} - {note}"


def _json_load(path: Path) -> tuple[Any | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig")), None
    except FileNotFoundError:
        return None, f"missing {path.relative_to(ROOT)}"
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON {path.name}: {exc}"
    except OSError as exc:
        return None, str(exc)


def _utf8_hygiene() -> dict[str, Any]:
    bad: list[str] = []
    checked = 0
    for folder in UTF8_DIRS:
        root = ROOT / folder
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in UTF8_SUFFIXES:
                continue
            if any(part.startswith(".") or part == "__pycache__" for part in path.parts):
                continue
            checked += 1
            try:
                path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                bad.append(str(path.relative_to(ROOT)).replace("\\", "/"))
            except OSError:
                continue
    extra_docs_bad: list[str] = []
    docs = ROOT / UTF8_DOCS
    if docs.is_dir():
        for path in docs.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in UTF8_SUFFIXES:
                continue
            if any(part.startswith(".") or part == "__pycache__" for part in path.parts):
                continue
            checked += 1
            try:
                path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                extra_docs_bad.append(str(path.relative_to(ROOT)).replace("\\", "/"))
            except OSError:
                continue
    status = "fail" if bad else "pass"
    evidence = f"strict UTF-8 on {checked} files under {', '.join(UTF8_DIRS)}"
    if bad:
        evidence += f"; decode errors: {', '.join(bad[:8])}"
    elif extra_docs_bad:
        evidence += f"; Docs has {len(extra_docs_bad)} non-UTF-8 files (recorded, not gating): {', '.join(extra_docs_bad[:4])}"
    return {"status": status, "evidence": evidence, "bad": bad + extra_docs_bad, "checked": checked}


def _doc_links() -> dict[str, Any]:
    script = TOOLS / "doc_link_check.py"
    if not script.is_file():
        return {"status": "hold", "evidence": "Tools/doc_link_check.py missing", "broken": -1}
    try:
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "hold", "evidence": f"doc_link_check failed to run: {exc}", "broken": -1}
    text = (proc.stdout or "") + (proc.stderr or "")
    checked = broken = 0
    for line in text.splitlines():
        if line.startswith("checked ") and "BROKEN" in line:
            parts = line.replace(",", "").split()
            try:
                checked = int(parts[1])
                broken = int(parts[3])
            except (IndexError, ValueError):
                pass
            break
    if broken >= DOC_LINK_FAIL_AT:
        status = "fail"
    elif broken > 0:
        status = "warn"
    else:
        status = "pass"
    return {
        "status": status,
        "evidence": f"Tools/doc_link_check.py - {checked} local links, {broken} broken (fail at {DOC_LINK_FAIL_AT})",
        "broken": broken,
        "checked": checked,
    }


def _policy_coverage() -> dict[str, Any]:
    policy, err = _json_load(SPECS / "mcp_tool_policy.v1.json")
    if err:
        return {"status": "fail", "evidence": err}
    if not isinstance(policy, dict):
        return {"status": "fail", "evidence": "mcp_tool_policy.v1.json is not an object"}
    default = policy.get("default_decision")
    tokens = policy.get("forbidden_path_tokens") or []
    tools = policy.get("tools") or {}
    hits: list[str] = []
    # Only path-shaped tokens (e.g. content/_project/, l_sakurapath). The
    # policy also lists a bare "sakura" token for MCP path args; that would
    # false-positive every Docs/ file that mentions the world.
    path_tokens = [str(t).lower() for t in tokens if "/" in str(t) or str(t).lower().startswith("l_")]
    for folder in (SPECS,):
        for path in folder.rglob("*"):
            if not path.is_file():
                continue
            rel = str(path.relative_to(ROOT)).replace("\\", "/").lower()
            for tok in path_tokens:
                if tok and tok in rel:
                    hits.append(str(path.relative_to(ROOT)).replace("\\", "/"))
                    break
    if default != "deny":
        return {
            "status": "fail",
            "evidence": f"default_decision={default!r} (want deny); {len(tools)} tools",
        }
    status = "fail" if hits else "pass"
    evidence = (
        f"specs/mcp_tool_policy.v1.json parseable, default deny, {len(tools)} tools, "
        f"{len(tokens)} forbidden tokens"
    )
    if hits:
        evidence += f"; forbidden path hits: {', '.join(hits[:6])}"
    return {"status": status, "evidence": evidence, "hits": hits}


def _allowlist(live: bool) -> dict[str, Any]:
    seed = SPECS / "progression" / "melodia_integration_allowlist_seed.v1.json"
    data, src, err = echo_run.resolve_allowlist(None, live=live)
    if data:
        n = sum(len(v) for v in data.values())
        if src and str(src).startswith("live:"):
            return {
                "status": "pass",
                "evidence": f"live allowlist {src} ({n} ids across {len(data)} sets)",
            }
        return {
            "status": "hold",
            "evidence": f"file allowlist {src} ({n} ids). Live DA_MelodiaIntegrationConfig not used this stamp.",
        }
    if seed.is_file():
        raw, seed_err = _json_load(seed)
        if raw and isinstance(raw, dict) and isinstance(raw.get("sets"), dict):
            sets = raw["sets"]
            n = sum(len(v) for v in sets.values() if isinstance(v, list))
            return {
                "status": "hold",
                "evidence": (
                    f"{seed.relative_to(ROOT).as_posix()} parseable ({n} seed ids). "
                    f"resolve_allowlist: {err or 'no echo_allowlist.json; live query skipped or failed'}"
                ),
            }
        return {"status": "fail", "evidence": seed_err or err or "seed unreadable"}
    return {"status": "fail", "evidence": err or "no allowlist file configured"}


def _run_mcp_suite() -> dict[str, Any]:
    script = TOOLS / "test_melodia_mcp.py"
    try:
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "fail", "evidence": f"test_melodia_mcp.py did not run: {exc}", "passed": 0, "total": 0}
    line = ""
    for candidate in reversed((proc.stdout or "").splitlines()):
        if " passed," in candidate:
            line = candidate.strip()
            break
    passed = total = 0
    if "/" in line:
        head = line.split()[0]
        try:
            passed, total = (int(x) for x in head.split("/", 1))
        except ValueError:
            pass
    status = "pass" if proc.returncode == 0 and (total == 0 or passed == total) else "fail"
    return {
        "status": status,
        "evidence": f"Tools/test_melodia_mcp.py {line or f'rc={proc.returncode}'}",
        "passed": passed,
        "total": total,
    }


def _run_math() -> dict[str, Any]:
    try:
        from run_math_eval import run_eval, write_report
    except ImportError:
        sys.path.insert(0, str(TOOLS))
        from run_math_eval import run_eval, write_report  # type: ignore
    report = run_eval()
    path = write_report(report)
    status = "pass" if report.get("failed") == 0 else "fail"
    return {
        "status": status,
        "evidence": (
            f"{path.relative_to(ROOT).as_posix()} - {report['passed']}/{report['total']} "
            f"TCA={report['tca_pct']}% (harness self-eval, not an LLM)"
        ),
        "passed": report["passed"],
        "total": report["total"],
        "tca_pct": report["tca_pct"],
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
    }


def _overall(claims: list[dict[str, Any]]) -> str:
    required = [c for c in claims if c.get("required")]
    if any(c["status"] == "fail" for c in required):
        return "fail"
    if any(c["status"] in {"hold", "open", "warn"} for c in required):
        return "hold"
    if any(c["status"] == "fail" for c in claims):
        return "hold"
    return "pass"


def collect(*, run_math: bool = True, run_mcp: bool = False) -> dict[str, Any]:
    live = echo_run.editor_live()
    latest = echo_run._ledger_latest()
    pipeline, pipe_err = _json_load(SPECS / "echo_pipeline.json")
    ci_gates, ci_err = _json_load(SPECS / "ci_gates.json")
    fingerprints, fp_err = _json_load(ROOT / "Docs" / "T3D_Baseline" / "bp_fingerprints.json")
    policy = _policy_coverage()
    allow = _allowlist(live)
    utf8 = _utf8_hygiene()
    docs = _doc_links()

    claims: list[dict[str, Any]] = []
    defs = (pipeline or {}).get("completion_definitions") or {}
    for gid in REQUIRED_COMPLETION:
        rec = _ledger_row(latest, gid)
        claims.append(
            _claim(
                f"completion_{gid}",
                f"Completion gate: {gid}",
                _gate_status(rec),
                _gate_evidence(rec, gid),
                required=True,
                editor_backed=True,
                note=defs.get(gid, ""),
            )
        )
    for gid in TRACKED_BATTLE:
        rec = _ledger_row(latest, gid)
        claims.append(
            _claim(
                gid,
                f"Gameplay gate: {gid}",
                _gate_status(rec),
                _gate_evidence(rec, gid),
                required=False,
                editor_backed=True,
            )
        )

    if pipeline and isinstance(pipeline, dict) and set(REQUIRED_COMPLETION).issubset(set(pipeline.get("completion_gates", []))):
        verb_status, verb_ev = "pass", f"specs/echo_pipeline.json parseable; {len(pipeline.get('completion_gates', []))} completion gates + 7-verb agent_contract"
    else:
        verb_status, verb_ev = "fail", pipe_err or "echo_pipeline.json missing completion_gates"
    claims.append(_claim("contract_verb", "Verb contract valid (echo_pipeline.json)", verb_status, verb_ev, required=True))

    claims.append(
        _claim(
            "contract_allowlist",
            "Allowlist authority resolvable",
            allow["status"],
            allow["evidence"],
            required=True,
            editor_backed=allow["status"] == "pass",
        )
    )
    claims.append(
        _claim("policy_coverage", "MCP tool policy parseable + default deny", policy["status"], policy["evidence"], required=True)
    )

    if fingerprints and isinstance(fingerprints, dict) and fingerprints:
        fp_status, fp_ev = "pass", f"Docs/T3D_Baseline/bp_fingerprints.json parseable ({len(fingerprints)} assets)"
    else:
        fp_status, fp_ev = "fail", fp_err or "fingerprints empty"
    claims.append(_claim("baseline_fingerprints", "Blueprint fingerprint baseline present + parseable", fp_status, fp_ev, required=True))

    if ci_gates and isinstance(ci_gates, dict) and ci_gates:
        ci_status, ci_ev = "pass", f"specs/ci_gates.json valid ({len(ci_gates)} keys)"
    else:
        ci_status, ci_ev = "fail", ci_err or "ci_gates.json empty"
    claims.append(_claim("baseline_ci_gates", "ci_gates.json valid", ci_status, ci_ev, required=True))

    claims.append(_claim("doc_links", "Doc links below threshold", docs["status"], docs["evidence"]))
    claims.append(_claim("hygiene_utf8", "Tracked text files strict UTF-8", utf8["status"], utf8["evidence"], required=True))
    claims.append(
        _claim(
            "editor_reachable",
            "Monolith reachable on 9316",
            "yes" if live else "no",
            "echo_run.editor_live() socket 127.0.0.1:9316",
            editor_backed=True,
        )
    )

    hermes_mcp = ROOT / "deploy" / "hermes_mcp.py"
    hermes_daemon = ROOT / "deploy" / "hermes_daemon.py"
    if hermes_mcp.is_file() and hermes_daemon.is_file():
        claims.append(
            _claim(
                "hermes_harness",
                "Hermes agentic harness present (not a model pull)",
                "pass",
                "deploy/hermes_mcp.py + deploy/hermes_daemon.py; MATH self-eval scores this surface, not Nous Hermes 3 weights",
            )
        )
    else:
        claims.append(
            _claim(
                "hermes_harness",
                "Hermes agentic harness present (not a model pull)",
                "fail",
                "deploy/hermes_mcp.py or hermes_daemon.py missing",
            )
        )

    swe = Path(r"C:\EnvironmentPortfolio\.agents\swe_3\progress.md")
    if swe.is_file():
        text = swe.read_text(encoding="utf-8", errors="replace")
        if "Victory Audit" in text and "[x]" in text.lower():
            orch_status, orch_ev = "pass", str(swe)
        elif "Phase 1: Implementation" in text:
            orch_status, orch_ev = (
                "hold",
                ".agents/swe_3 Phase 1 running (teamwork_preview_swe). No Animation/Audio/UI wrapper files landed yet; Qwen/Muse wiring eval not on disk.",
            )
        else:
            orch_status, orch_ev = "hold", f"{swe} present"
        claims.append(
            _claim(
                "orchestrator_swe_light",
                "SWE Light orchestrator (Qwen/Muse wrapper expansion)",
                orch_status,
                orch_ev,
            )
        )

    try:
        import urllib.request

        tags = json.loads(urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3).read().decode())
        names = [str(m.get("name") or "") for m in tags.get("models") or []]
    except Exception:
        names = []
    qwen = [n for n in names if "qwen" in n.lower()]
    muse = [n for n in names if "muse" in n.lower() or "glimmer" in n.lower()]
    claims.append(
        _claim(
            "model_qwen_local",
            "Local Qwen available for harness eval",
            "pass" if qwen else "hold",
            f"ollama tags: {', '.join(qwen) or 'none'}. Eval runner: Tools/run_math_models.py (does not pull Hermes weights).",
        )
    )
    claims.append(
        _claim(
            "model_muse_glimmer",
            "Muse Glimmer available for harness eval",
            "pass" if muse else "open",
            (
                f"ollama tags: {', '.join(muse)}"
                if muse
                else "no ollama tag, G:\\ Muse-Glimmer-30B-direct missing, OPENROUTER_API_KEY unset - skip, do not invent scores"
            ),
        )
    )

    if run_mcp:
        mcp = _run_mcp_suite()
        claims.append(
            _claim(
                "mcp_suite",
                "MCP registry/policy suite",
                mcp["status"],
                mcp["evidence"],
                required=True,
                extra={"passed": mcp.get("passed"), "total": mcp.get("total")},
            )
        )
    if run_math:
        math = _run_math()
        claims.append(
            _claim(
                "math_eval",
                "MATH harness self-eval",
                math["status"],
                math["evidence"],
                required=True,
                extra={"passed": math.get("passed"), "total": math.get("total"), "tca_pct": math.get("tca_pct")},
            )
        )

    overall = _overall(claims)
    payload = {
        "schema": "melodia.project_health_claims.v1",
        "generated_at": _now(),
        "overall": overall,
        "editor_reachable": live,
        "refresh_policy": {
            "project_health": "on demand via python Tools/health.py; stale if generated_at is old or editor_reachable is no for editor-backed claims",
            "pie_telemetry": "current only while PIE is active (live_dashboard / metrics_dashboard)",
            "agent_loop": "reflects deploy stop files / Saved/AgentMemory",
            "ci": "offline slice only; editor-backed completion gates are ledger history, not a live re-check",
        },
        "orchestra": [
            {"id": "project_health", "path": "Saved/project_health.html", "role": "standing scorecard"},
            {"id": "loop_monitor", "path": "Saved/loop_monitor.html", "role": "editor connection + BP wiring"},
            {"id": "live", "path": "Saved/live_dashboard.html", "role": "PIE telemetry"},
            {"id": "metrics", "path": "Saved/metrics_dashboard.html", "role": "PIE character / loop phase"},
            {"id": "t3d_claims", "path": "Saved/agent-dashboard-t3d.html", "role": "session claim verification"},
            {"id": "agent_loop", "path": "wix/agent-dashboard.html", "role": "agent loop stop/ready"},
        ],
        "claims": claims,
    }
    return payload


def write_claims(payload: dict[str, Any]) -> Path:
    AUDIT.mkdir(parents=True, exist_ok=True)
    path = AUDIT / "project_health_claims.json"
    text = json.dumps(payload, indent=2)
    path.write_text(text, encoding="utf-8")
    if STATUS_SIBLING.is_dir():
        (STATUS_SIBLING / "project_health_claims.json").write_text(text, encoding="utf-8")
    return path


def print_summary(payload: dict[str, Any]) -> None:
    print(f"project health: {payload['overall'].upper()}  editor={ 'yes' if payload['editor_reachable'] else 'no' }  {payload['generated_at']}")
    for claim in payload["claims"]:
        mark = str(claim["status"]).upper()
        req = " *" if claim.get("required") else ""
        print(f"  [{mark:<7}] {claim['id']:<28}{req}  {claim['evidence'][:110]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--skip-math", action="store_true")
    parser.add_argument("--mcp", action="store_true", help="also run Tools/test_melodia_mcp.py")
    args = parser.parse_args(argv)
    payload = collect(run_math=not args.skip_math, run_mcp=args.mcp)
    path = write_claims(payload)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print_summary(payload)
        print(f"wrote {path}")
    return 0 if payload["overall"] != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
