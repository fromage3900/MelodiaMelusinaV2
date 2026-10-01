// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Data/ACFCharacterFragment.h"
#include "Data/ACFBaseCombatBehaviorDataAsset.h"
#include "ACFCombatBehaviourFragment.generated.h"

class UACFCombatBehaviourComponent;

/**
 * Fragment that applies a combat behaviour DataAsset to the character's AI controller.
 * Add this fragment to a UACFCharacterDataAsset's Fragments array and set CombatBehaviour to apply it during init.
 */
UCLASS(Blueprintable, EditInlineNew, DefaultToInstanced)
class AIFRAMEWORK_API UACFCombatBehaviourFragment : public UACFCharacterFragment
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	TObjectPtr<UACFBaseCombatBehaviorDataAsset> CombatBehaviour;

	virtual void ApplyFragment_Implementation(APawn* pawnOwner) override;
};
