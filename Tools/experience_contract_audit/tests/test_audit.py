import json
import pathlib
import sys
import unittest


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from Tools.experience_contract_audit.audit import build_report
from Tools.experience_contract_audit.contract import normalized_json, render_markdown


class TestExperienceContractAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = build_report()

    def test_deterministic_model_and_renderers(self):
        second = build_report()
        self.assertEqual(self.report, second)
        self.assertEqual(normalized_json(self.report), normalized_json(second))
        self.assertEqual(render_markdown(self.report), render_markdown(second))
        self.assertEqual(self.report["meta"]["audit_id"], "FIRST_DREAM_EXPERIENCE_CONTRACT_AUDIT_2026-08-24")

    def test_input_inventory_is_hash_based(self):
        self.assertGreaterEqual(len(self.report["inputs_compared"]), 15)
        for source in self.report["inputs_compared"]:
            self.assertTrue(source["exists"], source["path"])
            self.assertEqual(len(source["sha256"]), 64, source["path"])

    def test_exact_three_phase_day(self):
        day = self.report["three_phase_day"]
        self.assertEqual(day["phase_order"], ["MorningPreparation", "Expedition", "EveningReturn"])
        self.assertEqual([phase["phase"] for phase in day["phases"]], day["phase_order"])
        self.assertEqual(day["duration_minutes"]["minimum"], 20)
        self.assertEqual(day["duration_minutes"]["maximum"], 30)
        self.assertIn("Exactly one preparation", day["scarcity_rule"])

    def test_preparation_choices_are_distinct_and_scarce(self):
        choices = self.report["preparation_choices"]
        self.assertEqual([choice["relationship"] for choice in choices], ["Sir", "Priestess"])
        self.assertNotEqual(choices[0]["effect"], choices[1]["effect"])
        self.assertIn("rhythm-grace", choices[0]["effect"])
        self.assertIn("Harmony", choices[1]["effect"])
        for choice in choices:
            self.assertTrue(choice["choice_id"].startswith("NEED:"))
            self.assertTrue(choice["evening_reaction_id"].startswith("NEED:"))

    def test_all_four_outcomes_resume_once(self):
        outcomes = self.report["battle_outcomes"]
        self.assertEqual([row["outcome"] for row in outcomes], ["victory", "defeat", "fled", "unavailable"])
        for row in outcomes:
            path = self.report["state_graph"]["outcome_paths"][row["outcome"]]
            self.assertEqual(path.count("EveningReturn.QuillResumedOnce"), 1, row["outcome"])
            self.assertIn("CanonicalJRPGSaveRequested", path)
        self.assertIn("mutates no JRPG state", outcomes[-1]["runtime_proof"])

    def test_fresh_continue_and_replay_paths(self):
        graph = self.report["state_graph"]
        self.assertEqual(graph["fresh_slot_path"][0], "FreshSlot")
        self.assertEqual(graph["fresh_slot_path"][-1], "DayComplete")
        self.assertEqual(set(graph["continue_paths"]), {
            "MorningPreparation",
            "Expedition.before_phrase",
            "Expedition.after_phrase",
            "Expedition.encounter_pending",
            "EveningReturn.after_outcome",
            "DayComplete",
        })
        self.assertEqual(set(graph["continue_outcome_paths"]), {"victory", "defeat", "fled", "unavailable"})
        for outcome, path in graph["continue_outcome_paths"].items():
            self.assertIn(f"RestoreTypedOutcome.{outcome}", path)
            self.assertIn("DoNotDuplicateRewardOrIntent", path)
        self.assertIn("Return AlreadyApplied", graph["replay_path"])
        self.assertIn("Do not add command ID", graph["atomic_failure_path"])

    def test_exactly_once_matrix_is_unique_and_failure_safe(self):
        matrix = self.report["exactly_once_matrix"]
        analysis_ids = [row["analysis_id"] for row in matrix]
        command_ids = [row["command_id"] for row in matrix]
        self.assertEqual(len(analysis_ids), len(set(analysis_ids)))
        self.assertEqual(len(command_ids), len(set(command_ids)))
        required = {
            "preparation.sir", "preparation.priestess", "dialogue.advance",
            "wardrobe.equip", "phrase.complete", "capability.unlock.glide",
            "encounter.request", "battle.outcome.victory", "battle.outcome.defeat",
            "battle.outcome.fled", "battle.outcome.unavailable", "quill.resume",
            "evening.reaction", "reward.present", "phase.advance",
            "canonical.save", "canonical.reload", "replay.applied_command",
        }
        self.assertTrue(required.issubset(analysis_ids))
        for row in matrix:
            self.assertTrue(row["exactly_once"])
            self.assertEqual(row["applied_disposition"], "Applied")
            self.assertEqual(row["repeat_disposition"], "AlreadyApplied")
            self.assertEqual(row["failure_disposition"], "Rejected")
            self.assertFalse(row["consume_on_failure"])
            self.assertFalse(row["advance_on_failure"])

    def test_pacing_covers_zero_to_thirty_with_required_fields(self):
        pacing = self.report["pacing_table"]
        self.assertEqual(pacing[0]["start_minute"], 0)
        self.assertEqual(pacing[-1]["end_minute"], 30)
        self.assertEqual({row["phase"] for row in pacing}, {"MorningPreparation", "Expedition", "EveningReturn"})
        for previous, current in zip(pacing, pacing[1:]):
            self.assertEqual(previous["end_minute"], current["start_minute"])
        for row in pacing:
            for key in ("player_verb", "choice", "feedback", "payoff", "failure_recovery", "proof_tier"):
                self.assertIn(key, row)
        self.assertFalse(any(not row["agency_present"] and row["duration_minutes"] > 4 for row in pacing))

    def test_required_heuristics_are_explicit(self):
        heuristics = self.report["heuristics"]
        self.assertFalse(heuristics["more_than_four_minutes_without_agency"]["flagged"])
        self.assertTrue(heuristics["apparently_meaningful_identical_effects"]["flagged"])
        self.assertTrue(heuristics["payoff_delayed_over_six_minutes"]["flagged"])
        self.assertTrue(heuristics["absent_core_pillar"]["flagged"])

    def test_persona_lens_separates_choice_kinds(self):
        persona = self.report["persona_lens"]
        self.assertTrue(persona["expressive_choices"])
        self.assertTrue(persona["consequential_choices"])
        self.assertTrue(persona["score"]["expressive_scored_separately"])
        self.assertTrue(persona["score"]["consequential_scored_separately"])
        self.assertIn("One preparation per day", persona["scarce_activity_slot"])

    def test_infinity_nikki_lens_has_full_outfit_loop_without_parity_claim(self):
        lens = self.report["infinity_nikki_lens"]
        self.assertIn("accessory", lens["acquisition_equip_payoff"])
        self.assertIn("Glide", lens["acquisition_equip_payoff"])
        self.assertIn("route", lens["acquisition_equip_payoff"])
        self.assertFalse(lens["currently_playable"])
        self.assertIn("never as a parity", lens["thesis"])

    def test_content_ids_resolve_or_are_need(self):
        resolution = self.report["id_resolution"]
        self.assertTrue(resolution["every_id_resolves_or_NEED"])
        self.assertGreater(resolution["resolved_count"], 0)
        self.assertGreater(resolution["need_count"], 0)
        for ref in resolution["references"]:
            if ref["resolution"] != "resolved":
                self.assertTrue(ref["value"].startswith("NEED:"), ref)

    def test_proof_tiers_are_not_conflated(self):
        allowed = set(self.report["meta"]["proof_tiers"])
        self.assertEqual(allowed, {"source_built", "offline_proven", "live_proven", "design_intent", "LIVE_EVIDENCE_REQUIRED"})
        for row in self.report["exactly_once_matrix"]:
            self.assertIn(row["proof_tier"], allowed)
        self.assertEqual(self.report["scorecard"]["runtime_status"], "LIVE_EVIDENCE_REQUIRED")
        self.assertIn("COMPLETE_OFFLINE", self.report["scorecard"]["target_contract"])

    def test_source_observations_and_drift(self):
        observations = self.report["source_observations"]
        self.assertTrue(observations["morning_mentions_sir"])
        self.assertTrue(observations["priestess_choices_converge"])
        self.assertTrue(observations["smoke_authors_four_reactions"])
        self.assertTrue(observations["wardrobe_accessory_resonant_form_is_null"])
        drift_ids = {row["id"] for row in self.report["drift_report"]}
        self.assertTrue({"target_day_phase_absent", "wardrobe_resonance_gap", "piano_world_result_gap", "unavailable_terminal_gap", "reward_semantics_unresolved"}.issubset(drift_ids))

    def test_markdown_contains_all_acceptance_sections(self):
        markdown = render_markdown(self.report)
        for heading in (
            "## Three-phase day", "## Fresh, Continue, and replay state contract",
            "## Battle outcome contract", "## Exactly-once matrix",
            "## 0–30 minute pacing", "## Persona lens", "## Infinity Nikki lens",
            "## Drift report", "## Content ID resolution",
            "## Live-only proof still required",
        ):
            self.assertIn(heading, markdown)
        json.loads(normalized_json(self.report))


if __name__ == "__main__":
    unittest.main()
