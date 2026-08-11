// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"

#include "PCGExEnumSelector.generated.h"

/**
 * Type-safe enum selection: pairs a UEnum* with one of its values (or a bitmask of values).
 *
 * Drop-in replacement for FEnumSelector with two motivating differences:
 *  - Picker/customization is owned by this plugin, so we control the entire detail-panel
 *    flow (no crashes from the engine's ReloadValueOptions on ForceRefresh re-entry).
 *  - Native UEnum and UUserDefinedEnum (blueprint enumerations) are both selectable, with
 *    no special-casing -- UUserDefinedEnum derives from UEnum and is treated uniformly.
 *
 * Layout intentionally mirrors FEnumSelector field-for-field so a struct redirect carries
 * pre-existing serialized data forward without loss.
 */
USTRUCT(BlueprintType)
struct PCGEXPROPERTIES_API FPCGExEnumSelector
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Enum")
	TObjectPtr<UEnum> Class = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Enum")
	int64 Value = 0;

	bool IsValid() const
	{
		return Class != nullptr;
	}

	FText GetDisplayName() const;
	FString GetCultureInvariantDisplayName() const;
};
