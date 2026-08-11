#include "MelodiaFirstDungeonGate.h"

#include "Components/BoxComponent.h"
#include "Components/TextRenderComponent.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "MelodiaDungeonRunCoordinator.h"
#include "MelodiaOpeningFlowSubsystem.h"
#include "MelodiaRulesGenerated.h"

AMelodiaFirstDungeonGate::AMelodiaFirstDungeonGate()
{
	PrimaryActorTick.bCanEverTick = false;
	FirstRunSeed = MelodiaRulesGen::OpeningFirstDungeonSeed;
	TriggerVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("TriggerVolume"));
	SetRootComponent(TriggerVolume);
	TriggerVolume->SetBoxExtent(FVector(180.0f, 180.0f, 220.0f));
	TriggerVolume->SetCollisionProfileName(TEXT("Trigger"));

	PromptText = CreateDefaultSubobject<UTextRenderComponent>(TEXT("PromptText"));
	PromptText->SetupAttachment(TriggerVolume);
	PromptText->SetRelativeLocation(FVector(0.0f, 0.0f, 240.0f));
	PromptText->SetHorizontalAlignment(EHTA_Center);
	PromptText->SetWorldSize(34.0f);
	PromptText->SetText(FText::FromString(TEXT("First Resonant Door")));
}

void AMelodiaFirstDungeonGate::BeginPlay()
{
	Super::BeginPlay();
	TriggerVolume->OnComponentBeginOverlap.AddDynamic(this, &AMelodiaFirstDungeonGate::HandleOverlap);
	if (!RunCoordinator)
	{
		for (TActorIterator<AMelodiaDungeonRunCoordinator> It(GetWorld()); It; ++It)
		{
			RunCoordinator = *It;
			break;
		}
	}

	if (UMelodiaOpeningFlowSubsystem* Flow = UMelodiaOpeningFlowSubsystem::Get(this))
	{
		Flow->OnFirstDungeonUnlocked.AddUniqueDynamic(this, &AMelodiaFirstDungeonGate::HandleFirstDungeonUnlocked);
		SetUnlocked(Flow->IsFirstDungeonUnlocked());
	}
	else
	{
		SetUnlocked(false);
	}
}

void AMelodiaFirstDungeonGate::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UMelodiaOpeningFlowSubsystem* Flow = UMelodiaOpeningFlowSubsystem::Get(this))
	{
		Flow->OnFirstDungeonUnlocked.RemoveDynamic(this, &AMelodiaFirstDungeonGate::HandleFirstDungeonUnlocked);
	}
	Super::EndPlay(EndPlayReason);
}

void AMelodiaFirstDungeonGate::HandleFirstDungeonUnlocked()
{
	SetUnlocked(true);
}

void AMelodiaFirstDungeonGate::SetUnlocked(const bool bNewUnlocked)
{
	bUnlocked = bNewUnlocked;
	TriggerVolume->SetCollisionEnabled(bUnlocked ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
	PromptText->SetVisibility(bUnlocked);
}

void AMelodiaFirstDungeonGate::HandleOverlap(UPrimitiveComponent*, AActor* OtherActor,
	UPrimitiveComponent*, int32, bool, const FHitResult&)
{
	APawn* Pawn = Cast<APawn>(OtherActor);
	if (!bUnlocked || bEntered || !Pawn || !Pawn->IsPlayerControlled() || !RunCoordinator)
	{
		return;
	}

	if (RunCoordinator->StartFirstDungeonRun(FirstRunSeed))
	{
		bEntered = true;
		TriggerVolume->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		PromptText->SetVisibility(false);
	}
}
