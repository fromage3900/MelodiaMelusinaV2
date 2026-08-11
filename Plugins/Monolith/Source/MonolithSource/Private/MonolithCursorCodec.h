// SPDX-License-Identifier: MIT
// Survivor E (`source_query("search_source")` cursor pagination) — opaque
// cursor codec. Plan: Plugins/Monolith/Docs/plans/2026-05-27-mcp-llm-ergonomics.md §3.E
//
// The cursor is base64-encoded JSON, opaque to the client. Server-side it
// carries:
//   - QueryHash: GetTypeHash(query+filters), so we can detect cursor reuse
//     across a mismatched query and reject cleanly.
//   - SymbolPage / SourcePage: 0-indexed page indices for the rerun-slice
//     pagination strategy. v1 uses ONE page index pair that walks all scopes
//     simultaneously; per-scope page tracking is deferred (see plan §3.E).
//   - CachedTotalEstimate: -1 means unknown. >=0 means the total COUNT(*)
//     MATCH was computed on page 0 and is being threaded forward so pages 1+
//     don't pay the count cost.
//
// FTS5 rank instability (see plan §8) means keyset cursors are unsound;
// rerun-slice is the chosen strategy.

#pragma once

#include "CoreMinimal.h"
#include "Containers/UnrealString.h"

namespace MonolithCursorCodec
{
	struct FCursorState
	{
		uint32 QueryHash = 0;            // GetTypeHash of (query+filters) — cursor-reuse detector
		int32  SymbolPage = 0;           // 0-indexed page over the symbol FTS table
		int32  SourcePage = 0;           // 0-indexed page over source FTS table
		int32  CachedTotalEstimate = -1; // -1 = unknown; >=0 = cached COUNT(*) MATCH from page 0
	};

	/** Base64-encoded JSON serialization. Opaque to clients. */
	FString Encode(const FCursorState& State);

	/**
	 * Decode an opaque cursor string. Returns false on any failure (bad
	 * base64, malformed JSON, missing fields). Caller is responsible for
	 * comparing OutState.QueryHash to the current request's hash and
	 * issuing an INVALID_CURSOR error on mismatch.
	 *
	 * Never throws, never crashes, never logs spam.
	 */
	bool Decode(const FString& EncodedCursor, FCursorState& OutState);

	/**
	 * Compute the stable hash used in FCursorState::QueryHash. Folds the
	 * query string plus all filter fields together via GetTypeHash + HashCombine.
	 * Cheap; cursor-reuse detection only needs a low-collision-rate signal,
	 * not cryptographic strength.
	 */
	uint32 ComputeQueryHash(
		const FString& Query,
		const FString& Scope,
		const FString& Mode,
		const FString& Module,
		const FString& PathFilter,
		const FString& SymbolKind);
}
