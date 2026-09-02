#include "MelodiaTravelInteractionPortal.h"

#include "Components/BoxComponent.h"
#include "Components/TextRenderComponent.h"
#include "GameFramework/Pawn.h"
#include "MelodiaTravelSubsystem.h"
#include "MelodiaTraversalCapabilityProvider.h"
#include "Engine/GameInstance.h"
#include "TimerManager.h"

AMelodiaTravelInteractionPortal::AMelodiaTravelInteractionPortal()
{
	PrimaryActorTick.bCanEverTick = false;

	InteractionVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("InteractionVolume"));
	SetRootComponent(InteractionVolume);
	InteractionVolume->SetBoxExtent(FVector(150.0f));
	InteractionVolume->SetCollisionProfileName(TEXT("Trigger"));

	PromptText = CreateDefaultSubobject<UTextRenderComponent>(TEXT("PromptText"));
	PromptText->SetupAttachment(InteractionVolume);
	PromptText->SetRelativeLocation(FVector(0.0f, 0.0f, 160.0f));
	PromptText->SetHorizontalAlignment(EHTA_Center);
	PromptText->SetWorldSize(28.0f);
}

void AMelodiaTravelInteractionPortal::BeginPlay()
{
	Super::BeginPlay();
	if (PromptText)
	{
		RefreshCapabilityPrompt();
	}
	GetWorldTimerManager().SetTimer(CapabilityRefreshTimerHandle, this,
		&AMelodiaTravelInteractionPortal::RefreshCapabilityPrompt, 0.25f, true);
}

bool AMelodiaTravelInteractionPortal::IsTraversalUnlocked(FName& OutBlockReason) const
{
	OutBlockReason = NAME_None;
	if (RequiredTraversalCapability.IsNone())
	{
		return true;
	}

	const UGameInstance* GameInstance = GetGameInstance();
	const UMelodiaTraversalCapabilityRegistry* Registry = GameInstance
		? GameInstance->GetSubsystem<UMelodiaTraversalCapabilityRegistry>() : nullptr;
	return Registry && Registry->QueryCapability(
		RequiredTraversalCapability, TraversalCapabilityContext, OutBlockReason);
}

void AMelodiaTravelInteractionPortal::RefreshCapabilityPrompt()
{
	FName BlockReason;
	if (PromptText)
	{
		PromptText->SetText(IsTraversalUnlocked(BlockReason) ? InteractionPrompt : LockedInteractionPrompt);
	}
}

bool AMelodiaTravelInteractionPortal::TryInteract(AActor* InteractingActor)
{
	const APawn* Pawn = Cast<APawn>(InteractingActor);
	FName CapabilityBlockReason;
	if (bTravelRequested || DestinationMap.IsNone() || !Pawn || !Pawn->IsPlayerControlled()
		|| !InteractionVolume || !InteractionVolume->IsOverlappingActor(InteractingActor)
		|| !IsTraversalUnlocked(CapabilityBlockReason))
	{
		return false;
	}

	UMelodiaTravelSubsystem* Travel = UMelodiaTravelSubsystem::Get(this);
	if (!Travel || !Travel->TravelTo(DestinationMap, DestinationSpawnTag))
	{
		return false;
	}

	bTravelRequested = true;
	UE_LOG(LogTemp, Log, TEXT("MELODIA_TRAVEL_INTERACTION destination=%s spawn_tag=%s portal=%s"),
		*DestinationMap.ToString(), *DestinationSpawnTag.ToString(), *GetName());
	return true;
}
