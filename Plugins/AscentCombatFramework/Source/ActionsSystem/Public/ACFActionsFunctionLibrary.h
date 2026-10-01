// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ARSTypes.h"
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include <GameplayEffect.h>
#include <GameplayEffectTypes.h>

#include "ACFActionsFunctionLibrary.generated.h"

class UAbilitySystemComponent;
struct FGameplayAttribute;

/**
 *
 */
UCLASS()
class ACTIONSSYSTEM_API UACFActionsFunctionLibrary : public UBlueprintFunctionLibrary {
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = ACFLibrary)
    static FGameplayTag GetDefaultActionsState();

    UFUNCTION(BlueprintCallable, Category = ACFLibrary)
    static FGameplayTag GetMovesetActionsTagRoot();

    UFUNCTION(BlueprintCallable, Category = ACFLibrary)
    static bool IsValidMovesetActionsTag(FGameplayTag TagToCheck);


};
