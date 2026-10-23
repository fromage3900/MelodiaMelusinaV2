#include "MelodiaStoryDoorComponent.h"

#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "MelodiaNarrativeSubsystem.h"
#include "TimerManager.h"

UMelodiaStoryDoorComponent::UMelodiaStoryDoorComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UMelodiaStoryDoorComponent::BeginPlay()
{
	Super::BeginPlay();

	if (const UWorld* World = GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			Narrative = GI->GetSubsystem<UMelodiaNarrativeSubsystem>();
		}
	}
	if (Narrative)
	{
		Narrative->OnFlagChanged.AddDynamic(this, &UMelodiaStoryDoorComponent::HandleFlagChanged);
	}
	RefreshFromFlag();
}

void UMelodiaStoryDoorComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (Narrative)
	{
		Narrative->OnFlagChanged.RemoveDynamic(this, &UMelodiaStoryDoorComponent::HandleFlagChanged);
	}
	if (const UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(AssemblyTimer);
	}
	Super::EndPlay(EndPlayReason);
}

bool UMelodiaStoryDoorComponent::ReadFlag() const
{
	if (RequiredFlagId.IsNone())
	{
		return true;
	}
	return Narrative && Narrative->GetNarrativeFlag(RequiredFlagId);
}

void UMelodiaStoryDoorComponent::RefreshFromFlag()
{
	if (const UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(AssemblyTimer);
	}
	SetStage(ReadFlag() ? EMelodiaStoryDoorStage::Open : EMelodiaStoryDoorStage::Sealed, true);
}

void UMelodiaStoryDoorComponent::HandleFlagChanged(const FName FlagId, const bool Value)
{
	if (RequiredFlagId.IsNone() || FlagId != RequiredFlagId)
	{
		return;
	}
	if (!Value)
	{
		if (const UWorld* World = GetWorld())
		{
			World->GetTimerManager().ClearTimer(AssemblyTimer);
		}
		SetStage(EMelodiaStoryDoorStage::Sealed, false);
		return;
	}
	if (Stage != EMelodiaStoryDoorStage::Sealed)
	{
		return; // idempotent: already assembling or open
	}
	const UWorld* World = GetWorld();
	if (!World || AssemblySeconds <= KINDA_SMALL_NUMBER)
	{
		SetStage(EMelodiaStoryDoorStage::Open, false);
		return;
	}
	SetStage(EMelodiaStoryDoorStage::Assembling, false);
	World->GetTimerManager().SetTimer(AssemblyTimer, this, &UMelodiaStoryDoorComponent::FinishAssembly, AssemblySeconds, false);
}

void UMelodiaStoryDoorComponent::FinishAssembly()
{
	SetStage(EMelodiaStoryDoorStage::Open, false);
}

void UMelodiaStoryDoorComponent::SetStage(const EMelodiaStoryDoorStage NewStage, const bool bFromLoad)
{
	if (NewStage == Stage && !bFromLoad)
	{
		return;
	}
	Stage = NewStage;
	OnStageChanged.Broadcast(Stage, bFromLoad);
}
