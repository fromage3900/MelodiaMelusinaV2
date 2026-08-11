#include "MelodiaBattleInteractionTrigger.h"

#include "Components/BoxComponent.h"
#include "Components/TextRenderComponent.h"
#include "GameFramework/Pawn.h"
#include "MelodiaNarrativeSubsystem.h"

AMelodiaBattleInteractionTrigger::AMelodiaBattleInteractionTrigger()
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

void AMelodiaBattleInteractionTrigger::BeginPlay()
{
	Super::BeginPlay();
	if (PromptText)
	{
		PromptText->SetText(InteractionPrompt);
	}
}

bool AMelodiaBattleInteractionTrigger::TryInteract(AActor* InteractingActor)
{
	const APawn* Pawn = Cast<APawn>(InteractingActor);
	if (EncounterId.IsNone() || !Pawn || !Pawn->IsPlayerControlled()
		|| !InteractionVolume || !InteractionVolume->IsOverlappingActor(InteractingActor))
	{
		return false;
	}

	UMelodiaNarrativeSubsystem* Narrative =
		UMelodiaNarrativeSubsystem::GetMelodiaNarrativeSubsystem(this);
	if (!Narrative || Narrative->IsBattlePending())
	{
		return false;
	}

	const bool bAccepted = Narrative->StartBattle(EncounterId);
	if (bAccepted)
	{
		UE_LOG(LogTemp, Log, TEXT("MELODIA_BATTLE_INTERACTION requested encounter=%s trigger=%s"),
			*EncounterId.ToString(), *GetName());
	}
	return bAccepted;
}
