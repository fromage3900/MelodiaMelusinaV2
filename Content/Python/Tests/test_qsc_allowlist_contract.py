"""Every gated ID a .qsc emits must exist in the live allowlist asset.

UMelodiaNarrativeSubsystem::IsAllowed rejects any ID absent from
DA_MelodiaIntegrationConfig, silently at runtime. Four P0 scripts shipped on
2026-08-27 against IDs the runtime refuses; this test makes that class of bug
impossible to ship again without a red test.

Gated sets, per MelodiaNarrativeSubsystem.cpp:
    EncounterIds, QuestIds, NarrativeFlagIds, TravelLevelIds,
    DialogueRewardIds, SocialStatIds

NOT gated, and therefore not asserted here: intent ids, checkpoint ids, and
item ids (HandleItemVerb is log-only and performs no allowlist check).

The allowlist lives in a .uasset, so membership is checked by substring against
the asset bytes. That is sound for these ids: they are long and dotted, and a
coincidental match is not credible.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
NARRATIVE_DIR = PROJECT_ROOT / "Content" / "MelodiaIntegration" / "Narrative"
CONFIG_ASSET = (
    PROJECT_ROOT / "Content" / "MelodiaIntegration" / "Config" / "DA_MelodiaIntegrationConfig.uasset"
)

NOTIFY_RE = re.compile(r"^\s*\$ Notify (melodia:[^\s\r\n]+)", re.MULTILINE)


def _gated_ids(notification: str) -> list[tuple[str, str]]:
    """Return (kind, id) pairs that IsAllowed will check for one notification."""
    parts = notification.split(":")
    if len(parts) < 3:
        return []
    verb = parts[1].lower()
    if verb == "battle":
        return [("encounter", parts[2])]
    if verb == "quest":
        return [("quest", parts[2])]
    if verb == "flag":
        return [("flag", parts[2])]
    if verb == "reward":
        return [("reward", parts[2])]
    if verb == "travel":
        return [("travel", parts[2])]
    if verb == "stat":
        # melodia:stat:<IntentId>:<StatId>:<Delta> -- only StatId is gated
        return [("stat", parts[3])] if len(parts) >= 5 else []
    if verb == "questcomplete":
        # melodia:questcomplete:Quest:CompletionFlag:Reward:Intent:Checkpoint
        out = [("quest", parts[2])]
        if len(parts) >= 4:
            out.append(("flag", parts[3]))
        if len(parts) >= 5:
            out.append(("reward", parts[4]))
        return out
    return []


class TestQscAllowlistContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scripts = sorted(NARRATIVE_DIR.glob("*.qsc"))
        cls.config_bytes = CONFIG_ASSET.read_bytes() if CONFIG_ASSET.is_file() else b""

    def test_fixtures_present(self):
        self.assertTrue(self.scripts, f"no .qsc files under {NARRATIVE_DIR}")
        self.assertTrue(CONFIG_ASSET.is_file(), f"allowlist asset missing: {CONFIG_ASSET}")

    def test_every_gated_id_is_allowlisted(self):
        missing: list[str] = []
        for script in self.scripts:
            text = script.read_text(encoding="utf-8")
            for notification in NOTIFY_RE.findall(text):
                for kind, ident in _gated_ids(notification):
                    if not ident:
                        continue
                    if ident.encode("ascii", "ignore") not in self.config_bytes:
                        missing.append(f"{script.name}: {kind} '{ident}'")
        self.assertFalse(
            missing,
            "IDs emitted by .qsc but absent from DA_MelodiaIntegrationConfig "
            "(IsAllowed will reject these at runtime):\n  " + "\n  ".join(sorted(set(missing))),
        )

    def test_flag_prefix_is_singular(self):
        """'flags.' is a typo for 'flag.'; it produces an unmatchable id."""
        offenders = [
            f"{s.name}: {n}"
            for s in self.scripts
            for n in NOTIFY_RE.findall(s.read_text(encoding="utf-8"))
            if ":flags." in n
        ]
        self.assertFalse(offenders, "flag ids must use the 'flag.' prefix:\n  " + "\n  ".join(offenders))

    def test_no_reward_grant_shadows_a_questcomplete_reward(self):
        """A standalone reward grant makes the questcomplete reward leg an
        unobservable no-op, because reward grants are idempotent."""
        offenders: list[str] = []
        for script in self.scripts:
            notifications = NOTIFY_RE.findall(script.read_text(encoding="utf-8"))
            granted = {n.split(":")[2] for n in notifications if n.split(":")[1].lower() == "reward"}
            for n in notifications:
                parts = n.split(":")
                if parts[1].lower() == "questcomplete" and len(parts) >= 5 and parts[4] in granted:
                    offenders.append(f"{script.name}: reward '{parts[4]}' granted separately and via questcomplete")
        self.assertFalse(offenders, "\n  ".join(offenders))


if __name__ == "__main__":
    unittest.main()
