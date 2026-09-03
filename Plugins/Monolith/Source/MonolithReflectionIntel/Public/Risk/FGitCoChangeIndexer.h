// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 2 — v0.17.0).
//
// FGitCoChangeIndexer — mines `git log` output from each known nested git repo,
// produces co-change pair counts and per-file churn rows, writes them to
// EngineSource.db. Plain C++ worker (no UObject). Idempotent on the tables:
// each Run() does EnsureSchema → wipe-and-rewrite of git_cochange_pairs +
// git_file_churn for the supplied repo set.
//
// Threading: invoked from the module's lazy-bootstrap path on the game thread.
// The git subprocess runs concurrently; the indexer blocks in a CreateProc +
// ReadPipe poll loop with a settings-driven timeout (Phase 2 §8 gotcha — must
// not hang the editor).
//
// API verifications (per Iron Law 1, re-checked at Phase 2 execution time):
//   - FPlatformProcess::CreateProc / CreatePipe / ReadPipe / ClosePipe /
//     IsProcRunning / GetProcReturnCode — VERIFIED at
//     `Engine/Source/Editor/UnrealEd/Private/Commandlets/DiffAssetRegistriesCommandlet.cpp:1459-1496`
//     (canonical LaunchP4 pattern; Phase 2 mirrors the structure exactly).
//   - FString::ParseIntoArrayLines — VERIFIED at
//     `DiffAssetRegistriesCommandlet.cpp:1494`.
//
// Diversion note: the project's outer working tree is tracked by Diversion, not
// git, and has no `.git` directory. Mining for the project-level tree returns
// no commits and is silently skipped. Phase 2 mines NESTED git repos only
// (Monolith plugin, Resonance sibling, etc.). Diversion `dv_log` mining is a
// Phase 4 work item per plan §2 non-goals.

#pragma once

#include "CoreMinimal.h"
#include "Containers/Map.h"
#include "Containers/Set.h"
#include "Templates/Tuple.h"

class FSQLiteDatabase;

/** Result row buffered between in-memory parse and SQLite write. Internal. */
struct FGitCommitFileTouches
{
	/** 40-char hex commit hash. */
	FString CommitHash;
	/** Author-date in Unix seconds. */
	int64 CommitTimestamp = 0;
	/** Project-relative forward-slashed file paths touched by this commit. */
	TArray<FString> Files;
};

class MONOLITHREFLECTIONINTEL_API FGitCoChangeIndexer
{
public:
	/**
	 * Run a single indexer pass.
	 *
	 * @param DB                  Open writable FSQLiteDatabase. Caller must have
	 *                            already enforced `PRAGMA journal_mode=DELETE`.
	 * @param GitRepoRoots        Absolute or project-relative paths to nested git
	 *                            repos. Each is probed for `.git/`; missing ones
	 *                            are silently skipped (Diversion working tree).
	 * @param MaxCommitWindow     Hard cap on commits scanned per repo (passes
	 *                            `--max-count=N` to `git log`).
	 * @param NoiseFilter         File-path substrings to exclude from co-change
	 *                            tallies (e.g. CHANGELOG.md, *.uplugin). Match
	 *                            is substring containment, case-insensitive.
	 * @param MaxCommitFileCount  Skip commits touching more than N files
	 *                            (release / mass-rename commits dominate
	 *                            co-change weights otherwise — design spec Q6).
	 * @param OutStatus           One-line human-readable summary (counts).
	 * @return true on full success, false on schema or write failure. Per-repo
	 *         git-log failures are logged + counted but do not abort.
	 */
	bool Run(
		FSQLiteDatabase& DB,
		const TArray<FString>& GitRepoRoots,
		int32 MaxCommitWindow,
		const TArray<FString>& NoiseFilter,
		int32 MaxCommitFileCount,
		FString& OutStatus);

private:
	bool EnsureSchema(FSQLiteDatabase& DB);

	/** Spawns `git log` in `RepoRoot`, captures stdout, parses to commit rows. */
	bool RunGitLog(
		const FString& RepoRoot,
		int32 MaxCommits,
		int32 TimeoutSeconds,
		TArray<FGitCommitFileTouches>& OutCommits,
		FString& OutErr);

	/** Parse `git log --name-only --pretty=format:"COMMIT %H %at" -z`-ish output. */
	void ParseGitLog(
		const FString& StdoutText,
		TArray<FGitCommitFileTouches>& OutCommits);

	/** Tally co-change pairs + per-file churn from a parsed commit list. */
	void TallyCoChangePairs(
		const TArray<FGitCommitFileTouches>& Commits,
		const TArray<FString>& NoiseFilter,
		int32 MaxFiles,
		TMap<TPair<FString, FString>, int32>& OutPairs,
		TMap<FString, int32>& OutChurn,
		TMap<FString, int64>& OutLastTouched);

	bool WritePairs(
		FSQLiteDatabase& DB,
		const FString& RepoTag,
		const TMap<TPair<FString, FString>, int32>& Pairs,
		const TMap<FString, int32>& Churn,
		const TMap<FString, int64>& LastTouched);

	/** True if `Path` contains any substring in `NoiseFilter` (case-insensitive). */
	static bool IsNoise(const FString& Path, const TArray<FString>& NoiseFilter);
};
