#include "MelodiaRoomExit.h"

#include "Components/BoxComponent.h"
#include "Components/TextRenderComponent.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "MelodiaDungeonRunCoordinator.h"

AMelodiaRoomExit::AMelodiaRoomExit()
{
	PrimaryActorTick.bCanEverTick = false;
	TriggerVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("TriggerVolume"));
	SetRootComponent(TriggerVolume);
	TriggerVolume->SetBoxExtent(FVector(120.0f, 120.0f, 180.0f));
	TriggerVolume->SetCollisionProfileName(TEXT("Trigger"));

	StatusLabel = CreateDefaultSubobject<UTextRenderComponent>(TEXT("StatusLabel"));
	StatusLabel->SetupAttachment(TriggerVolume);
	StatusLabel->SetRelativeLocation(FVector(0.0f, 0.0f, 210.0f));
	StatusLabel->SetHorizontalAlignment(EHTA_Center);
	StatusLabel->SetWorldSize(36.0f);
	SetLocked(true);
}

void AMelodiaRoomExit::BeginPlay()
{
	Super::BeginPlay();
	if (!Coordinator && bAllowCoordinatorAutoResolve)
	{
		int32 CoordinatorCount = 0;
		for (TActorIterator<AMelodiaDungeonRunCoordinator> It(GetWorld()); It; ++It)
		{
			++CoordinatorCount;
			if (!Coordinator)
			{
				Coordinator = *It;
			}
		}
		if (CoordinatorCount != 1)
		{
			UE_LOG(LogTemp, Error, TEXT("Melodia room exit '%s' requires one explicit coordinator; found %d candidates."),
				*GetName(), CoordinatorCount);
			Coordinator = nullptr;
		}
	}
	if (!Coordinator)
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia room exit '%s' is disabled because no roguelike coordinator is assigned."), *GetName());
		SetLocked(true);
	}
	TriggerVolume->OnComponentBeginOverlap.AddUniqueDynamic(this, &AMelodiaRoomExit::HandleOverlap);
}

void AMelodiaRoomExit::SetLocked(const bool bNewLocked)
{
	bLocked = bNewLocked;
	if (bLocked)
	{
		bTransitionRequested = false;
	}
	if (StatusLabel)
	{
		StatusLabel->SetText(FText::FromString(bLocked ? TEXT("Harmony required") : TEXT("Doorway open")));
		StatusLabel->SetTextRenderColor(bLocked ? FColor(180, 80, 120) : FColor(100, 220, 255));
	}
	if (TriggerVolume)
	{
		TriggerVolume->SetCollisionEnabled(bLocked ? ECollisionEnabled::NoCollision : ECollisionEnabled::QueryOnly);
	}
}

void AMelodiaRoomExit::HandleOverlap(UPrimitiveComponent*, AActor* OtherActor, UPrimitiveComponent*, int32, bool, const FHitResult&)
{
	APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(this, 0);
	if (bLocked || bTransitionRequested || !PlayerPawn || OtherActor != PlayerPawn || !PlayerPawn->IsPlayerControlled() || !Coordinator)
	{
		return;
	}
	bTransitionRequested = Coordinator->RequestNextStage();
}
