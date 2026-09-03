// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"

class UPCGExAssetCollection;

/**
 * Self-contained exporter that turns a UPCGExAssetCollection's top-level entries
 * into a Grammit v2 snapshot payload (one atom per entry, one molecule per
 * non-empty Category), base64url-encodes it, and opens the result in the
 * user's default browser at https://pcgex.github.io/grammit/.
 *
 * Editor-only. Lives entirely in PCGExCollectionsEditor.
 */
namespace PCGExGrammitExport
{
	PCGEXCOLLECTIONSEDITOR_API void OpenInGrammit(const UPCGExAssetCollection* InCollection);
}
