// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Animation/ACFBlendMaskOverlayLayer.h"

#include "ACFCCFunctionLibrary.h"
#include "Animation/ACFAnimInstance.h"
#include "Components/ACFCharacterMovementComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include <GameFramework/Pawn.h>

UACFBlendMaskOverlayLayer::UACFBlendMaskOverlayLayer()
{
	bHasActiveStance = false;
}

void UACFBlendMaskOverlayLayer::SetReferences()
{
	const APawn* pawn = TryGetPawnOwner();
	if (pawn) {
		MovementComp = Cast<UACFCharacterMovementComponent>(pawn->GetMovementComponent());
		if (!MovementComp) {
			UE_LOG(LogTemp, Error, TEXT("Owner doesn't have ACFCharachterMovement Comp - UACFBlendMaskOverlayLayer::SetReferences!!!!"));
		}
	}

	if (USkeletalMeshComponent* mesh = GetOwningComponent()) {
		OwnerAnimInstance = Cast<UACFAnimInstance>(mesh->GetAnimInstance());
	}
}

void UACFBlendMaskOverlayLayer::SetMovStance(const FGameplayTag& inOverlay)
{
	const FACFOverlayAnimationData* Entry = RuntimeOverlayData.LocomotionStancesOverlays.Find(inOverlay);
	currentOverlayTag = Entry ? inOverlay : FGameplayTag();
	if (!Entry) {
		Entry = &RuntimeOverlayData.IdleOverlay;
	}

	currentOverlay = Entry->Overlay;
	CurrentBlendMask = Entry->BlendMask;
	CurrentBlendMode = Entry->BlendMode;
	AimOffset = Entry->AimOffset;
	AimOffsetAlpha = Entry->AimOffsetAlpha;

	// No overlay animation -> no mask, so ACFBlendByMask leaves the base pose untouched
	// instead of blending in the (ref/T-pose) sampled from an empty sequence.
	if (!currentOverlay.OverlayAnim) {
		CurrentBlendMask = nullptr;
	}

	targetBlendAlpha = currentOverlay.BlendAlpha;
	bHasActiveStance = currentOverlayTag != FGameplayTag();
	RefreshGraphVariables();
}

void UACFBlendMaskOverlayLayer::RefreshGraphVariables()
{
	CurrentOverlayAnim = currentOverlay.OverlayAnim;
}

void UACFBlendMaskOverlayLayer::NativeInitializeAnimation()
{
	Super::NativeInitializeAnimation();
	SetReferences();
}

void UACFBlendMaskOverlayLayer::NativeThreadSafeUpdateAnimation(float DeltaSeconds)
{
	Super::NativeThreadSafeUpdateAnimation(DeltaSeconds);

	if (!MovementComp || !OwnerAnimInstance) {
		SetReferences();
	}

	// Pull the active overlay profile from the main AnimInstance. Only refresh the runtime data
	// when the active overlay tag actually changes, so editing is cheap and the layer stays
	// self-sufficient (the main never pushes into us).
	if (OwnerAnimInstance) {
		const FGameplayTag activeTag = OwnerAnimInstance->GetCurrentOverlay();
		if (activeTag != appliedOverlayTag) {
			appliedOverlayTag = activeTag;
			RuntimeOverlayData = FACFOverlayData();
			DefaultSwitchTime = RuntimeOverlayData.DefaultSwitchTime;
			bForceStanceRefresh = true;
		}
	}

	const FGameplayTag newStance = MovementComp ? MovementComp->GetCurrentLocomotionStance() : FGameplayTag();
	if (bForceStanceRefresh || newStance != currentOverlayTag) {
		SetMovStance(newStance);
		bForceStanceRefresh = false;
	}

	if (!FMath::IsNearlyEqual(targetBlendAlpha, OverlayBlendAlfa)) {
		OverlayBlendAlfa = FMath::FInterpTo(OverlayBlendAlfa, targetBlendAlpha, DeltaSeconds, 1.f);
	}
}

void UACFBlendMaskOverlayLayer::OnActivated_Implementation()
{
	bForceStanceRefresh = true;
}
