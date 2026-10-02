// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ACFStorageComponent.h"
#include "CoreMinimal.h"

#include "ACFProceduralStorageComponent.generated.h"

/**
 *
 */
UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent))
class CRAFTINGSYSTEM_API UACFProceduralStorageComponent : public UACFStorageComponent {
    GENERATED_BODY()

public:
    /*Call this to fill the storage with the provided generation rules*/
    UFUNCTION(Server, Reliable, WithValidation, BlueprintCallable, Category = ACF)
    void GenerateStorageItems();

    UFUNCTION(BlueprintPure, Category = ACF)
    UACFItemsManagerComponent* GetItemsManager() const;

protected:
    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = ACF)
    TArray<FACFItemGenerationRule> ItemGenerationRules;

private:
    UPROPERTY(SaveGame)
    bool bGenerated = false;
};
