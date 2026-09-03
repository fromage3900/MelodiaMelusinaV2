#include "MelodiaChoralSheepActor.h"

#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SphereComponent.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "MelodiaCompanionComponent.h"

AMelodiaChoralSheepActor::AMelodiaChoralSheepActor()
{
	PrimaryActorTick.bCanEverTick = false;

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

	if (bAutoFollowFirstPlayer && CompanionComponent)
	{
		if (APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(this, 0))
		{
			CompanionComponent->SetFollowTarget(PlayerPawn);
		}
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
	const bool bStarted = IsInteractorInRange(Interactor)
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
	const bool bStarted = IsInteractorInRange(Interactor)
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
	if (!IsInteractorInRange(Interactor) || !CompanionComponent || !IsValid(GuideTarget))
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
