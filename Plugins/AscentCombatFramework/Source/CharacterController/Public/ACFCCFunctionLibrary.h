// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "Kismet/BlueprintFunctionLibrary.h"
#include <GameplayTagContainer.h>
#include "ACFCoreTypes.h"
#include "ACFCCFunctionLibrary.generated.h"

UCLASS()
class CHARACTERCONTROLLER_API UACFCCFunctionLibrary : public UBlueprintFunctionLibrary {
    GENERATED_BODY()

public:

    UFUNCTION(BlueprintCallable, Category = ACFLibrary)
    static FGameplayTag GetMovesetTypeTagRoot();

    UFUNCTION(BlueprintCallable, Category = ACFLibrary)
    static FGameplayTag GetAnimationOverlayTagRoot();

    UFUNCTION(BlueprintCallable, Category = ACFLibrary)
    static bool IsValidMovesetTypeTag(FGameplayTag TagToCheck);

    UFUNCTION(BlueprintCallable, Category = ACFLibrary)
    static bool IsValidAnimOverlayTag(FGameplayTag TagToCheck);

	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static EACFDirection GetDirectionFromAngle(float angle);

	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static EACFDirection GetOppositeDirection(EACFDirection direction);

	UFUNCTION(BlueprintCallable, Category = ACFLibrary)
	static EACFDirection GetOppositeDirectionFromAngle(float angle);

};
