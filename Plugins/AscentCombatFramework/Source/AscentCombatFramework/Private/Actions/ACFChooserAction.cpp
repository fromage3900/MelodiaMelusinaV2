// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.


#include "Actions/ACFChooserAction.h"

#include "Chooser.h"
#include "ChooserFunctionLibrary.h"
#include "Animation/AnimMontage.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "GameFramework/Actor.h"
#include "Engine/World.h"
#include "Logging.h"
#include "Net/UnrealNetwork.h"
#include "Game/ACFFunctionLibrary.h"


UACFChooserAction::UACFChooserAction()
{
    // Replication policy is already set in parent class
}

void UACFChooserAction::SetChooserParams_Implementation()
{
    // Default implementation. To be overridden in Blueprints.
    UE_LOG(LogTemp, Warning, TEXT("SetChooserParams was called! Override this in Blueprints to set parameters."));
}

void UACFChooserAction::ActivateAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo,
    const FGameplayAbilityActivationInfo ActivationInfo, const FGameplayEventData* TriggerEventData)
{
    if (!ChooserTable)
    {
        UE_LOG(ACFLog, Error, TEXT("[ChooserAction] ChooserTable is not set!"));
        return;
    }

    SetChooserParams();

    // Build weight map from chooser table (handles nested choosers automatically)
    TMap<UAnimMontage*, float> MontageWeightMap;
    if (!UACFFunctionLibrary::BuildMontageWeightMapFromChooser(ChooserTable, WeightColumnIndex, MontageWeightMap))
    {
        UE_LOG(ACFLog, Warning, TEXT("[ChooserAction] No montages found in chooser table '%s'"), *GetNameSafe(ChooserTable));
        return;
    }

    // Get all montages matching filter criteria using EvaluateChooserMulti
    TArray<UObject*> Results = UChooserFunctionLibrary::EvaluateChooserMulti(this, ChooserTable, UAnimMontage::StaticClass());

    TArray<UAnimMontage*> FilteredMontages;
    for (UObject* Result : Results)
    {
        if (UAnimMontage* Montage = Cast<UAnimMontage>(Result))
        {
            FilteredMontages.Add(Montage);
        }
    }

    if (FilteredMontages.Num() == 0)
    {
        UE_LOG(ACFLog, Warning, TEXT("[ChooserAction] No valid montages passed filters!"));
        return;
    }

    // Deterministic weighted random selection using GAS prediction key
    UAnimMontage* SelectedMontage = SelectMontageWithDeterministicWeightedRandom(FilteredMontages, MontageWeightMap, ActivationInfo);

    if (SelectedMontage)
    {
        animMontage = SelectedMontage;
    }
    else
    {
        UE_LOG(ACFLog, Error, TEXT("[ChooserAction] Deterministic selection failed!"));
        return;
    }

    // Both client and server activate immediately with same montage
    Super::ActivateAbility(Handle, ActorInfo, ActivationInfo, TriggerEventData);
}

UAnimMontage* UACFChooserAction::SelectMontageWithDeterministicWeightedRandom(
    const TArray<UAnimMontage*>& Montages,
    const TMap<UAnimMontage*, float>& WeightMap,
    const FGameplayAbilityActivationInfo& ActivationInfo)
{
    if (Montages.Num() == 0)
    {
        return nullptr;
    }

    if (Montages.Num() == 1)
    {
        // Only one option, no randomization needed
        LastSelectedMontage = Montages[0];
        return Montages[0];
    }

    // Use GAS prediction key as random seed for deterministic behavior
    // Both client and server use the same prediction key, so they generate identical random sequences
    const int32 Seed = ActivationInfo.GetActivationPredictionKey().Current;
    FRandomStream SyncedRNG(Seed);

    // Build weights array with anti-repeat penalty
    TArray<float> Weights;
    float TotalWeight = 0.0f;

    for (int32 i = 0; i < Montages.Num(); i++)
    {
        UAnimMontage* Montage = Montages[i];

        // Get weight from map (default to 1.0 if not found)
        float Weight = 1.0f;
        if (const float* WeightPtr = WeightMap.Find(Montage))
        {
            Weight = *WeightPtr;
        }

        // Apply anti-repeat penalty to previously selected montage
        if (Montage == LastSelectedMontage)
        {
            Weight *= RepeatProbabilityMultiplier;
        }

        Weights.Add(Weight);
        TotalWeight += Weight;
    }

    if (TotalWeight <= 0.0f)
    {
        UE_LOG(ACFLog, Warning, TEXT("[ChooserAction] Total weight is zero! Selecting first montage."));
        LastSelectedMontage = Montages[0];
        return Montages[0];
    }

    // Generate random value in range [0, TotalWeight]
    const float RandomValue = SyncedRNG.FRandRange(0.0f, TotalWeight);

    // Select montage based on weighted random
    float CurrentWeight = 0.0f;
    for (int32 i = 0; i < Montages.Num(); i++)
    {
        CurrentWeight += Weights[i];
        if (RandomValue <= CurrentWeight)
        {
            LastSelectedMontage = Montages[i];
            return Montages[i];
        }
    }

    // Fallback (should never reach here due to floating point precision)
    LastSelectedMontage = Montages.Last();
    return Montages.Last();
}
