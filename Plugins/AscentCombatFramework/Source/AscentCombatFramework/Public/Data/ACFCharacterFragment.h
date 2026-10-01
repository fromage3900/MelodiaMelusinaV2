// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "ACFCharacterFragment.generated.h"

/**
 * Base class for character fragments used to compose character definitions in ACF.
 * Can be extended in Blueprint to add custom data and apply logic when the character is initialized from a DataAsset.
 */
UCLASS(Abstract, Blueprintable, EditInlineNew, DefaultToInstanced)
class ASCENTCOMBATFRAMEWORK_API UACFCharacterFragment : public UObject
{
	GENERATED_BODY()

public:
	UACFCharacterFragment() {}

	/** Called by the Character Initializer when applying this fragment to the pawn. */
	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	void ApplyFragment(APawn* pawnOwner);
	virtual void ApplyFragment_Implementation(APawn* pawnOwner);
};
