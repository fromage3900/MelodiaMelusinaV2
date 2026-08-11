#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/ScopeExit.h"
#include "HAL/FileManager.h"
#include "Serialization/MemoryReader.h"
#include "Serialization/MemoryWriter.h"
#include "Engine/GameInstance.h"
#include "MelodiaDevEntitlementProvider.h"
#include "MelodiaEntitlementSubsystem.h"
#include "MelodiaSaveGame.h"
#include "MelodiaRoguelikePersistence.h"
#include "MelodiaRoguelikeRunSubsystem.h"
#include "MelodiaBattleSession.h"
#include "Kismet/GameplayStatics.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaSaveGameDefaultsTest,
	"Melodia.Persistence.SaveGameDefaults",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaSaveGameDefaultsTest::RunTest(const FString& Parameters)
{
	UMelodiaSaveGame* Save = NewObject<UMelodiaSaveGame>(GetTransientPackage());
	TestEqual(TEXT("SaveSystemVersion is 2"), Save->SaveSystemVersion, 2);
	TestEqual(TEXT("Currency defaults to 0"), Save->Currency, 0LL);
	TestEqual(TEXT("HeartMelodyTokens defaults to 0"), Save->HeartMelodyTokens, 0);
	TestEqual(TEXT("SwirlMelodyTokens defaults to 0"), Save->SwirlMelodyTokens, 0);
	TestTrue(TEXT("OwnedContentPacks defaults to empty"), Save->OwnedContentPacks.IsEmpty());
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaEntitlementRestoreTest,
	"Melodia.Persistence.EntitlementRestore",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaEntitlementRestoreTest::RunTest(const FString& Parameters)
{
	UGameInstance* Owner = NewObject<UGameInstance>();
	UMelodiaEntitlementSubsystem* Entitlements = NewObject<UMelodiaEntitlementSubsystem>(Owner);

	TArray<FName> SavedPacks;
	SavedPacks.Add(TEXT("Cosmetic.Plumage.Amethyst"));
	SavedPacks.Add(TEXT("Cosmetic.Wings.Crimson"));

	Entitlements->RestoreFromSave(SavedPacks);

	TestTrue(TEXT("Core is always owned"), Entitlements->OwnsContentPack(TEXT("Core")));
	TestTrue(TEXT("Restored pack is owned"), Entitlements->OwnsContentPack(TEXT("Cosmetic.Plumage.Amethyst")));
	TestTrue(TEXT("Second restored pack is owned"), Entitlements->OwnsContentPack(TEXT("Cosmetic.Wings.Crimson")));
	TestFalse(TEXT("Unrestored pack is not owned"), Entitlements->OwnsContentPack(TEXT("Cosmetic.Nonexistent")));

	const TArray<FName> Queried = Entitlements->QueryEntitlements();
	TestTrue(TEXT("Query returns restored packs"), Queried.Contains(TEXT("Cosmetic.Plumage.Amethyst")));
	TestTrue(TEXT("Query returns Core"), Queried.Contains(TEXT("Core")));
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaDevEntitlementRoundTripTest,
	"Melodia.Persistence.DevEntitlementRoundTrip",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaDevEntitlementRoundTripTest::RunTest(const FString& Parameters)
{
	const FString DevEntitlementPath = UMelodiaDevEntitlementProvider::GetDevFilePath();
	FString OriginalFileContents;
	const bool bHadOriginalFile = FFileHelper::LoadFileToString(OriginalFileContents, *DevEntitlementPath);
	ON_SCOPE_EXIT
	{
		if (bHadOriginalFile)
		{
			FFileHelper::SaveStringToFile(OriginalFileContents, *DevEntitlementPath);
		}
		else
		{
			IFileManager::Get().Delete(*DevEntitlementPath);
		}
	};
	UGameInstance* Owner = NewObject<UGameInstance>();
	UMelodiaDevEntitlementProvider* Provider = NewObject<UMelodiaDevEntitlementProvider>(Owner);

	Provider->ContentPacks.Add(TEXT("Cosmetic.TestPackA"));
	Provider->ContentPacks.Add(TEXT("Cosmetic.TestPackB"));

	TestTrue(TEXT("SaveToFile succeeds"), Provider->SaveToFile());
	TestTrue(TEXT("File exists on disk"), IFileManager::Get().FileExists(*UMelodiaDevEntitlementProvider::GetDevFilePath()));

	Provider->ContentPacks.Empty();
	TestEqual(TEXT("Packs cleared before load"), Provider->ContentPacks.Num(), 0);

	TestTrue(TEXT("LoadFromFile succeeds"), Provider->LoadFromFile());
	TestEqual(TEXT("Two packs after round-trip"), Provider->ContentPacks.Num(), 2);
	TestTrue(TEXT("Round-tripped TestPackA"), Provider->ContentPacks.Contains(TEXT("Cosmetic.TestPackA")));
	TestTrue(TEXT("Round-tripped TestPackB"), Provider->ContentPacks.Contains(TEXT("Cosmetic.TestPackB")));
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaDevEntitlementQueryTest,
	"Melodia.Persistence.DevEntitlementQuery",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaDevEntitlementQueryTest::RunTest(const FString& Parameters)
{
	UGameInstance* Owner = NewObject<UGameInstance>();
	UMelodiaDevEntitlementProvider* Provider = NewObject<UMelodiaDevEntitlementProvider>(Owner);

	Provider->ContentPacks.Add(TEXT("Cosmetic.DevOnly"));

	const TArray<FName> Owned = IMelodiaEntitlementProvider::Execute_QueryOwnedContentPacks(Provider);
	TestTrue(TEXT("Dev packs include Core"), Owned.Contains(TEXT("Core")));
	TestTrue(TEXT("Dev packs include added pack"), Owned.Contains(TEXT("Cosmetic.DevOnly")));
	TestEqual(TEXT("Dev query returns exactly 2 packs"), Owned.Num(), 2);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaRunCheckpointSerializedRoundTripTest,
	"Melodia.Persistence.RunCheckpointSerializedRoundTrip",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaRunCheckpointSerializedRoundTripTest::RunTest(const FString& Parameters)
{
	UGameInstance* Owner = NewObject<UGameInstance>();
	UMelodiaRoguelikeRunSubsystem* SourceRun = NewObject<UMelodiaRoguelikeRunSubsystem>(Owner);
	SourceRun->StartStructuredRun(20260718, 2, 3);
	TestTrue(TEXT("Generation reaches exploration"), SourceRun->RecordGenerationResult(true));
	TestTrue(TEXT("Encounter starts"), SourceRun->NotifyEncounterStarted());
	TestTrue(TEXT("Victory produces rewards"), SourceRun->RecordEncounterResult(EMelodiaEncounterResult::Victory));
	TestTrue(TEXT("Reward commits without advancing"), SourceRun->CommitReward(0));
	SourceRun->SetCompanionState(true, true, false, 9);

	UMelodiaRoguelikeRunCheckpointSaveGame* SourceSave = NewObject<UMelodiaRoguelikeRunCheckpointSaveGame>();
	SourceSave->Snapshot = SourceRun->ExportSnapshot();
	SourceSave->PartyHP = 63.5f;
	SourceSave->PartyMaxHP = 120.0f;
	SourceSave->SkillPoints = 2;
	SourceSave->SkillPointMax = 5;
	SourceSave->UltimateGauge = 74.0f;
	SourceSave->KeyElement = EMelodiaSpellElement::Tide;
	SourceSave->bHarmonicKeyEquipped = true;
	SourceSave->SavedAtUtc = FDateTime::UtcNow();

	TArray<uint8> Bytes;
	TestTrue(TEXT("Checkpoint serializes to SaveGame bytes"), UGameplayStatics::SaveGameToMemory(SourceSave, Bytes));
	TestTrue(TEXT("Serialized checkpoint is non-empty"), !Bytes.IsEmpty());
	UMelodiaRoguelikeRunCheckpointSaveGame* LoadedSave = Cast<UMelodiaRoguelikeRunCheckpointSaveGame>(
		UGameplayStatics::LoadGameFromMemory(Bytes));
	if (!TestNotNull(TEXT("Serialized checkpoint loads as expected class"), LoadedSave))
	{
		return false;
	}

	UMelodiaRoguelikeRunSubsystem* LoadedRun = NewObject<UMelodiaRoguelikeRunSubsystem>(Owner);
	TestTrue(TEXT("Fresh run imports serialized snapshot"), LoadedRun->ImportSnapshot(LoadedSave->Snapshot));
	TestEqual(TEXT("Seed survives serialization"), LoadedRun->RunSeed, SourceRun->RunSeed);
	TestEqual(TEXT("Stage survives serialization"), LoadedRun->CurrentStageIndex, SourceRun->CurrentStageIndex);
	TestEqual(TEXT("Transition phase survives serialization"), LoadedRun->LifecyclePhase, EMelodiaRunLifecyclePhase::TransitionReady);
	TestEqual(TEXT("RoomData survives serialization"), LoadedRun->AuthoritativeStage.RoomDataId, SourceRun->AuthoritativeStage.RoomDataId);
	TestEqual(TEXT("Acquired rewards survive serialization"), LoadedRun->AcquiredRewardIds, SourceRun->AcquiredRewardIds);
	TestTrue(TEXT("Sir presence survives serialization"), LoadedRun->bCompanionPresent);
	TestTrue(TEXT("Sir resonance survives serialization"), LoadedRun->CanUseEmpoweredMusic());
	TestFalse(TEXT("Playable companion remains independently locked"), LoadedRun->bCompanionPlayable);
	TestEqual(TEXT("Companion bond survives serialization"), LoadedRun->CompanionBond, 9);

	UMelodiaBattleSession* LoadedBattle = NewObject<UMelodiaBattleSession>(Owner);
	LoadedBattle->RestorePersistentPartyState(LoadedSave->PartyHP, LoadedSave->PartyMaxHP,
		LoadedSave->SkillPoints, LoadedSave->SkillPointMax, LoadedSave->UltimateGauge,
		LoadedSave->KeyElement, LoadedSave->bHarmonicKeyEquipped);
	TestEqual(TEXT("HP survives serialization"), LoadedBattle->PersistentPartyHP, 63.5f);
	TestEqual(TEXT("Max HP survives serialization"), LoadedBattle->PersistentPartyMaxHP, 120.0f);
	TestEqual(TEXT("SP survives serialization"), LoadedBattle->PersistentSkillPoints, 2);
	TestEqual(TEXT("SP cap survives serialization"), LoadedBattle->PersistentSkillPointMax, 5);
	TestEqual(TEXT("Ultimate survives serialization"), LoadedBattle->PersistentUltimateGauge, 74.0f);
	TestEqual(TEXT("Key element survives serialization"), LoadedBattle->PersistentEquippedKeyElement, EMelodiaSpellElement::Tide);
	TestTrue(TEXT("Harmonic key survives serialization"), LoadedBattle->bPersistentHarmonicKeyEquipped);

	const int32 StageBeforeExit = LoadedRun->CurrentStageIndex;
	TestTrue(TEXT("Restored transition accepts exactly one exit"), LoadedRun->RequestStageAdvance());
	TestFalse(TEXT("Restored transition rejects duplicate exit"), LoadedRun->RequestStageAdvance());
	TestEqual(TEXT("Restored exit advances one stage"), LoadedRun->CurrentStageIndex, StageBeforeExit + 1);
	return true;
}
#endif
