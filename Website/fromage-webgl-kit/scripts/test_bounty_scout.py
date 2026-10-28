"""Synthetic, no-network tests for the read-only Treasury bounty scout.

Run:
  python -m unittest discover -s Website/fromage-webgl-kit/scripts -p test_bounty_scout.py -v
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

import bounty_scout as scout

NOW = datetime(2026, 10, 10, tzinfo=timezone.utc)


def issue(**changes):
    data = {
        "html_url": "https://github.com/example/graphics-tools/issues/42",
        "title": "[Bounty $150 USD] Fix Python GLB material export regression",
        "body": "Reproduction steps and acceptance tests are documented. "
                "Reward $150. Details: https://algora.io/bounties/42",
        "state": "open",
        "updated_at": "2026-10-09T12:00:00Z",
        "assignees": [],
        "labels": [{"name": "bounty"}],
    }
    data.update(changes)
    return data


class BountyScoutTests(unittest.TestCase):
    def test_bounded_issue_is_review_not_confirmed_funded(self):
        lead = scout.assess(issue(), now=NOW)
        self.assertIsNotNone(lead)
        self.assertEqual(lead["funding_verification"], "UNVERIFIED")
        self.assertEqual(lead["eligibility_and_ai_rules"], "UNVERIFIED")
        self.assertEqual(lead["claimed_reward"]["amount"], 150.0)
        self.assertEqual(lead["claimed_reward"]["currency"], "USD")
        self.assertEqual(lead["status"], "REVIEW_PAYMENT")
        self.assertEqual(lead["score_out_of_16"], sum(lead["scores"].values()))

    def test_rejects_mirror_fabricated_reward_and_unassigned_money(self):
        self.assertIsNone(scout.assess(issue(
            html_url="https://github.com/fake/bounty-plaza/issues/2"), now=NOW))
        self.assertIsNone(scout.assess(issue(
            title="[Bounty] Claim $999999999999999999999 bounty"), now=NOW))
        self.assertIsNone(scout.assess(issue(
            title="[Bounty] Improve documentation", body="Thanks for contributing."), now=NOW))

    def test_rejects_assigned_closed_stale_and_pull_request(self):
        self.assertIsNone(scout.assess(issue(assignees=[{"login": "someone"}]), now=NOW))
        self.assertIsNone(scout.assess(issue(state="closed"), now=NOW))
        self.assertIsNone(scout.assess(issue(updated_at="2024-01-01T00:00:00Z"), now=NOW))
        self.assertIsNone(scout.assess(issue(pull_request={"url": "https://api.github.com/pulls/42"}), now=NOW))

    def test_rejects_spam_claims(self):
        self.assertIsNone(scout.assess(issue(body="PPPDUD free coins, pay me $100"), now=NOW))
        self.assertIsNone(scout.assess(issue(body="### 原始链接 / Source URL\nRepost of another issue"), now=NOW))

    def test_rejects_explicit_non_cash_tokens(self):
        self.assertIsNone(scout.assess(issue(
            title="[$35 BOUNTY] [Python] Add module docstrings",
            body="**Bounty:** $35 (LT); acceptance tests required."), now=NOW))
        self.assertIsNone(scout.assess(issue(
            title="[Bounty $200] Improve CLI",
            body="Reward: $200 (MRG) in project points."), now=NOW))

    def test_deduplicates_and_limits_to_three(self):
        items = [issue(), issue(), issue(
            html_url="https://github.com/example/graphics-tools/issues/43",
            title="[Bounty $100] Add Python CLI tests"
        ), issue(
            html_url="https://github.com/example/graphics-tools/issues/44",
            title="[Bounty $80] Repair Blender export test"
        ), issue(
            html_url="https://github.com/example/graphics-tools/issues/45",
            title="[Bounty $50] Repair a Python GLB cache test"
        )]
        result = scout.shortlist(items, now=NOW)
        self.assertEqual(result["discovery_count"], 5)
        self.assertEqual(result["candidates_after_gates"], 4)
        self.assertEqual(len(result["shortlist"]), 3)
        self.assertEqual(len({x["issue_url"] for x in result["shortlist"]}), 3)
        self.assertEqual(result["money_received"], 0)

    def test_fixture_mode_writes_no_file_without_output_flag(self):
        with tempfile.TemporaryDirectory() as temporary:
            input_path = Path(temporary) / "issues.json"
            input_path.write_text(json.dumps([issue()]), encoding="utf-8")
            old_files = {p.name for p in Path(temporary).iterdir()}
            # The clock intentionally isn't injected into CLI; valid fixture dates
            # must be within the real execution window for CLI output to be nonempty.
            self.assertEqual(scout.main(["--input", str(input_path)]), 0)
            self.assertEqual(old_files, {p.name for p in Path(temporary).iterdir()})


if __name__ == "__main__":
    unittest.main()
