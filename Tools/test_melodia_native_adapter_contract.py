"""Check that progression specs, reflected headers, and native source agree.

This is a dependency-free, editor-free gate. It cannot prove UHT, Blueprint
reflection, or runtime behavior; it prevents a contract from claiming a native
surface that the source does not expose and checks the fail-closed allowlist seam.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_HEADER = ROOT / "Source" / "BS_GodFile" / "MelodiaIntegration" / "MelodiaIntegrationConfig.h"
NARRATIVE_HEADER = ROOT / "Source" / "BS_GodFile" / "MelodiaIntegration" / "MelodiaNarrativeSubsystem.h"
NARRATIVE_TYPES = ROOT / "Source" / "BS_GodFile" / "MelodiaIntegration" / "MelodiaNarrativeTypes.h"
NARRATIVE_CPP = ROOT / "Source" / "BS_GodFile" / "MelodiaIntegration" / "MelodiaNarrativeSubsystem.cpp"
WORLD_SPEC = ROOT / "specs" / "progression" / "melodia_world_challenge_adapter.v1.json"
ANCHOR_SPEC = ROOT / "specs" / "progression" / "melodia_state_anchor_adapter.v1.json"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise AssertionError(f"expected object: {path}")
    return value


def require_reflected_method(header: str, method: str, macro: str) -> None:
    pattern = rf"{re.escape(macro)}.*?\b{re.escape(method)}\s*\(" 
    assert re.search(pattern, header, re.DOTALL), f"missing reflected method: {method}"


def main() -> int:
    config = CONFIG_HEADER.read_text(encoding="utf-8")
    header = NARRATIVE_HEADER.read_text(encoding="utf-8")
    types = NARRATIVE_TYPES.read_text(encoding="utf-8")
    cpp = NARRATIVE_CPP.read_text(encoding="utf-8")
    world = load_json(WORLD_SPEC)
    anchor = load_json(ANCHOR_SPEC)

    for field in ("WorldChallengeIds", "StateAnchorIds"):
        assert f"TSet<FName> {field};" in config
        assert f"Config->{field}.Contains" in cpp

    for method in ("IsWorldChallengeCompleted", "CommitWorldChallenge"):
        require_reflected_method(header, method, "UFUNCTION")
        assert header.count(method) == 1
        assert cpp.count(f"UMelodiaNarrativeSubsystem::{method}") == 1

    for method in ("IsStateAnchorApplied", "ApplyStateAnchor"):
        require_reflected_method(header, method, "UFUNCTION")
        assert header.count(method) == 1
        assert cpp.count(f"UMelodiaNarrativeSubsystem::{method}") == 1

    assert "BeginWorldChallengeAttempt" not in header
    assert "BeginWorldChallengeAttempt" not in cpp
    assert world["transient_attempt_surface"]["native_adapter_required"] is False
    assert world["required_native_surface"]["read_completion"].startswith(
        "BlueprintPure IsWorldChallengeCompleted"
    )
    assert anchor["required_native_surface"]["read"].startswith(
        "BlueprintPure IsStateAnchorApplied"
    )

    assert "UENUM(BlueprintType)" in types
    assert "EMelodiaContentCommitFailure" in types
    assert "UnknownChallenge" in types and "UnknownAnchor" in types
    assert "FMelodiaStateAnchorOperation" in types

    challenge_validation = cpp.index("Config->WorldChallengeIds.Contains(ChallengeId)")
    challenge_mutation = cpp.index("NarrativeRecord.Flags.Add(CompletionFlagId, true)")
    anchor_validation = cpp.index("Config->StateAnchorIds.Contains(AnchorId)")
    anchor_mutation = cpp.index("NarrativeRecord.ConsumedIntentIds.Add(ApplyIntentId)")
    assert challenge_validation < challenge_mutation
    assert anchor_validation < anchor_mutation
    assert "All validation is complete before the first canonical field is changed" in cpp
    assert "The complete operation list has been validated before this transaction" in cpp

    print("validated native adapter contract surfaces")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
