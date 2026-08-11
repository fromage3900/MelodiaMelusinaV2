// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 1).
//
// FDecisionRecordIndexer — mines decision records from project markdown corpora
// (specs, plans, CHANGELOG, .claude/rules) into the shared EngineSource.db SQLite
// store. Plain C++ worker (no UObject). Idempotent on the table: each Run() does
// EnsureSchema → wipe-and-rewrite of decision_records / decision_supersedes for
// the roots it walks.
//
// Threading: invoked from the source indexer worker thread (sequential). All
// SQLite ops use the same FSQLiteDatabase handle owned by the source subsystem;
// the subsystem's existing serialization (DB is closed during indexer runs and
// reopened on completion) covers cross-thread safety here.

#pragma once

#include "CoreMinimal.h"

class FSQLiteDatabase;

/** One extracted decision row before INSERT. Internal to the indexer. */
struct FDecisionRecordRow
{
	/** Stable id derived from path + header anchor (sha-ish). */
	FString DecisionId;
	/** Decision title — first header line OR explicit `title:` frontmatter. */
	FString Title;
	/** "open", "accepted", "superseded", "deprecated", "draft". */
	FString Status;
	/** Source markdown file (relative to project root). */
	FString SourcePath;
	/** Line number of the matching header (1-based). */
	int32 SourceLine = 0;
	/** Heuristic confidence in [0,1]. */
	float Confidence = 0.0f;
	/** Free-text rationale paragraph if mined; empty otherwise. */
	FString Rationale;
	/** Source-file mtime in UTC ticks (FDateTime::ToUnixTimestamp basis). */
	int64 SourceMtimeUnix = 0;
	/** Decision ids this record explicitly supersedes (resolved to edges in Run). */
	TArray<FString> SupersedesIds;
};

class MONOLITHREFLECTIONINTEL_API FDecisionRecordIndexer
{
public:
	/**
	 * Run a single indexer pass over the supplied markdown roots.
	 *
	 * @param DB             Open, writable FSQLiteDatabase handle. Must NOT be
	 *                       the source-indexer's mid-run database — call only
	 *                       when the subsystem's DB is reopened.
	 * @param MarkdownRoots  Absolute or project-relative directory paths to
	 *                       walk recursively for *.md files.
	 * @param OutStatus      One-line human-readable summary (counts).
	 * @return true on full success, false on schema or write failure. Per-file
	 *         parse errors are logged + counted but do not abort.
	 */
	bool Run(FSQLiteDatabase& DB, const TArray<FString>& MarkdownRoots, FString& OutStatus);

private:
	bool EnsureSchema(FSQLiteDatabase& DB);
	void WalkMarkdownRoot(const FString& Root, TArray<FString>& OutFiles);
	bool ExtractRecordsFromFile(const FString& AbsPath, const FString& ProjectRoot,
		TArray<FDecisionRecordRow>& OutRows);
	bool WriteRecords(FSQLiteDatabase& DB, const TArray<FDecisionRecordRow>& Rows);
	bool ResolveSupersessionEdges(FSQLiteDatabase& DB, const TArray<FDecisionRecordRow>& Rows);

	/** Generate a stable decision id from a path + header anchor. Deterministic. */
	static FString MakeDecisionId(const FString& RelPath, const FString& HeaderAnchor);
	/** Convert path to project-relative form using forward slashes. */
	static FString ToProjectRelative(const FString& AbsPath, const FString& ProjectRoot);
};
