#include "CoreMinimal.h"

#if !UE_BUILD_SHIPPING

#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "MelodiaRoguelikePersistence.h"
#include "MelodiaRoguelikeRunSubsystem.h"
#include "Misc/CoreDelegates.h"

namespace
{
bool CompleteStage(UMelodiaRoguelikeRunSubsystem& Run, const bool bAdvance)
{
	if (!Run.RecordGenerationResult(true)
		|| !Run.NotifyEncounterStarted()
		|| !Run.RecordEncounterResult(EMelodiaEncounterResult::Victory))
	{
		return false;
	}

	if (Run.LifecyclePhase == EMelodiaRunLifecyclePhase::EndlessOffer)
	{
		return !bAdvance;
	}

	if (!Run.CommitReward(0))
	{
		return false;
	}
	return !bAdvance || Run.RequestStageAdvance();
}

bool VerifyPackagedRoguelike(FString& OutFailure)
{
	UWorld* GameWorld = nullptr;
	if (GEngine)
	{
		for (const FWorldContext& Context : GEngine->GetWorldContexts())
		{
			if (Context.WorldType == EWorldType::Game && Context.World())
			{
				GameWorld = Context.World();
				break;
			}
		}
	}
	if (!GameWorld || !GameWorld->GetGameInstance())
	{
		OutFailure = TEXT("No packaged game world or GameInstance");
		return false;
	}

	UGameInstance* GameInstance = GameWorld->GetGameInstance();
	UMelodiaRoguelikeRunSubsystem* Run = GameInstance->GetSubsystem<UMelodiaRoguelikeRunSubsystem>();
	if (!Run)
	{
		OutFailure = TEXT("Melodia run subsystem unavailable");
		return false;
	}

	Run->StartStructuredRun(20260718, 1, 3);
	for (int32 Stage = 0; Stage < 3; ++Stage)
	{
		const bool bAdvance = Stage < 2;
		if (!CompleteStage(*Run, bAdvance))
		{
			OutFailure = FString::Printf(TEXT("Structured stage %d failed"), Stage);
			return false;
		}
	}
	if (Run->LifecyclePhase != EMelodiaRunLifecyclePhase::EndlessOffer || !Run->ContinueEndless())
	{
		OutFailure = TEXT("Structured completion did not enter endless mode");
		return false;
	}

	for (int32 Stage = 0; Stage < 100; ++Stage)
	{
		if (!CompleteStage(*Run, true))
		{
			OutFailure = FString::Printf(TEXT("Endless stage %d failed"), Stage);
			return false;
		}
	}
	if (!Run->bEndlessMode || Run->EndlessDepth < 100)
	{
		OutFailure = TEXT("Endless depth did not reach 100");
		return false;
	}

	UMelodiaRoguelikeRunCheckpointSaveGame* Save = NewObject<UMelodiaRoguelikeRunCheckpointSaveGame>();
	Save->Snapshot = Run->ExportSnapshot();
	TArray<uint8> Bytes;
	if (!UGameplayStatics::SaveGameToMemory(Save, Bytes) || Bytes.IsEmpty())
	{
		OutFailure = TEXT("Checkpoint failed SaveGame serialization");
		return false;
	}
	const UMelodiaRoguelikeRunCheckpointSaveGame* LoadedSave = Cast<UMelodiaRoguelikeRunCheckpointSaveGame>(
		UGameplayStatics::LoadGameFromMemory(Bytes));
	if (!LoadedSave)
	{
		OutFailure = TEXT("Checkpoint failed SaveGame deserialization");
		return false;
	}

	UMelodiaRoguelikeRunSubsystem* Restored = NewObject<UMelodiaRoguelikeRunSubsystem>(GameInstance);
	if (!Restored->ImportSnapshot(LoadedSave->Snapshot)
		|| Restored->CurrentStageIndex != Run->CurrentStageIndex
		|| Restored->EndlessDepth != Run->EndlessDepth
		|| Restored->AuthoritativeStage.StageSeed != Run->AuthoritativeStage.StageSeed)
	{
		OutFailure = TEXT("Fresh authority failed checkpoint parity");
		return false;
	}
	return true;
}

void RunPackagedVerification()
{
	FString Failure;
	if (VerifyPackagedRoguelike(Failure))
	{
		UE_LOG(LogTemp, Display, TEXT("MELODIA_PACKAGED_VERIFY: PASS structured=3 endless=100 checkpoint=pass"));
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("MELODIA_PACKAGED_VERIFY: FAIL %s"), *Failure);
	}
	FPlatformMisc::RequestExit(false);
}

FAutoConsoleCommand VerifyPackagedRoguelikeCommand(
	TEXT("Melodia.VerifyPackagedRoguelike"),
	TEXT("Runs the non-shipping packaged MelodiaCore structured/endless/checkpoint verification and exits."),
	FConsoleCommandDelegate::CreateStatic(&RunPackagedVerification));
}

#endif