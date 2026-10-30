#!/usr/bin/env python3
"""Unit/contract tests for agent-lane local production authority.

These tests use fixtures and mocks. They do NOT establish real workstation
safety for Windows, Unreal, Houdini, or Perforce. Owner-local -DryRun and
machine inspection remain required before trusting a land path.

Run:
  python Tools/test_agent_lane_local_authority.py
  python -m unittest Tools.test_agent_lane_local_authority -q
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from agent_lane_local_authority import (  # noqa: E402
    LocalAuthoritySnapshot,
    evaluate_local_authority,
    evaluate_missing_lane_target,
    evaluate_reuse,
    main as authority_main,
    processes_indicate_houdini,
    processes_indicate_unreal,
)

ROOT = HERE.parent


def _ok_snapshot(**overrides) -> dict:
    base = {
        "owner_reviewed_local_state": True,
        "uproject_present": True,
        "unreal_running": False,
        "houdini_running": False,
        "primary_git_porcelain": [],
        "lane_git_porcelain": [],
        "primary_ignored_porcelain": [],
        "lane_ignored_porcelain": [],
        "p4_available": True,
        "p4_info_ok": True,
        "p4_info_lines": ["User name: owner", "Server address: perforce:1666"],
        "p4_opened_code": 0,
        "p4_opened_lines": ["File(s) not opened on this client."],
        "git_status_failed": False,
        "p4_info_failed": False,
        "p4_opened_failed": False,
    }
    base.update(overrides)
    return base


class ReuseGuardTests(unittest.TestCase):
    def test_existing_lane_unique_commits_preserved_no_reset(self) -> None:
        # Unique commits already pinned: ref == HEAD. Reuse must preserve, never reset.
        decision = evaluate_reuse(
            ref_exists=True,
            ref_sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            head_sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            lane_ref="refs/agents/recovery",
        )
        self.assertTrue(decision.ok)
        self.assertEqual(decision.code, "reuse_preserved")
        self.assertFalse(decision.may_reset_ref)

    def test_unexpected_head_fails_closed(self) -> None:
        decision = evaluate_reuse(
            ref_exists=True,
            ref_sha="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            head_sha="cccccccccccccccccccccccccccccccccccccccc",
            lane_ref="refs/agents/recovery",
        )
        self.assertFalse(decision.ok)
        self.assertEqual(decision.code, "reuse_ref_head_mismatch")
        self.assertFalse(decision.may_reset_ref)
        self.assertIn("SAFE STOP", decision.message)

    def test_missing_ref_fails_closed(self) -> None:
        decision = evaluate_reuse(
            ref_exists=False,
            ref_sha=None,
            head_sha="dddddddddddddddddddddddddddddddddddddddd",
        )
        self.assertFalse(decision.ok)
        self.assertEqual(decision.code, "reuse_ref_missing")
        self.assertFalse(decision.may_reset_ref)


class LocalAuthorityTests(unittest.TestCase):
    def test_missing_owner_approval(self) -> None:
        decision = evaluate_local_authority(_ok_snapshot(owner_reviewed_local_state=False))
        self.assertFalse(decision.ok)
        self.assertEqual(decision.code, "owner_review_missing")

    def test_missing_local_production_workspace(self) -> None:
        decision = evaluate_local_authority(_ok_snapshot(uproject_present=False))
        self.assertFalse(decision.ok)
        self.assertEqual(decision.code, "uproject_missing")
        self.assertIn("UNKNOWN", decision.message)

    def test_pending_perforce_changelists(self) -> None:
        decision = evaluate_local_authority(
            _ok_snapshot(
                p4_opened_code=0,
                p4_opened_lines=["//depot/Content/Foo.uasset#3 - edit default change (binary)"],
            )
        )
        self.assertFalse(decision.ok)
        self.assertEqual(decision.code, "p4_pending_opened")

    def test_uncommitted_unreal_tracked_dirt(self) -> None:
        decision = evaluate_local_authority(
            _ok_snapshot(primary_git_porcelain=[" M Source/BS_GodFile/Foo.cpp"])
        )
        self.assertFalse(decision.ok)
        self.assertEqual(decision.code, "primary_dirty")

    def test_ignored_unreal_or_houdini_assets(self) -> None:
        decision = evaluate_local_authority(
            _ok_snapshot(
                primary_ignored_porcelain=["!! Content/Melodia/Maps/Secret.umap"],
            )
        )
        self.assertFalse(decision.ok)
        self.assertEqual(decision.code, "ignored_production_dirt")
        self.assertIn("UNKNOWN/DIRTY", decision.message)

        hip = evaluate_local_authority(
            _ok_snapshot(lane_ignored_porcelain=["!! Exports/houdini/scene.hip"])
        )
        self.assertFalse(hip.ok)
        self.assertEqual(hip.code, "ignored_production_dirt")

    def test_failed_git_status(self) -> None:
        decision = evaluate_local_authority(_ok_snapshot(git_status_failed=True))
        self.assertFalse(decision.ok)
        self.assertEqual(decision.code, "git_status_failed")
        self.assertIn("UNKNOWN", decision.message)

    def test_failed_perforce_info(self) -> None:
        decision = evaluate_local_authority(
            _ok_snapshot(p4_info_ok=False, p4_info_failed=True, p4_info_lines=["Connect failed"])
        )
        self.assertFalse(decision.ok)
        self.assertEqual(decision.code, "p4_info_failed")

    def test_failed_perforce_opened_command(self) -> None:
        decision = evaluate_local_authority(
            _ok_snapshot(
                p4_opened_failed=True,
                p4_opened_code=1,
                p4_opened_lines=["Client 'cloud' unknown"],
            )
        )
        self.assertFalse(decision.ok)
        self.assertEqual(decision.code, "p4_opened_failed")

    def test_p4_unavailable_is_unknown(self) -> None:
        decision = evaluate_local_authority(_ok_snapshot(p4_available=False))
        self.assertFalse(decision.ok)
        self.assertEqual(decision.code, "p4_unavailable")
        self.assertIn("UNKNOWN", decision.message)

    def test_unreal_or_houdini_running(self) -> None:
        unreal = evaluate_local_authority(_ok_snapshot(unreal_running=True))
        self.assertFalse(unreal.ok)
        self.assertEqual(unreal.code, "unreal_running")
        houdini = evaluate_local_authority(_ok_snapshot(houdini_running=True))
        self.assertFalse(houdini.ok)
        self.assertEqual(houdini.code, "houdini_running")

    def test_clean_attested_snapshot_passes(self) -> None:
        decision = evaluate_local_authority(_ok_snapshot())
        self.assertTrue(decision.ok)
        self.assertEqual(decision.code, "local_gate_passed")

    def test_empty_opened_with_nonzero_exit_still_clean(self) -> None:
        # Perforce often prints "File(s) not opened" with a nonzero exit.
        decision = evaluate_local_authority(
            _ok_snapshot(
                p4_opened_code=1,
                p4_opened_lines=["File(s) not opened on this client."],
            )
        )
        self.assertTrue(decision.ok)

    def test_snapshot_dataclass_roundtrip(self) -> None:
        snap = LocalAuthoritySnapshot.from_mapping(_ok_snapshot())
        decision = evaluate_local_authority(snap)
        self.assertTrue(decision.ok)


class MissingTargetPolicyTests(unittest.TestCase):
    def test_named_lane_missing_worktree_fails_closed(self) -> None:
        decision = evaluate_missing_lane_target(
            named_lane=True, worktree_exists=False, ref_exists=True
        )
        self.assertFalse(decision.ok)
        self.assertEqual(decision.code, "named_lane_target_missing")

    def test_named_lane_missing_ref_fails_closed(self) -> None:
        decision = evaluate_missing_lane_target(
            named_lane=True, worktree_exists=True, ref_exists=False
        )
        self.assertFalse(decision.ok)
        self.assertEqual(decision.code, "named_lane_target_missing")

    def test_all_mode_missing_is_unknown_not_clean(self) -> None:
        decision = evaluate_missing_lane_target(
            named_lane=False, worktree_exists=False, ref_exists=False
        )
        self.assertFalse(decision.ok)
        self.assertEqual(decision.code, "batch_lane_target_unknown")
        self.assertIn("UNKNOWN", decision.message)
        self.assertIn("not clean", decision.message)


class ProcessNameHelpersTests(unittest.TestCase):
    def test_unreal_and_houdini_name_detection(self) -> None:
        self.assertTrue(processes_indicate_unreal(["UnrealEditor", "chrome"]))
        self.assertTrue(processes_indicate_unreal(["UnrealEditor-Cmd"]))
        self.assertFalse(processes_indicate_unreal(["notepad"]))
        self.assertTrue(processes_indicate_houdini(["houdini", "explorer"]))
        self.assertTrue(processes_indicate_houdini(["hython"]))
        self.assertFalse(processes_indicate_houdini(["blender"]))


class CliAndContractTests(unittest.TestCase):
    def test_cli_evaluate_fail_and_pass(self) -> None:
        bad = authority_main(
            [
                "evaluate",
                "--snapshot-json",
                json.dumps(_ok_snapshot(owner_reviewed_local_state=False)),
            ]
        )
        self.assertEqual(bad, 2)
        good = authority_main(["evaluate", "--snapshot-json", json.dumps(_ok_snapshot())])
        self.assertEqual(good, 0)

    def test_cli_reuse_and_missing_target_exit_codes(self) -> None:
        self.assertEqual(
            authority_main(
                [
                    "reuse",
                    "--ref-exists",
                    "--ref-sha",
                    "a" * 40,
                    "--head-sha",
                    "b" * 40,
                ]
            ),
            2,
        )
        self.assertEqual(
            authority_main(
                [
                    "reuse",
                    "--ref-exists",
                    "--ref-sha",
                    "a" * 40,
                    "--head-sha",
                    "a" * 40,
                ]
            ),
            0,
        )
        self.assertEqual(
            authority_main(["missing-target", "--named-lane"]),
            2,
        )
        self.assertEqual(authority_main(["missing-target"]), 3)

    def test_cli_evaluate_from_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "snap.json"
            path.write_text(json.dumps(_ok_snapshot()), encoding="utf-8")
            self.assertEqual(authority_main(["evaluate", "--snapshot-file", str(path)]), 0)

    def test_powershell_scripts_contain_required_safety_markers(self) -> None:
        new_lane = (ROOT / "deploy/new_agent_lane.ps1").read_text(encoding="utf-8-sig")
        land = (ROOT / "deploy/land_agent_lane.ps1").read_text(encoding="utf-8-sig")

        # Reuse must never silently update-ref the existing lane to base.
        reuse_block_start = new_lane.index("if ($ReusingExistingLane)")
        reuse_block = new_lane[reuse_block_start:]
        # First reuse branch (before the else that creates a new lane) must not update-ref.
        first_reuse = reuse_block.split("} else {", 1)[0]
        self.assertNotIn("update-ref", first_reuse)
        self.assertIn("agent_lane_local_authority.py", new_lane)
        self.assertIn("SAFE STOP", new_lane)
        self.assertIn("owner approval", new_lane.lower())

        for needle in (
            "OwnerReviewedLocalState",
            "OwnerApprovedBranchDeletion",
            "OwnerApprovedPrimarySync",
            "agent_lane_local_authority.py",
            "preserving remote landing branch",
            "preserve by default",
            "houdini",
            "--ignored=matching",
            "missing-target",
            "--named-lane",
            "UNKNOWN",
        ):
            self.assertIn(needle, land, f"missing marker in land_agent_lane.ps1: {needle}")

        # Destructive delete/FF remain opt-in.
        self.assertIn("if ($OwnerApprovedBranchDeletion", land)
        self.assertIn("if ($OwnerApprovedPrimarySync)", land)


if __name__ == "__main__":
    unittest.main(verbosity=2)
