// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 2 — v0.17.0).
//
// RiskSchema.cpp — CREATE TABLE statements for the four Phase 2 tables. Same
// `IF NOT EXISTS` idempotency pattern as DecisionSchema.cpp; statements are
// exposed via namespace MonolithRiskSchema and consumed exclusively from the
// indexer EnsureSchema() entry points. See SPEC_MonolithReflectionIntel.md
// (Phase 2 Schema section) for per-column documentation.

#include "Risk/RiskSchema.h"

namespace MonolithRiskSchema
{
	const TCHAR* GetCreateCoChangePairsTableSQL()
	{
		// Co-change edges are stored UNDIRECTED — we always insert with
		// (file_a < file_b) lexicographically so the (file_a, file_b) PK acts as
		// a set-membership key. Per-repo split via the `repo_tag` column so
		// nested-git mining can report which repo a pair came from. `count` is
		// the number of commits that touched BOTH files together; the indexer
		// recomputes it on each Run() (wipe-and-rewrite) to keep semantics
		// simple.
		return TEXT(
			"CREATE TABLE IF NOT EXISTS git_cochange_pairs ("
			"    repo_tag         TEXT NOT NULL,"
			"    file_a           TEXT NOT NULL,"
			"    file_b           TEXT NOT NULL,"
			"    count            INTEGER NOT NULL DEFAULT 0,"
			"    PRIMARY KEY (repo_tag, file_a, file_b)"
			");"
		);
	}

	const TCHAR* GetCreateFileChurnTableSQL()
	{
		// Per-file commit-touch count, partitioned by repo. `file_path` is
		// project-relative (forward slashes) so a `risk_query` lookup against
		// the same path the user pastes from their editor can join cleanly.
		return TEXT(
			"CREATE TABLE IF NOT EXISTS git_file_churn ("
			"    repo_tag      TEXT NOT NULL,"
			"    file_path     TEXT NOT NULL,"
			"    commit_count  INTEGER NOT NULL DEFAULT 0,"
			"    last_touched  INTEGER NOT NULL DEFAULT 0,"
			"    PRIMARY KEY (repo_tag, file_path)"
			");"
		);
	}

	const TCHAR* GetCreateHotspotScoresTableSQL()
	{
		// Composite score = normalised_churn × normalised_complexity. Both
		// components stored alongside so callers can inspect the breakdown.
		// `complexity_proxy` is the indexer's chosen proxy (line count by
		// default; brace-depth heuristic if Phase 3 ships a richer one).
		return TEXT(
			"CREATE TABLE IF NOT EXISTS risk_hotspot_scores ("
			"    file_path           TEXT PRIMARY KEY,"
			"    churn               INTEGER NOT NULL DEFAULT 0,"
			"    complexity_proxy    INTEGER NOT NULL DEFAULT 0,"
			"    normalised_churn        REAL NOT NULL DEFAULT 0.0,"
			"    normalised_complexity   REAL NOT NULL DEFAULT 0.0,"
			"    score               REAL NOT NULL DEFAULT 0.0"
			");"
		);
	}

	const TCHAR* GetCreateConditionalGatesTableSQL()
	{
		// One row per detected `#if WITH_*` site or `bHas*` Build.cs probe.
		// `macro_name` is the captured identifier (e.g. "WITH_GBA").
		// `gate_kind` is one of: "cpp_if", "build_cs_probe", "uplugin_optional".
		// `source_path` is project-relative forward-slashed.
		// `source_line` is the matched line (1-based).
		return TEXT(
			"CREATE TABLE IF NOT EXISTS reflect_conditional_gates ("
			"    id            INTEGER PRIMARY KEY AUTOINCREMENT,"
			"    source_path   TEXT NOT NULL,"
			"    source_line   INTEGER NOT NULL DEFAULT 0,"
			"    macro_name    TEXT NOT NULL,"
			"    gate_kind     TEXT NOT NULL,"
			"    context_snippet TEXT"
			");"
		);
	}

	const TCHAR* GetCreateCoChangePairsIndexFileASQL()
	{
		return TEXT(
			"CREATE INDEX IF NOT EXISTS idx_git_cochange_pairs_file_a "
			"ON git_cochange_pairs(file_a);"
		);
	}

	const TCHAR* GetCreateCoChangePairsIndexFileBSQL()
	{
		return TEXT(
			"CREATE INDEX IF NOT EXISTS idx_git_cochange_pairs_file_b "
			"ON git_cochange_pairs(file_b);"
		);
	}

	const TCHAR* GetCreateFileChurnIndexPathSQL()
	{
		return TEXT(
			"CREATE INDEX IF NOT EXISTS idx_git_file_churn_path "
			"ON git_file_churn(file_path);"
		);
	}

	const TCHAR* GetCreateHotspotScoresIndexScoreSQL()
	{
		return TEXT(
			"CREATE INDEX IF NOT EXISTS idx_risk_hotspot_scores_score "
			"ON risk_hotspot_scores(score DESC);"
		);
	}

	const TCHAR* GetCreateConditionalGatesIndexMacroSQL()
	{
		return TEXT(
			"CREATE INDEX IF NOT EXISTS idx_reflect_conditional_gates_macro "
			"ON reflect_conditional_gates(macro_name);"
		);
	}
}
