#include "MelodiaChoralSheepActor.h"

#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SphereComponent.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "MelodiaCompanionComponent.h"
#include "MelodiaReactiveMeshRegistrar.h"
#include "MelodiaRhythmReactivitySubsystem.h"

AMelodiaChoralSheepActor::AMelodiaChoralSheepActor()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = true;

	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	SkeletalMeshComponent = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("SkeletalMesh"));
	SkeletalMeshComponent->SetupAttachment(Root);
	SkeletalMeshComponent->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	SkeletalMeshComponent->SetCollisionResponseToAllChannels(ECR_Ignore);

	InteractionRange = CreateDefaultSubobject<USphereComponent>(TEXT("InteractionRange"));
	InteractionRange->SetupAttachment(Root);
	InteractionRange->SetSphereRadius(160.0f);
	InteractionRange->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	InteractionRange->SetCollisionResponseToAllChannels(ECR_Ignore);
	InteractionRange->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	InteractionRange->SetGenerateOverlapEvents(true);

	CompanionComponent = CreateDefaultSubobject<UMelodiaCompanionComponent>(TEXT("Companion"));

	// Option A: Tag actor for auto-discovery
	Tags.AddUnique(UMelodiaReactiveMeshRegistrar::ReactiveTag);
}

void AMelodiaChoralSheepActor::PostInitializeComponents()
{
	Super::PostInitializeComponents();
	if (CompanionComponent && !CompanionDefinition.IsNull())
	{
		CompanionComponent->CompanionDefinition = CompanionDefinition;
	}
}

void AMelodiaChoralSheepActor::BeginPlay()
{
	Super::BeginPlay();
	ApplyChoralSheepDefinition();

	// Option B: Deterministic explicit registration with Rhythm Reactivity Subsystem
	if (SkeletalMeshComponent)
	{
		if (UWorld* World = GetWorld())
		{
			if (UMelodiaRhythmReactivitySubsystem* Reactivity = World->GetSubsystem<UMelodiaRhythmReactivitySubsystem>())
			{
				Reactivity->RegisterReactiveMeshComponent(SkeletalMeshComponent);
			}
		}

		// Ensure Dynamic Material Instance is created and cached
		UMaterialInterface* CurrentMat = SkeletalMeshComponent->GetMaterial(0);
		SheepDynamicMaterial = Cast<UMaterialInstanceDynamic>(CurrentMat);
		if (!SheepDynamicMaterial && CurrentMat)
		{
			SheepDynamicMaterial = SkeletalMeshComponent->CreateAndSetMaterialInstanceDynamic(0);
		}

		if (SheepDynamicMaterial)
		{
			SheepDynamicMaterial->SetScalarParameterValue(TEXT("HarmonizeActive"), 0.0f);
		}
	}

	if (bAutoFollowFirstPlayer && CompanionComponent)
	{
		if (APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(this, 0))
		{
			CompanionComponent->SetFollowTarget(PlayerPawn);
		}
	}
}

void AMelodiaChoralSheepActor::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	const bool bHarmonizeActive = (ActiveInteraction == EMelodiaCompanionInteractionKind::Harmonize)
		&& CompanionComponent
		&& (CompanionComponent->CurrentState == EMelodiaCompanionBehaviorState::Harmonize);

	const float TargetWeight = bHarmonizeActive ? 1.0f : 0.0f;
	CurrentHarmonizeWeight = FMath::FInterpTo(CurrentHarmonizeWeight, TargetWeight, DeltaTime, FMath::Max(0.1f, HarmonizeFadeSpeed));

	if (!SheepDynamicMaterial && SkeletalMeshComponent)
	{
		SheepDynamicMaterial = Cast<UMaterialInstanceDynamic>(SkeletalMeshComponent->GetMaterial(0));
	}

	if (SheepDynamicMaterial)
	{
		SheepDynamicMaterial->SetScalarParameterValue(TEXT("HarmonizeActive"), CurrentHarmonizeWeight);
	}
}

bool AMelodiaChoralSheepActor::ApplyChoralSheepDefinition()
{
	if (!CompanionComponent || CompanionDefinition.IsNull())
	{
		return false;
	}

	UMelodiaCompanionDefinitionAsset* LoadedDefinition = CompanionDefinition.LoadSynchronous();
	return CompanionComponent->SetCompanionDefinition(LoadedDefinition);
}

bool AMelodiaChoralSheepActor::SetChoralSheepDefinition(UMelodiaCompanionDefinitionAsset* InDefinition)
{
	if (!CompanionComponent || !InDefinition)
	{
		return false;
	}

	CompanionDefinition = InDefinition;
	CompanionComponent->CompanionDefinition = InDefinition;
	return CompanionComponent->SetCompanionDefinition(InDefinition);
}

bool AMelodiaChoralSheepActor::IsInteractorInRange(const AActor* Interactor) const
{
	return InteractionRange && IsValid(Interactor) && InteractionRange->IsOverlappingActor(Interactor);
}

bool AMelodiaChoralSheepActor::TryBeginGraze(AActor* Interactor)
{
	const bool bStarted = (!Interactor || IsInteractorInRange(Interactor))
		&& CompanionComponent
		&& CompanionComponent->BeginInteraction(EMelodiaCompanionInteractionKind::Graze);
	if (bStarted)
	{
		ActiveInteraction = EMelodiaCompanionInteractionKind::Graze;
	}
	return bStarted;
}

bool AMelodiaChoralSheepActor::TryBeginHarmonize(AActor* Interactor)
{
	const bool bStarted = (!Interactor || IsInteractorInRange(Interactor))
		&& CompanionComponent
		&& CompanionComponent->BeginInteraction(EMelodiaCompanionInteractionKind::Harmonize);
	if (bStarted)
	{
		ActiveInteraction = EMelodiaCompanionInteractionKind::Harmonize;
	}
	return bStarted;
}

bool AMelodiaChoralSheepActor::TryBeginGuide(AActor* Interactor, AActor* GuideTarget)
{
	if ((Interactor && !IsInteractorInRange(Interactor)) || !CompanionComponent || !IsValid(GuideTarget))
	{
		return false;
	}

	CompanionComponent->SetGuidanceTarget(GuideTarget);
	const bool bStarted = CompanionComponent->BeginInteraction(EMelodiaCompanionInteractionKind::Guide);
	if (bStarted)
	{
		ActiveInteraction = EMelodiaCompanionInteractionKind::Guide;
	}
	return bStarted;
}

void AMelodiaChoralSheepActor::EndCompanionInteraction()
{
	if (CompanionComponent)
	{
		CompanionComponent->EndInteraction(ActiveInteraction);
	}
}
