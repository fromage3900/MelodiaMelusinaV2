// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 1).
//
// Internal-only schema accessors for the decision tables. Lives under Private/
// because no other module needs the raw SQL strings — they exist only so the
// indexer .cpp and any future migration script share one source of truth.

#pragma once

#include "CoreMinimal.h"

namespace MonolithDecisionSchema
{
	const TCHAR* GetCreateRecordsTableSQL();
	const TCHAR* GetCreateSupersedesTableSQL();
	const TCHAR* GetCreateRecordsIndexStatusSQL();
	const TCHAR* GetCreateRecordsIndexPathSQL();
	const TCHAR* GetCreateSupersedesIndexToSQL();
}
