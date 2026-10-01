// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "AIController.h" 
#include "ACFAIManagerSubsystem.generated.h" 


DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAIAddedToBattle, AAIController*, Controller);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAIRemovedFromBattle, AAIController*, Controller);

/**
 * World subsystem managing all registered AI controllers.
 * Handles registration, battle participation, and pausing/resuming during turn-based battles.
 */
UCLASS()
class AIFRAMEWORK_API UACFAIManagerSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()

public:
    // ==================== REGISTRATION ====================

    /**
     * Registers an AI controller with the subsystem.
     *
     * @param Controller - AI controller to register
     */
    UFUNCTION(BlueprintCallable, Category = "ACF|AI")
    void RegisterAI(AAIController* Controller);

    /**
     * Unregisters an AI controller from the subsystem.
     *
     * @param Controller - AI controller to unregister
     */
    UFUNCTION(BlueprintCallable, Category = "ACF|AI")
    void UnregisterAI(AAIController* Controller);

    /**
     * Returns all registered AI controllers.
     *
     * @return Array of registered controllers
     */
    UFUNCTION(BlueprintPure, Category = "ACF|AI")
    TArray<AAIController*> GetAllRegisteredAIs() const;

    /**
     * Returns the number of registered AI controllers.
     *
     * @return Number of registered AIs
     */
    UFUNCTION(BlueprintPure, Category = "ACF|AI")
    int32 GetRegisteredAICount() const { return RegisteredAIs.Num(); }

    // ==================== BATTLE MANAGEMENT ====================

    /**
     * Adds an AI controller to the battle participants list.
     *
     * @param Controller - AI controller to add
     */
    UFUNCTION(BlueprintCallable, Category = "ACF|AI")
    void AddAIToBattle(AAIController* Controller);

    /**
     * Removes an AI controller from the battle participants list.
     *
     * @param Controller - AI controller to remove
     */
    UFUNCTION(BlueprintCallable, Category = "ACF|AI")
    void RemoveAIFromBattle(AAIController* Controller);

    /**
     * Removes all AI controllers from battle.
     */
    UFUNCTION(BlueprintCallable, Category = "ACF|AI")
    void ClearAllAIsFromBattle();

    /**
     * Returns all AI controllers currently in battle.
     *
     * @return Array of in-battle controllers
     */
    UFUNCTION(BlueprintPure, Category = "ACF|AI")
    TArray<AAIController*> GetInBattleAIs() const;

    /**
     * Checks if an AI controller is currently in battle.
     *
     * @param Controller - AI controller to check
     * @return True if in battle
     */
    UFUNCTION(BlueprintPure, Category = "ACF|AI")
    bool IsAIInBattle(AAIController* Controller) const;

    /**
     * Returns the number of AI controllers in battle.
     *
     * @return Number of in-battle AIs
     */
    UFUNCTION(BlueprintPure, Category = "ACF|AI")
    int32 GetInBattleAICount() const { return InBattleAIs.Num(); }

    // ==================== PAUSE/RESUME ====================

    /**
     * Pauses all AI controllers not currently in battle.
     * Hides pawns and disables their collision.
     *
     * @param Reason - Pause reason for debugging
     */
    UFUNCTION(BlueprintCallable, Category = "ACF|AI")
    void PauseNonBattleAIs(const FString& Reason = TEXT("TurnBattle"));

    /**
     * Resumes all paused AI controllers.
     * Shows pawns and re-enables their collision.
     *
     * @param Reason - Must match the pause reason
     */
    UFUNCTION(BlueprintCallable, Category = "ACF|AI")
    void ResumeAllAIs(const FString& Reason = TEXT("TurnBattle"));

    // ==================== DELEGATES ====================

    /** Called when an AI is added to battle */
    UPROPERTY(BlueprintAssignable, Category = "ACF|AI")
    FOnAIAddedToBattle OnAIAddedToBattle;

    /** Called when an AI is removed from battle */
    UPROPERTY(BlueprintAssignable, Category = "ACF|AI")
    FOnAIRemovedFromBattle OnAIRemovedFromBattle;

protected:
    /** All registered AI controllers in the world */
    UPROPERTY()
    TArray<TObjectPtr<AAIController>> RegisteredAIs;

    /** AI controllers currently in battle */
    UPROPERTY()
    TArray<TObjectPtr<AAIController>> InBattleAIs;

    /** AI controllers that were paused by this subsystem */
    UPROPERTY()
    TArray<TObjectPtr<AAIController>> PausedAIs;
};
