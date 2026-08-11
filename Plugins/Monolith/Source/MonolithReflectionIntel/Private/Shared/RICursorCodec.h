// SPDX-License-Identifier: MIT
//
// RICursorCodec — module-internal shared pagination-cursor codec for the
// MonolithReflectionIntel query adapters.
//
// WHY THIS EXISTS: Six query adapters (Audit / CppReflect / Decision / Network /
// Risk / SourceAudit) each carried a byte-identical copy of this codec inside a
// file-level anonymous `namespace { }`. Under UE's adaptive unity build every
// `.cpp` in a module concatenates into one translation unit, so those six
// identical anon-namespace `EncodeCursor` / `DecodeCursor` / `InvalidCursorError`
// definitions (plus the duplicated `FAuditCursorState` struct across Audit and
// SourceAudit) collided as C2084 / C2011 on a from-scratch unity build. The
// source comments already flagged the consolidation as "Phase 5+" work; this
// header lands it at the module-internal level (no public API change).
//
// LINKAGE NOTE: the free functions are declared here and defined ONCE in
// RICursorCodec.cpp — they are NOT in an anonymous namespace and are NOT marked
// inline, so there is exactly one external-linkage definition module-wide. This
// avoids trading the old per-file-collision for a new ODR violation.
//
// BEHAVIOUR: byte-identical to the six former copies. Cursor wire format is
// base64(JSON{ "qh": uint32, "p": int32, "tc": int32 }). FRICursorState field
// layout and defaults (CachedTotalEstimate = -1) match the old per-adapter
// F*CursorState structs exactly. Do NOT change the JSON keys, field names, or
// defaults — pagination cursors are emitted to and re-consumed from MCP clients.
//
// FILTER-HASH NOTE: four adapters (Audit / CppReflect / Network / Risk) defined
// an identical `uint32 ComputeFilterHash(std::initializer_list<FString>)` — those
// four collided under unity and ARE consolidated here as RIComputeFilterHash.
// FDecisionQueryAdapter, by contrast, has a DIFFERENT-signature filter hash
// (`(FString, double, FString)`); unifying the two signatures would change
// behaviour, so Decision keeps its own `ComputeFilterHash` file-local. After the
// four-way consolidation it is the only remaining `ComputeFilterHash` in the
// module, so it no longer collides. (SourceAudit never had a filter hash.)

#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h" // FMonolithActionResult (returned by value)

#include <initializer_list>

/**
 * Pagination cursor state shared by all MonolithReflectionIntel query adapters.
 * Field layout is byte-identical to the former per-adapter F*CursorState structs.
 */
struct FRICursorState
{
	uint32 QueryHash = 0;            // GetTypeHash of the filter set — cursor-reuse detector
	int32  Page = 0;                 // 0-indexed page over the result set
	int32  CachedTotalEstimate = -1; // -1 = unknown; >=0 = COUNT(*) captured on page 0
};

/** Serialize a cursor to base64(JSON{qh,p,tc}). */
FString EncodeRICursor(const FRICursorState& S);

/** Parse a base64(JSON{qh,p,tc}) cursor. Returns false (and zeroes Out) on any
 *  malformed / out-of-range input. */
bool DecodeRICursor(const FString& Enc, FRICursorState& Out);

/** Standard INVALID_CURSOR error result with structured error_code payload. */
FMonolithActionResult RIInvalidCursorError(const FString& Reason);

/** Order-sensitive filter-set hash used as the cursor-reuse detector. Mirrors the
 *  four adapters that took a brace-init list of filter strings. */
uint32 RIComputeFilterHash(std::initializer_list<FString> Parts);
