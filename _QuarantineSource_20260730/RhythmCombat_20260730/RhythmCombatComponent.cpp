// Copyright Epic Games, Inc. All Rights Reserved.

#include "RhythmCombatComponent.h"
#include "RhythmInputComponent.h"

URhythmCombatComponent::URhythmCombatComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void URhythmCombatComponent::BeginPlay()
{
    Super::BeginPlay();
}

void URhythmCombatComponent::Initialize(URhythmInputComponent* InRhythmInput)
{
    RhythmInput = InRhythmInput;
    
    if (RhythmInput)
    {
        // Bind to rhythm input events
        RhythmInput->OnRhythmInput.AddDynamic(this, &URhythmCombatComponent::HandleRhythmInput);
        
        UE_LOG(LogTemp, Log, TEXT("RhythmCombatComponent initialized with RhythmInputComponent"));
    }
    else
    {
        UE_LOG(LogTemp, Warning, TEXT("RhythmCombatComponent: RhythmInputComponent is null"));
    }
}

void URhythmCombatComponent::ExecuteRhythmAttack(float BaseDamage)
{
    if (!RhythmInput)
    {
        UE_LOG(LogTemp, Warning, TEXT("RhythmCombatComponent: Cannot execute attack - RhythmInputComponent not initialized"));
        return;
    }
    
    // Register rhythm input
    RhythmInput->RegisterRhythmInput();
    
    // The actual damage calculation and event broadcasting happens in HandleRhythmInput
    // which is called by the OnRhythmInput delegate
}

void URhythmCombatComponent::ResetCombo()
{
    if (ComboCount > 0)
    {
        UE_LOG(LogTemp, Log, TEXT("Combo broken at %d hits"), ComboCount);
        OnComboBreak.Broadcast();
    }
    
    ComboCount = 0;
    DamageMultiplier = 1.0f;
}

void URhythmCombatComponent::HandleRhythmInput(ERhythmAccuracy Accuracy, float TimingOffset)
{
    // Update combo
    UpdateCombo(Accuracy);
    
    // Calculate damage multiplier
    DamageMultiplier = CalculateDamageMultiplier(Accuracy);
    
    // Apply combo bonus
    float FinalMultiplier = DamageMultiplier + (ComboCount * ComboBonus);
    
    UE_LOG(LogTemp, Log, TEXT("Rhythm Attack: Accuracy=%d, Combo=%d, Multiplier=%.2f"), 
        static_cast<int32>(Accuracy), ComboCount, FinalMultiplier);
    
    // Broadcast attack event
    OnRhythmAttack.Broadcast(FinalMultiplier, ComboCount);
}

float URhythmCombatComponent::CalculateDamageMultiplier(ERhythmAccuracy Accuracy) const
{
    switch (Accuracy)
    {
        case ERhythmAccuracy::Perfect:
            return PerfectMultiplier;
        case ERhythmAccuracy::Good:
            return GoodMultiplier;
        case ERhythmAccuracy::Miss:
        default:
            return MissMultiplier;
    }
}

void URhythmCombatComponent::UpdateCombo(ERhythmAccuracy Accuracy)
{
    if (Accuracy == ERhythmAccuracy::Perfect || Accuracy == ERhythmAccuracy::Good)
    {
        // Increase combo
        ComboCount++;
        
        // Update max combo
        if (ComboCount > MaxCombo)
        {
            MaxCombo = ComboCount;
        }
        
        UE_LOG(LogTemp, Verbose, TEXT("Combo increased to %d"), ComboCount);
    }
    else
    {
        // Break combo
        ResetCombo();
    }
}