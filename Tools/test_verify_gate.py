#!/usr/bin/env python3
"""Offline contract tests for the verify gate and the workstation handshake.

Run:  python Tools/test_verify_gate.py

The verify gate is the interlock that stops a recursive loop from closing cards on
an agent's own say-so, so its refusals are the product. Most of these tests assert
that something is REFUSED. A loosened check here is how the gate stops working.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import verify_gate  # noqa: E402
import workstation_status  # noqa: E402

REAL_ARTIFACT = os.path.join(HERE, "verify_gate.py")


class TestVerifyGateRefusals(unittest.TestCase):
    """Every one of these must be REFUSED. That is the whole point."""

    def setUp(self):
        self._saved = verify_gate.AUDIT
        self._tmp = tempfile.mkdtemp(prefix="melodia_vgate_")
        verify_gate.AUDIT = self._tmp

    def tearDown(self):
        verify_gate.AUDIT = self._saved
        shutil.rmtree(self._tmp, ignore_errors=True)

    def record(self, **kw):
        args = dict(card="c1", verifier="verifier-lane", producer="producer-lane",
                    artifacts=["Tools/verify_gate.py"], measured="35 tests, exit 0",
                    result="pass")
        args.update(kw)
        return verify_gate.record(args["card"], args["verifier"], args["producer"],
                                 args["artifacts"], args["measured"], args["result"],
                                 args.get("uncertainty", ""))

    def test_producer_may_not_verify_its_own_work(self):
        code, detail = self.record(verifier="same-lane", producer="same-lane")
        self.assertEqual(verify_gate.EXIT_REFUSED, code)
        self.assertIn("no_self_certification", detail)

    def test_receipt_without_an_artifact_is_refused(self):
        code, detail = self.record(artifacts=[])
        self.assertEqual(verify_gate.EXIT_REFUSED, code)
        self.assertIn("at least one artifact", detail)

    def test_receipt_naming_a_missing_artifact_is_refused(self):
        code, detail = self.record(artifacts=["Docs/does-not-exist.md"])
        self.assertEqual(verify_gate.EXIT_REFUSED, code)
        self.assertIn("not on disk", detail)

    def test_uncertain_requires_stating_the_uncertainty(self):
        code, detail = self.record(result="uncertain", uncertainty="")
        self.assertEqual(verify_gate.EXIT_REFUSED, code)

    def test_bad_result_value_is_refused(self):
        code, _ = self.record(result="probably-fine")
        self.assertEqual(verify_gate.EXIT_REFUSED, code)

    def test_close_refuses_when_there_is_no_receipt(self):
        code, reasons = verify_gate.check("never-recorded")
        self.assertEqual(verify_gate.EXIT_NO_RECEIPT, code)
        self.assertIn("self-report", reasons[0])

    def test_sweep_flags_a_receipt_whose_artifact_vanished(self):
        # A receipt that once named a real artifact, where the artifact is now gone.
        # The gate must not accept "I opened it" for a file that is not there.
        tmp_art = os.path.join(self._tmp, "gone.txt")
        with open(tmp_art, "w") as fh:
            fh.write("x")
        rel = os.path.relpath(tmp_art, ROOT).replace("\\", "/")
        path = verify_gate.receipt_path("c2")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            json.dump({"card": "c2", "verifier": "v", "producer": "p", "result": "pass",
                       "artifacts_opened": [rel], "measured": "looked", "recorded_at": "now"},
                      fh)
        os.remove(tmp_art)
        code, reasons = verify_gate.check("c2")
        self.assertNotEqual(verify_gate.EXIT_PASS, code)
        self.assertTrue(any("no longer on disk" in r for r in reasons), reasons)


class TestVerifyGateAccepts(unittest.TestCase):

    def setUp(self):
        self._saved = verify_gate.AUDIT
        self._tmp = tempfile.mkdtemp(prefix="melodia_vgate_")
        verify_gate.AUDIT = self._tmp

    def tearDown(self):
        verify_gate.AUDIT = self._saved
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_a_real_receipt_closes(self):
        code, _ = verify_gate.record("card-ok", "t1-verifier", "bulk-lane",
                                     ["Tools/verify_gate.py"], "35 tests, exit 0", "pass")
        self.assertEqual(verify_gate.EXIT_PASS, code)
        self.assertEqual(verify_gate.EXIT_PASS, verify_gate.close_card("card-ok"))

    def test_uncertain_is_recordable_and_not_silently_pass(self):
        code, _ = verify_gate.record("card-unsure", "t1-verifier", "bulk-lane",
                                     ["Tools/verify_gate.py"], "read the log",
                                     "uncertain", uncertainty="cook not rerun yet")
        self.assertEqual(verify_gate.EXIT_PASS, code)
        code, reasons = verify_gate.check("card-unsure")
        self.assertNotEqual(verify_gate.EXIT_PASS, code,
                            "uncertainty must not count as done")

    def test_producer_mismatch_is_caught_at_close(self):
        verify_gate.record("card-x", "t1-verifier", "bulk-lane",
                           ["Tools/verify_gate.py"], "measured", "pass")
        code, reasons = verify_gate.check("card-x", producer="some-other-lane")
        self.assertNotEqual(verify_gate.EXIT_PASS, code)
        self.assertTrue(any("does not match the dispatched producer" in r for r in reasons))


class TestLoopSweep(unittest.TestCase):

    def setUp(self):
        self._saved = verify_gate.AUDIT
        self._tmp = tempfile.mkdtemp(prefix="melodia_vgate_")
        verify_gate.AUDIT = self._tmp

    def tearDown(self):
        verify_gate.AUDIT = self._saved
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_sweep_passes_when_every_receipt_is_honest(self):
        verify_gate.record("a", "v1", "p1", ["Tools/verify_gate.py"], "m", "pass")
        verify_gate.record("b", "v2", "p2", ["Tools/verify_gate.py"], "m", "fail")
        code = verify_gate.sweep(verify_gate.AUDIT)
        self.assertEqual(verify_gate.EXIT_REFUSED, code,
                         "a 'fail' receipt must stop the loop")

    def test_sweep_ignores_open_cards_without_receipts(self):
        os.makedirs(os.path.join(verify_gate.AUDIT, "not-started"))
        verify_gate.record("a", "v1", "p1", ["Tools/verify_gate.py"], "m", "pass")
        self.assertEqual(verify_gate.EXIT_PASS, verify_gate.sweep(verify_gate.AUDIT))

    def test_sweep_flags_a_self_certified_receipt(self):
        path = verify_gate.receipt_path("selfcert")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            json.dump({"card": "selfcert", "verifier": "same", "producer": "same",
                       "result": "pass", "artifacts_opened": ["Tools/verify_gate.py"],
                       "measured": "trust me", "recorded_at": "now"}, fh)
        self.assertEqual(verify_gate.EXIT_REFUSED, verify_gate.sweep(verify_gate.AUDIT))


class TestWorkstationMayStartWork(unittest.TestCase):
    """The contract's rule, expressed once so desktop and laptop agree."""

    @staticmethod
    def _status(sync_state, dirty=0, lease_held=False, p4_up=True):
        return {
            "sync": {"sync_state": sync_state},
            "git": {"available": True, "dirty_file_count": dirty},
            "editor_lease": {"held": lease_held, "holder": "other-lane",
                             "stop_sentinels": []},
            "p4": {"available": p4_up},
        }

    def test_synced_and_clean_may_work(self):
        self.assertTrue(workstation_status.may_start_work(self._status("synced"))["ok"])

    def test_diverged_blocks(self):
        gate = workstation_status.may_start_work(self._status("diverged"))
        self.assertFalse(gate["ok"])
        self.assertTrue(any("no automatic pull" in b for b in gate["blockers"]))

    def test_ahead_blocks(self):
        self.assertFalse(workstation_status.may_start_work(self._status("ahead"))["ok"])

    def test_dirty_blocks(self):
        self.assertFalse(workstation_status.may_start_work(self._status("synced", dirty=3))["ok"])

    def test_held_lease_blocks_a_second_writer(self):
        gate = workstation_status.may_start_work(self._status("synced", lease_held=True))
        self.assertFalse(gate["ok"])
        self.assertTrue(any("editor lease HELD" in b for b in gate["blockers"]))

    def test_unreachable_perforce_blocks(self):
        self.assertFalse(workstation_status.may_start_work(self._status("synced", p4_up=False))["ok"])

    def test_never_synced_blocks(self):
        self.assertFalse(workstation_status.may_start_work(self._status(None))["ok"])


class TestWorkstationCollect(unittest.TestCase):

    def test_collect_returns_the_shared_schema(self):
        status = workstation_status.collect()
        for key in ("schema", "machine", "generated_at", "git", "sync", "p4",
                    "editor_lease", "lanes", "local_tier", "may_start_work"):
            self.assertIn(key, status)
        self.assertEqual(workstation_status.SCHEMA, status["schema"])

    def test_status_is_json_serialisable(self):
        # A status file that cannot be written is a status file nobody can read.
        json.dumps(workstation_status.collect())


class TestBOMTolerance(unittest.TestCase):
    """Both status producers on this project are PowerShell, which prefixes a
    UTF-8 BOM. Reading either file with plain utf-8 raises on byte 0 and the tool
    reports 'unreadable' on the one machine whose job is to be believed. This
    bit the tool twice during development, so it is pinned here."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="melodia_bom_")
        self._saved_dir = workstation_status.workstation_dir

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _write_bom(self, name, payload):
        path = os.path.join(self._tmp, name)
        with open(path, "w", encoding="utf-8-sig") as fh:
            json.dump(payload, fh)
        return path

    def test_compare_reads_a_bom_prefixed_laptop_file(self):
        mine = workstation_status.collect()
        path = self._write_bom("NITRO-workstation.json", {
            "machine": "NITRO", "git": {"head": "deadbeef"},
            "sync": {"sync_state": "behind"}, "p4": {"client": "Melodia_ws"},
            "editor_lease": {"held": False}, "local_tier": {"reachable": True},
        })
        rows = workstation_status.compare(mine, path)
        by_fact = {r["fact"]: r for r in rows}
        self.assertFalse(by_fact["git.head"]["agrees"],
                         "a different HEAD must be reported as a disagreement")
        self.assertTrue(by_fact["git.head"]["must_match"])
        self.assertFalse(by_fact["p4.client"]["must_match"],
                         "client name is informational, not a must-match fact")

    def test_sync_state_reads_a_bom_prefixed_report(self):
        self._write_bom("FROMAGE-sync-report.json", {
            "generated_at": "2026-10-02T00:00:00", "sync_state": "synced",
            "recommended_action": "work may begin", "lfs": {"ok": True},
        })
        real = workstation_status.workstation_dir
        workstation_status.workstation_dir = lambda: self._tmp
        try:
            state = workstation_status.sync_state()
        finally:
            workstation_status.workstation_dir = real
        self.assertEqual("synced", state["sync_state"])
        self.assertNotEqual("unreadable", state["sync_state"])


if __name__ == "__main__":
    unittest.main(verbosity=2)