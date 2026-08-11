// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "RhythmInputComponent.h"
#include "RhythmCombatComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnRhythmAttack, float, DamageMultiplier, int32, ComboCount);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnComboBreak);

UCLASS(ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class BS_GODFILE_API URhythmCombatComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    URhythmCombatComponent();

    // Initialize with rhythm input component
    UFUNCTION(BlueprintCallable, Category="Melodia|RhythmCombat")
    void Initialize(URhythmInputComponent* InRhythmInput);

    // Execute a rhythm-based attack
    UFUNCTION(BlueprintCallable, Category="Melodia|RhythmCombat")
    void ExecuteRhythmAttack(float BaseDamage);

    // Get current combo count
    UFUNCTION(BlueprintPure, Category="Melodia|RhythmCombat")
    int32 GetComboCount() const { return ComboCount; }

    // Get max combo achieved
    UFUNCTION(BlueprintPure, Category="Melodia|RhythmCombat")
    int32 GetMaxCombo() const { return MaxCombo; }

    // Get damage multiplier based on accuracy
    UFUNCTION(BlueprintPure, Category="Melodia|RhythmCombat")
    float GetDamageMultiplier() const { return DamageMultiplier; }

    // Reset combo
    UFUNCTION(BlueprintCallable, Category="Melodia|RhythmCombat")
    void ResetCombo();

    // Event fired when rhythm attack is executed
    UPROPERTY(BlueprintAssignable, Category="Melodia|RhythmCombat")
    FOnRhythmAttack OnRhythmAttack;

    // Event fired when combo breaks
    UPROPERTY(BlueprintAssignable, Category="Melodia|RhythmCombat")
    FOnComboBreak OnComboBreak;

protected:
    virtual void BeginPlay() override;

private:
    // Reference to rhythm input component
    UPROPERTY()
    URhythmInputComponent* RhythmInput;

    // Combo tracking
    int32 ComboCount = 0;
    int32 MaxCombo = 0;

    // Damage multipliers
    UPROPERTY(EditAnywhere, Category="Melodia|RhythmCombat", meta=(ClampMin="0.5", ClampMax="3.0"))
    float PerfectMultiplier = 2.0f;

    UPROPERTY(EditAnywhere, Category="Melodia|RhythmCombat", meta=(ClampMin="0.5", ClampMax="2.0"))
    float GoodMultiplier = 1.5f;

    UPROPERTY(EditAnywhere, Category="Melodia|RhythmCombat", meta=(ClampMin="0.1", ClampMax="1.0"))
    float MissMultiplier = 0.5f;

    // Combo bonus (additional multiplier per combo hit)
    UPROPERTY(EditAnywhere, Category="Melodia|RhythmCombat", meta=(ClampMin="0.0", ClampMax="0.5"))
    float ComboBonus = 0.1f;

    // Current damage multiplier
    float DamageMultiplier = 1.0f;

    // Handle rhythm input
    UFUNCTION()
    void HandleRhythmInput(ERhythmAccuracy Accuracy, float TimingOffset);

    // Calculate damage multiplier from accuracy
    float CalculateDamageMultiplier(ERhythmAccuracy Accuracy) const;

    // Update combo
    void UpdateCombo(ERhythmAccuracy Accuracy);
};