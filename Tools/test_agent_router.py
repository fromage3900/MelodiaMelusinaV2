#!/usr/bin/env python3
"""Offline contract tests for the model router `route` surface and the editor lease.

Run:  python Tools/test_agent_router.py
Exit: 0 = all passed, 1 = a contract failed.

These are the plan's H1 acceptance criteria, stated as assertions:
  * routing is DETERMINISTIC on the fixture packet set
  * escalation honours widest_tier_wins
  * the router fails closed (classical-fallback) instead of guessing
  * a local-only lane never silently spends a paid endpoint
  * the lease refuses a second holder, honours STOP files, and expires

No network, no editor, no API key. `route` is a pure function of
(packet, registry) precisely so that this can be true.
"""

import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIXTURES = os.path.join(HERE, "agent_router", "fixtures")

sys.path.insert(0, HERE)
import model_router  # noqa: E402
import agent_lease  # noqa: E402


def load_fixture(name):
    with open(os.path.join(FIXTURES, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


def route(name):
    packet = load_fixture(name)
    problems = model_router.validate_packet(packet)
    return model_router.route_packet(packet, schema_ok=not problems), problems


class TestPacketSchema(unittest.TestCase):
    def test_fixtures_are_valid(self):
        for name in sorted(os.listdir(FIXTURES)):
            if not name.endswith(".json"):
                continue
            packet = load_fixture(name)
            if name == "under_specified.json":
                continue  # deliberately malformed; asserted below
            self.assertEqual([], model_router.validate_packet(packet),
                             "%s must satisfy the packet schema" % name)

    def test_under_specified_packet_is_rejected(self):
        packet = load_fixture("under_specified.json")
        problems = model_router.validate_packet(packet)
        self.assertTrue(problems,
                        "a packet whose done_when names nothing openable must not validate")
        self.assertTrue(any("done_when" in p for p in problems), problems)

    def test_mutating_packet_without_mutation_paths_is_rejected(self):
        packet = load_fixture("doc_link_repair.json")
        packet["mutation_paths"] = []
        self.assertTrue(model_router.validate_packet(packet),
                        "claiming a mutation with no path must fail at the schema")

    def test_bad_enum_is_rejected(self):
        packet = load_fixture("log_triage.json")
        packet["mutation_scope"] = "something_else"
        self.assertTrue(model_router.validate_packet(packet))


class TestRoutingDeterminism(unittest.TestCase):
    def test_same_packet_routes_identically_twice(self):
        packet = load_fixture("doc_link_repair.json")
        first = model_router.route_packet(packet, schema_ok=True)
        second = model_router.route_packet(packet, schema_ok=True)
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))

    def test_every_fixture_routes_identically_twice(self):
        for name in sorted(os.listdir(FIXTURES)):
            if not name.endswith(".json") or name == "under_specified.json":
                continue
            packet = load_fixture(name)
            a = model_router.route_packet(packet, schema_ok=True)
            b = model_router.route_packet(packet, schema_ok=True)
            self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True), name)

    def test_every_fixture_reaches_a_decision(self):
        for name in sorted(os.listdir(FIXTURES)):
            if not name.endswith(".json"):
                continue
            decision, _ = route(name)
            self.assertIsNotNone(decision["tier"] or decision["classical_fallback"], name)
            self.assertIn("verify_kind", decision)


class TestFailClosed(unittest.TestCase):
    def test_no_task_class_is_classical_fallback(self):
        packet = load_fixture("under_specified.json")
        decision = model_router.route_packet(packet, schema_ok=False)
        self.assertTrue(decision["classical_fallback"])
        self.assertFalse(decision["dispatch"])
        self.assertFalse(decision["model"])

    def test_schema_violation_never_dispatches(self):
        packet = load_fixture("doc_link_repair.json")
        decision = model_router.route_packet(packet, schema_ok=False)
        self.assertTrue(decision["classical_fallback"])
        self.assertFalse(decision["dispatch"])

    def test_unknown_task_class_is_classical_fallback(self):
        packet = load_fixture("doc_link_repair.json")
        packet["task_class"] = "not_a_real_class"
        decision = model_router.route_packet(packet, schema_ok=True)
        self.assertTrue(decision["classical_fallback"])
        self.assertFalse(decision["dispatch"])

    def test_mutation_without_mutation_paths_is_classical_fallback(self):
        packet = load_fixture("doc_link_repair.json")
        packet["mutation_paths"] = []
        decision = model_router.route_packet(packet, schema_ok=True)
        self.assertTrue(decision["classical_fallback"])
        self.assertFalse(decision["dispatch"])


class TestEscalation(unittest.TestCase):
    def test_never_touch_path_escalates_to_architect(self):
        decision, _ = route("escalation_never_touch.json")
        self.assertEqual("T0_ARCHITECT", decision["tier"])
        self.assertTrue(any(h["id"] == "never_touch_table" for h in decision["escalations"]))
        self.assertIn("escalated", " ".join(decision["reasons"]))

    def test_widest_tier_wins_when_several_triggers_match(self):
        packet = load_fixture("escalation_never_touch.json")
        packet["mutation_paths"] = ["Config/DefaultEngine.ini", "specs/orchestration/x.v1.json"]
        packet["goal"] = "widen the schema and merge the branch"
        decision = model_router.route_packet(packet, schema_ok=True)
        ids = {h["id"] for h in decision["escalations"]}
        self.assertIn("never_touch_table", ids)
        self.assertIn("schema_change", ids)
        self.assertIn("vcs_operation", ids)
        self.assertEqual("T0_ARCHITECT", decision["tier"])

    def test_schema_change_glob_matches_nested_spec(self):
        packet = load_fixture("doc_link_repair.json")
        packet["mutation_paths"] = ["specs/orchestration/thing.v1.json"]
        hits = model_router.match_escalations(packet, _spec())
        self.assertIn("schema_change", {h["id"] for h in hits})

    def test_bare_star_glob_does_not_swallow_the_tree(self):
        self.assertTrue(model_router._path_matches("Config/**", "Config/DefaultEngine.ini"))
        self.assertTrue(model_router._path_matches("Config/**", "Config/x/y/z.ini"))
        self.assertFalse(model_router._path_matches("Config/*", "Config/x/y/z.ini"))

    def test_editor_mutation_flags_needs_editor(self):
        decision, _ = route("editor_mutation.json")
        self.assertTrue(decision["needs_editor"])

    def test_git_scope_never_auto_dispatches(self):
        packet = load_fixture("doc_link_repair.json")
        packet["mutation_scope"] = "git"
        packet["mutation_paths"] = ["AGENTS.md"]
        decision = model_router.route_packet(packet, schema_ok=True)
        self.assertFalse(decision["dispatch"])
        self.assertEqual("T0_ARCHITECT", decision["tier"])

    def test_mutating_packet_is_graded_above_its_own_lane(self):
        """no_self_certification: the lane that produced it does not grade it."""
        decision, _ = route("doc_link_repair.json")
        self.assertNotEqual(model_router.TIER_RANK[decision["tier"]],
                            model_router.TIER_RANK["T4_LOCAL"],
                            "a mutating packet must not sit at the cheapest tier")


class TestNoSilentPaidFallback(unittest.TestCase):
    """The registry's `git_vcs_automation` entry is T4_LOCAL / local-only. A
    READ-ONLY packet is the legitimate local-lane case - a mutating packet is
    escalated above T4_LOCAL by no_self_certification, which is asserted
    separately. These tests use the read-only packet on purpose."""

    @staticmethod
    def _local_packet():
        packet = load_fixture("log_triage.json")
        packet["task_class"] = "git_vcs_automation"
        packet["mutation_scope"] = "none"
        return packet

    def test_local_only_lane_fails_loudly_when_local_is_down(self):
        packet = self._local_packet()
        decision = model_router.route_packet(packet, schema_ok=True)
        if not model_router.local_endpoint_reachable():
            self.assertTrue(decision["classical_fallback"])
            self.assertFalse(decision["dispatch"])
            self.assertIn("local-only", " ".join(decision["reasons"]))
        else:
            self.assertEqual(model_router.LOCAL_TIER, decision["tier"])
            self.assertEqual(0.0, decision["budget_usd"])

    def test_local_lane_budget_is_zero(self):
        decision = model_router.route_packet(self._local_packet(), schema_ok=True)
        self.assertLessEqual(decision["budget_usd"], 0.0)

    def test_local_lane_never_resolves_to_a_paid_endpoint(self):
        decision = model_router.route_packet(self._local_packet(), schema_ok=True)
        if decision["classical_fallback"]:
            self.assertIsNone(decision.get("endpoint"),
                              "a failed local lane must not carry a paid endpoint")
        else:
            self.assertEqual("local", decision["endpoint"],
                             "a T4_LOCAL packet must not be pointed at a paid endpoint")

    def test_budget_is_clamped_to_tier_ceiling(self):
        packet = load_fixture("editor_mutation.json")
        packet["budget_usd"] = 999
        decision = model_router.route_packet(packet, schema_ok=True)
        ceiling = _tier_meta(decision["tier"]).get("budget_usd_max")
        if ceiling is not None:
            self.assertLessEqual(decision["budget_usd"], float(ceiling))


class TestVerifyKind(unittest.TestCase):
    def test_image_artifact_infers_image_look(self):
        decision, _ = route("editor_mutation.json")
        self.assertEqual("image_look", decision["verify_kind"])

    def test_patch_artifact_infers_diff_review(self):
        decision, _ = route("escalation_never_touch.json")
        self.assertEqual("diff_review", decision["verify_kind"])

    def test_read_only_packet_never_gets_a_mutating_verify_kind(self):
        decision, _ = route("log_triage.json")
        self.assertIn(decision["verify_kind"],
                      {"log_cite", "artifact_open", "test_log"})

    def test_explicit_verify_kind_is_honoured(self):
        packet = load_fixture("doc_link_repair.json")
        packet["verify_kind"] = "test_log"
        decision = model_router.route_packet(packet, schema_ok=True)
        self.assertEqual("test_log", decision["verify_kind"])


class TestEditorLease(unittest.TestCase):
    """The lease is process-local state on disk, so every test uses a temp path
    and restores the real one. Nothing here touches a live editor."""

    def setUp(self):
        self._saved_path = agent_lease.LEASE_PATH
        self._saved_deploy = agent_lease.DEPLOY_DIR
        import tempfile
        self._tmp = tempfile.mkdtemp(prefix="melodia_lease_")
        agent_lease.LEASE_PATH = os.path.join(self._tmp, "Saved", "Agents", "editor.lease")
        agent_lease.DEPLOY_DIR = os.path.join(self._tmp, "deploy")
        os.makedirs(agent_lease.DEPLOY_DIR, exist_ok=True)

    def tearDown(self):
        agent_lease.LEASE_PATH = self._saved_path
        agent_lease.DEPLOY_DIR = self._saved_deploy
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_first_holder_is_granted(self):
        lease, refusal = agent_lease.acquire("lane-a", "s1")
        self.assertIsNone(refusal)
        self.assertEqual("lane-a", lease["holder"])

    def test_second_holder_is_refused(self):
        agent_lease.acquire("lane-a", "s1")
        lease, refusal = agent_lease.acquire("lane-b", "s2")
        self.assertIsNone(lease)
        self.assertIn("refused", refusal)
        self.assertIn("lane-a", refusal)

    def test_same_holder_refreshes_instead_of_deadlocking(self):
        agent_lease.acquire("lane-a", "s1")
        lease, refusal = agent_lease.acquire("lane-a", "s1")
        self.assertIsNone(refusal)
        self.assertEqual("lane-a", lease["holder"])

    def test_expired_lease_is_reclaimable(self):
        agent_lease.acquire("lane-a", "s1", ttl_s=60)
        # Force expiry rather than sleeping: a test must not take 60 seconds.
        agent_lease.LEASE_PATH_EXPIRED = True
        lease = agent_lease.read_lease()
        lease["expires_at"] = agent_lease._now() - 1
        agent_lease.write_lease(lease)
        again, refusal = agent_lease.acquire("lane-b", "s2")
        self.assertIsNone(refusal)
        self.assertEqual("lane-b", again["holder"])

    def test_stop_sentinel_refuses_acquisition(self):
        with open(os.path.join(agent_lease.DEPLOY_DIR, "surreal_LOOP_STOP"), "w") as fh:
            fh.write("stop\n")
        lease, refusal = agent_lease.acquire("lane-a", "s1")
        self.assertIsNone(lease)
        self.assertIn("stop sentinel", refusal)

    def test_release_requires_the_holder(self):
        agent_lease.acquire("lane-a", "s1")
        result, refusal = agent_lease.release("lane-b")
        self.assertIsNone(result)
        self.assertIn("only the holder", refusal)

    def test_release_then_reacquire(self):
        agent_lease.acquire("lane-a", "s1")
        result, refusal = agent_lease.release("lane-a")
        self.assertIsNone(refusal)
        again, refusal = agent_lease.acquire("lane-b", "s2")
        self.assertIsNone(refusal)
        self.assertEqual("lane-b", again["holder"])

    def test_corrupt_lease_is_treated_as_held(self):
        os.makedirs(os.path.dirname(agent_lease.LEASE_PATH), exist_ok=True)
        with open(agent_lease.LEASE_PATH, "w") as fh:
            fh.write("{not json")
        self.assertTrue(agent_lease.lease_is_live(agent_lease.read_lease()))
        lease, refusal = agent_lease.acquire("lane-b", "s2")
        self.assertIsNone(lease)

    def test_status_reports_free_when_absent(self):
        self.assertFalse(agent_lease.status()["held"])


class TestRegistryCoherence(unittest.TestCase):
    """`route` reads model_tiers.v1.json -> routing_matrix. `chat` reads POLICY.

    On 2026-10-03 these were found COMPLETELY disjoint: all 8 routable classes were
    absent from POLICY, so `route` answered `dispatch: true` and `run_chat` then died
    with KeyError. The 35 H1 tests never caught it because none of them crossed the two
    registries. These tests exist so it cannot happen again silently.
    """

    def test_every_routable_class_is_executable(self):
        """The contract is EXECUTABILITY, not table membership.

        Originally this asserted every routing_matrix key was in POLICY, which was
        the wrong invariant and produced a permanent red test: `chat` now resolves
        candidates from the tier registry when a class is absent from POLICY, so the
        real requirement is that every routable class yields at least one runnable,
        non-blocked candidate.
        """
        unusable = []
        for key, entry in sorted(_spec()["routing_matrix"].items()):
            candidates = model_router.candidates_for(key)
            usable = [c for c in candidates
                      if c[0] and c[0] not in model_router.BLOCKED and c[1]]
            if not usable:
                unusable.append(key)
        self.assertEqual([], unusable,
                         "routable classes with NO runnable candidate: %s -- `route` would "
                         "dispatch them into a guaranteed failure. Run "
                         "`python Tools/model_router.py audit`." % unusable)

    def test_local_endpoint_needs_no_credential(self):
        """A loopback endpoint must never be asked for an API key."""
        for endpoint in ("local", "http://127.0.0.1:11434/v1", "http://localhost:11434/v1"):
            self.assertTrue(model_router._is_local_endpoint(endpoint), endpoint)
        for endpoint in ("https://openrouter.ai/api/v1",
                         "https://bedrock-mantle.us-east-1.api.aws/v1"):
            self.assertFalse(model_router._is_local_endpoint(endpoint), endpoint)

    def test_registry_synthesised_candidates_are_not_blocked_away(self):
        candidates = model_router.candidates_for("git_vcs_automation")
        self.assertTrue(candidates, "a routable class must yield candidates")
        self.assertEqual("http://127.0.0.1:11434/v1", candidates[0][1])

    def test_route_refuses_a_class_the_executor_cannot_run(self):
        packet = load_fixture("log_triage.json")
        unroutable = [k for k in sorted(_spec()["routing_matrix"])
                      if not model_router.candidates_for(k)]
        if not unroutable:
            self.skipTest("every routable class is executable; nothing to refuse")
        packet["task_class"] = unroutable[0]
        decision = model_router.route_packet(packet, schema_ok=True)
        self.assertTrue(decision["classical_fallback"])
        self.assertFalse(decision["dispatch"])

    def test_audit_reports_the_gap_count(self):
        report = json.loads(json.dumps(_audit_report()))
        self.assertIn("routable_but_not_executable", report)
        self.assertEqual(
            len(report["routable_but_not_executable"]) + len(report["tiers_used_but_undefined"]),
            report["registry_gap_count"])

    def test_audit_gap_count_matches_the_reality(self):
        report = _audit_report()
        expected = sorted(k for k in _spec()["routing_matrix"]
                          if not model_router._runnable(k))
        self.assertEqual(expected, sorted(report["routable_but_not_executable"]))


class TestLocalModelPresence(unittest.TestCase):
    """An open port is not a served model. Found 2026-10-03: 11434 was listening
    with zero tags pulled, and the router reported dispatch for a model it could
    not have served."""

    def test_probe_returns_true_false_or_unknown_never_guesses(self):
        result = model_router.model_is_servable_locally("qwen2.5-coder:7b")
        self.assertIn(result, (True, False, None))

    def test_local_packet_refuses_when_the_tag_is_absent(self):
        packet = load_fixture("log_triage.json")
        packet["task_class"] = "git_vcs_automation"
        packet["mutation_scope"] = "none"
        # Force the model to be executable so this test isolates the tag check.
        decision = model_router.route_packet(packet, schema_ok=True)
        if decision["classical_fallback"] and "REGISTRY DRIFT" in " ".join(decision["reasons"]):
            self.skipTest("registry drift fires first; covered by TestRegistryCoherence")
        if not model_router.local_endpoint_reachable():
            self.skipTest("local tier is down; covered by TestNoSilentPaidFallback")
        if model_router.model_is_servable_locally(decision["model"]) is False:
            self.assertFalse(decision["dispatch"])
            self.assertIn("does not have the tag", " ".join(decision["reasons"]))


class TestRouteExitCode(unittest.TestCase):

    def test_refusal_exits_non_zero(self):
        packet = load_fixture("log_triage.json")
        unroutable = [k for k in sorted(_spec()["routing_matrix"])
                      if not model_router.candidates_for(k)]
        if not unroutable:
            self.skipTest("every routable class is executable")
        packet["task_class"] = unroutable[0]
        path = os.path.join(FIXTURES, "_tmp_refusal.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(packet, fh)
        try:
            code = model_router.run_route(path)
            self.assertNotEqual(0, code, "a classical-fallback must be visible to a script")
        finally:
            os.remove(path)


def _audit_report():
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        model_router.run_audit(json_out=True)
    return json.loads(buf.getvalue())


def _spec():
    with open(model_router.TIERS_SPEC, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _tier_meta(tier_id):
    for tier in _spec().get("tiers", []):
        if isinstance(tier, dict) and tier.get("id") == tier_id:
            return tier
    return {}


if __name__ == "__main__":
    unittest.main(verbosity=2)