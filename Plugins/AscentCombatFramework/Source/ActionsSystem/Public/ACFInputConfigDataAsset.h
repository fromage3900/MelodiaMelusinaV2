// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "ACFInputConfigDataAsset.generated.h"


/**
 *
 */
UCLASS()
class ACTIONSSYSTEM_API UACFInputConfigDataAsset : public UPrimaryDataAsset {
    GENERATED_BODY()

public:
    UACFInputConfigDataAsset();

    // Array di binding configurabili nell'editor
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Input Bindings", meta = (TitleProperty = "{Description} - {AbilityTag}"))
    TArray<FACFInputAbilityBinding> InputAbilityBindings;


    void GetBindings(TArray<FACFInputAbilityBinding>& outBindings) {
        outBindings = InputAbilityBindings;
    }
    UFUNCTION(BlueprintCallable, Category = "ACF Input")
    bool GetBindingForAbilityTag(FGameplayTag AbilityTag, FACFInputAbilityBinding& OutBinding) const;

    UFUNCTION(BlueprintCallable, Category = "ACF Input")
    bool GetBindingForInputAction(UInputAction* InputAction, FACFInputAbilityBinding& OutBinding) const;
};
