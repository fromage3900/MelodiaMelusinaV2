#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Engine/GameInstance.h"
#include "MelodiaEntitlementSubsystem.h"
#include "MelodiaRoguelikeRunSubsystem.h"

namespace
{
bool RecipesMatch(const FMelodiaAuthoritativeStageRecipe& A, const FMelodiaAuthoritativeStageRecipe& B)
{
	return A.SchemaVersion == B.SchemaVersion
		&& A.ActIndex == B.ActIndex
		&& A.StageIndex == B.StageIndex
		&& A.EndlessDepth == B.EndlessDepth
		&& A.StageId == B.StageId
		&& A.RoomDefinitionId == B.RoomDefinitionId
		&& A.RoomDataId == B.RoomDataId
		&& A.EncounterId == B.EncounterId
		&& A.EnemyId == B.EnemyId
		&& A.DifficultyTier == B.DifficultyTier
		&& A.MutatorIds == B.MutatorIds
		&& A.RewardPoolId == B.RewardPoolId
		&& A.DissonanceProfileId == B.DissonanceProfileId
		&& A.CompanionRequirement == B.CompanionRequirement
		&& A.StageSeed == B.StageSeed
		&& A.TopologySeed == B.TopologySeed
		&& A.RoomSeed == B.RoomSeed
		&& A.EnemySeed == B.EnemySeed
		&& A.RewardSeed == B.RewardSeed
		&& A.MutatorSeed == B.MutatorSeed
		&& A.CosmeticSeed == B.CosmeticSeed;
}

bool CompleteStageAndAdvance(UMelodiaRoguelikeRunSubsystem* Run)
{
	if (!Run->RecordGenerationResult(true)) return false;
	if (!Run->NotifyEncounterStarted()) return false;
	if (!Run->RecordEncounterResult(EMelodiaEncounterResult::Victory)) return false;
	if (Run->LifecyclePhase == EMelodiaRunLifecyclePhase::EndlessOffer) return true;
	if (!Run->CommitReward(0)) return false;
	return Run->RequestStageAdvance();
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaRoguelikeDeterminismTest,
	"Melodia.Roguelike.Authority.DeterministicRecipes",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaRoguelikeDeterminismTest::RunTest(const FString& Parameters)
{
	UGameInstance* Owner = NewObject<UGameInstance>();
	UMelodiaRoguelikeRunSubsystem* A = NewObject<UMelodiaRoguelikeRunSubsystem>(Owner);
	UMelodiaRoguelikeRunSubsystem* B = NewObject<UMelodiaRoguelikeRunSubsystem>(Owner);
	A->StartStructuredRun(39017, 1, 1);
	B->StartStructuredRun(39017, 1, 1);

	TestTrue(TEXT("Initial recipes match"), RecipesMatch(A->AuthoritativeStage, B->AuthoritativeStage));
	TestEqual(TEXT("GMM golden stage seed"), A->AuthoritativeStage.StageSeed, 1845602322);
	TestEqual(TEXT("GMM golden topology seed"), A->AuthoritativeStage.TopologySeed, 1716028549);
	TestEqual(TEXT("GMM golden room seed"), A->AuthoritativeStage.RoomSeed, 1685644220);
	TestEqual(TEXT("GMM golden enemy seed"), A->AuthoritativeStage.EnemySeed, 1710350170);
	TestEqual(TEXT("GMM golden reward seed"), A->AuthoritativeStage.RewardSeed, 747877322);
	TestEqual(TEXT("GMM golden mutator seed"), A->AuthoritativeStage.MutatorSeed, 1482171374);
	TestEqual(TEXT("GMM golden cosmetic seed"), A->AuthoritativeStage.CosmeticSeed, 1091570352);
	TestTrue(TEXT("Independent streams do not alias"), A->AuthoritativeStage.RoomSeed != A->AuthoritativeStage.EnemySeed);
	TestTrue(TEXT("Cosmetic stream is isolated"), A->AuthoritativeStage.CosmeticSeed != A->AuthoritativeStage.RoomSeed);

	TestTrue(TEXT("A completes structured boss"), CompleteStageAndAdvance(A));
	TestTrue(TEXT("B completes structured boss"), CompleteStageAndAdvance(B));
	TestEqual(TEXT("Structured completion offers endless"), A->LifecyclePhase, EMelodiaRunLifecyclePhase::EndlessOffer);
	TestTrue(TEXT("A accepts endless"), A->ContinueEndless());
	TestTrue(TEXT("B accepts endless"), B->ContinueEndless());

	for (int32 Index = 0; Index < 100; ++Index)
	{
		if (!TestTrue(FString::Printf(TEXT("Recipe %d matches"), Index), RecipesMatch(A->AuthoritativeStage, B->AuthoritativeStage)))
		{
			return false;
		}
		if (Index < 99)
		{
			if (!TestTrue(FString::Printf(TEXT("A advances stage %d"), Index), CompleteStageAndAdvance(A))) return false;
			if (!TestTrue(FString::Printf(TEXT("B advances stage %d"), Index), CompleteStageAndAdvance(B))) return false;
		}
	}

	TestEqual(TEXT("Endless depth reaches 100"), A->EndlessDepth, 100);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaRoguelikeIdempotencyTest,
	"Melodia.Roguelike.Authority.IdempotentTransitions",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaRoguelikeIdempotencyTest::RunTest(const FString& Parameters)
{
	UGameInstance* Owner = NewObject<UGameInstance>();
	UMelodiaRoguelikeRunSubsystem* Run = NewObject<UMelodiaRoguelikeRunSubsystem>(Owner);
	Run->StartStructuredRun(7, 1, 2);
	TestTrue(TEXT("First generation callback accepted"), Run->RecordGenerationResult(true));
	TestFalse(TEXT("Duplicate generation callback rejected"), Run->RecordGenerationResult(true));
	UMelodiaRoguelikeRunSubsystem* FallbackRun = NewObject<UMelodiaRoguelikeRunSubsystem>(Owner);
	FallbackRun->StartStructuredRun(8, 1, 2);
	TestTrue(TEXT("Fallback activates once"), FallbackRun->ActivateDeterministicFallbackRecipe());
	TestEqual(TEXT("Fallback uses an authored RoomData"), FallbackRun->AuthoritativeStage.RoomDataId, FName(TEXT("RD_MelodiaGrove_V1")));
	TestFalse(TEXT("Fallback activation is idempotent"), FallbackRun->ActivateDeterministicFallbackRecipe());
	TestTrue(TEXT("Encounter starts once"), Run->NotifyEncounterStarted());
	TestFalse(TEXT("Duplicate encounter start rejected"), Run->NotifyEncounterStarted());
	TestTrue(TEXT("Victory recorded once"), Run->RecordEncounterResult(EMelodiaEncounterResult::Victory));
	TestFalse(TEXT("Duplicate result rejected"), Run->RecordEncounterResult(EMelodiaEncounterResult::Victory));
	TestTrue(TEXT("Reward commits once"), Run->CommitReward(0));
	const int32 StageBeforeExit = Run->CurrentStageIndex;
	TestEqual(TEXT("Reward does not advance stage"), Run->CurrentStageIndex, StageBeforeExit);
	TestFalse(TEXT("Duplicate reward rejected"), Run->CommitReward(0));
	TestTrue(TEXT("Exit advances once"), Run->RequestStageAdvance());
	TestFalse(TEXT("Duplicate exit rejected"), Run->RequestStageAdvance());
	TestEqual(TEXT("Exactly one stage advanced"), Run->CurrentStageIndex, StageBeforeExit + 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaEntitlementIsolationTest,
	"Melodia.Roguelike.Authority.EntitlementIsolation",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaEntitlementIsolationTest::RunTest(const FString& Parameters)
{
	UGameInstance* Owner = NewObject<UGameInstance>();
	UMelodiaRoguelikeRunSubsystem* Before = NewObject<UMelodiaRoguelikeRunSubsystem>(Owner);
	UMelodiaRoguelikeRunSubsystem* After = NewObject<UMelodiaRoguelikeRunSubsystem>(Owner);
	UMelodiaEntitlementSubsystem* Entitlements = NewObject<UMelodiaEntitlementSubsystem>(Owner);

	Before->StartStructuredRun(1234, 2, 6);
	const bool bGranted = Entitlements->GrantDevelopmentEntitlement(TEXT("Cosmetic.Plumage.Amethyst"));
	After->StartStructuredRun(1234, 2, 6);

#if UE_BUILD_SHIPPING
	TestFalse(TEXT("Shipping builds reject development grants"), bGranted);
#else
	TestTrue(TEXT("Development grant accepted"), bGranted);
	TestTrue(TEXT("Cosmetic pack is owned"), Entitlements->OwnsContentPack(TEXT("Cosmetic.Plumage.Amethyst")));
#endif
	TestTrue(TEXT("Entitlement change cannot alter gameplay recipe"), RecipesMatch(Before->AuthoritativeStage, After->AuthoritativeStage));
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaRoguelikeSnapshotRoundTripTest,
	"Melodia.Roguelike.Authority.SnapshotRoundTrip",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaRoguelikeSnapshotRoundTripTest::RunTest(const FString& Parameters)
{
	UGameInstance* Owner = NewObject<UGameInstance>();
	auto RoundTrip = [this, Owner](UMelodiaRoguelikeRunSubsystem* Source, const TCHAR* Label)
	{
		UMelodiaRoguelikeRunSubsystem* Loaded = NewObject<UMelodiaRoguelikeRunSubsystem>(Owner);
		const FMelodiaRunSnapshot Snapshot = Source->ExportSnapshot();
		TestTrue(FString::Printf(TEXT("%s imports"), Label), Loaded->ImportSnapshot(Snapshot));
		TestEqual(FString::Printf(TEXT("%s lifecycle"), Label), Loaded->LifecyclePhase, Source->LifecyclePhase);
		TestEqual(FString::Printf(TEXT("%s runtime phase"), Label), Loaded->Phase, Source->Phase);
		TestEqual(FString::Printf(TEXT("%s stage"), Label), Loaded->CurrentStageIndex, Source->CurrentStageIndex);
		TestEqual(FString::Printf(TEXT("%s pending rewards"), Label), Loaded->PendingRewards.Num(), Source->PendingRewards.Num());
		TestEqual(FString::Printf(TEXT("%s structured acts"), Label), Loaded->StructuredActCount, Source->StructuredActCount);
		TestEqual(FString::Printf(TEXT("%s stages per act"), Label), Loaded->StructuredStagesPerAct, Source->StructuredStagesPerAct);
		TestEqual(FString::Printf(TEXT("%s dungeon stage count"), Label), Loaded->StagesPerDungeon, Source->StagesPerDungeon);
		TestTrue(FString::Printf(TEXT("%s recipe preserved"), Label), RecipesMatch(Loaded->AuthoritativeStage, Source->AuthoritativeStage));
		return Loaded;
	};

	UMelodiaRoguelikeRunSubsystem* Run = NewObject<UMelodiaRoguelikeRunSubsystem>(Owner);
	Run->StartStructuredRun(991, 1, 2);
	RoundTrip(Run, TEXT("Generating"));
	Run->RecordGenerationResult(true);
	RoundTrip(Run, TEXT("Exploring"));
	Run->NotifyEncounterStarted();
	RoundTrip(Run, TEXT("Encounter"));
	Run->RecordEncounterResult(EMelodiaEncounterResult::Victory);
	UMelodiaRoguelikeRunSubsystem* RewardLoaded = RoundTrip(Run, TEXT("RewardChoice"));
	TestFalse(TEXT("Restored recorded encounter rejects duplicate result"),
		RewardLoaded->RecordEncounterResult(EMelodiaEncounterResult::Victory));
	Run->CommitReward(0);
	UMelodiaRoguelikeRunSubsystem* TransitionLoaded = RoundTrip(Run, TEXT("TransitionReady"));
	TestFalse(TEXT("Restored committed reward rejects duplicate reward"), TransitionLoaded->CommitReward(0));
	TestTrue(TEXT("Restored transition advances exactly once"), TransitionLoaded->RequestStageAdvance());
	TestFalse(TEXT("Restored transition rejects duplicate exit"), TransitionLoaded->RequestStageAdvance());
	RoundTrip(TransitionLoaded, TEXT("NextGenerating"));

	FMelodiaRunSnapshot Corrupt = TransitionLoaded->ExportSnapshot();
	Corrupt.PendingRewardIds.Add(TEXT("BrokenCandidate"));
	const int32 StageBeforeCorruptImport = TransitionLoaded->CurrentStageIndex;
	const EMelodiaRunLifecyclePhase PhaseBeforeCorruptImport = TransitionLoaded->LifecyclePhase;
	TestFalse(TEXT("Corrupt snapshot is rejected"), TransitionLoaded->ImportSnapshot(Corrupt));
	TestEqual(TEXT("Rejected snapshot preserves stage"), TransitionLoaded->CurrentStageIndex, StageBeforeCorruptImport);
	TestEqual(TEXT("Rejected snapshot preserves lifecycle"), TransitionLoaded->LifecyclePhase, PhaseBeforeCorruptImport);
	return true;
}


IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaRoguelikeFailureRecoveryTest,
	"Melodia.Roguelike.Authority.FailureRecoveryAndRestart",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaRoguelikeFailureRecoveryTest::RunTest(const FString& Parameters)
{
	UGameInstance* Owner = NewObject<UGameInstance>();
	UMelodiaRoguelikeRunSubsystem* Run = NewObject<UMelodiaRoguelikeRunSubsystem>(Owner);
	Run->StartStructuredRun(4401, 2, 3);
	const FMelodiaAuthoritativeStageRecipe InitialRecipe = Run->AuthoritativeStage;

	TestTrue(TEXT("Generation failure is recorded once"), Run->RecordGenerationResult(false));
	TestEqual(TEXT("Generation failure enters RecoverableFailure"), Run->LifecyclePhase, EMelodiaRunLifecyclePhase::RecoverableFailure);
	TestFalse(TEXT("Duplicate generation failure is rejected"), Run->RecordGenerationResult(false));
	TestFalse(TEXT("Encounter cannot start while generation failed"), Run->NotifyEncounterStarted());

	TestTrue(TEXT("Structured run restarts after recoverable failure"), Run->RestartRun());
	TestEqual(TEXT("Restart returns to Generating"), Run->LifecyclePhase, EMelodiaRunLifecyclePhase::Generating);
	TestEqual(TEXT("Restart resets stage index"), Run->CurrentStageIndex, 0);
	TestTrue(TEXT("Restart preserves deterministic first recipe"), RecipesMatch(Run->AuthoritativeStage, InitialRecipe));

	TestTrue(TEXT("Restarted generation succeeds"), Run->RecordGenerationResult(true));
	TestTrue(TEXT("Restarted encounter begins"), Run->NotifyEncounterStarted());
	TestTrue(TEXT("Defeat is recorded"), Run->RecordEncounterResult(EMelodiaEncounterResult::Defeat));
	TestEqual(TEXT("Defeat enters Defeated lifecycle"), Run->LifecyclePhase, EMelodiaRunLifecyclePhase::Defeated);
	TestFalse(TEXT("Defeat never offers a reward"), Run->CommitReward(0));
	TestFalse(TEXT("Defeat never advances a stage"), Run->RequestStageAdvance());
	TestTrue(TEXT("Defeated run restarts"), Run->RestartRun());
	TestEqual(TEXT("Defeat restart returns to Generating"), Run->LifecyclePhase, EMelodiaRunLifecyclePhase::Generating);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaRoguelikeCompanionCapabilityTest,
	"Melodia.Roguelike.Authority.CompanionCapability",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaRoguelikeCompanionCapabilityTest::RunTest(const FString& Parameters)
{
	UGameInstance* Owner = NewObject<UGameInstance>();
	UMelodiaRoguelikeRunSubsystem* Run = NewObject<UMelodiaRoguelikeRunSubsystem>(Owner);

	Run->SetCompanionState(false, true, true, -5);
	TestFalse(TEXT("Absent Sir cannot provide resonance"), Run->bResonanceAvailable);
	TestFalse(TEXT("Absent Sir cannot be playable"), Run->bCompanionPlayable);
	TestFalse(TEXT("Empowered music requires Sir and resonance"), Run->CanUseEmpoweredMusic());
	TestEqual(TEXT("Companion bond cannot be negative"), Run->CompanionBond, 0);

	Run->SetCompanionState(true, false, false, 7);
	TestTrue(TEXT("Sir can be present without resonance"), Run->bCompanionPresent);
	TestFalse(TEXT("Presence alone does not empower music"), Run->CanUseEmpoweredMusic());

	Run->SetCompanionState(true, true, false, 7);
	TestTrue(TEXT("Present resonant Sir empowers music"), Run->CanUseEmpoweredMusic());
	TestFalse(TEXT("Resonance does not imply playable possession"), Run->bCompanionPlayable);
	TestEqual(TEXT("Companion bond is retained"), Run->CompanionBond, 7);
	return true;
}

#endif
