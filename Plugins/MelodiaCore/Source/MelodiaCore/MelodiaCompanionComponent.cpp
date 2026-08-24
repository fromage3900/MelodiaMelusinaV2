#include "MelodiaCompanionComponent.h"

#include "Animation/AnimInstance.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/Actor.h"
#include "MelodiaCompanionWardrobeBridge.h"

UMelodiaCompanionComponent::UMelodiaCompanionComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
}

void UMelodiaCompanionComponent::BeginPlay()
{
	Super::BeginPlay();

	ApplyCompanionDefinition();

	if (UWorld* World = GetWorld())
	{
		ReactivitySubsystem = World->GetSubsystem<UMelodiaRhythmReactivitySubsystem>();
		if (ReactivitySubsystem)
		{
			ReactivitySubsystem->OnSignalChanged.AddDynamic(this, &ThisClass::HandleRhythmSignal);
		}
	}

	if (FollowTarget)
	{
		SetStateInternal(EMelodiaCompanionBehaviorState::Follow);
	}
}

void UMelodiaCompanionComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (ReactivitySubsystem)
	{
		ReactivitySubsystem->OnSignalChanged.RemoveDynamic(this, &ThisClass::HandleRhythmSignal);
		ReactivitySubsystem = nullptr;
	}

	Super::EndPlay(EndPlayReason);
}

void UMelodiaCompanionComponent::TickComponent(const float DeltaTime, const ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (!bDriveOwnerTransform || !GetOwner())
	{
		return;
	}

	if (CurrentState == EMelodiaCompanionBehaviorState::Follow)
	{
		if (FollowTarget)
		{
			DriveOwnerToward(GetDesiredNavigationLocation(), ActiveDefinition.FollowAcceptanceRadius, DeltaTime);
		}
		else
		{
			SetStateInternal(EMelodiaCompanionBehaviorState::Idle);
		}
	}
	else if (CurrentState == EMelodiaCompanionBehaviorState::Seek)
	{
		if (GuidanceTarget)
		{
			DriveOwnerToward(GuidanceTarget->GetActorLocation(), ActiveDefinition.FollowAcceptanceRadius, DeltaTime);
		}
		else
		{
			SetStateInternal(FollowTarget ? EMelodiaCompanionBehaviorState::Follow : EMelodiaCompanionBehaviorState::Idle);
		}
	}
}

bool UMelodiaCompanionComponent::ApplyCompanionDefinition()
{
	if (CompanionDefinition.IsNull())
	{
		return false;
	}

	UMelodiaCompanionDefinitionAsset* LoadedDefinition = CompanionDefinition.LoadSynchronous();
	return SetCompanionDefinition(LoadedDefinition);
}

bool UMelodiaCompanionComponent::SetCompanionDefinition(UMelodiaCompanionDefinitionAsset* InDefinition)
{
	if (!InDefinition)
	{
		return false;
	}

	FText ValidationError;
	if (!InDefinition->Definition.IsValid(&ValidationError))
	{
		return false;
	}

	ActiveDefinition = InDefinition->Definition;
	RhythmResponse = FMath::Clamp(RhythmResponse, 0.0f, 2.0f);
	return !GetOwner() || ApplyCompanionPresentation();
}

USkeletalMeshComponent* UMelodiaCompanionComponent::FindPresentationMeshComponent() const
{
	AActor* Owner = GetOwner();
	return Owner ? Owner->FindComponentByClass<USkeletalMeshComponent>() : nullptr;
}

bool UMelodiaCompanionComponent::ApplyCompanionPresentation()
{
	USkeletalMeshComponent* PresentationMesh = FindPresentationMeshComponent();
	if (!PresentationMesh)
	{
		return false;
	}

	USkeletalMesh* SkeletalMesh = ActiveDefinition.NPCDefinition.SkeletalMesh.LoadSynchronous();
	if (!SkeletalMesh)
	{
		return false;
	}

	UClass* AnimationClass = nullptr;
	if (!ActiveDefinition.AnimationBlueprint.IsNull())
	{
		AnimationClass = ActiveDefinition.AnimationBlueprint.LoadSynchronous();
		if (!AnimationClass)
		{
			return false;
		}
	}

	PresentationMesh->SetSkeletalMeshAsset(SkeletalMesh);
	PresentationMesh->SetRelativeTransform(ActiveDefinition.MeshRelativeTransform);
	if (AnimationClass)
	{
		PresentationMesh->SetAnimationMode(EAnimationMode::AnimationBlueprint);
		PresentationMesh->SetAnimInstanceClass(AnimationClass);
	}
	return true;
}

bool UMelodiaCompanionComponent::RequestState(const EMelodiaCompanionBehaviorState NewState)
{
	switch (NewState)
	{
	case EMelodiaCompanionBehaviorState::Follow:
		if (!FollowTarget) return false;
		break;
	case EMelodiaCompanionBehaviorState::Seek:
		if (!GuidanceTarget) return false;
		break;
	case EMelodiaCompanionBehaviorState::Graze:
		if (!SupportsInteraction(EMelodiaCompanionInteractionKind::Graze)) return false;
		break;
	case EMelodiaCompanionBehaviorState::Harmonize:
		if (!SupportsInteraction(EMelodiaCompanionInteractionKind::Harmonize)) return false;
		break;
	default:
		break;
	}

	SetStateInternal(NewState);
	return true;
}

bool UMelodiaCompanionComponent::BeginInteraction(const EMelodiaCompanionInteractionKind Interaction)
{
	if (!SupportsInteraction(Interaction))
	{
		return false;
	}

	const EMelodiaCompanionBehaviorState RequestedState = Interaction == EMelodiaCompanionInteractionKind::Graze
		? EMelodiaCompanionBehaviorState::Graze
		: Interaction == EMelodiaCompanionInteractionKind::Harmonize
			? EMelodiaCompanionBehaviorState::Harmonize
			: EMelodiaCompanionBehaviorState::Seek;

	if (!RequestState(RequestedState))
	{
		return false;
	}

	OnInteractionStarted.Broadcast(Interaction);
	return true;
}

void UMelodiaCompanionComponent::EndInteraction(const EMelodiaCompanionInteractionKind Interaction)
{
	OnInteractionFinished.Broadcast(Interaction);
	SetStateInternal(FollowTarget ? EMelodiaCompanionBehaviorState::Follow : EMelodiaCompanionBehaviorState::Idle);
}

void UMelodiaCompanionComponent::SetFollowTarget(AActor* NewTarget)
{
	FollowTarget = NewTarget;
	if (FollowTarget && CurrentState == EMelodiaCompanionBehaviorState::Idle)
	{
		SetStateInternal(EMelodiaCompanionBehaviorState::Follow);
	}
	else if (!FollowTarget && CurrentState == EMelodiaCompanionBehaviorState::Follow)
	{
		SetStateInternal(EMelodiaCompanionBehaviorState::Idle);
	}
}

void UMelodiaCompanionComponent::SetGuidanceTarget(AActor* NewTarget)
{
	GuidanceTarget = NewTarget;
}

FVector UMelodiaCompanionComponent::GetDesiredNavigationLocation() const
{
	if (!FollowTarget)
	{
		return GetOwner() ? GetOwner()->GetActorLocation() : FVector::ZeroVector;
	}

	const FVector TargetLocation = FollowTarget->GetActorLocation();
	const FVector FromTarget = GetOwner() ? GetOwner()->GetActorLocation() - TargetLocation : FVector::BackwardVector;
	const FVector FollowOffset = FromTarget.IsNearlyZero()
		? -FollowTarget->GetActorForwardVector()
		: FromTarget.GetSafeNormal();
	return TargetLocation + FollowOffset * ActiveDefinition.FollowDistance;
}

bool UMelodiaCompanionComponent::SupportsInteraction(const EMelodiaCompanionInteractionKind Interaction) const
{
	return ActiveDefinition.SupportedInteractions.Contains(Interaction);
}

bool UMelodiaCompanionComponent::RequestWardrobePresentation()
{
	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return false;
	}

	if (!WardrobeBridge)
	{
		WardrobeBridge = Owner->FindComponentByClass<UMelodiaCompanionWardrobeBridge>();
	}
	if (!WardrobeBridge)
	{
		return false;
	}

	// Resolve the provider by interface, not by module type. This keeps Core
	// independent of MelodiaWardrobe while still binding an authored wardrobe
	// component on the same actor when the request is explicitly made.
	if (!WardrobeBridge->HasWardrobeProvider())
	{
		TArray<UActorComponent*> Components;
		Owner->GetComponents(Components);
		for (UActorComponent* Component : Components)
		{
			if (Component
				&& Component->GetClass()->ImplementsInterface(UMelodiaCompanionWardrobeInterface::StaticClass())
				&& WardrobeBridge->SetWardrobeProvider(Component))
			{
				break;
			}
		}
	}

	if (!WardrobeBridge->HasWardrobeProvider())
	{
		return false;
	}

	const FMelodiaCompanionWardrobeProfile& DefinitionProfile = ActiveDefinition.WardrobeProfile;
	const EMelodiaCompanionWardrobeRequestResult Result = DefinitionProfile.PreferredCosmeticIds.IsEmpty()
		? WardrobeBridge->RequestPresentation()
		: WardrobeBridge->RequestPresentationWithProfile(DefinitionProfile);

	return Result == EMelodiaCompanionWardrobeRequestResult::AppliedOwnedCosmetic
		|| Result == EMelodiaCompanionWardrobeRequestResult::GrantedAndAppliedPrototypeCosmetic;
}

void UMelodiaCompanionComponent::HandleRhythmSignal(const FMelodiaRhythmReactivitySignal& Signal)
{
	const float RawIntensity = FMath::Clamp(
		Signal.BeatPulse * 0.60f
		+ Signal.WarmthGlow * 0.20f
		+ Signal.CozyBloom * 0.20f,
		0.0f,
		1.0f);
	ResonanceIntensity = FMath::Clamp(RawIntensity * RhythmResponse, 0.0f, 1.0f);

	if (CurrentState == EMelodiaCompanionBehaviorState::Harmonize
		&& Signal.BeatPulse > 0.85f
		&& LastBeatPulse <= 0.85f)
	{
		OnHarmonizePulse.Broadcast(ResonanceIntensity);
	}
	LastBeatPulse = Signal.BeatPulse;
}

void UMelodiaCompanionComponent::SetStateInternal(const EMelodiaCompanionBehaviorState NewState)
{
	if (CurrentState == NewState)
	{
		return;
	}

	const EMelodiaCompanionBehaviorState PreviousState = CurrentState;
	CurrentState = NewState;
	OnStateChanged.Broadcast(PreviousState, NewState);
}

void UMelodiaCompanionComponent::DriveOwnerToward(const FVector& DesiredLocation, const float AcceptanceRadius, const float DeltaTime)
{
	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return;
	}

	const FVector CurrentLocation = Owner->GetActorLocation();
	if (FVector::DistSquared2D(CurrentLocation, DesiredLocation) <= FMath::Square(AcceptanceRadius))
	{
		return;
	}

	const FVector NewLocation = FMath::VInterpTo(CurrentLocation, DesiredLocation, DeltaTime, FMath::Max(0.0f, FollowInterpSpeed));
	FHitResult Hit;
	Owner->SetActorLocation(NewLocation, true, &Hit);
}
