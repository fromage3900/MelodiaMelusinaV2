// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 2 — v0.17.0).
//
// FConditionalGateIndexer — regex sweep over `.cpp` / `.h` / `.Build.cs` files
// under the project tree, surfacing `#if WITH_*` and `bHas*` conditional gates.
// Output to `reflect_conditional_gates`. Plain C++ worker. Idempotent: wipes +
// rewrites the table each Run().
//
// Phase 2 code-quality non-negotiable item 4: FRegexPattern instances are
// constructed ONCE at class-member scope, never per-file. The matcher is
// constructed per-line (matcher binds to a specific input), but the pattern
// is reused. This matters — Monolith + project + plugins sweep is ~thousands
// of files; per-file pattern construction would be wasteful.

#pragma once

#include "CoreMinimal.h"
#include "Containers/Array.h"
#include "Internationalization/Regex.h"

class FSQLiteDatabase;

/** One detected gate row. Internal buffer between scan and write. */
struct FConditionalGateRow
{
	FString SourcePath;     // project-relative, forward-slashed
	int32   SourceLine = 0; // 1-based
	FString MacroName;      // e.g. "WITH_GBA"
	FString GateKind;       // "cpp_if" | "build_cs_probe"
	FString ContextSnippet; // the matched line text, trimmed
};

class MONOLITHREFLECTIONINTEL_API FConditionalGateIndexer
{
public:
	FConditionalGateIndexer();

	/**
	 * Walk `ScanRoots` for `.cpp` / `.h` / `.Build.cs` files, scan for gate
	 * patterns, write rows to `reflect_conditional_gates`.
	 *
	 * @param DB         Open writable handle. Caller has enforced
	 *                   `PRAGMA journal_mode=DELETE`.
	 * @param ScanRoots  Absolute or project-relative directories.
	 * @param OutStatus  One-line summary.
	 */
	bool Run(FSQLiteDatabase& DB, const TArray<FString>& ScanRoots, FString& OutStatus);

private:
	bool EnsureSchema(FSQLiteDatabase& DB);

	void ScanFile(const FString& AbsPath, const FString& ProjectRoot,
		TArray<FConditionalGateRow>& OutRows);

	bool WriteRows(FSQLiteDatabase& DB, const TArray<FConditionalGateRow>& Rows);

	// Phase 2 code-quality item 4 — hoist FRegexPattern out of per-file loops.
	// These are members so they exist for the lifetime of the indexer instance
	// (Run() is the only public entry, scoped one call).
	FRegexPattern IfWithPattern;       // matches `#if WITH_<MACRO>` or `#ifdef WITH_<MACRO>`
	FRegexPattern BuildCsProbePattern; // matches `bHas<Word>` Build.cs probe identifiers
};
