from __future__ import annotations

import importlib.util
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ECHO_PATH = PROJECT_ROOT / "Tools" / "echo_run.py"
SPEC = importlib.util.spec_from_file_location("melodia_echo_run", ECHO_PATH)
assert SPEC and SPEC.loader
echo_run = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(echo_run)


def write_allowlist(path: Path, **overrides: list[str]) -> Path:
    payload = {
        "encounters": [],
        "quests": [],
        "flags": [],
        "travel": [],
        "rewards": [],
        "social_stats": [],
        "items": [],
    }
    payload.update(overrides)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_json_without_intents_is_valid(tmp_path: Path) -> None:
    proposal = tmp_path / "proposal.json"
    proposal.write_text(json.dumps({"name": "neutral"}), encoding="utf-8")

    result = echo_run.validate_spec(str(proposal))

    assert result["ok"] is True
    assert result["tokens"] == []


def test_stat_arity_and_delta_are_checked(tmp_path: Path) -> None:
    proposal = tmp_path / "proposal.qsc"
    proposal.write_text(
        "$ Notify melodia:stat:only_two_parts\n"
        "$ Notify melodia:stat:intent:melodia_harmony:not_an_integer\n",
        encoding="utf-8",
    )
    allowlist = write_allowlist(tmp_path / "allowlist.json", social_stats=["melodia_harmony"])

    result = echo_run.validate_spec(str(proposal), allowlist_file=str(allowlist))

    assert result["ok"] is False
    assert any("expects 3 argument" in error for error in result["errors"])
    assert any("delta must be an integer" in error for error in result["errors"])


def test_duplicate_reward_identity_is_rejected(tmp_path: Path) -> None:
    proposal = tmp_path / "proposal.qsc"
    proposal.write_text(
        "$ Notify melodia:reward:melodia_smoke_reward\n"
        "$ Notify melodia:reward:melodia_smoke_reward\n",
        encoding="utf-8",
    )
    allowlist = write_allowlist(
        tmp_path / "allowlist.json",
        rewards=["melodia_smoke_reward"],
    )

    result = echo_run.validate_spec(str(proposal), allowlist_file=str(allowlist))

    assert result["ok"] is False
    assert any("duplicate consume-once identity" in error for error in result["errors"])


def test_allowlist_rejects_unknown_identifier(tmp_path: Path) -> None:
    proposal = tmp_path / "proposal.qsc"
    proposal.write_text("$ Notify melodia:quest:melodia_q_missing\n", encoding="utf-8")
    allowlist = write_allowlist(tmp_path / "allowlist.json", quests=["melodia_q_known"])

    result = echo_run.validate_spec(str(proposal), allowlist_file=str(allowlist))

    assert result["ok"] is False
    assert any("not in live allowlist 'quests'" in error for error in result["errors"])
