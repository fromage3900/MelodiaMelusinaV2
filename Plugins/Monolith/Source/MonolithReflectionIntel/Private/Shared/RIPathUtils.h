// SPDX-License-Identifier: MIT
//
// RIPathUtils — module-internal shared path helpers for the
// MonolithReflectionIntel indexers / adapters.
//
// WHY THIS EXISTS: Three indexers (Risk/FConditionalGateIndexer,
// CppReflect/FUHTArtefactReader, SourceAudit/FModuleDepRealityAdapter) each
// carried a byte-identical copy of `ToProjectRelative` inside a file-level
// anonymous `namespace { }`. Under UE's adaptive unity build every `.cpp` in a
// module concatenates into one translation unit, so those identical
// anon-namespace definitions collided as C2084 (function already has a body) on
// a from-scratch / -DisableUnity build. A prior static sweep missed this because
// adaptive unity only co-located two of the copies in the same blob on the
// build that first surfaced it. This header lands the consolidation at the
// module-internal level (no public API change).
//
// LINKAGE NOTE: the free function is declared here and defined ONCE in
// RIPathUtils.cpp — it is NOT in an anonymous namespace and is NOT marked
// inline, so there is exactly one external-linkage definition module-wide. This
// avoids trading the old per-file collision for a new ODR violation.
//
// BEHAVIOUR: byte-identical to the three former copies. The two Risk/CppReflect
// copies stripped both leading '/' and '\' after the slash-normalisation pass;
// the SourceAudit copy stripped only '/'. Because both first replace '\' with
// '/', no backslash can survive into the strip loop, so all three were
// functionally identical — the consolidated body strips '/' only, matching the
// observable result of every former copy.
//
// NOT INCLUDED: Risk/FHotspotScorer's same-named helper is DIVERGENT — it does
// NOT call FPaths::ConvertRelativePathToFull, operating on the raw input string
// instead. Unifying it would change behaviour, so it stays file-local (renamed
// to FHotspotScorer-unique to clear the unity collision). See that .cpp.

#pragma once

#include "CoreMinimal.h"

/**
 * Convert an absolute (or relative) filesystem path to a forward-slashed,
 * project-relative path. Both inputs are first resolved to full paths via
 * FPaths::ConvertRelativePathToFull and slash-normalised. If the resulting path
 * sits under ProjectRoot (case-insensitive), the root prefix and any leading
 * slash are stripped; otherwise the forward-slashed full path is returned
 * verbatim (e.g. an engine-plugin scan path outside the project root).
 */
FString RIToProjectRelative(const FString& AbsPath, const FString& ProjectRoot);
