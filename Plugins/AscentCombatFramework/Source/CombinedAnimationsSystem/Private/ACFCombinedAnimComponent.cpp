// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFCombinedAnimComponent.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "Components/ACFDamageHandlerComponent.h"

// Sets default values for this component's properties
UACFCombinedAnimComponent::UACFCombinedAnimComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;
    bIsPlayingAContextualAnim = false;
}

// Called when the game starts
void UACFCombinedAnimComponent::BeginPlay()
{
    Super::BeginPlay();
    combinedAnimationComponent = GetOwner()->FindComponentByClass<UContextualAnimSceneActorComponent>();

    if (combinedAnimationComponent) {
        // World Partition can stream actors in/out, so BeginPlay may run more than once
        // against a re-used ContextualAnim component. Guard against double-binding.
        if (!combinedAnimationComponent->OnJoinedSceneDelegate.IsAlreadyBound(this, &UACFCombinedAnimComponent::HandleJoinedScene)) {
            combinedAnimationComponent->OnJoinedSceneDelegate.AddDynamic(this, &UACFCombinedAnimComponent::HandleJoinedScene);
        }
        if (!combinedAnimationComponent->OnLeftSceneDelegate.IsAlreadyBound(this, &UACFCombinedAnimComponent::HandleLeftScene)) {
            combinedAnimationComponent->OnLeftSceneDelegate.AddDynamic(this, &UACFCombinedAnimComponent::HandleLeftScene);
        }

    } else {
        UE_LOG(LogTemp, Error, TEXT("UACFCombinedAnimComponent: Contextual Animation Component not found on owner."));
    }
}

void UACFCombinedAnimComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (combinedAnimationComponent) {
        combinedAnimationComponent->OnJoinedSceneDelegate.RemoveDynamic(this, &UACFCombinedAnimComponent::HandleJoinedScene);
        combinedAnimationComponent->OnLeftSceneDelegate.RemoveDynamic(this, &UACFCombinedAnimComponent::HandleLeftScene);
    }

    Super::EndPlay(EndPlayReason);
}

void UACFCombinedAnimComponent::HandleJoinedScene(UContextualAnimSceneActorComponent* SceneActorComponent)
{
    bIsPlayingAContextualAnim = true;
    if (bLockAbilityTriggersDuringCombinedAnims) {
        UACFAbilitySystemComponent* actionComp = GetOwner()->FindComponentByClass<UACFAbilitySystemComponent>();
        if (actionComp) {
            actionComp->LockActionsTrigger();
        } else {
            UE_LOG(LogTemp, Warning, TEXT("UACFCombinedAnimComponent: Actions Manager Component not found on owner."));
        }
    }
    if (!bCanBeHitDuringCombinedAnims) {
        UACFDamageHandlerComponent* damageComp = GetOwner()->FindComponentByClass<UACFDamageHandlerComponent>();
        if (damageComp) {
            damageComp->SetIsImmortal(true);
        } else {
            UE_LOG(LogTemp, Warning, TEXT("UACFCombinedAnimComponent: Actions Manager Component not found on owner."));
        }
    }
    OnJoinedScene();
}

void UACFCombinedAnimComponent::HandleLeftScene(UContextualAnimSceneActorComponent* SceneActorComponent)
{
    bIsPlayingAContextualAnim = false;
    if (bLockAbilityTriggersDuringCombinedAnims) {
        UACFAbilitySystemComponent* actionComp = GetOwner()->FindComponentByClass<UACFAbilitySystemComponent>();
        if (actionComp) {
            actionComp->UnlockActionsTrigger();
        } else {
            UE_LOG(LogTemp, Warning, TEXT("UACFCombinedAnimComponent: Actions Manager Component not found on owner."));
        }
    }
    if (!bCanBeHitDuringCombinedAnims) {
        UACFDamageHandlerComponent* damageComp = GetOwner()->FindComponentByClass<UACFDamageHandlerComponent>();
        if (damageComp) {
            damageComp->SetIsImmortal(false);
        } else {
            UE_LOG(LogTemp, Warning, TEXT("UACFCombinedAnimComponent: Actions Manager Component not found on owner."));
        }
    }
    OnLeftScene();
}

void UACFCombinedAnimComponent::OnJoinedScene_Implementation()
{
}

void UACFCombinedAnimComponent::OnLeftScene_Implementation()
{
}
