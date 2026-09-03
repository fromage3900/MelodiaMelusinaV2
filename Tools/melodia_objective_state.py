"""Deterministic offline projection for a Melodia progression package.

This module is a contract verifier, not a runtime or save authority.  It models
the fields already owned by ``FMelodiaNarrativeRecord`` so a package can prove
ordered objective transitions, exactly-once effects, and restore behavior before
any editor or Blueprint materialization work begins.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE_PATH = ROOT / "specs" / "progression" / "melodia_first_dream_progression.v1.json"


class ObjectiveState(str, Enum):
    LOCKED = "locked"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class TransitionStatus(str, Enum):
    APPLIED = "applied"
    ALREADY_APPLIED = "already_applied"


class ProgressionError(ValueError):
    """Base error for malformed package or canonical-record state."""


class TransitionRejected(ProgressionError):
    """Raised when an objective or quest cannot transition yet."""


class InconsistentRecord(ProgressionError):
    """Raised when a save contains a partial or contradictory transition."""


@dataclass(frozen=True)
class TransitionResult:
    status: TransitionStatus
    owner_id: str
    outcome: str


def load_package(path: Path = DEFAULT_PACKAGE_PATH) -> dict[str, Any]:
    """Load one source-controlled progression package without editor access."""

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProgressionError(f"progression package must be an object: {path}")
    return value


def fresh_record() -> dict[str, Any]:
    """Return the save-backed fields used by the offline projection."""

    return {
        "flags": {},
        "active_quest_ids": [],
        "consumed_intent_ids": [],
        "consumed_reward_ids": [],
        "script_checkpoint": None,
    }


class ObjectiveStateProjection:
    """Read/transition model for the canonical narrative-record fields.

    The projection intentionally stores no package-owned save file and has no
    Unreal imports.  A runtime implementation must route equivalent operations
    through ``UMelodiaNarrativeSubsystem`` and persist them in
    ``FMelodiaNarrativeRecord``.
    """

    def __init__(
        self,
        package: Mapping[str, Any],
        record: Mapping[str, Any] | None = None,
    ) -> None:
        self.package = deepcopy(dict(package))
        self.record = _normalise_record(record)
        self._chapters = {self.package["chapter"]["chapter_id"]: self.package["chapter"]}
        self._beats = _index(self.package.get("beats", []), "beat_id")
        self._quests = _index(self.package.get("quests", []), "quest_id")
        self._objectives = _index(self.package.get("objectives", []), "objective_id")
        self._rewards = _index(self.package.get("rewards", []), "reward_id")
        self._consequences = _index(self.package.get("consequences", []), "consequence_id")
        self._validate_indexes()

    @classmethod
    def from_package_path(
        cls,
        path: Path = DEFAULT_PACKAGE_PATH,
        record: Mapping[str, Any] | None = None,
    ) -> "ObjectiveStateProjection":
        return cls(load_package(path), record)

    @classmethod
    def from_snapshot(
        cls,
        package: Mapping[str, Any],
        snapshot: Mapping[str, Any],
    ) -> "ObjectiveStateProjection":
        projection = cls(package)
        projection.restore(snapshot)
        return projection

    def snapshot(self) -> dict[str, Any]:
        """Return a stable, JSON-serializable canonical-record projection."""

        return {
            "flags": {
                key: self.record["flags"][key]
                for key in sorted(self.record["flags"])
            },
            "active_quest_ids": sorted(self.record["active_quest_ids"]),
            "consumed_intent_ids": sorted(self.record["consumed_intent_ids"]),
            "consumed_reward_ids": sorted(self.record["consumed_reward_ids"]),
            "script_checkpoint": self.record["script_checkpoint"],
        }

    def restore(self, snapshot: Mapping[str, Any]) -> None:
        """Restore canonical fields and reject partial transitions fail-closed."""

        candidate = _normalise_record(snapshot)
        previous = self.record
        self.record = candidate
        try:
            self._validate_record_consistency()
        except Exception:
            self.record = previous
            raise

    def quest_state(self, quest_id: str) -> ObjectiveState:
        quest = self._require(self._quests, quest_id, "quest")
        completion_flag = quest["completion_flag_id"]
        complete_intent = quest["complete_intent_id"]
        flag_present = self.record["flags"].get(completion_flag, False)
        intent_present = complete_intent in self.record["consumed_intent_ids"]
        if flag_present != intent_present:
            raise InconsistentRecord(
                f"quest {quest_id} has a partial completion marker"
            )
        if flag_present:
            return ObjectiveState.COMPLETED
        if quest_id in self.record["active_quest_ids"]:
            if quest["accept_intent_id"] not in self.record["consumed_intent_ids"]:
                raise InconsistentRecord(
                    f"active quest {quest_id} is missing its accept intent"
                )
            return ObjectiveState.ACTIVE
        return ObjectiveState.LOCKED

    def beat_state(self, beat_id: str) -> ObjectiveState:
        beat = self._require(self._beats, beat_id, "beat")
        states = [self.objective_state(objective_id) for objective_id in beat["objective_ids"]]
        if any(state == ObjectiveState.ACTIVE for state in states):
            return ObjectiveState.ACTIVE
        if any(state == ObjectiveState.FAILED for state in states):
            if all(state in (ObjectiveState.COMPLETED, ObjectiveState.FAILED) for state in states):
                return ObjectiveState.FAILED
        if states and all(state == ObjectiveState.COMPLETED for state in states):
            return ObjectiveState.COMPLETED
        return ObjectiveState.LOCKED

    def objective_state(self, objective_id: str) -> ObjectiveState:
        objective = self._require(self._objectives, objective_id, "objective")
        completed = self._transition_marker(objective["completion"])
        failed = (
            self._transition_marker(objective["failure"])
            if objective["failure"] is not None
            else False
        )
        if completed and failed:
            raise InconsistentRecord(
                f"objective {objective_id} is both completed and failed"
            )
        if completed:
            self._assert_effects_applied(objective["completion"]["effects"])
            return ObjectiveState.COMPLETED
        if failed:
            self._assert_effects_applied(objective["failure"]["effects"])
            return ObjectiveState.FAILED
        if not self._quest_is_active(objective["quest_id"]):
            return ObjectiveState.LOCKED
        return (
            ObjectiveState.ACTIVE
            if self._prerequisites_satisfied(objective["prerequisites"])
            else ObjectiveState.LOCKED
        )

    def current_objective(self, quest_id: str) -> str | None:
        """Return the first active objective in the authored quest order."""

        quest = self._require(self._quests, quest_id, "quest")
        for objective_id in quest["objective_ids"]:
            if self.objective_state(objective_id) == ObjectiveState.ACTIVE:
                return objective_id
        return None

    def activate_quest(self, quest_id: str) -> TransitionResult:
        quest = self._require(self._quests, quest_id, "quest")
        state = self.quest_state(quest_id)
        accept_intent = quest["accept_intent_id"]
        if state == ObjectiveState.COMPLETED:
            raise TransitionRejected(f"completed quest cannot be activated: {quest_id}")
        if state == ObjectiveState.ACTIVE:
            return TransitionResult(
                TransitionStatus.ALREADY_APPLIED, quest_id, "accept"
            )
        if accept_intent in self.record["consumed_intent_ids"]:
            raise InconsistentRecord(
                f"quest {quest_id} has an accept intent but is not active"
            )
        if not self._prerequisites_satisfied(quest["prerequisites"]):
            raise TransitionRejected(f"quest prerequisites are unmet: {quest_id}")

        candidate = deepcopy(self.record)
        candidate["active_quest_ids"].append(quest_id)
        candidate["consumed_intent_ids"].append(accept_intent)
        self.record = candidate
        return TransitionResult(TransitionStatus.APPLIED, quest_id, "accept")

    def complete_objective(
        self,
        objective_id: str,
        outcome: str = "complete",
    ) -> TransitionResult:
        objective = self._require(self._objectives, objective_id, "objective")
        if outcome not in ("complete", "fail"):
            raise TransitionRejected(f"unknown objective outcome: {outcome}")
        transition = objective["completion"] if outcome == "complete" else objective["failure"]
        if transition is None:
            raise TransitionRejected(f"objective has no failure branch: {objective_id}")

        state = self.objective_state(objective_id)
        desired = ObjectiveState.COMPLETED if outcome == "complete" else ObjectiveState.FAILED
        if state == desired:
            self._assert_effects_applied(transition["effects"])
            return TransitionResult(TransitionStatus.ALREADY_APPLIED, objective_id, outcome)
        if state != ObjectiveState.ACTIVE:
            raise TransitionRejected(
                f"objective {objective_id} is {state.value}, cannot {outcome}"
            )

        candidate = deepcopy(self.record)
        self._apply_transition(candidate, transition)
        checkpoint_id = objective.get("checkpoint_id")
        if checkpoint_id:
            candidate["script_checkpoint"] = checkpoint_id
        self.record = candidate
        return TransitionResult(TransitionStatus.APPLIED, objective_id, outcome)

    def complete_quest(self, quest_id: str) -> TransitionResult:
        quest = self._require(self._quests, quest_id, "quest")
        state = self.quest_state(quest_id)
        if state == ObjectiveState.COMPLETED:
            return TransitionResult(TransitionStatus.ALREADY_APPLIED, quest_id, "complete")
        if state != ObjectiveState.ACTIVE:
            raise TransitionRejected(f"quest is not active: {quest_id}")

        objective_states = [
            self.objective_state(objective_id) for objective_id in quest["objective_ids"]
        ]
        if not all(
            state in (ObjectiveState.COMPLETED, ObjectiveState.FAILED)
            for state in objective_states
        ):
            raise TransitionRejected(f"quest objectives are not terminal: {quest_id}")

        completion_flag = quest["completion_flag_id"]
        complete_intent = quest["complete_intent_id"]
        candidate = deepcopy(self.record)
        if completion_flag in candidate["flags"] or complete_intent in candidate["consumed_intent_ids"]:
            raise InconsistentRecord(f"quest {quest_id} has a partial completion marker")
        candidate["flags"][completion_flag] = True
        candidate["consumed_intent_ids"].append(complete_intent)
        candidate["active_quest_ids"].remove(quest_id)
        candidate["script_checkpoint"] = self.package["chapter"]["checkpoint_id"]
        self.record = candidate
        return TransitionResult(TransitionStatus.APPLIED, quest_id, "complete")

    def _apply_transition(
        self,
        candidate: dict[str, Any],
        transition: Mapping[str, Any],
    ) -> None:
        intent_id = transition["intent_id"]
        flag_id = transition["flag_id"]
        if intent_id in candidate["consumed_intent_ids"] or flag_id in candidate["flags"]:
            raise InconsistentRecord(f"transition marker already exists: {intent_id}")
        candidate["consumed_intent_ids"].append(intent_id)
        candidate["flags"][flag_id] = True

        effects = transition["effects"]
        for reward_id in effects["reward_ids"]:
            reward = self._require(self._rewards, reward_id, "reward")
            grant_intent = reward["grant_intent_id"]
            if (
                reward_id in candidate["consumed_reward_ids"]
                or grant_intent in candidate["consumed_intent_ids"]
            ):
                raise InconsistentRecord(f"reward already partially consumed: {reward_id}")
            candidate["consumed_reward_ids"].append(reward_id)
            candidate["consumed_intent_ids"].append(grant_intent)

        for consequence_id in effects["consequence_ids"]:
            consequence = self._require(self._consequences, consequence_id, "consequence")
            consequence_intent = consequence["intent_id"]
            if consequence_intent in candidate["consumed_intent_ids"]:
                raise InconsistentRecord(
                    f"consequence intent already consumed: {consequence_id}"
                )
            candidate["consumed_intent_ids"].append(consequence_intent)
            self._apply_consequence(candidate, consequence)

    def _apply_consequence(
        self,
        candidate: dict[str, Any],
        consequence: Mapping[str, Any],
    ) -> None:
        target = consequence["target"]
        target_type = target["type"]
        target_id = target["id"]
        value = target["value"]
        if target_type == "narrative_flag":
            if target_id in candidate["flags"]:
                raise InconsistentRecord(f"consequence flag already exists: {target_id}")
            candidate["flags"][target_id] = value
        elif target_type == "checkpoint":
            if candidate["script_checkpoint"] is not None:
                raise InconsistentRecord("consequence cannot overwrite an existing checkpoint")
            candidate["script_checkpoint"] = value
        elif target_type == "quest":
            if not isinstance(value, bool):
                raise ProgressionError("quest consequence value must be boolean")
            is_active = target_id in candidate["active_quest_ids"]
            if is_active == value:
                raise InconsistentRecord(f"quest consequence is already applied: {target_id}")
            if value:
                candidate["active_quest_ids"].append(target_id)
            else:
                candidate["active_quest_ids"].remove(target_id)
        else:
            raise ProgressionError(f"unsupported consequence target: {target_type}")

    def _assert_effects_applied(self, effects: Mapping[str, Any]) -> None:
        for reward_id in effects["reward_ids"]:
            reward = self._require(self._rewards, reward_id, "reward")
            reward_consumed = reward_id in self.record["consumed_reward_ids"]
            intent_consumed = reward["grant_intent_id"] in self.record["consumed_intent_ids"]
            if reward_consumed != intent_consumed or not reward_consumed:
                raise InconsistentRecord(f"reward effect is partial: {reward_id}")

        for consequence_id in effects["consequence_ids"]:
            consequence = self._require(self._consequences, consequence_id, "consequence")
            intent_consumed = consequence["intent_id"] in self.record["consumed_intent_ids"]
            target = consequence["target"]
            if target["type"] == "narrative_flag":
                target_applied = (
                    target["id"] in self.record["flags"]
                    and self.record["flags"][target["id"]] == target["value"]
                )
            elif target["type"] == "checkpoint":
                target_applied = self.record["script_checkpoint"] == target["value"]
            elif target["type"] == "quest":
                target_applied = (
                    target["id"] in self.record["active_quest_ids"]
                    if target["value"]
                    else target["id"] not in self.record["active_quest_ids"]
                )
            else:
                raise ProgressionError(f"unsupported consequence target: {target['type']}")
            if intent_consumed != target_applied or not intent_consumed:
                raise InconsistentRecord(f"consequence effect is partial: {consequence_id}")

    def _transition_marker(self, transition: Mapping[str, Any] | None) -> bool:
        if transition is None:
            return False
        flag_present = self.record["flags"].get(transition["flag_id"], False)
        intent_present = transition["intent_id"] in self.record["consumed_intent_ids"]
        if flag_present != intent_present:
            raise InconsistentRecord(
                f"transition marker is partial: {transition['intent_id']}"
            )
        return flag_present

    def _quest_is_active(self, quest_id: str) -> bool:
        return self.quest_state(quest_id) == ObjectiveState.ACTIVE

    def _prerequisites_satisfied(self, prerequisites: list[Mapping[str, Any]]) -> bool:
        for prerequisite in prerequisites:
            state = self._entity_state(prerequisite["type"], prerequisite["id"])
            if state.value not in prerequisite["satisfied_states"]:
                return False
        return True

    def _entity_state(self, entity_type: str, entity_id: str) -> ObjectiveState:
        if entity_type == "objective":
            return self.objective_state(entity_id)
        if entity_type == "quest":
            return self.quest_state(entity_id)
        if entity_type == "beat":
            return self.beat_state(entity_id)
        if entity_type == "chapter":
            chapter = self._require(self._chapters, entity_id, "chapter")
            states = [self.beat_state(beat_id) for beat_id in chapter["beat_ids"]]
            if states and all(state == ObjectiveState.COMPLETED for state in states):
                return ObjectiveState.COMPLETED
            if any(state == ObjectiveState.ACTIVE for state in states):
                return ObjectiveState.ACTIVE
            return ObjectiveState.LOCKED
        raise ProgressionError(f"unsupported prerequisite type: {entity_type}")

    def _validate_indexes(self) -> None:
        for objective in self._objectives.values():
            self._require(self._quests, objective["quest_id"], "quest")
            self._require(self._beats, objective["beat_id"], "beat")
        for beat in self._beats.values():
            for objective_id in beat["objective_ids"]:
                self._require(self._objectives, objective_id, "objective")
        for quest in self._quests.values():
            for objective_id in quest["objective_ids"]:
                self._require(self._objectives, objective_id, "objective")
        for objective in self._objectives.values():
            for transition in (objective["completion"], objective["failure"]):
                if transition is None:
                    continue
                for reward_id in transition["effects"]["reward_ids"]:
                    self._require(self._rewards, reward_id, "reward")
                for consequence_id in transition["effects"]["consequence_ids"]:
                    self._require(self._consequences, consequence_id, "consequence")

    def _validate_record_consistency(self) -> None:
        for quest_id in self.record["active_quest_ids"]:
            # A save can contain active quests from another chapter package.
            # Preserve those canonical IDs; this projection only validates
            # entities it owns.
            if quest_id in self._quests:
                self.quest_state(quest_id)
        for objective_id in self._objectives:
            self.objective_state(objective_id)
        for quest_id in self._quests:
            self.quest_state(quest_id)

    @staticmethod
    def _require(index: Mapping[str, Mapping[str, Any]], key: str, kind: str) -> Mapping[str, Any]:
        try:
            return index[key]
        except KeyError as exc:
            raise ProgressionError(f"unknown {kind} id: {key}") from exc


def _index(items: list[Mapping[str, Any]], key: str) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for item in items:
        value = item.get(key)
        if not isinstance(value, str) or not value:
            raise ProgressionError(f"missing {key}")
        if value in result:
            raise ProgressionError(f"duplicate {key}: {value}")
        result[value] = item
    return result


def _normalise_record(record: Mapping[str, Any] | None) -> dict[str, Any]:
    source = fresh_record() if record is None else dict(record)
    flags = source.get("flags", {})
    if not isinstance(flags, Mapping) or any(not isinstance(value, bool) for value in flags.values()):
        raise ProgressionError("record flags must be a string-to-bool mapping")
    result = {
        "flags": dict(flags),
        "active_quest_ids": _string_list(source.get("active_quest_ids", []), "active_quest_ids"),
        "consumed_intent_ids": _string_list(
            source.get("consumed_intent_ids", []), "consumed_intent_ids"
        ),
        "consumed_reward_ids": _string_list(
            source.get("consumed_reward_ids", []), "consumed_reward_ids"
        ),
        "script_checkpoint": source.get("script_checkpoint"),
    }
    if result["script_checkpoint"] is not None and not isinstance(result["script_checkpoint"], str):
        raise ProgressionError("script_checkpoint must be a string or null")
    for field in ("active_quest_ids", "consumed_intent_ids", "consumed_reward_ids"):
        if len(result[field]) != len(set(result[field])):
            raise ProgressionError(f"record field contains duplicate IDs: {field}")
    return result


def _string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ProgressionError(f"{field} must be a list of non-empty strings")
    return list(value)
