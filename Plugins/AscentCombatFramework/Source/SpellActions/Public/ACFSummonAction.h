// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Actions/ACFActionAbility.h"
#include "CoreMinimal.h"

#include "ACFSummonAction.generated.h"

class AACFCharacter;

/**
 * Ability used to spawn companions during gameplay.
 */
UCLASS()
class SPELLACTIONS_API UACFSummonAction : public UACFActionAbility {
    GENERATED_BODY()

protected:
    // The character class to spawn as a companion
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACF)
    TSubclassOf<class AACFCharacter> CompanionToSummonClass;

    // Maximum number of companions that can be active at once
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACF)
    uint8 MaxCompanionNumb = 1;

    // Radius around the owner where the companions should be spawned
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACF)
    float SpawnRadius = 350.f;

    // Whether the summoned companion should be auto-destroyed after a delay
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACF)
    bool bAutoKillAfterSeconds = true;

    // Time in seconds after which the summoned companion is auto-destroyed (if enabled)
    UPROPERTY(BlueprintReadWrite, meta = (EditCondition = bAutoKillAfterSeconds), EditAnywhere, Category = ACF)
    float AutoKillTime = 30.f;

    virtual bool CanExecuteAction_Implementation(class ACharacter* owner) const override;

    virtual void OnNotablePointReached_Implementation() override;

private:
    TArray<TObjectPtr<AACFCharacter>> Companions;

    UFUNCTION()
    void KillCompanion(class AACFCharacter* comp);

    UFUNCTION()
    void OnCompanionDeath();
    uint8 currentCompIndex = 0;
};
