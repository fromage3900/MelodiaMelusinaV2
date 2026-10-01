// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "ACFAITypes.h"
#include "ACFBaseCombatBehaviorDataAsset.generated.h"

/**
 * Base Data Asset describing how this AI should behave in Combat
 */
UCLASS()
class AIFRAMEWORK_API UACFBaseCombatBehaviorDataAsset : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:

	UACFBaseCombatBehaviorDataAsset() {};

	/*Generic conditionals action you can define by creating your own ActionCondition class*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	TArray<FConditions> ActionByCondition;

};
