// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFCombinedAnimMasterComponent.h"
#include <ContextualAnimTypes.h>
#include "Components/ACFAbilitySystemComponent.h"
#include "ACFCombinedAnimSlaveComponent.h"
#include "ACFCombinedAnimationsDataAsset.h"

// Sets default values for this component's properties
UACFCombinedAnimMasterComponent::UACFCombinedAnimMasterComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;

    // ...
}

bool UACFCombinedAnimMasterComponent::CanPlayCombinedAnimWithActor(const FCombinedAnimConfig& combinedAnim, AActor* targetActor)
{
    if (GetIsPlayingContextualAnim()) {
        return false;
    }
    if (!targetActor) {
        return false; // No target actor provided
    }
    if (GetOwner()->GetDistanceTo(targetActor) > combinedAnim.MaxDistanceToStart) {
        return false; // Target actor is too far away
    }

    if (combinedAnim.MasterRequiredActionsSet.IsValid()) {
        const UACFAbilitySystemComponent* abilityComp = GetOwner()->FindComponentByClass<UACFAbilitySystemComponent>();
        if (abilityComp && !abilityComp->GetCurrentMovesetActionsTag().MatchesTag(combinedAnim.MasterRequiredActionsSet)) {
            // The master does not have the required actions set
            return false;
        }
    }

    UACFCombinedAnimSlaveComponent* slaveComp = targetActor->FindComponentByClass<UACFCombinedAnimSlaveComponent>();
    if (!slaveComp) {
        return false; // Target actor does not have a slave component
    }

    return slaveComp->CanStartCombinedAnimation(combinedAnim, Cast<ACharacter>(GetOwner()));
}

bool UACFCombinedAnimMasterComponent::TryGetBestCombinedAnimForActor(AActor* targetActor, FCombinedAnimConfig& outCombinedAnim)
{
    if (CombinedAnimations) {
        TArray<FCombinedAnimConfig> combinedAnims;

        CombinedAnimations->GetCombinedAnims(combinedAnims);

        TArray<FCombinedAnimConfig> selectedAnims;
        for (const FCombinedAnimConfig& combinedAnim : combinedAnims) {
            if (CanPlayCombinedAnimWithActor(combinedAnim, targetActor)) {
                selectedAnims.Add(combinedAnim); // Found a valid combined animation
            }
        }

        if (selectedAnims.Num() > 0) {
            const UACFAbilitySystemComponent* abilityComp = GetOwner()->FindComponentByClass<UACFAbilitySystemComponent>();
            if (abilityComp && abilityComp->GetCurrentMovesetActionsTag().IsValid()) {
                for (const FCombinedAnimConfig& combinedAnim : selectedAnims) {
                    if (combinedAnim.MasterRequiredActionsSet.MatchesTag(abilityComp->GetCurrentMovesetActionsTag())) {
                        outCombinedAnim = combinedAnim; // Return the first valid animation that matches the required actions set
                        return true;
                    }
                }

            } else {
                // otherwise just the  first one
                outCombinedAnim = selectedAnims[0];
                return true;
            }
        } else {
            UE_LOG(LogTemp, Warning, TEXT("CombinedAnimations is null in UACFCombinedAnimMasterComponent::TryGetBestCombinedAnimForActor"));
        }
    }
    return false;
}

bool UACFCombinedAnimMasterComponent::GetContextualAnimsByTag(const FGameplayTag& AnimTag, TArray<FCombinedAnimConfig>& outCombinedAnims)
{
    outCombinedAnims.Empty();

    if (!CombinedAnimations) {
        return false;
    }

    TArray<FCombinedAnimConfig> allAnims;
    CombinedAnimations->GetCombinedAnims(allAnims);

    for (const FCombinedAnimConfig& anim : allAnims) {
        if (anim.AnimTag.MatchesTag(AnimTag)) {
            outCombinedAnims.Add(anim);
        }
    }

    return outCombinedAnims.Num() > 0;
}

// Called when the game starts
void UACFCombinedAnimMasterComponent::BeginPlay()
{
    Super::BeginPlay();

    // ...
}
