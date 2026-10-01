// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFClimbingComponent.h"

#include "ACFActionTypes.h"
#include "Animation/ACFAnimInstance.h"
#include "Components/ACFCharacterMovementComponent.h"
#include "Components/CapsuleComponent.h"
#include "EnhancedInputComponent.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "DrawDebugHelpers.h"
#include "Engine/EngineTypes.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "Net/UnrealNetwork.h"

namespace
{
	float ComputeSurfaceTiltFromVerticalDegrees(const FVector& SurfaceNormal)
	{
		const float ClampedAbsZ = FMath::Clamp(FMath::Abs(SurfaceNormal.GetSafeNormal().Z), 0.f, 1.f);
		return FMath::RadiansToDegrees(FMath::Asin(ClampedAbsZ));
	}
}

UACFClimbingComponent::UACFClimbingComponent()
{
	PrimaryComponentTick.bCanEverTick = false; // Ticking is driven by the movement component
	SetIsReplicatedByDefault(true);
}

void UACFClimbingComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(UACFClimbingComponent, CurrentClimbingNormal);
}

void UACFClimbingComponent::BeginPlay()
{
	Super::BeginPlay();

	ClimbQueryParams.AddIgnoredActor(GetOwner());

	ACharacter* Character = Cast<ACharacter>(GetOwner());
	if (Character) {
		MovementComponent = Character->GetComponentByClass<UACFCharacterMovementComponent>();
		AbilitySystem = Character->GetComponentByClass<UACFAbilitySystemComponent>();
		if (Character->GetMesh()) {
			DefaultMeshRelativeLocation = Character->GetMesh()->GetRelativeLocation();
			bHasStoredMeshRelativeLocation = true;
			AnimInstance = Cast<UACFAnimInstance>(Character->GetMesh()->GetAnimInstance());
		}
	}

	if (!MovementComponent) {
		UE_LOG(LogTemp, Error, TEXT("ACFClimbingComponent: No ACFCharacterMovementComponent found on owner %s. Climbing will not work."),
			*GetOwner()->GetName());
	}

	TryBindExitClimbingInputAction();
}

// --- Public API ---

bool UACFClimbingComponent::TryClimbing()
{
	if (!MovementComponent || !MovementComponent->UpdatedComponent) {
		return false;
	}
	if (bHasPendingEnterClimb) {
		return true;
	}
	if (const UWorld* World = GetWorld()) {
		if (World->GetTimeSeconds() - LastExitRequestTime < ReattachDelayAfterExitRequest) {
			bWantsToClimb = false;
			return false;
		}
	}
	if (ClimbableObjectTypes.IsEmpty()) {
		bWantsToClimb = false;
		return false;
	}

	SweepAndStoreWallHits();

	const FVector Forward = MovementComponent->UpdatedComponent->GetForwardVector();
	auto HitIt = CurrentWallHits.CreateConstIterator();
	bool bCanStartClimbing = bWantsToClimb;
	while (!bWantsToClimb && HitIt) {
		const bool bClimbable = IsWallClimbable(*HitIt, Forward);
		bCanStartClimbing = bClimbable;
		bWantsToClimb = bCanStartClimbing;
		++HitIt;
	}

	if (bCanStartClimbing) {
		bExitClimbingRequested = false;

		const bool bAuthority = GetOwner() && GetOwner()->HasAuthority();
		if (bAuthority) {
			const bool bStartingFromGround = MovementComponent && MovementComponent->IsMovingOnGround();
			if (bStartingFromGround && AnimInstance) {
				// Play enter montage first, then switch to climbing when montage ends.
				bHasPendingEnterClimb = true;
				bWantsToClimb = false;

				if (ACharacter* CharOwner = MovementComponent->GetCharacterOwner()) {
					if (!FMath::IsNearlyZero(EnterClimbForwardOffset) || !FMath::IsNearlyZero(EnterClimbVerticalOffset)) {
						const FVector EnterOffset = CharOwner->GetActorForwardVector() * EnterClimbForwardOffset + FVector::UpVector * EnterClimbVerticalOffset;
						CharOwner->SetActorLocation(CharOwner->GetActorLocation() + EnterOffset, true);
					}
				}

				// Apply visual mesh offset before montage starts to avoid a visible snap at attach time.
				ApplyClimbingMeshOffset();

				if (bLockMovementDuringEnterClimbMontage) {
					bPrevCanMoveBeforeEnterMontage = MovementComponent->GetCanMove();
					MovementComponent->SetCanMove(false);
				}

				// Trigger Ability to enter
				if (!AbilitySystem) {
					return false;
				}
				else {
					AbilitySystem->TriggerAction(EnterClimbingTag, EActionPriority::EHighest, false);
				}

			}
			else {
				// Fallback: allow Blueprint or external listeners to control enter transition.
				bHasPendingEnterClimb = true;
				bWantsToClimb = false;
				OnEnterClimbRequested.Broadcast();
			}

			return true;
		}
	}

	if (GetOwner() && !GetOwner()->HasAuthority()) {
		ServerTryClimbing();
	}

	return bCanStartClimbing;
}

void UACFClimbingComponent::ServerTryClimbing_Implementation()
{
	TryClimbing();
}

void UACFClimbingComponent::CancelClimbing_Implementation()
{
	RequestExitClimbing();
}

void UACFClimbingComponent::RequestExitClimbing_Implementation()
{
	bExitClimbingRequested = true;
	bHasPendingEnterClimb = false;
	if (bLockMovementDuringEnterClimbMontage && MovementComponent) {
		MovementComponent->SetCanMove(bPrevCanMoveBeforeEnterMontage);
	}
	if (bRequireForwardReleaseAfterExit) {
		bHasReleasedForwardSinceExit = false;
	}
	if (UWorld* World = GetWorld()) {
		LastExitRequestTime = World->GetTimeSeconds();
	}

	// Make exit immediate when requested, without waiting for next climbing physics tick.
	PerformImmediateExitClimbing();
}

void UACFClimbingComponent::ConfirmEnterClimb_Implementation()
{
	if (!GetOwner() || !GetOwner()->HasAuthority()) {
		return;
	}

	bHasPendingEnterClimb = false;
	bWantsToClimb = true;
}

void UACFClimbingComponent::BeginClimbingFromAbility()
{
	if (!GetOwner()) {
		return;
	}
	if (!GetOwner()->HasAuthority()) {
		UE_LOG(LogTemp, Warning, TEXT("BeginClimbingFromAbility: ignored on non-authority — call from server-side ability only. Owner=%s"),
			*GetOwner()->GetName());
		return;
	}
	ApplyClimbingMovementModeFromAbilityInternal();
}

void UACFClimbingComponent::ApplyClimbingMovementModeFromAbilityInternal()
{
	if (!GetOwner() || !GetOwner()->HasAuthority()) {
		return;
	}
	if (!MovementComponent || !MovementComponent->UpdatedComponent) {
		return;
	}
	if (IsClimbing()) {
		return;
	}
	if (ClimbableObjectTypes.IsEmpty()) {
		return;
	}

	SweepAndStoreWallHits();

	const FVector Forward = MovementComponent->UpdatedComponent->GetForwardVector();
	bool bFoundClimbableWall = false;
	for (const FHitResult& Hit : CurrentWallHits) {
		if (IsWallClimbable(Hit, Forward)) {
			bFoundClimbableWall = true;
			break;
		}
	}
	if (!bFoundClimbableWall) {
		return;
	}

	ComputeSurfaceInfo();

	bHasPendingEnterClimb = false;
	bExitClimbingRequested = false;
	bWantsToClimb = false;

	MovementComponent->SetCanMove(true);

	MovementComponent->SetMovementMode(EMovementMode::MOVE_Custom, EACFCustomMovementMode::CMOVE_Climbing);
	MovementComponent->StopMovementImmediately();
}

void UACFClimbingComponent::ConfirmExitClimbing_Implementation()
{
	PerformImmediateExitClimbing();
}

void UACFClimbingComponent::HandleExitClimbingInputAction(const UInputAction* TriggeredInputAction)
{
	if (!IsClimbing() || !ExitClimbingInputAction || !TriggeredInputAction) {
		return;
	}

	if (TriggeredInputAction == ExitClimbingInputAction) {
		RequestExitClimbing();
	}
}

void UACFClimbingComponent::OnExitClimbingActionTriggered(const FInputActionValue& InputValue)
{
	HandleExitClimbingInputAction(ExitClimbingInputAction);
}

bool UACFClimbingComponent::IsClimbing() const
{
	return MovementComponent
		&& MovementComponent->MovementMode == EMovementMode::MOVE_Custom
		&& MovementComponent->CustomMovementMode == EACFCustomMovementMode::CMOVE_Climbing;
}

FVector UACFClimbingComponent::GetClimbSurfaceNormal() const
{
	return CurrentClimbingNormal;
}

FVector UACFClimbingComponent::GetClimbingForwardDirection() const
{
	if (!IsClimbing() || !MovementComponent) {
		return FVector::ZeroVector;
	}
	return FVector::CrossProduct(GetClimbSurfaceNormal(), -GetOwner()->GetActorRightVector());
}

FVector UACFClimbingComponent::GetClimbingRightDirection() const
{
	if (!IsClimbing() || !MovementComponent) {
		return FVector::ZeroVector;
	}
	return FVector::CrossProduct(GetClimbSurfaceNormal(), GetOwner()->GetActorUpVector());
}

// --- Movement Component Delegation Interface ---

void UACFClimbingComponent::TickClimbing()
{
	//TryBindExitClimbingInputAction();

	// Failsafe: if enter montage-end delegate is missed, resume attach decision anyway.
	if (bHasPendingEnterClimb && GetOwner() && GetOwner()->HasAuthority()) {
		if (AbilitySystem && !AbilitySystem->IsInActionState(EnterClimbingTag)) {
			HandleEnterClimbMontageEnded(false);
		}
	}

	if (!IsClimbing()) {
		return;
	}

	UWorld* World = GetWorld();
	if (!World) {
		return;
	}

	const float Now = World->GetTimeSeconds();
	if (Now - LastWallHitSweepTime < WallHitSweepInterval) {
		return;
	}

	LastWallHitSweepTime = Now;
	SweepAndStoreWallHits();
}

void UACFClimbingComponent::HandleMovementUpdated(float DeltaSeconds, const FVector& OldLocation, const FVector& OldVelocity)
{
	if (bHasPendingEnterClimb) {
		return;
	}

	if (MovementComponent && !bHasReleasedForwardSinceExit) {
		const bool bForwardReleased = MovementComponent->GetMoveForwardAxis() <= 0.1f;
		if (bForwardReleased) {
			bHasReleasedForwardSinceExit = true;
		}
	}

	if (bAutoClimb && !IsClimbing() && !bWantsToClimb && !bHasPendingLedgeExit && MovementComponent && AbilitySystem) {
			
		const bool bCanClimbDuringCurrentAbility   = CheckClimbingDuringAbilities.Contains(AbilitySystem->GetCurrentActionTag());
		const bool bPressingTowardWall = MovementComponent->GetMoveForwardAxis() > AutoClimbForwardInputThreshold;
		const bool bCanAutoClimbForMovementMode = !bAutoClimbOnlyWhenFalling || MovementComponent->IsFalling();
		const bool bExitForwardReleaseGatePassed = !bRequireForwardReleaseAfterExit || bHasReleasedForwardSinceExit;
		if (bCanClimbDuringCurrentAbility   && bPressingTowardWall && bCanAutoClimbForMovementMode && bExitForwardReleaseGatePassed) {
			TryClimbing();
		}
	}

	if (bWantsToClimb && MovementComponent) {
		if (const UWorld* World = GetWorld()) {
			if (World->GetTimeSeconds() - LastExitRequestTime < ReattachDelayAfterExitRequest) {
				bWantsToClimb = false;
				return;
			}
		}
		MovementComponent->SetMovementMode(EMovementMode::MOVE_Custom, EACFCustomMovementMode::CMOVE_Climbing);
	}
}

void UACFClimbingComponent::HandleMovementModeChanged(EMovementMode PreviousMovementMode, uint8 PreviousCustomMode)
{
	if (!MovementComponent) {
		return;
	}

	if (IsClimbing()) {
		MovementComponent->bOrientRotationToMovement = false;
		MovementComponent->StopMovementImmediately();
		MovementComponent->SetReplicatedClimbingState(true);
		OnClimbingStateChanged.Broadcast(true);
		bExitClimbingRequested = false;
		bHasPendingEnterClimb = false;
		ApplyClimbingMeshOffset();
	}

	if (PreviousMovementMode == EMovementMode::MOVE_Custom && PreviousCustomMode == EACFCustomMovementMode::CMOVE_Climbing) {
		// Hard reset climb intent/state when leaving climbing to avoid sticky wall attraction.
		bWantsToClimb = false;
		CurrentWallHits.Reset();
		CurrentClimbingNormal = FVector::ZeroVector;
		CurrentClimbingPosition = FVector::ZeroVector;
		LastValidClimbingNormalTime = -1000.f;
		bExitClimbingRequested = false;
		bHasPendingEnterClimb = false;
		if (bLockMovementDuringEnterClimbMontage) {
			MovementComponent->SetCanMove(bPrevCanMoveBeforeEnterMontage);
		}

		MovementComponent->bOrientRotationToMovement = true;

		const FRotator StandRotation = FRotator(0., MovementComponent->UpdatedComponent->GetComponentRotation().Yaw, 0.);
		MovementComponent->UpdatedComponent->SetRelativeRotation(StandRotation);

		MovementComponent->StopMovementImmediately();
		MovementComponent->SetReplicatedClimbingState(false);
		OnClimbingStateChanged.Broadcast(false);
		RestoreClimbingMeshOffset();
	}
}

void UACFClimbingComponent::PhysClimbing(float DeltaTime, int32 Iterations)
{
	if (!MovementComponent) {
		return;
	}

	ComputeSurfaceInfo();
	if (CurrentWallHits.IsEmpty()) {
		// First physics frame after entering climbing might happen before TickClimbing.
		// Ensure we have wall hits so the normal isn't left at zero.
		SweepAndStoreWallHits();
		if (UWorld* World = GetWorld()) {
			LastWallHitSweepTime = World->GetTimeSeconds();
		}
		ComputeSurfaceInfo();
	}

	const bool bAuthority = GetOwner() && GetOwner()->HasAuthority();

	if (bAuthority && ShouldStopClimbing()) {
		if (bEnableClimbingDebugDraw) {
			FVector NormalToCheck = CurrentClimbingNormal.GetSafeNormal();
			FVector PredictedNormal = FVector::ZeroVector;
			float CornerAngle = 0.f;
			bool bHasPredicted = false;
			if (GetPredictedClimbingNormal(PredictedNormal)) {
				NormalToCheck = PredictedNormal;
				bHasPredicted = true;
				const float Dot = FVector::DotProduct(CurrentClimbingNormal.GetSafeNormal(), PredictedNormal.GetSafeNormal());
				CornerAngle = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(Dot, -1.f, 1.f)));
			}
			const float EffectiveMaxTiltAngle = FMath::Max(0.f, MaxClimbSurfaceTiltAngle - ClimbSurfaceExitAnticipationAngle);
			const bool bIsOnCeiling = FVector::Parallel(CurrentClimbingNormal, FVector::UpVector);
			const bool bSurfaceTooTilted = bHasPredicted && CornerAngle > EffectiveMaxTiltAngle;
			UE_LOG(LogTemp, Warning, TEXT("[ClimbDebug] Exit by ShouldStopClimbing | ExitRequested=%d | NormalZero=%d | OnCeiling=%d | HasPredicted=%d | CornerAngle=%.2f > Max=%.2f ? %d | Vel=%s"),
				(int32)bExitClimbingRequested,
				(int32)CurrentClimbingNormal.IsZero(),
				(int32)bIsOnCeiling,
				(int32)bHasPredicted,
				CornerAngle,
				EffectiveMaxTiltAngle,
				(int32)bSurfaceTooTilted,
				*MovementComponent->Velocity.ToCompactString());
		}
		StopClimbing(DeltaTime, Iterations);
		return;
	}

	if (bAuthority && ClimbDownToFloor()) {
		if (bEnableClimbingDebugDraw) {
			FFindFloorResult FloorResult;
			MovementComponent->FindFloor(MovementComponent->UpdatedComponent->GetComponentLocation(), FloorResult, false);
			const float FloorDistance = FloorResult.bLineTrace ? FloorResult.LineDist : FloorResult.FloorDist;
			UE_LOG(LogTemp, Warning, TEXT("[ClimbDebug] Exit by ClimbDownToFloor | Walkable=%d | FloorDist=%.2f <= %.2f | MoveForwardAxis=%.2f"),
				(int32)FloorResult.IsWalkableFloor(),
				FloorDistance,
				GroundProximityExitDistance,
				MovementComponent->GetMoveForwardAxis());
		}
		bWantsToClimb = false;
		bExitClimbingRequested = false;
		MovementComponent->SetMovementMode(EMovementMode::MOVE_Walking);
		MovementComponent->StopMovementImmediately();
		return;
	}

	ComputeClimbingVelocity(DeltaTime);

	const FVector OldLocation = MovementComponent->UpdatedComponent->GetComponentLocation();

	MoveAlongClimbingSurface(DeltaTime);

	TryClimbUpLedge();

	if (!MovementComponent->HasAnimRootMotion() && !MovementComponent->CurrentRootMotion.HasOverrideVelocity()) {
		MovementComponent->Velocity = (MovementComponent->UpdatedComponent->GetComponentLocation() - OldLocation) / DeltaTime;
	}

	SnapToClimbingSurface(DeltaTime);
}

// --- Private Climbing Logic ---

void UACFClimbingComponent::SweepAndStoreWallHits()
{
	if (!MovementComponent || !MovementComponent->UpdatedComponent) {
		return;
	}

	const FCollisionShape CollisionShape = FCollisionShape::MakeCapsule(CollisionCapsuleRadius, CollisionCapsuleHalfHeight);

	const FVector Forward = MovementComponent->UpdatedComponent->GetForwardVector();
	const FVector StartOffset = Forward * 20.f;

	const FVector Start = MovementComponent->UpdatedComponent->GetComponentLocation() + StartOffset;
	const FVector End = Start + Forward * ClimbDetectionDistance;

	TArray<FHitResult> Hits;
	const FCollisionObjectQueryParams ObjParams = BuildClimbObjectQueryParams();
	GetWorld()->SweepMultiByObjectType(Hits, Start, End, FQuat::Identity, ObjParams, CollisionShape, ClimbQueryParams);

	if (bEnableClimbingDebugDraw) {
		DrawDebugCapsule(GetWorld(), Start, CollisionCapsuleHalfHeight, CollisionCapsuleRadius, FQuat::Identity, FColor::Green, false, 2.f, 0, 3);
		for (const FHitResult& Hit : Hits) {
			DrawDebugSphere(GetWorld(), Hit.ImpactPoint, 5.f, 8, FColor::Yellow, false, 2.f, 0, .5f);
		}
	}

	CurrentWallHits = Hits;
}

bool UACFClimbingComponent::IsWallClimbable(const FHitResult& Hit, const FVector& Forward) const noexcept
{
	const FVector HorizontalNormal = Hit.Normal.GetSafeNormal2D();

	const float HorizontalDot = FVector::DotProduct(Forward, -HorizontalNormal);
	const float VerticalDot = FVector::DotProduct(Hit.Normal, HorizontalNormal);

	const float HorizontalDegrees = FMath::RadiansToDegrees(FMath::Acos(HorizontalDot));

	const bool bIsCeiling = FMath::IsNearlyZero(VerticalDot);
	const bool bFacing = IsFacingSurface(VerticalDot);

	return HorizontalDegrees <= MinHorizontalDegreesToStartClimbing && !bIsCeiling && bFacing;
}

bool UACFClimbingComponent::EyeHeightTrace(const float TraceDistance) const
{
	if (!MovementComponent || !MovementComponent->UpdatedComponent) {
		return false;
	}

	FHitResult UpperEdgeHit;

	const ACharacter* CharOwner = MovementComponent->GetCharacterOwner();
	if (!CharOwner) {
		return false;
	}

	const float ProbeHeight = LedgeClimbTargetVerticalOffset;
	const FVector Start = MovementComponent->UpdatedComponent->GetComponentLocation()
		+ MovementComponent->UpdatedComponent->GetUpVector() * ProbeHeight;
	const FVector End = Start + (MovementComponent->UpdatedComponent->GetForwardVector() * TraceDistance);

#if WITH_EDITOR
	if (bEnableClimbingDebugDraw) {
		DrawDebugLine(GetWorld(), Start, End, FColor::Red, false, -1.f, 0, 1.f);
	}
#endif

	return GetWorld()->LineTraceSingleByObjectType(UpperEdgeHit, Start, End, BuildClimbObjectQueryParams(), ClimbQueryParams);
}

bool UACFClimbingComponent::IsFacingSurface(const float Steepness) const
{
	constexpr float BASE_LENGTH = 80.f;
	const float SteepnessMultiplier = 1 + (1 - Steepness) * 5;

	return EyeHeightTrace(BASE_LENGTH * SteepnessMultiplier);
}

void UACFClimbingComponent::ComputeSurfaceInfo()
{
	CurrentClimbingNormal = FVector::ZeroVector;
	CurrentClimbingPosition = FVector::ZeroVector;

	if (CurrentWallHits.IsEmpty() || !MovementComponent || !MovementComponent->UpdatedComponent) {
		return;
	}

	const FVector Start = MovementComponent->UpdatedComponent->GetComponentLocation();
	const FCollisionShape CollisionSphere = FCollisionShape::MakeSphere(6);

	for (const auto& Hit : CurrentWallHits) {
		const FVector End = Start + (Hit.ImpactPoint - Start).GetSafeNormal() * 120.f;

		FHitResult AssistHit;
		GetWorld()->SweepSingleByObjectType(AssistHit, Start, End, FQuat::Identity, BuildClimbObjectQueryParams(), CollisionSphere, ClimbQueryParams);

		CurrentClimbingPosition += AssistHit.ImpactPoint;
		CurrentClimbingNormal += AssistHit.Normal;
	}

	CurrentClimbingPosition /= CurrentWallHits.Num();
	CurrentClimbingNormal = CurrentClimbingNormal.GetSafeNormal();
	if (!CurrentClimbingNormal.IsZero()) {
		if (const UWorld* World = GetWorld()) {
			LastValidClimbingNormalTime = World->GetTimeSeconds();
		}
	}

#if WITH_EDITOR
	if (bEnableClimbingDebugDraw) {
		DrawDebugSphere(GetWorld(), CurrentClimbingPosition, 5.f, 8, FColor::Blue, false, -1.f, 0, .5f);
		DrawDebugLine(GetWorld(), CurrentClimbingPosition, CurrentClimbingPosition + 10.f * CurrentClimbingNormal, FColor::Blue, false, -1.f, 0, 1.f);
	}
#endif
}

void UACFClimbingComponent::ComputeClimbingVelocity(float DeltaTime)
{
	MovementComponent->RestorePreAdditiveRootMotionVelocityForClimbing();

	if (!MovementComponent->HasAnimRootMotion() && !MovementComponent->CurrentRootMotion.HasOverrideVelocity()) {
		MovementComponent->CalcVelocity(DeltaTime, .0f, false, BrakingDecelerationClimbing);
	}

	MovementComponent->ApplyRootMotionToVelocityForClimbing(DeltaTime);
}

bool UACFClimbingComponent::ShouldStopClimbing()
{
	const bool bNormalLost = CurrentClimbingNormal.IsZero();
	bool bNormalLostTooLong = false;
	if (bNormalLost) {
		const UWorld* World = GetWorld();
		const float TimeSinceLastValidNormal = World ? (World->GetTimeSeconds() - LastValidClimbingNormalTime) : BIG_NUMBER;
		bNormalLostTooLong = TimeSinceLastValidNormal > LostSurfaceNormalGraceTime;
	}

	const bool bIsOnCeiling = FVector::Parallel(CurrentClimbingNormal, FVector::UpVector);
	bool bCornerTooSharp = false;
	if (!bNormalLost) {
		FVector PredictedNormal = FVector::ZeroVector;
		if (GetPredictedClimbingNormal(PredictedNormal)) {
			const float Dot = FVector::DotProduct(CurrentClimbingNormal.GetSafeNormal(), PredictedNormal.GetSafeNormal());
			const float CornerAngle = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(Dot, -1.f, 1.f)));
			const float EffectiveMaxCornerAngle = FMath::Max(0.f, MaxClimbSurfaceTiltAngle - ClimbSurfaceExitAnticipationAngle);
			bCornerTooSharp = CornerAngle > EffectiveMaxCornerAngle;
		}
	}

	const bool bInputSaysStop = bExitClimbingRequested;
	return bInputSaysStop || bNormalLostTooLong || bIsOnCeiling || bCornerTooSharp;
}

void UACFClimbingComponent::StopClimbing(float DeltaTime, int32 Iterations)
{
	bWantsToClimb = false;
	MovementComponent->SetMovementMode(EMovementMode::MOVE_Falling);
	MovementComponent->StartNewPhysicsForClimbing(DeltaTime, Iterations);
}

void UACFClimbingComponent::MoveAlongClimbingSurface(float DeltaTime)
{
	const FVector Adjusted = MovementComponent->Velocity * DeltaTime;

	FHitResult Hit(1.f);
	MovementComponent->SafeMoveUpdatedComponent(Adjusted, GetClimbingRotation(DeltaTime), true, Hit);

	if (Hit.Time < 1.f) {
		MovementComponent->HandleImpactForClimbing(Hit, DeltaTime, Adjusted);
		MovementComponent->SlideAlongSurfaceForClimbing(Adjusted, (1.f - Hit.Time), Hit.Normal, Hit, true);
	}
}

void UACFClimbingComponent::SnapToClimbingSurface(float DeltaTime) const
{
	const FVector Forward = MovementComponent->UpdatedComponent->GetForwardVector();
	const FVector Location = MovementComponent->UpdatedComponent->GetComponentLocation();
	const FQuat Rotation = MovementComponent->UpdatedComponent->GetComponentQuat();

	const FVector ForwardDifference = (CurrentClimbingPosition - Location).ProjectOnTo(Forward);
	const FVector Offset = -CurrentClimbingNormal * (ForwardDifference.Length() - DistanceFromSurface);

	MovementComponent->UpdatedComponent->MoveComponent(Offset * ClimbingSnapSpeed * DeltaTime, Rotation, true);
}

FQuat UACFClimbingComponent::GetClimbingRotation(float DeltaTime) const
{
	const FQuat Current = MovementComponent->UpdatedComponent->GetComponentQuat();

	if (MovementComponent->HasAnimRootMotion() || MovementComponent->CurrentRootMotion.HasOverrideVelocity()) {
		return Current;
	}

	const FQuat Target = FRotationMatrix::MakeFromX(-CurrentClimbingNormal).ToQuat();
	return FMath::QInterpTo(Current, Target, DeltaTime, ClimbingRotationSpeed);
}

bool UACFClimbingComponent::ClimbDownToFloor() const
{
	FFindFloorResult FloorResult;
	MovementComponent->FindFloor(MovementComponent->UpdatedComponent->GetComponentLocation(), FloorResult, false);
	if (!FloorResult.IsWalkableFloor()) {
		return false;
	}

	const float FloorDistance = FloorResult.bLineTrace ? FloorResult.LineDist : FloorResult.FloorDist;
	const bool bNearFloor = FloorDistance <= GroundProximityExitDistance;
	const bool bPressingDown = MovementComponent->GetMoveForwardAxis() < -0.1f;

	return bPressingDown && bNearFloor;
}

bool UACFClimbingComponent::TryClimbUpLedge()
{
	const float UpSpeed = FVector::DotProduct(MovementComponent->Velocity, MovementComponent->UpdatedComponent->GetUpVector());
	const bool bIsMovingUp = UpSpeed >= MaxClimbingSpeed / 10;

	const bool bReachedEdge = HasReachedEdge();
	if (!bIsMovingUp || !bReachedEdge) {
		return false;
	}

	FVector LedgeClimbLocation = FVector::ZeroVector;
	if (!CanMoveToLedgeClimbLocation(&LedgeClimbLocation)) {
		FVector VelocityNoUp = MovementComponent->Velocity;
		VelocityNoUp.Z = FMath::Min(0.f, VelocityNoUp.Z);
		MovementComponent->Velocity = VelocityNoUp;
		return false;
	}

	if (GetOwner()) {
		const FRotator StandRotation = FRotator(0, MovementComponent->UpdatedComponent->GetComponentRotation().Yaw, 0);
		MovementComponent->UpdatedComponent->SetRelativeRotation(StandRotation);

		// Defer final snap on top until montage end.
		bHasPendingLedgeExit = true;
		PendingLedgeExitLocation = LedgeClimbLocation;
		PendingLedgeExitTriggerLocation = MovementComponent->UpdatedComponent->GetComponentLocation();

		// Keep locomotion simulation active for root motion/motion warping while
		// preventing gravity from pulling the character down during the montage.
		MovementComponent->SetMovementMode(EMovementMode::MOVE_Flying);
		MovementComponent->StopMovementImmediately();
		bWantsToClimb = false;
		CurrentWallHits.Reset();
		CurrentClimbingNormal = FVector::ZeroVector;
		CurrentClimbingPosition = FVector::ZeroVector;

		if (AnimInstance) {
			// Trigger Ability ExitLedge
			if (!AbilitySystem) {
				return false;
			}
			AbilitySystem->TriggerAction(ExitClimbingTag, EActionPriority::EHighest, false);
		}
		return true;
	}

	return false;
}

bool UACFClimbingComponent::HasReachedEdge() const
{
	const ACharacter* CharOwner = MovementComponent->GetCharacterOwner();
	if (!CharOwner) {
		return false;
	}

	return !EyeHeightTrace(LedgeEdgeTraceDistance);
}

bool UACFClimbingComponent::CanMoveToLedgeClimbLocation(FVector* OutLedgeClimbLocation) const
{
	const ACharacter* CharOwner = MovementComponent->GetCharacterOwner();
	if (!CharOwner) {
		return false;
	}

	const FVector VerticalOffset = FVector::UpVector * LedgeClimbTargetVerticalOffset;
	const FVector HorizontalOffset = MovementComponent->UpdatedComponent->GetForwardVector() * LedgeClimbTargetForwardOffset;

	const FVector ProbeLocation = MovementComponent->UpdatedComponent->GetComponentLocation() + HorizontalOffset + VerticalOffset;

	if (!IsLocationWalkable(GetWorld(), ProbeLocation, MovementComponent->GetWalkableFloorZ(), ClimbQueryParams)) {
		return false;
	}

	// Snap final target to the actual floor hit so the capsule lands on top.
	FHitResult FloorHit = CheckFloor(GetWorld(), ProbeLocation, 300.f, ClimbQueryParams);
	if (!FloorHit.bBlockingHit || FloorHit.Normal.Z < MovementComponent->GetWalkableFloorZ()) {
		return false;
	}

	const UCapsuleComponent* Capsule = CharOwner->GetCapsuleComponent();
	const FVector LocationToCheck = FloorHit.ImpactPoint + FVector::UpVector * (Capsule->GetScaledCapsuleHalfHeight() + 2.f);
	if (OutLedgeClimbLocation) {
		*OutLedgeClimbLocation = LocationToCheck;
	}

	FHitResult CapsuleHit;
	const FVector CapsuleStartCheck = LocationToCheck - HorizontalOffset;

#if WITH_EDITOR
	if (bEnableClimbingDebugDraw) {
		DrawDebugCapsule(GetWorld(), LocationToCheck, Capsule->GetScaledCapsuleHalfHeight(), Capsule->GetScaledCapsuleRadius(), FQuat::Identity, FColor::Red, false, -1, 0, 2.f);
	}
#endif

	const bool bBlocked = GetWorld()->SweepSingleByObjectType(
		CapsuleHit, CapsuleStartCheck, LocationToCheck, FQuat::Identity, BuildClimbObjectQueryParams(), Capsule->GetCollisionShape(), ClimbQueryParams);
	return !bBlocked;
}

void UACFClimbingComponent::HandleEnterClimbMontageEnded(bool bInterrupted)
{
	if (!GetOwner() || !GetOwner()->HasAuthority()) {
		return;
	}

	if (bLockMovementDuringEnterClimbMontage && MovementComponent) {
		MovementComponent->SetCanMove(bPrevCanMoveBeforeEnterMontage);
	}

	bHasPendingEnterClimb = false;
	if (bInterrupted || !MovementComponent || !MovementComponent->UpdatedComponent) {
		bWantsToClimb = false;
		return;
	}

	// Revalidate wall right after enter montage, then actually attach.
	SweepAndStoreWallHits();
	const FVector Forward = MovementComponent->UpdatedComponent->GetForwardVector();
	bool bCanAttach = false;
	for (const FHitResult& Hit : CurrentWallHits) {
		if (IsWallClimbable(Hit, Forward)) {
			bCanAttach = true;
			break;
		}
	}

	bWantsToClimb = bCanAttach;
}

void UACFClimbingComponent::PerformImmediateExitClimbing()
{
	if (!MovementComponent || !GetOwner() || !GetOwner()->HasAuthority() || !IsClimbing()) {
		return;
	}

	bWantsToClimb = false;
	bExitClimbingRequested = false;
	bHasPendingEnterClimb = false;
	if (bLockMovementDuringEnterClimbMontage && MovementComponent) {
		MovementComponent->SetCanMove(bPrevCanMoveBeforeEnterMontage);
	}

	FFindFloorResult FloorResult;
	MovementComponent->FindFloor(MovementComponent->UpdatedComponent->GetComponentLocation(), FloorResult, false);
	const bool bHasWalkableFloor = FloorResult.IsWalkableFloor()
		&& (FloorResult.bLineTrace ? FloorResult.LineDist : FloorResult.FloorDist) <= GroundProximityExitDistance;

	MovementComponent->SetMovementMode(bHasWalkableFloor ? EMovementMode::MOVE_Walking : EMovementMode::MOVE_Falling);
	MovementComponent->StopMovementImmediately();
}

void UACFClimbingComponent::FinalizePendingLedgeExit()
{
	if (!bHasPendingLedgeExit || !MovementComponent) {
		return;
	}

	ACharacter* CharOwner = MovementComponent->GetCharacterOwner();
	if (CharOwner) {
		CharOwner->StopJumping();
		// Use the validated ledge-top target when available, then optionally apply designer forward offset.
		const FVector BaseExitLocation = PendingLedgeExitLocation.IsNearlyZero()
			? CharOwner->GetActorLocation()
			: PendingLedgeExitLocation;

		// Keep ledge validation anticipation on Z (VerticalOffset) separate from actual warp target height.
		// Z must come from the validated ledge-top location, while forward comes from ledge settings.
		const FVector ForwardOffset = CharOwner->GetActorForwardVector() * LedgeClimbTargetForwardOffset;
		WarpLocation = BaseExitLocation+  FVector(0.f,0.f,LedgeExitVerticalOffset);
	}
}

void UACFClimbingComponent::LedgeExit()
{
	ACharacter* CharOwner = MovementComponent->GetCharacterOwner();
	if (CharOwner)
	{
		CharOwner->StopJumping();
		MovementComponent->Velocity = FVector::ZeroVector;
		MovementComponent->SetMovementMode(EMovementMode::MOVE_Walking);
		MovementComponent->StopMovementImmediately();
		MovementComponent->SetReplicatedClimbingState(false);
		bHasPendingLedgeExit = false;
		PendingLedgeExitLocation = FVector::ZeroVector;
		PendingLedgeExitTriggerLocation = FVector::ZeroVector;
	}
}

bool UACFClimbingComponent::IsLocationWalkable(const UWorld* World, const FVector& LocationToCheck, const float WalkableHeight, const FCollisionQueryParams& QueryParams) const
{
	const FVector CheckEnd = LocationToCheck + (FVector::DownVector * 250.);
	FHitResult LedgeHit;
	const bool bHitLedgeGround = World->LineTraceSingleByObjectType(LedgeHit, LocationToCheck, CheckEnd, BuildFloorObjectQueryParams(), QueryParams);

#if WITH_EDITOR
	if (bEnableClimbingDebugDraw) {
		DrawDebugLine(World, LocationToCheck, CheckEnd, FColor::Red, false, -1.f, 0, 4.f);
	}
#endif

	return bHitLedgeGround && LedgeHit.Normal.Z >= WalkableHeight;
}

FHitResult UACFClimbingComponent::CheckFloor(const UWorld* World, const FVector& Location, float MaxDistance, const FCollisionQueryParams& QueryParams) const
{
	FHitResult Hit{};
	const FVector End = Location + FVector::DownVector * MaxDistance;
	World->LineTraceSingleByObjectType(Hit, Location, End, BuildFloorObjectQueryParams(), QueryParams);
	return Hit;
}

bool UACFClimbingComponent::GetPredictedClimbingNormal(FVector& OutPredictedNormal) const
{
	OutPredictedNormal = FVector::ZeroVector;

	if (!MovementComponent || !MovementComponent->UpdatedComponent || ClimbSurfaceExitLookAheadDistance <= KINDA_SMALL_NUMBER) {
		return false;
	}

	UWorld* World = GetWorld();
	if (!World) {
		return false;
	}

	// Predict side wall while moving left/right on the climbing surface.
	// This catches true cube corners without breaking vertical up/down movement.
	const FVector ClimbingRightDir = GetClimbingRightDirection().GetSafeNormal();
	if (ClimbingRightDir.IsNearlyZero()) {
		return false;
	}

	// Determine side from actual movement first (symmetric for left/right on any wall orientation).
	const float LateralSpeed = FVector::DotProduct(MovementComponent->Velocity, ClimbingRightDir);
	float SideSign = 0.f;
	if (FMath::Abs(LateralSpeed) > KINDA_SMALL_NUMBER) {
		SideSign = FMath::Sign(LateralSpeed);
	}
	else {
		// Fallback to raw input only when velocity has no lateral component yet.
		const float RightInput = MovementComponent->GetMoveRightAxis();
		if (FMath::Abs(RightInput) <= 0.1f) {
			return false;
		}
		SideSign = FMath::Sign(RightInput);
	}

	const FVector SideDir = ClimbingRightDir * SideSign;
	const FVector ForwardDir = MovementComponent->UpdatedComponent->GetForwardVector().GetSafeNormal();
	const FVector ProbeOrigin = MovementComponent->UpdatedComponent->GetComponentLocation()
		+ (ForwardDir * ClimbCornerCheckForwardOffset)
		+ (SideDir * ClimbSurfaceExitLookAheadDistance);

	// Build a directional probe based on current climbing normal:
	// start slightly away from the wall, then raycast toward it at the lateral-future point.
	const FVector CurrentNormal = CurrentClimbingNormal.GetSafeNormal();
	if (CurrentNormal.IsNearlyZero()) {
		return false;
	}

	const float ProbeBackoffFromWall = 20.f;
	const FVector ProbeStart = ProbeOrigin + (CurrentNormal * ProbeBackoffFromWall);
	const FVector ProbeEnd = ProbeOrigin + (-CurrentNormal * ClimbDetectionDistance);
	FHitResult ProbeHit;
	const bool bHit = World->LineTraceSingleByObjectType(
		ProbeHit,
		ProbeStart,
		ProbeEnd,
		BuildClimbObjectQueryParams(),
		ClimbQueryParams);

#if WITH_EDITOR
	if (bEnableClimbingDebugDraw) {
		const FColor C = bHit ? FColor::Cyan : FColor::Silver;
		DrawDebugLine(World, ProbeStart, ProbeEnd, C, false, 0.05f, 0, 1.f);
		if (bHit) {
			DrawDebugSphere(World, ProbeHit.ImpactPoint, 6.f, 8, C, false, 0.05f, 0, 1.f);
		}
	}
#endif

	if (!bHit || ProbeHit.Normal.IsNearlyZero()) {
		return false;
	}
	OutPredictedNormal = ProbeHit.Normal.GetSafeNormal();
	return true;
}

FCollisionObjectQueryParams UACFClimbingComponent::BuildClimbObjectQueryParams() const
{
	FCollisionObjectQueryParams Params;
	for (const TEnumAsByte<EObjectTypeQuery>& ObjType : ClimbableObjectTypes)
	{
		Params.AddObjectTypesToQuery(UEngineTypes::ConvertToCollisionChannel(ObjType));
	}
	return Params;
}

FCollisionObjectQueryParams UACFClimbingComponent::BuildFloorObjectQueryParams() const
{
	FCollisionObjectQueryParams Params;
	Params.AddObjectTypesToQuery(ECC_WorldStatic);
	Params.AddObjectTypesToQuery(ECC_WorldDynamic);
	for (const TEnumAsByte<EObjectTypeQuery>& ObjType : ClimbableObjectTypes)
	{
		Params.AddObjectTypesToQuery(UEngineTypes::ConvertToCollisionChannel(ObjType));
	}
	return Params;
}

void UACFClimbingComponent::TryBindExitClimbingInputAction()
{
	if (bExitInputActionBound || !ExitClimbingInputAction) {
		return;
	}

	ACharacter* Character = Cast<ACharacter>(GetOwner());
	if (!Character || !Character->InputComponent) {
		return;
	}

	if (UEnhancedInputComponent* EnhancedInput = Cast<UEnhancedInputComponent>(Character->InputComponent)) {
		EnhancedInput->BindAction(ExitClimbingInputAction, ETriggerEvent::Started, this, &UACFClimbingComponent::OnExitClimbingActionTriggered);
		bExitInputActionBound = true;
	}
}

void UACFClimbingComponent::ApplyClimbingMeshOffset()
{
	ACharacter* CharOwner = MovementComponent ? MovementComponent->GetCharacterOwner() : nullptr;
	if (!CharOwner || !CharOwner->GetMesh()) {
		return;
	}

	if (!bHasStoredMeshRelativeLocation) {
		DefaultMeshRelativeLocation = CharOwner->GetMesh()->GetRelativeLocation();
		bHasStoredMeshRelativeLocation = true;
	}

	const FVector NewMeshLocation = DefaultMeshRelativeLocation + FVector(MeshForwardOffsetOnClimbing, 0.f, 0.f);
	CharOwner->GetMesh()->SetRelativeLocation(NewMeshLocation);
}

void UACFClimbingComponent::RestoreClimbingMeshOffset()
{
	ACharacter* CharOwner = MovementComponent ? MovementComponent->GetCharacterOwner() : nullptr;
	if (!CharOwner || !CharOwner->GetMesh() || !bHasStoredMeshRelativeLocation) {
		return;
	}

	CharOwner->GetMesh()->SetRelativeLocation(DefaultMeshRelativeLocation);
}
