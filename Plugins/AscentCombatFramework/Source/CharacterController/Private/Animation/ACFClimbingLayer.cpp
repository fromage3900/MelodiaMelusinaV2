// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Animation/ACFClimbingLayer.h"
#include "Components/ACFCharacterMovementComponent.h"
#include "Components/ACFClimbingComponent.h"
#include <GameFramework/Pawn.h>

UACFClimbingLayer::UACFClimbingLayer()
{
	NormalizedClimbingSpeed = 0.f;
	LocalClimbingVelocity = FVector::ZeroVector;
	ClimbingSurfaceNormal = FVector::ZeroVector;
}

void UACFClimbingLayer::SetReferences()
{
	const APawn* Pawn = TryGetPawnOwner();
	if (Pawn) {
		MovementComp = Cast<UACFCharacterMovementComponent>(Pawn->GetMovementComponent());
		if (!MovementComp) {
			UE_LOG(LogTemp, Error, TEXT("Owner doesn't have ACFCharacterMovement Comp - UACFClimbingLayer::SetReferences!"));
		}
		ClimbingComp = Pawn->FindComponentByClass<UACFClimbingComponent>();
	}
}

void UACFClimbingLayer::NativeInitializeAnimation()
{
	Super::NativeInitializeAnimation();
	SetReferences();
}

void UACFClimbingLayer::NativeThreadSafeUpdateAnimation(float DeltaSeconds)
{
	Super::NativeThreadSafeUpdateAnimation(DeltaSeconds);
	if (!MovementComp || !ClimbingComp) {
		SetReferences();
		return;
	}

	if (ClimbingComp->IsClimbing()) {
		const float MaxSpeed = ClimbingComp->GetMaxClimbingSpeed();
		const FVector Velocity = MovementComp->Velocity;
		NormalizedClimbingSpeed = MaxSpeed > 0.f ? Velocity.Size() / MaxSpeed : 0.f;

		const APawn* Pawn = TryGetPawnOwner();
		if (Pawn) {
			LocalClimbingVelocity = Pawn->GetActorRotation().UnrotateVector(Velocity);
		}
		ClimbingSurfaceNormal = ClimbingComp->GetClimbSurfaceNormal();
	} else {
		NormalizedClimbingSpeed = 0.f;
		LocalClimbingVelocity = FVector::ZeroVector;
	}
}

void UACFClimbingLayer::OnActivated_Implementation()
{
	SetReferences();
}
