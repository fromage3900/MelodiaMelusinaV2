// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"

enum class EPCGMetadataTypes : uint8;
struct FEdGraphPinType;

/**
 * Shared mapping between EPCGMetadataTypes and Blueprint pin-type / display-name
 * representations. Used by UK2Node_GetPCGExProperty and UK2Node_SetPCGExProperty
 * to populate their "Change Type" right-click menus and validate type stamping.
 */
namespace PCGExK2NodeTypeHelpers
{
	/**
	 * Build an FEdGraphPinType matching the given EPCGMetadataTypes. Returns false for
	 * EPCGMetadataTypes::Unknown / Count and any future entry without a Blueprint analog.
	 */
	PCGEXPROPERTIESEDITOR_API bool MakePinTypeForMetadataType(EPCGMetadataTypes Type, FEdGraphPinType& OutPinType);

	/** Human-readable name for the right-click "Change Type" menu entries. */
	PCGEXPROPERTIESEDITOR_API FText GetDisplayNameForMetadataType(EPCGMetadataTypes Type);
}
