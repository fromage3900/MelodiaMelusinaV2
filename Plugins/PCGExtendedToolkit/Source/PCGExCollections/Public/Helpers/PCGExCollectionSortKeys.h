// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"

struct FPCGExMeshCollectionEntry;
struct FPCGExLevelCollectionEntry;

/**
 * Process-stable lexicographic sort keys for SharedCompact merge entries.
 *
 * Used by UPCGExPCGDataAssetCollection's CompactSharedMesh / CompactSharedLevel to
 * produce a deterministic ordering of merged shared entries -- identical across editor
 * sessions, cooker runs, and machines for identical inputs.
 *
 * Lifted to free functions in a public header so they can be exercised directly from
 * the test plugin (PCGExtendedToolkitTest) without exposing the SharedCompact policy
 * templates.
 */
namespace PCGExSharedCompact
{
	/**
	 * Build a process-stable sort key for a mesh collection entry.
	 *
	 * Contract:
	 *  - Process-stable: same input -> same key, always. Does NOT depend on per-process
	 *    FName comparison indices (FNameEntryId::ToUnstableInt).
	 *  - Fully discriminating: every field MeshContentEquals compares is folded into
	 *    the key, so two distinct entries cannot produce the same key. Descriptor structs
	 *    are digested with Blake3 (256-bit) -- collision probability is ~2^-128.
	 *  - Leading-field stable: StaticMesh path is the leading lexicographic field. Edits
	 *    to non-leading fields keep an entry inside its mesh's sort cluster, so
	 *    regenerated diffs stay minimal under typical content changes.
	 */
	PCGEXCOLLECTIONS_API FString MeshSortKey(const FPCGExMeshCollectionEntry& E);

	/**
	 * Build a process-stable sort key for a level collection entry.
	 *
	 * Level entries have no other discriminating fields beyond the Level soft path,
	 * so the key is just that path's string representation.
	 */
	PCGEXCOLLECTIONS_API FString LevelSortKey(const FPCGExLevelCollectionEntry& E);
}
