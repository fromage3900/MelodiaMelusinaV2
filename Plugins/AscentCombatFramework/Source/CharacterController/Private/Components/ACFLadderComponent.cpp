// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFLadderComponent.h"

#include "ACFActionTypes.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "Components/ACFCharacterMovementComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Character.h"
#include "GameplayTagContainer.h"
#include "Kismet/KismetMathLibrary.h"
#include "MotionWarpingComponent.h"
#include "Components/ACFEquipmentComponent.h"

UACFLadderComponent::UACFLadderComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UACFLadderComponent::BeginPlay()
{
	Super::BeginPlay();
	CacheOwnerComponents();
}

// ────────────────────────────────────────────────────────────────────────────
// Public API
// ────────────────────────────────────────────────────────────────────────────

void UACFLadderComponent::SetLadder(AActor* InLadder)
{
	Ladder = InLadder;
	OnLadderSet.Broadcast(InLadder);
}

void UACFLadderComponent::InitiateLadderClimb()
{
	if (!LadderClimbChecks())
	{
		return;
	}

	StartLadderClimb();
}

void UACFLadderComponent::StartLadderClimb()
{
	if (!IsValid(Ladder) || !PlayerCharacterMovement)
	{
		return;
	}

	// Determine if the player is closer to the bottom or the top of the ladder.
	// We compare the player's Z location to the midpoint between the two reach points.
	const USceneComponent* BottomPoint = GetLadderReachPoint(true);
	const USceneComponent* TopPoint = GetLadderReachPoint(false);

	if (BottomPoint && TopPoint)
	{
		const float PlayerZ = GetOwner()->GetActorLocation().Z;
		const float BottomZ = BottomPoint->GetComponentLocation().Z;
		const float TopZ = TopPoint->GetComponentLocation().Z;
		const float MidZ = (BottomZ + TopZ) * 0.5f;
		bPlayerAtBottom = PlayerZ <= MidZ;
	}
	else
	{
		bPlayerAtBottom = true;
	}

	InternalStart(bPlayerAtBottom);
}

void UACFLadderComponent::ExitLadderClimb()
{
	InternalExit();
}

void UACFLadderComponent::EndLadderClimb()
{
	bIsClimbing = false;
	bCanClimb = false;

	if (PlayerCharacterMovement)
	{
		PlayerCharacterMovement->SetMovementMode(EMovementMode::MOVE_Walking);
	}

	if (AbilityComponent)
	{
		AbilityComponent->UnlockActionsTrigger();
	}

	OnLadderClimbEnded.Broadcast();
}

void UACFLadderComponent::ClimbStartCompleted()
{
	bIsClimbing = true;
	bCanClimb = true;
	OnLadderClimbStarted.Broadcast();
}

void UACFLadderComponent::ClimbEndCompleted()
{
	EndLadderClimb();
}

void UACFLadderComponent::ClimbingCompleted()
{
	bIsClimbing = false;
	bCanClimb = false;

	if (AbilityComponent)
	{
		AbilityComponent->UnlockActionsTrigger();
	}
}

void UACFLadderComponent::HandleClimbInput(float AxisValue)
{
	if (!bCanClimb || !bIsClimbing)
	{
		return;
	}

	if (!PlayerCharacterMovement)
	{
		return;
	}

	const bool bIsOnLadder = PlayerCharacterMovement->MovementMode == EMovementMode::MOVE_Custom
		&& PlayerCharacterMovement->CustomMovementMode == 1;

	if (!bIsOnLadder)
	{
		return;
	}

	InternalClimb(AxisValue);
}

// ────────────────────────────────────────────────────────────────────────────
// Private helpers
// ────────────────────────────────────────────────────────────────────────────

void UACFLadderComponent::CacheOwnerComponents()
{
	ACharacter* Character = Cast<ACharacter>(GetOwner());
	if (!Character)
	{
		UE_LOG(LogTemp, Error, TEXT("ACFLadderComponent: Owner is not an ACharacter (%s)."), *GetOwner()->GetName());
		return;
	}

	PlayerCharacterMovement = Character->GetComponentByClass<UACFCharacterMovementComponent>();
	PlayerSkeletalMesh = Character->GetMesh();
	PlayerCapsule = Character->GetCapsuleComponent();
	AbilityComponent = Character->GetComponentByClass<UACFAbilitySystemComponent>();
	MotionWarpingComp = Character->GetComponentByClass<UMotionWarpingComponent>();

	if (!PlayerCharacterMovement)
	{
		UE_LOG(LogTemp, Warning, TEXT("ACFLadderComponent: No ACFCharacterMovementComponent found on %s."), *Character->GetName());
	}
	if (!AbilityComponent)
	{
		UE_LOG(LogTemp, Warning, TEXT("ACFLadderComponent: No ACFAbilitySystemComponent found on %s."), *Character->GetName());
	}
	if (!MotionWarpingComp)
	{
		UE_LOG(LogTemp, Warning, TEXT("ACFLadderComponent: No UMotionWarpingComponent found on %s. Motion warping will be skipped."), *Character->GetName());
	}
}

bool UACFLadderComponent::LadderClimbChecks() const
{
	// 1. Not currently performing any ability action
	if (AbilityComponent && AbilityComponent->IsPerformingAction())
	{
		return false;
	}

	// 2. Not already climbing
	if (bIsClimbing)
	{
		return false;
	}

	// 3. Not falling (must be grounded)
	if (PlayerCharacterMovement && PlayerCharacterMovement->IsFalling())
	{
		return false;
	}

	// 4. Ladder reference is valid
	if (!IsValid(Ladder))
	{
		return false;
	}

	// 5. Ladder reports valid placement (reads Blueprint bool property via reflection)
	if (!GetLadderHasValidPlacement())
	{
		return false;
	}

	// 6. Player is facing the ladder within tolerance
	if (!DirectionalCheck())
	{
		return false;
	}

	// 7. Player is within interact distance
	if (!DistanceCheck())
	{
		return false;
	}

	return true;
}

bool UACFLadderComponent::DistanceCheck() const
{
	if (!IsValid(Ladder) || !GetOwner())
	{
		return false;
	}

	// Find the ladder root component to use as reference point
	const USceneComponent* LadderRoot = FindLadderComponentByName(LadderRootName);
	const FVector LadderLocation = LadderRoot
		? LadderRoot->GetComponentLocation()
		: Ladder->GetActorLocation();

	const FVector PlayerLocation = GetOwner()->GetActorLocation();

	// XY-only distance check (Z not relevant for approach detection)
	const float DistanceXY = FVector::DistXY(PlayerLocation, LadderLocation);
	return DistanceXY <= InteractDistance;
}

bool UACFLadderComponent::DirectionalCheck() const
{
	if (!IsValid(Ladder) || !GetOwner())
	{
		return false;
	}

	const FVector ToLadder = (Ladder->GetActorLocation() - GetOwner()->GetActorLocation()).GetSafeNormal();
	const FVector PlayerForward = GetOwner()->GetActorForwardVector();

	const float DotProduct = FVector::DotProduct(PlayerForward, ToLadder);
	const float AngleDegrees = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(DotProduct, -1.f, 1.f)));

	return AngleDegrees <= FacingTolerance;
}

void UACFLadderComponent::MotionWarp()
{
	if (!MotionWarpingComp || !IsValid(Ladder))
	{
		return;
	}

	const USceneComponent* ReachPoint = GetLadderReachPoint(bPlayerAtBottom);
	if (!ReachPoint)
	{
		UE_LOG(LogTemp, Warning, TEXT("ACFLadderComponent: Could not find ReachPoint on ladder %s."), *Ladder->GetName());
		return;
	}

	const FVector ReachLocation = ReachPoint->GetComponentLocation();

	// Apply Z offset from the appropriate reach point
	const double ZOffset = bPlayerAtBottom ? BottomStartZOffset : TopStartZOffset;
	const FVector WarpLocation = FVector(ReachLocation.X, ReachLocation.Y, ReachLocation.Z + ZOffset);

	// Build warp rotation: keep the ladder's yaw so the character faces it correctly,
	// but preserve the player's pitch/roll (usually 0) for natural orientation.
	const FRotator LadderRotation = Ladder->GetActorRotation();
	const FRotator WarpRotation = FRotator(0.0, LadderRotation.Yaw, 0.0);

	FMotionWarpingTarget WarpTarget;
	WarpTarget.Name = WarpTargetName;
	WarpTarget.Location = WarpLocation;
	WarpTarget.Rotation = WarpRotation;

	MotionWarpingComp->AddOrUpdateWarpTarget(WarpTarget);
}

void UACFLadderComponent::InternalStart(bool bAtBottom)
{
	if (!AbilityComponent || !PlayerCharacterMovement)
	{
		return;
	}

	bPlayerAtBottom = bAtBottom;

	// Lock ability actions while the start montage plays
	AbilityComponent->LockActionsTrigger();

	// Sheath any equipped weapon before climbing
	if (UACFEquipmentComponent* Equipment = GetOwner()->GetComponentByClass<UACFEquipmentComponent>())
	{
		Equipment->SheathCurrentWeapon();
	}

	// Set up the motion warp target on the ladder reach point
	MotionWarp();

	// Switch to custom movement mode (mode 1 = ladder)
	PlayerCharacterMovement->SetMovementMode(EMovementMode::MOVE_Custom, 1);

	// Build payload: tag indicates climb direction (up from bottom, down from top)
	FACFAbilityPayload Payload;
	Payload.bIsValid = true;
	Payload.PayloadTag = bAtBottom ? ClimbUpTag : ClimbDownTag;

	AbilityComponent->TriggerActionWithPayload(StartAbility, Payload, EActionPriority::EHigh, false);
}

void UACFLadderComponent::InternalClimb(float AxisValue)
{
	if (!AbilityComponent)
	{
		return;
	}

	bCanClimb = false;
	AbilityComponent->UnlockActionsTrigger();

	// Build payload with climb direction tag
	FACFAbilityPayload Payload;
	Payload.bIsValid = true;
	Payload.FloatPayload = AxisValue;
	Payload.PayloadTag = AxisValue >= 0.f ? ClimbUpTag : ClimbDownTag;

	AbilityComponent->TriggerActionWithPayload(ClimbLoopTag, Payload, EActionPriority::EHigh, false);
}

void UACFLadderComponent::InternalExit()
{
	if (!AbilityComponent)
	{
		return;
	}

	bCanClimb = false;
	bIsClimbing = false;

	// Reposition the character to the correct exit point
	if (GetOwner() && IsValid(Ladder))
	{
		const double ZOffset = bPlayerAtBottom ? BottomStartZOffset : TopStartZOffset;
		const FVector CurrentLocation = GetOwner()->GetActorLocation();
		const FVector ExitLocation = FVector(CurrentLocation.X, CurrentLocation.Y, CurrentLocation.Z + ZOffset);
		GetOwner()->SetActorLocation(ExitLocation, false, nullptr, ETeleportType::None);
	}

	AbilityComponent->UnlockActionsTrigger();
	AbilityComponent->TriggerAction(EndAbilityTag, EActionPriority::EHigh, false);
}

USceneComponent* UACFLadderComponent::FindLadderComponentByName(FName ComponentName) const
{
	if (!IsValid(Ladder))
	{
		return nullptr;
	}

	TArray<USceneComponent*> Components;
	Ladder->GetComponents<USceneComponent>(Components);

	for (USceneComponent* Comp : Components)
	{
		if (Comp && Comp->GetFName() == ComponentName)
		{
			return Comp;
		}
	}

	// Blueprint components may have an auto-generated suffix (e.g. "ReachPoint-Top_GEN_VARIABLE")
	// Fall back to partial name match if exact match fails.
	const FString SearchName = ComponentName.ToString();
	for (USceneComponent* Comp : Components)
	{
		if (Comp && Comp->GetFName().ToString().StartsWith(SearchName))
		{
			return Comp;
		}
	}

	return nullptr;
}

bool UACFLadderComponent::GetLadderHasValidPlacement() const
{
	if (!IsValid(Ladder))
	{
		return false;
	}

	const FBoolProperty* Prop = FindFProperty<FBoolProperty>(
		Ladder->GetClass(), LadderValidPlacementPropertyName);

	if (Prop)
	{
		return Prop->GetPropertyValue_InContainer(Ladder.Get());
	}

	// If the property is not found (e.g., the ladder actor doesn't expose it),
	// assume placement is valid so the system doesn't silently break.
	return true;
}

USceneComponent* UACFLadderComponent::GetLadderReachPoint(bool bBottom) const
{
	return FindLadderComponentByName(bBottom ? ReachPointBottomName : ReachPointTopName);
}
