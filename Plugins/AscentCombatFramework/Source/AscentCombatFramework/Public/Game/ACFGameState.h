// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFTypes.h"
#include "CoreMinimal.h"
#include "GameFramework/GameState.h"

#include "ACFGameState.generated.h"

class UACFTeamManagerComponent;
class UACMEffectsDispatcherComponent;
class UACFDifficultyManagerComponent;


/**
 * Custom ACF GameState that holds shared game-wide systems and replicated state.
 * Used for non-authority runtime components accessible by all clients.
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API AACFGameState : public AGameState {
    GENERATED_BODY()

public:
    AACFGameState();

    /**
     * Returns the effects dispatcher component
     * @return Pointer to the effects dispatcher component
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE class UACMEffectsDispatcherComponent* GetEffectsComponent() const { return EffectsComp; }

    /**
     * Returns the team manager component
     * @return Pointer to the team manager component
   */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE class UACFTeamManagerComponent* GetTeamManager() const { return TeamManagerComponent; }  

    /**
     * Returns the difficulty manager component
     * @return Pointer to the difficulty manager component
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE class UACFDifficultyManagerComponent* GetDifficultyManager() const { return DifficultyManagerComponent; }

    /** Effects dispatcher used to handle replicated VFX/SFX */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<UACMEffectsDispatcherComponent> EffectsComp;

    /** Team manager component used to track factions and team behavior */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<UACFTeamManagerComponent> TeamManagerComponent;

    /** Difficulty manager component that holds the current difficulty level (SaveGame + Replicated) */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<UACFDifficultyManagerComponent> DifficultyManagerComponent;
};

