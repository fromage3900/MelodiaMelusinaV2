// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 1).
//
// DecisionSchema.cpp — CREATE TABLE statements for Phase 1 decision tables.
// Lives in its own TU per plan §6 to keep the indexer .cpp focused on the
// extraction logic. Statement strings exposed via namespace MonolithDecisionSchema.

#include "Decision/DecisionSchema.h"

namespace MonolithDecisionSchema
{
	const TCHAR* GetCreateRecordsTableSQL()
	{
		// Table layout — see SPEC_MonolithReflectionIntel.md for column documentation.
		// `decision_id` is a stable derived key (path + header anchor hash); not the rowid.
		// `INSERT OR REPLACE` is used by the indexer so re-runs are idempotent.
		return TEXT(
			"CREATE TABLE IF NOT EXISTS decision_records ("
			"    decision_id     TEXT PRIMARY KEY,"
			"    title           TEXT NOT NULL,"
			"    status          TEXT NOT NULL DEFAULT 'open',"
			"    source_path     TEXT NOT NULL,"
			"    source_line     INTEGER NOT NULL DEFAULT 0,"
			"    confidence      REAL NOT NULL DEFAULT 0.0,"
			"    rationale       TEXT,"
			"    source_mtime    INTEGER NOT NULL DEFAULT 0"
			");"
		);
	}

	const TCHAR* GetCreateSupersedesTableSQL()
	{
		// Edge table: a SUPERSEDES b. PK guarantees we can re-run the indexer
		// without duplicating edges; INSERT OR IGNORE on the indexer write path.
		// Both columns are decision_id strings (no FK enforcement in SQLite by
		// default, but the column is logically a reference to decision_records).
		return TEXT(
			"CREATE TABLE IF NOT EXISTS decision_supersedes ("
			"    from_decision_id TEXT NOT NULL,"
			"    to_decision_id   TEXT NOT NULL,"
			"    PRIMARY KEY (from_decision_id, to_decision_id)"
			");"
		);
	}

	const TCHAR* GetCreateRecordsIndexStatusSQL()
	{
		return TEXT(
			"CREATE INDEX IF NOT EXISTS idx_decision_records_status "
			"ON decision_records(status);"
		);
	}

	const TCHAR* GetCreateRecordsIndexPathSQL()
	{
		return TEXT(
			"CREATE INDEX IF NOT EXISTS idx_decision_records_source_path "
			"ON decision_records(source_path);"
		);
	}

	const TCHAR* GetCreateSupersedesIndexToSQL()
	{
		return TEXT(
			"CREATE INDEX IF NOT EXISTS idx_decision_supersedes_to "
			"ON decision_supersedes(to_decision_id);"
		);
	}
}
