// SPDX-License-Identifier: MIT
//
// MonolithRIMetaTable — indexer-code-version stamping for the RI reflect_* tables.
//
// PROBLEM (handover doc item #1): When the RI indexer code itself changes (parser
// logic / schema layout), the SQLite `reflect_*` tables silently serve STALE data
// because:
//   - the lazy bootstrap in each adapter's `GetRawDB()` only fires when a table
//     is ABSENT (presence is enough — content version is invisible),
//   - `OnReloadComplete` only fires for Live Coding (blocked by header changes),
//   - `source.trigger_(project_)reindex` rebuilds the source-symbol tables, NOT
//     the RI reflect_* tables.
//
// SOLUTION: stamp a per-subsystem `code_version` integer into a single-row-per-
// subsystem `monolith_ri_meta` table. On adapter lazy-bootstrap, if
// `ReadStoredVersion(...) != GetIndexerCodeVersion(...)`, force-rebuild that
// subsystem's tables and re-stamp the new version.
//
// To bump after a parser/schema change: increment the integer literal returned by
// `GetIndexerCodeVersion()` for the affected subsystem. Next adapter call (or
// next reflect.rebuild_reflection_index) auto-detects + force-rebuilds.

#pragma once

#include "CoreMinimal.h"

class FSQLiteDatabase;

namespace MonolithRIMeta
{
	/**
	 * Compile-time indexer-code-version constant per RI subsystem. Increment when
	 * you change the parser logic, schema, or row shape — the version mismatch
	 * triggers an auto-rebuild on the next adapter call.
	 *
	 * Subsystem keys (case-sensitive): "cppreflect" / "network" / "risk" /
	 * "decision". Unknown subsystem returns 0 (treated as "no stamp expected").
	 */
	int32 GetIndexerCodeVersion(const FString& Subsystem);

	/**
	 * Idempotent CREATE TABLE for `monolith_ri_meta`. Returns true on success.
	 * Caller must already hold the shared DB lock for the whole borrow.
	 */
	bool EnsureMetaTable(FSQLiteDatabase& DB);

	/**
	 * Read the stamped `code_version` for `Subsystem`. Returns true and sets
	 * `OutVersion` on a row hit; returns false (and leaves `OutVersion`
	 * untouched) when the row is absent OR the SELECT fails. Treat false as
	 * "stale / never-stamped → rebuild".
	 */
	bool ReadStoredVersion(FSQLiteDatabase& DB, const FString& Subsystem, int32& OutVersion);

	/**
	 * UPSERT a `(Subsystem, Version, stamped_at=now)` row. Returns true on
	 * success. Call once per successful Run() of the corresponding indexer.
	 * EnsureMetaTable is invoked internally — idempotent.
	 */
	bool WriteStoredVersion(FSQLiteDatabase& DB, const FString& Subsystem, int32 Version);
}
