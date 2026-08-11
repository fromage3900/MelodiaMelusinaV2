#include "MelodiaStorySequenceTrigger.h"

#include "Components/BoxComponent.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "MelodiaStorySequenceData.h"
#include "MelodiaStorySequenceWidget.h"

AMelodiaStorySequenceTrigger::AMelodiaStorySequenceTrigger()
{
	PrimaryActorTick.bCanEverTick = false;

	TriggerVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("TriggerVolume"));
	TriggerVolume->SetBoxExtent(FVector(140.0f, 140.0f, 140.0f));
	TriggerVolume->SetCollisionProfileName(TEXT("Trigger"));
	SetRootComponent(TriggerVolume);
	TriggerVolume->OnComponentBeginOverlap.AddDynamic(this, &ThisClass::HandleOverlap);

	SequenceWidgetClass = TSoftClassPtr<UMelodiaStorySequenceWidget>(
		FSoftObjectPath(TEXT("/Game/Melodia/UI/WBP_MelodiaOpeningSlideshow.WBP_MelodiaOpeningSlideshow_C")));
}

void AMelodiaStorySequenceTrigger::HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
	UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if ((bTriggerOnce && bConsumed) || ActiveSequence || !OtherActor)
	{
		return;
	}

	APlayerController* PlayerController = nullptr;
	if (const APawn* OverlappingPawn = Cast<APawn>(OtherActor))
	{
		PlayerController = Cast<APlayerController>(OverlappingPawn->GetController());
	}
	if (!PlayerController)
	{
		PlayerController = Cast<APlayerController>(OtherActor->GetInstigatorController());
	}
	if (!PlayerController)
	{
		return;
	}

	ActiveTriggeringActor = OtherActor;
	PlayFor(PlayerController);
}

bool AMelodiaStorySequenceTrigger::PlayFor(APlayerController* PlayerController)
{
	if ((bTriggerOnce && bConsumed) || ActiveSequence || !PlayerController)
	{
		return false;
	}

	UClass* WidgetClass = SequenceWidgetClass.LoadSynchronous();
	UMelodiaStorySequenceData* SequenceData = Sequence.LoadSynchronous();
	if (!WidgetClass || !WidgetClass->IsChildOf(UMelodiaStorySequenceWidget::StaticClass()) || !SequenceData)
	{
		UE_LOG(LogTemp, Warning, TEXT("MelodiaStorySequenceTrigger '%s' is missing a compatible widget class or sequence asset."), *GetName());
		return false;
	}

	ActiveSequence = CreateWidget<UMelodiaStorySequenceWidget>(PlayerController, WidgetClass);
	if (!ActiveSequence)
	{
		return false;
	}

	ActiveSequence->OnSequenceFinished.AddUniqueDynamic(this, &ThisClass::HandleSequenceFinished);
	if (!ActiveSequence->SetSequence(SequenceData))
	{
		ActiveSequence = nullptr;
		return false;
	}

	bConsumed = true;
	ActiveSequence->AddToViewport(100);
	FInputModeUIOnly InputMode;
	InputMode.SetWidgetToFocus(ActiveSequence->TakeWidget());
	InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
	PlayerController->SetInputMode(InputMode);
	PlayerController->SetShowMouseCursor(true);
	return true;
}

void AMelodiaStorySequenceTrigger::HandleSequenceFinished(UMelodiaStorySequenceData* FinishedSequence)
{
	if (!ActiveSequence)
	{
		return;
	}

	APlayerController* PlayerController = ActiveSequence->GetOwningPlayer();
	ActiveSequence->RemoveFromParent();
	ActiveSequence = nullptr;
	if (PlayerController)
	{
		PlayerController->SetInputMode(FInputModeGameOnly());
		PlayerController->SetShowMouseCursor(false);
	}

	OnSequenceFinished.Broadcast(ActiveTriggeringActor);
	ActiveTriggeringActor = nullptr;
}
