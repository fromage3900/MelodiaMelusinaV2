#include "MelodiaJRPGBattleOverlaySubsystem.h"

#include "Engine/GameInstance.h"
#include "MelodiaNarrativeSubsystem.h"

void UMelodiaJRPGBattleOverlaySubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	Collection.InitializeDependency<UMelodiaNarrativeSubsystem>();

	if (UMelodiaNarrativeSubsystem* Narrative =
		GetGameInstance()->GetSubsystem<UMelodiaNarrativeSubsystem>())
	{
		Narrative->OnBattleRequested.AddUniqueDynamic(this, &ThisClass::HandleBattleRequested);
		Narrative->OnBattleCompleted.AddUniqueDynamic(this, &ThisClass::HandleBattleCompleted);
		Narrative->OnBattleAborted.AddUniqueDynamic(this, &ThisClass::HandleBattleAborted);
	}
}

void UMelodiaJRPGBattleOverlaySubsystem::Deinitialize()
{
	if (const UGameInstance* GameInstance = GetGameInstance())
	{
		if (UMelodiaNarrativeSubsystem* Narrative =
			GameInstance->GetSubsystem<UMelodiaNarrativeSubsystem>())
		{
			Narrative->OnBattleRequested.RemoveDynamic(this, &ThisClass::HandleBattleRequested);
			Narrative->OnBattleCompleted.RemoveDynamic(this, &ThisClass::HandleBattleCompleted);
			Narrative->OnBattleAborted.RemoveDynamic(this, &ThisClass::HandleBattleAborted);
		}
	}

	Super::Deinitialize();
}

void UMelodiaJRPGBattleOverlaySubsystem::HandleBattleRequested(const FName EncounterId)
{
	UE_LOG(LogTemp, Verbose,
		TEXT("Melodia battle overlay observer retired for encounter %s; UMelodiaUIBridgeSubsystem owns battle widgets."),
		*EncounterId.ToString());
}

void UMelodiaJRPGBattleOverlaySubsystem::HandleBattleCompleted(
	const FName EncounterId,
	const EMelodiaBattleResult Result)
{
	UE_LOG(LogTemp, Verbose, TEXT("Melodia battle overlay observer saw completion %s result=%d."),
		*EncounterId.ToString(), static_cast<int32>(Result));
}

void UMelodiaJRPGBattleOverlaySubsystem::HandleBattleAborted(
	const FName EncounterId,
	const FString Reason)
{
	UE_LOG(LogTemp, Verbose, TEXT("Melodia battle overlay observer saw abort %s: %s."),
		*EncounterId.ToString(), *Reason);
}
