// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.


#include "ACFCameraPointComponent.h"
#include "CCMTypes.h"
#include "Engine/World.h"
#include "TimerManager.h"


UACFCameraPointComponent::UACFCameraPointComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = false;
	bHiddenInGame = true;
	SetUsingAbsoluteScale(true);
	bConstrainAspectRatio = false;
}

void UACFCameraPointComponent::BeginPlay()
{
	Super::BeginPlay();
	InitialRelativeTransform = GetRelativeTransform();
}

void UACFCameraPointComponent::OnCameraActivated()
{
	bIsActivated = true;
	InitialRelativeTransform = GetRelativeTransform();

	// Calculate orbit parameters from actual camera position relative to owner
	if (const AActor* OwnerActor = GetOwner())
	{
		const FVector CameraLocation = GetComponentLocation();
		const FVector OwnerLocation = OwnerActor->GetActorLocation();
		const FVector ToCamera = CameraLocation - OwnerLocation;

		// Radius is horizontal distance (XY plane)
		CachedOrbitRadius = FVector(ToCamera.X, ToCamera.Y, 0.0f).Size();

		// Height offset is Z difference
		CachedOrbitHeightOffset = ToCamera.Z;

		// Starting angle
		CurrentOrbitAngle = FMath::Atan2(ToCamera.Y, ToCamera.X);
	}

	CurrentCraneOffset = 0.0f;

	if (MovementConfig.MovementPreset != EACFCameraMovementPreset::None)
	{
		SetComponentTickEnabled(true);
		bIsMovementRunning = true;
	}

	// Clear any pending restore timer
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(RestoreTimerHandle);
	}
	OnActivated();
}

void UACFCameraPointComponent::OnCameraDeactivated()
{
	bIsActivated = false;
	bIsMovementRunning = false;
	SetComponentTickEnabled(false);
	// Delayed restore to allow blend to start first
	if (RestoreDelay > 0.0f)
	{
		if (UWorld* World = GetWorld())
		{
			World->GetTimerManager().SetTimer(
				RestoreTimerHandle,
				FTimerDelegate::CreateWeakLambda(this, [this]()
					{
						RestoreInitialTransform();
					}),
				RestoreDelay,
				false
			);
		}
	}
	else
	{
		RestoreInitialTransform();
	}
	OnDeactivated();
}

void UACFCameraPointComponent::OnActivated_Implementation()
{

}

void UACFCameraPointComponent::OnDeactivated_Implementation()
{

}


void UACFCameraPointComponent::StopMovement()
{
	bIsMovementRunning = false;
}

void UACFCameraPointComponent::ResumeMovement()
{
	if (bIsActivated && MovementConfig.MovementPreset != EACFCameraMovementPreset::None)
	{
		bIsMovementRunning = true;
		SetComponentTickEnabled(true);
	}
}

void UACFCameraPointComponent::ResetMovement()
{
	bIsMovementRunning = false;
	CurrentCraneOffset = 0.0f;
	CurrentLateralOffset = 0.0f;


	// Recalculate orbit parameters from initial position
	if (const AActor* OwnerActor = GetOwner())
	{
		const FVector InitialWorldLocation = OwnerActor->GetActorTransform().TransformPosition(InitialRelativeTransform.GetLocation());
		const FVector OwnerLocation = OwnerActor->GetActorLocation();
		const FVector ToCamera = InitialWorldLocation - OwnerLocation;

		CachedOrbitRadius = FVector(ToCamera.X, ToCamera.Y, 0.0f).Size();
		CachedOrbitHeightOffset = ToCamera.Z;
		CurrentOrbitAngle = FMath::Atan2(ToCamera.Y, ToCamera.X);
	}

	RestoreInitialTransform();
}

void UACFCameraPointComponent::RestoreInitialTransform()
{
	SetRelativeTransform(InitialRelativeTransform);
}


void UACFCameraPointComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (bIsActivated && bIsMovementRunning)
	{
		ProcessMovementPreset(DeltaTime);
	}
	// Se non sono più la camera attiva, auto-deattivo
	if (bIsActivated && GetWorld())
	{
		APlayerController* PC = GetWorld()->GetFirstPlayerController();
		if (PC && PC->GetViewTarget() != GetOwner())
		{
			OnCameraDeactivated();
			return;
		}
	}
}

// ============================================================================
// Setters
// ============================================================================

void UACFCameraPointComponent::SetMovementPreset(EACFCameraMovementPreset NewPreset)
{
	MovementConfig.MovementPreset = NewPreset;

	if (bIsActivated)
	{
		const bool bShouldTick = NewPreset != EACFCameraMovementPreset::None;
		SetComponentTickEnabled(bShouldTick);
		bIsMovementRunning = bShouldTick;
	}
}

void UACFCameraPointComponent::SetMovementSpeed(float NewSpeed)
{
	MovementConfig.MovementSpeed = FMath::Max(0.0f, NewSpeed);
}

void UACFCameraPointComponent::SetLookAtHeightOffset(float NewOffset)
{
	MovementConfig.LookAtHeightOffset = NewOffset;
}

void UACFCameraPointComponent::OnCustomMovementTick_Implementation(float DeltaTime)
{

}

// ============================================================================
// Movement Processing
// ============================================================================

void UACFCameraPointComponent::ProcessMovementPreset(float DeltaTime)
{
	switch (MovementConfig.MovementPreset)
	{
	case EACFCameraMovementPreset::None:
		break;

	case EACFCameraMovementPreset::RotateAroundOwner:
		ProcessRotateAroundOwner(DeltaTime);
		break;

	case EACFCameraMovementPreset::Crane:
		ProcessCrane(DeltaTime);
		break;
	case EACFCameraMovementPreset::PanLateral:
		ProcessPanLateral(DeltaTime);
		break;
	case EACFCameraMovementPreset::Custom:
		OnCustomMovementTick(DeltaTime);
		break;
	}
}

void UACFCameraPointComponent::ProcessRotateAroundOwner(float DeltaTime)
{
	const AActor* OwnerActor = GetOwner();
	if (!OwnerActor)
	{
		return;
	}

	// Continuous rotation
	CurrentOrbitAngle += FMath::DegreesToRadians(MovementConfig.MovementSpeed * MovementConfig.MovementDirection * DeltaTime);

	const FVector OwnerLocation = OwnerActor->GetActorLocation();
	const FVector Offset = FVector(
		FMath::Cos(CurrentOrbitAngle) * CachedOrbitRadius,
		FMath::Sin(CurrentOrbitAngle) * CachedOrbitRadius,
		CachedOrbitHeightOffset
	);

	SetWorldLocation(OwnerLocation + Offset);
	UpdateLookAtOwner();
}

void UACFCameraPointComponent::ProcessCrane(float DeltaTime)
{
	const AActor* OwnerActor = GetOwner();
	if (!OwnerActor)
	{
		return;
	}

	// Continuous vertical movement
	CurrentCraneOffset += MovementConfig.MovementSpeed * MovementConfig.MovementDirection * DeltaTime;
	const FVector InitialWorldLocation = OwnerActor->GetActorTransform().TransformPosition(InitialRelativeTransform.GetLocation());
	FVector NewLocation = InitialWorldLocation;
	NewLocation.Z += CurrentCraneOffset;

	SetWorldLocation(NewLocation);
	UpdateLookAtOwner();
}

void UACFCameraPointComponent::ProcessPanLateral(float DeltaTime)
{
	const AActor* OwnerActor = GetOwner();
	if (!OwnerActor)
	{
		return;
	}

	CurrentLateralOffset += MovementConfig.MovementSpeed * MovementConfig.MovementDirection * DeltaTime;

	const FVector InitialWorldLocation = OwnerActor->GetActorTransform().TransformPosition(InitialRelativeTransform.GetLocation());
	const FVector ToOwner = (OwnerActor->GetActorLocation() - InitialWorldLocation).GetSafeNormal();
	const FVector LateralDir = FVector::CrossProduct(ToOwner, FVector::UpVector).GetSafeNormal();

	const FVector NewLocation = InitialWorldLocation + LateralDir * CurrentLateralOffset;
	SetWorldLocation(NewLocation);
	UpdateLookAtOwner();
}

void UACFCameraPointComponent::UpdateLookAtOwner()
{
	const FVector LookTarget = GetLookAtTarget();
	const FVector CameraLocation = GetComponentLocation();
	SetWorldRotation((LookTarget - CameraLocation).Rotation());
}

FVector UACFCameraPointComponent::GetLookAtTarget() const
{
	if (const AActor* OwnerActor = GetOwner())
	{
		return OwnerActor->GetActorLocation() + FVector(0.0f, 0.0f, MovementConfig.LookAtHeightOffset);
	}
	return GetComponentLocation() + GetForwardVector() * 100.0f;
}

