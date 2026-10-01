// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Animation/ACFOverlayLayer.h"
#include "ACFCCFunctionLibrary.h"
#include "ACMTypes.h"
#include "Components/ACFCharacterMovementComponent.h"
#include <GameFramework/Pawn.h>

UACFOverlayLayer::UACFOverlayLayer()
{
    // LocomotionStancesOverlays.Add( UGameplayTagsManager::Get().RequestGameplayTag(ACF::AimTag));
    //  LocomotionStancesOverlays.Add( UGameplayTagsManager::Get().RequestGameplayTag(ACF::BlockTag));
    bHasActiveStance = false;
}

void UACFOverlayLayer::SetReferences()
{
    const APawn* pawn = TryGetPawnOwner();
    if (pawn) {
        MovementComp = Cast<UACFCharacterMovementComponent>(pawn->GetMovementComponent());
        if (!MovementComp) {
            UE_LOG(LogTemp, Error, TEXT("Owner doesn't have ACFCharachterMovement Comp - UACFOverlayLayer::SetReferences!!!!"));

        } else {
            SetMovStance(MovementComp->GetCurrentLocomotionStance());
        }
    }
}

void UACFOverlayLayer::SetMovStance(const FGameplayTag& inOverlay)
{
    if (LocomotionStancesOverlays.Contains(inOverlay)) {
        currentOverlayTag = inOverlay;
        currentOverlay = *(LocomotionStancesOverlays.Find(currentOverlayTag));
    } else {
        currentOverlayTag = FGameplayTag();
        currentOverlay = IdleOverlay;
    }
    targetBlendAlpha = currentOverlay.BlendAlpha;
    bHasActiveStance = currentOverlayTag != FGameplayTag();
}

void UACFOverlayLayer::NativeInitializeAnimation()
{
    Super::NativeInitializeAnimation();
    SetReferences();
}

void UACFOverlayLayer::NativeThreadSafeUpdateAnimation(float DeltaSeconds)
{
    Super::NativeThreadSafeUpdateAnimation(DeltaSeconds);
    if (!MovementComp) {
        SetReferences();
    } else {
        const FGameplayTag newOverlay = MovementComp->GetCurrentLocomotionStance();
        if (newOverlay != currentOverlayTag) {
            SetMovStance(newOverlay);
        }
        if (!FMath::IsNearlyEqual(targetBlendAlpha, OverlayBlendAlfa)) {
            OverlayBlendAlfa = FMath::FInterpTo(OverlayBlendAlfa, targetBlendAlpha, DeltaSeconds, 1.f);
        }
    }
}

void UACFOverlayLayer::OnActivated_Implementation()
{
    currentOverlay = IdleOverlay;
    SetMovStance(currentOverlayTag);
}
