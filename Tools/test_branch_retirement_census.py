#!/usr/bin/env python3
"""Offline structural checks for the pinned remote branch-retirement census.

This validates the proposed inventory and guarantees the tool can't silently
infer deletion approval from GitHub compare results. It never calls git, GitHub,
PowerShell, UE or Perforce and never edits a file.
"""
from __future__ import annotations

import copy
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "specs/branch_retirement_census_2026-10-10.json"
SHA = re.compile(r"^[0-9a-f]{40}$")
HOLD_PREFIXES = ("backup/", "recovery/", "collab/", "lane/")
CANDIDATE = "ANCESTOR_CANDIDATE_REVIEW"


def check_manifest(obj: dict) -> list[str]:
    problems: list[str] = []
    if obj.get("schema") != "melodia.branch_retirement_census/v2":
        problems.append("schema is not v2")
    if obj.get("repository") != "fromage3900/MelodiaMelusinaV2":
        problems.append("repository mismatch")
    baseline = obj.get("main_sha")
    if not isinstance(baseline, str) or SHA.fullmatch(baseline) is None:
        problems.append("main_sha is not a full hexadecimal SHA")
    if obj.get("destructive_action_performed") is not False:
        problems.append("destructive_action_performed must remain false")
    if obj.get("all_execution_approvals") is not False:
        problems.append("all_execution_approvals must remain false")
    entries = obj.get("entries")
    if not isinstance(entries, list) or not entries:
        return problems + ["entries must be a nonempty list"]
    count = {}
    seen: set[str] = set()
    for index, row in enumerate(entries):
        name = row.get("branch")
        label = f"entry {index}: {name!r}"
        if not isinstance(name, str) or not name or name == "main":
            problems.append(f"{label} invalid branch")
            continue
        if name in seen:
            problems.append(f"{label} duplicate")
        seen.add(name)
        tip = row.get("head_sha")
        if not isinstance(tip, str) or SHA.fullmatch(tip) is None:
            problems.append(f"{label} invalid head_sha")
        kind = row.get("disposition")
        count[kind] = count.get(kind, 0) + 1
        if row.get("execution_approved") is not False:
            problems.append(f"{label} must not carry automatic approval")
        expected_tag = f"archive/branches/{obj.get('generated_date')}/{name}"
        if row.get("archive_tag") != expected_tag:
            problems.append(f"{label} archive tag differs from exact name")
        if name.startswith(HOLD_PREFIXES) and kind == CANDIDATE:
            problems.append(f"{label} provenance/workstation ref cannot be candidate")
        if kind == CANDIDATE:
            if row.get("ahead_by") != 0:
                problems.append(f"{label} candidate must be zero ahead")
            if row.get("open_pr") is not None:
                problems.append(f"{label} open PR cannot be candidate")
            if row.get("verified_main_sha") != baseline:
                problems.append(f"{label} candidate verification base mismatch")
            if row.get("behind_by") is None:
                problems.append(f"{label} missing compare result")
        else:
            if row.get("ahead_by") == 0 and row.get("verified_main_sha") == baseline:
                problems.append(f"{label} reviewed ancestor not labelled candidate")
        if kind == "ACTIVE_PR_HOLD" and not row.get("open_pr"):
            problems.append(f"{label} open PR hold lacks PR number")
    if obj.get("remote_nonmain_count") != len(entries):
        problems.append("remote_nonmain_count mismatch")
    if obj.get("remote_branch_count_including_main") != len(entries) + 1:
        problems.append("remote branch count mismatch")
    if count != obj.get("counts"):
        problems.append("disposition histogram mismatch")
    return problems


class CensusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(CENSUS.read_text(encoding="utf-8"))

    def test_live_snapshot_valid(self):
        self.assertEqual(check_manifest(self.data), [])

    def test_exact_batch_count(self):
        candidates = [r for r in self.data["entries"] if r["disposition"] == CANDIDATE]
        self.assertEqual(len(candidates), 11)

    def test_no_automatic_approvals(self):
        self.assertFalse(any(r["execution_approved"] for r in self.data["entries"]))

    def test_open_pr_hold(self):
        pr_numbers = {r["open_pr"] for r in self.data["entries"] if r["disposition"] == "ACTIVE_PR_HOLD"}
        self.assertEqual(pr_numbers, {438, 439, 440})

    def test_tampered_candidate_is_rejected(self):
        changed = copy.deepcopy(self.data)
        row = next(r for r in changed["entries"] if r["disposition"] == CANDIDATE)
        row["ahead_by"] = 1
        self.assertTrue(check_manifest(changed))

    def test_tampered_approval_is_rejected(self):
        changed = copy.deepcopy(self.data)
        changed["entries"][0]["execution_approved"] = True
        self.assertTrue(check_manifest(changed))

    def test_tampered_archive_ref_is_rejected(self):
        changed = copy.deepcopy(self.data)
        changed["entries"][0]["archive_tag"] = "archive/branches/mismatch"
        self.assertTrue(check_manifest(changed))


if __name__ == "__main__":
    unittest.main()
