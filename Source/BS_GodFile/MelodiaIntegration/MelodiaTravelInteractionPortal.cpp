#include "MelodiaTravelInteractionPortal.h"

#include "Components/BoxComponent.h"
#include "Components/TextRenderComponent.h"
#include "GameFramework/Pawn.h"
#include "MelodiaTravelSubsystem.h"

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
		PromptText->SetText(InteractionPrompt);
	}
}

bool AMelodiaTravelInteractionPortal::TryInteract(AActor* InteractingActor)
{
	const APawn* Pawn = Cast<APawn>(InteractingActor);
	if (bTravelRequested || DestinationMap.IsNone() || !Pawn || !Pawn->IsPlayerControlled()
		|| !InteractionVolume || !InteractionVolume->IsOverlappingActor(InteractingActor))
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
