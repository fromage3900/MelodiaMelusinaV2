#include "MelodiaDungeonRunCoordinator.h"

#include "EngineUtils.h"
#include "MelodiaBattleSession.h"
#include "MelodiaRoomExit.h"
#include "MelodiaRoomEntrance.h"
#include "MelodiaEncounterTrigger.h"
#include "MelodiaDungeonRecipeConsumer.h"
#include "MelodiaRoguelikeRewardWidget.h"
#include "MelodiaRoguelikePersistence.h"
#include "MelodiaRoguelikeDefinitions.h"
#include "MelodiaSirMelodiousIntroActor.h"
#include "MelodiaOpeningFlowSubsystem.h"
#include "Blueprint/UserWidget.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"
#include "PCGComponent.h"
#include "DungeonBlueprintLibrary.h"
#include "RoomData.h"

AMelodiaDungeonRunCoordinator::AMelodiaDungeonRunCoordinator()
{
	PrimaryActorTick.bCanEverTick = false;
}

void AMelodiaDungeonRunCoordinator::BeginPlay()
{
	Super::BeginPlay();
	RunSubsystem = UMelodiaRoguelikeRunSubsystem::Get(this);
	BattleSession = UMelodiaBattleSession::Get(this);
	if (!DungeonGenerator)
	{
		for (TActorIterator<ADungeonGeneratorBase> It(GetWorld()); It; ++It)
		{
			DungeonGenerator = *It;
			break;
		}
	}

	if (BattleSession)
	{
		BattleSession->OnBattlePhaseChanged.AddUniqueDynamic(this, &AMelodiaDungeonRunCoordinator::HandleBattlePhaseChanged);
		BattleSession->OnEncounterEnded.AddUniqueDynamic(this, &AMelodiaDungeonRunCoordinator::HandleEncounterEnded);
	}
	if (RunSubsystem)
	{
		RunSubsystem->OnRewardCandidatesReady.AddUniqueDynamic(this, &AMelodiaDungeonRunCoordinator::HandleRewardsReady);
		RunSubsystem->OnRunCompleted.AddUniqueDynamic(this, &AMelodiaDungeonRunCoordinator::HandleRunCompleted);
		RunSubsystem->OnRunDefeated.AddUniqueDynamic(this, &AMelodiaDungeonRunCoordinator::HandleRunDefeated);
	}

	Persistence = UMelodiaRoguelikePersistenceSubsystem::Get(this);
	if (DungeonGenerator)
	{
		DungeonGenerator->OnPostGenerationEvent.AddUniqueDynamic(this, &AMelodiaDungeonRunCoordinator::HandleGenerationComplete);
		DungeonGenerator->OnGenerationFailedEvent.AddUniqueDynamic(this, &AMelodiaDungeonRunCoordinator::HandleGenerationFailed);
	}

	if (RunSubsystem && bStartRunOnBeginPlay && RunSubsystem->Phase == EMelodiaRunPhase::Inactive)
	{

		const bool bHasArchetype = ResolveArchetype();
		if (!bHasArchetype)
		{
			UE_LOG(LogTemp, Log, TEXT("Melodia: no archetype assigned for auto-start; using hardcoded stage pool."));
		}
		RunSubsystem->StartStructuredRun(InitialRunSeed,
			bHasArchetype ? RunSubsystem->StructuredActCount : 1,
			bHasArchetype ? RunSubsystem->StructuredStagesPerAct : 3);
		BeginStageTransition();
		SetPlayerTransitionLocked(true);
		BeginGenerationRequest();
	}
}

void AMelodiaDungeonRunCoordinator::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (BattleSession)
	{
		BattleSession->OnBattlePhaseChanged.RemoveDynamic(this, &AMelodiaDungeonRunCoordinator::HandleBattlePhaseChanged);
		BattleSession->OnEncounterEnded.RemoveDynamic(this, &AMelodiaDungeonRunCoordinator::HandleEncounterEnded);
	}
	if (RunSubsystem)
	{
		RunSubsystem->OnRewardCandidatesReady.RemoveDynamic(this, &AMelodiaDungeonRunCoordinator::HandleRewardsReady);
		RunSubsystem->OnRunCompleted.RemoveDynamic(this, &AMelodiaDungeonRunCoordinator::HandleRunCompleted);
		RunSubsystem->OnRunDefeated.RemoveDynamic(this, &AMelodiaDungeonRunCoordinator::HandleRunDefeated);
	}
	if (DungeonGenerator)
	{
		DungeonGenerator->OnPostGenerationEvent.RemoveDynamic(this, &AMelodiaDungeonRunCoordinator::HandleGenerationComplete);
		DungeonGenerator->OnGenerationFailedEvent.RemoveDynamic(this, &AMelodiaDungeonRunCoordinator::HandleGenerationFailed);
	}
	Super::EndPlay(EndPlayReason);
}

void AMelodiaDungeonRunCoordinator::HandleBattlePhaseChanged(const EMelodiaBattlePhase NewPhase, const EMelodiaBattlePhase PreviousPhase)
{
	if (RunSubsystem && NewPhase == EMelodiaBattlePhase::AwaitingPlayerCommand && PreviousPhase == EMelodiaBattlePhase::None)
	{
		RunSubsystem->NotifyEncounterStarted();
	}
}

void AMelodiaDungeonRunCoordinator::HandleEncounterEnded(const EMelodiaEncounterResult Result)
{
	if (RunSubsystem)
	{
		RunSubsystem->RecordEncounterResult(Result);
	}
}

void AMelodiaDungeonRunCoordinator::HandleRewardsReady(const TArray<FMelodiaRunRewardCandidate>& Candidates)
{
	SetRoomExitLocked(true);
	if (!RewardWidget)
	{
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
		{
			RewardWidget = CreateWidget<UMelodiaRoguelikeRewardWidget>(PC, UMelodiaRoguelikeRewardWidget::StaticClass());
			if (RewardWidget)
			{
				RewardWidget->Coordinator = this;
			}
		}
	}
	if (RewardWidget)
	{
		RewardWidget->ShowCandidates(Candidates);
	}
	PresentRewardChoices(Candidates);
}

bool AMelodiaDungeonRunCoordinator::CommitReward(const int32 CandidateIndex)
{
	if (!RunSubsystem || !RunSubsystem->SelectReward(CandidateIndex))
	{
		return false;
	}
	// GS-007: reward commit only unlocks the exit; RequestNextStage owns
	// AdvanceStage + Generate when the player actually crosses the doorway.
	SetRoomExitLocked(false);
	if (RewardWidget)
	{
		RewardWidget->HideChoices();
	}
	return true;
}

bool AMelodiaDungeonRunCoordinator::RequestNextStage()
{
	if (!RunSubsystem || !DungeonGenerator || !RunSubsystem->AdvanceStage())
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia stage transition rejected: run=%s generator=%s phase=%d."),
			RunSubsystem ? TEXT("valid") : TEXT("missing"), DungeonGenerator ? TEXT("valid") : TEXT("missing"),
			RunSubsystem ? static_cast<int32>(RunSubsystem->Phase) : -1);
		return false;
	}
	SetRoomExitLocked(true);
	SetPlayerTransitionLocked(true);
	BeginStageTransition();
	CheckpointCurrentStage();
	return BeginGenerationRequest();
}

bool AMelodiaDungeonRunCoordinator::StartFirstDungeonRun(const int32 Seed)
{
	if (!RunSubsystem || !DungeonGenerator || RunSubsystem->Phase != EMelodiaRunPhase::Inactive)
	{
		return false;
	}

	ResolveArchetype();
	RunSubsystem->StartStructuredRun(Seed,
		RunSubsystem->ResolvedArchetype ? RunSubsystem->StructuredActCount : 1,
		RunSubsystem->ResolvedArchetype ? RunSubsystem->StructuredStagesPerAct : 3);
	BeginStageTransition();
	SetPlayerTransitionLocked(true);
	return BeginGenerationRequest();
}

bool AMelodiaDungeonRunCoordinator::ContinueEndlessRun()
{
	if (!RunSubsystem || !DungeonGenerator || !RunSubsystem->ContinueEndless())
	{
		return false;
	}
	SetRoomExitLocked(true);
	SetPlayerTransitionLocked(true);
	BeginStageTransition();
	CheckpointCurrentStage();
	return BeginGenerationRequest();
}

bool AMelodiaDungeonRunCoordinator::RestartDungeonRun()
{
	if (!RunSubsystem || !DungeonGenerator || !RunSubsystem->RestartRun())
	{
		return false;
	}
	SetRoomExitLocked(true);
	SetPlayerTransitionLocked(true);
	BeginStageTransition();
	CheckpointCurrentStage();
	return BeginGenerationRequest();
}

void AMelodiaDungeonRunCoordinator::HandleGenerationComplete()
{
	if (!bGenerationRequestPending)
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia ignored stale or duplicate post-generation callback (attempt %d)."), GenerationAttemptId);
		return;
	}
	if (bGenerationFailedThisAttempt)
	{
		bGenerationRequestPending = false;
		return;
	}

	if (bRelocatePlayerAfterGeneration
		&& IsAnyStreamedRoomPCGGenerating()
		&& EntranceValidationRetryCount < MaxEntranceValidationRetries)
	{
		++EntranceValidationRetryCount;
		GetWorldTimerManager().SetTimer(EntranceValidationRetryHandle, this,
			&AMelodiaDungeonRunCoordinator::HandleGenerationComplete, EntranceValidationRetryDelaySeconds, false);
		return;
	}
	if (BattleSession && BattleSession->IsEncounterActive())
	{
		BattleSession->SubmitFleeCommand();
	}
	if (RunSubsystem)
	{
		for (TActorIterator<AMelodiaEncounterTrigger> It(GetWorld()); It; ++It)
		{
			if (!IsActorInAuthoritativeRoom(*It)) continue;
			It->EnemyId = RunSubsystem->AuthoritativeStage.EnemyId;
			It->EncounterDisplayName = RunSubsystem->AuthoritativeStage.StageIndex == 0
				? FText::FromString(TEXT("Sakura Sprite"))
				: FText::FromName(RunSubsystem->AuthoritativeStage.EnemyId);
			It->EncounterLevel = RunSubsystem->AuthoritativeStage.DifficultyTier;
		}
	}
	const bool bEntranceReady = !bRelocatePlayerAfterGeneration || RelocatePlayerToSafeEntrance();
	const bool bExitReady = ResolveActiveRoomExit();
	if ((!bEntranceReady || !bExitReady) && EntranceValidationRetryCount < MaxEntranceValidationRetries)
	{
		++EntranceValidationRetryCount;
		GetWorldTimerManager().SetTimer(EntranceValidationRetryHandle, this,
			&AMelodiaDungeonRunCoordinator::HandleGenerationComplete, EntranceValidationRetryDelaySeconds, false);
		return;
	}
	EntranceValidationRetryCount = 0;
	if (!bEntranceReady || !bExitReady)
	{
		if (!bEntranceReady)
		{
			ResolveActiveRoomEntrance(true);
		}
		UE_LOG(LogTemp, Error, TEXT("Melodia generation attempt %d rejected after streaming: entrance=%s exit=%s."),
			GenerationAttemptId, bEntranceReady ? TEXT("valid") : TEXT("invalid"),
			bExitReady ? TEXT("valid") : TEXT("invalid"));
		// Post-stream validation is part of generation. Route it through the same
		// deterministic fallback transaction as a native generator failure.
		HandleGenerationFailed();
		return;
	}
	bGenerationRequestPending = false;
	GetWorldTimerManager().ClearTimer(GenerationTimeoutHandle);
	if (RunSubsystem) RunSubsystem->RecordGenerationResult(true);
	SetRoomExitLocked(true);
	SetPlayerTransitionLocked(false);
}

void AMelodiaDungeonRunCoordinator::HandleGenerationFailed()
{
	if (!bGenerationRequestPending)
	{
		return;
	}
	bGenerationFailedThisAttempt = true;
	bGenerationRequestPending = false;
	GetWorldTimerManager().ClearTimer(GenerationTimeoutHandle);

	if (RunSubsystem
		&& FallbackAttemptsThisStage < MaxDeterministicFallbackAttempts
		&& RunSubsystem->ActivateDeterministicFallbackRecipe())
	{
		++FallbackAttemptsThisStage;
		UE_LOG(LogTemp, Warning, TEXT("Melodia generation failed; retrying stage %d with deterministic fallback (%d/%d)."),
			RunSubsystem->CurrentStageIndex, FallbackAttemptsThisStage, MaxDeterministicFallbackAttempts);
		bGenerationFailedThisAttempt = false;
		if (BeginGenerationRequest())
		{
			return;
		}
	}

	SetPlayerTransitionLocked(false);
	if (RunSubsystem)
	{
		RunSubsystem->RecordGenerationResult(false);
	}
}

void AMelodiaDungeonRunCoordinator::HandleGenerationTimeout()
{
	if (!bGenerationRequestPending)
	{
		return;
	}
	UE_LOG(LogTemp, Error, TEXT("Melodia stage generation timed out after %.1f seconds; run entered recoverable failure handling."),
		GenerationTimeoutSeconds);
	HandleGenerationFailed();
}

bool AMelodiaDungeonRunCoordinator::BeginGenerationRequest()
{
	if (!DungeonGenerator || !RunSubsystem || bGenerationRequestPending) return false;
	if (FallbackStageIndex != RunSubsystem->CurrentStageIndex)
	{
		FallbackStageIndex = RunSubsystem->CurrentStageIndex;
		FallbackAttemptsThisStage = 0;
	}
	if (!ApplyRecipeToGenerator())
	{
		RunSubsystem->RecordGenerationResult(false);
		SetPlayerTransitionLocked(false);
		return false;
	}
	ActiveRoomEntrance = nullptr;
	// Preserve an explicitly coordinator-owned exit in the persistent host map.
	// Streamed-room exits are transient and must be rediscovered after regeneration.
	const bool bPersistentAuthoredExit = IsValid(ActiveRoomExit)
		&& ActiveRoomExit->Coordinator == this
		&& UDungeonBlueprintLibrary::GetLevelRoomData(ActiveRoomExit) == nullptr;
	if (!bPersistentAuthoredExit)
	{
		ActiveRoomExit = nullptr;
	}
	++GenerationAttemptId;
	bGenerationRequestPending = true;
	bGenerationFailedThisAttempt = false;
	GetWorldTimerManager().SetTimer(GenerationTimeoutHandle, this,
		&AMelodiaDungeonRunCoordinator::HandleGenerationTimeout, GenerationTimeoutSeconds, false);
	DungeonGenerator->Generate();
	return true;
}

bool AMelodiaDungeonRunCoordinator::ApplyRecipeToGenerator()
{
	if (!DungeonGenerator || !RunSubsystem) return false;
	if (!DungeonGenerator->GetClass()->ImplementsInterface(UMelodiaDungeonRecipeConsumer::StaticClass()))
	{
		if (bRequireRecipeConsumer)
		{
			UE_LOG(LogTemp, Error,
				TEXT("[MELODIA_EDITOR_ACTION] Dungeon generator '%s' does not implement IMelodiaDungeonRecipeConsumer. ")
				TEXT("Open BP_RoguelikeDungeonGenerator > Class Settings > Interfaces, add 'MelodiaDungeonRecipeConsumer', recompile, re-save."),
				*GetNameSafe(DungeonGenerator));
			return false;
		}
		UE_LOG(LogTemp, Warning, TEXT("Dungeon generator '%s' bypasses recipe consumption in compatibility mode."),
			*GetNameSafe(DungeonGenerator));
		return true;
	}
	FText ValidationError;
	if (!IMelodiaDungeonRecipeConsumer::Execute_ValidateStageRecipe(
		DungeonGenerator, RunSubsystem->AuthoritativeStage, ValidationError))
	{
		UE_LOG(LogTemp, Error, TEXT("Generator rejected MelodiaCore recipe: %s"), *ValidationError.ToString());
		return false;
	}
	return IMelodiaDungeonRecipeConsumer::Execute_ApplyStageRecipe(
		DungeonGenerator, RunSubsystem->AuthoritativeStage);
}

bool AMelodiaDungeonRunCoordinator::IsAnyStreamedRoomPCGGenerating() const
{
	const UWorld* World = GetWorld();
	for (TObjectIterator<UPCGComponent> It; It; ++It)
	{
		if (It->GetWorld() == World && It->IsGenerating() && IsActorInAuthoritativeRoom(It->GetOwner()))
		{
			return true;
		}
	}
	return false;
}

bool AMelodiaDungeonRunCoordinator::IsActorInAuthoritativeRoom(const AActor* Actor) const
{
	if (!Actor || !RunSubsystem || RunSubsystem->AuthoritativeStage.RoomDataId.IsNone())
	{
		return false;
	}
	const URoomData* RoomData = UDungeonBlueprintLibrary::GetLevelRoomData(Actor);
	return RoomData && RoomData->GetFName() == RunSubsystem->AuthoritativeStage.RoomDataId;
}

bool AMelodiaDungeonRunCoordinator::RelocatePlayerToSafeEntrance()
{
	if (!ResolveActiveRoomEntrance(false)) return false;
	APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!PlayerPawn) return false;
	const FVector TraceStart = ActiveRoomEntrance->GetActorLocation() + FVector::UpVector * 200.0f;
	const FVector TraceEnd = ActiveRoomEntrance->GetActorLocation() - FVector::UpVector * SafeGroundTraceDepth;
	FHitResult GroundHit;
	FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(MelodiaSafeArrival), false, PlayerPawn);
	bool bFoundGround = GetWorld()->LineTraceSingleByChannel(
		GroundHit, TraceStart, TraceEnd, ECC_Visibility, QueryParams);
	if (!bFoundGround)
	{
		// Walkable room floors are not required to block Visibility. Query their
		// object type as a fallback so valid WorldStatic collision is authoritative
		// without accepting non-colliding art or weakening the grounded-arrival gate.
		FCollisionObjectQueryParams GroundObjectTypes;
		GroundObjectTypes.AddObjectTypesToQuery(ECC_WorldStatic);
		bFoundGround = GetWorld()->LineTraceSingleByObjectType(
			GroundHit, TraceStart, TraceEnd, GroundObjectTypes, QueryParams);
	}
	if (!bFoundGround)
	{
		UE_LOG(LogTemp, Error,
			TEXT("No safe ground found beneath entrance '%s' from %s to %s (Visibility and WorldStatic queries failed)."),
			*GetNameSafe(ActiveRoomEntrance), *TraceStart.ToCompactString(), *TraceEnd.ToCompactString());
		return false;
	}
	FVector Origin;
	FVector Extent;
	PlayerPawn->GetActorBounds(true, Origin, Extent);
	const FVector Destination = GroundHit.ImpactPoint + FVector::UpVector * (Extent.Z + SafeGroundClearance);
	if (!PlayerPawn->TeleportTo(Destination, ActiveRoomEntrance->GetActorRotation(), false, true))
	{
		UE_LOG(LogTemp, Error, TEXT("Could not place player at grounded entrance '%s'."), *GetNameSafe(ActiveRoomEntrance));
		return false;
	}
	FHitResult ConfirmationHit;
	const FVector ConfirmEnd = Destination - FVector::UpVector * (Extent.Z + SafeGroundClearance + 50.0f);
	bool bGroundConfirmed = GetWorld()->LineTraceSingleByChannel(
		ConfirmationHit, Destination, ConfirmEnd, ECC_Visibility, QueryParams);
	if (!bGroundConfirmed)
	{
		FCollisionObjectQueryParams GroundObjectTypes;
		GroundObjectTypes.AddObjectTypesToQuery(ECC_WorldStatic);
		bGroundConfirmed = GetWorld()->LineTraceSingleByObjectType(
			ConfirmationHit, Destination, ConfirmEnd, GroundObjectTypes, QueryParams);
	}
	return bGroundConfirmed;
}

void AMelodiaDungeonRunCoordinator::HandleRunCompleted()
{
	SetRoomExitLocked(true);
	if (RunSubsystem)
	{
		FMelodiaRunHistoryEntry Entry;
		Entry.RunSeed = RunSubsystem->RunSeed;
		Entry.FinalStageIndex = RunSubsystem->CurrentStageIndex;
		Entry.EndlessDepth = RunSubsystem->EndlessDepth;
		Entry.bCompletedStructuredRun = true;
		Entry.RewardIds = RunSubsystem->AcquiredRewardIds;
		if (Persistence)
		{
			Persistence->AppendRunHistory(Entry);
			// Preserve the EndlessOffer boundary so a crash or restart cannot erase
			// the player's earned option to continue the same deterministic run.
			Persistence->SaveRunCheckpoint();
			Persistence->SaveProfile();
		}
	}
	const FVector SpawnLocation = GetActorTransform().TransformPosition(SirMelodiousReunionOffset);
	GetWorld()->SpawnActor<AMelodiaSirMelodiousIntroActor>(AMelodiaSirMelodiousIntroActor::StaticClass(), SpawnLocation, GetActorRotation());
	UE_LOG(LogTemp, Log, TEXT("Melodia run: dungeon complete - Sir Melodious reunion spawned."));

	if (UMelodiaOpeningFlowSubsystem* Flow = UMelodiaOpeningFlowSubsystem::Get(this))
	{
		if (Flow->NotifySirRescued())
		{
			UE_LOG(LogTemp, Log, TEXT("Melodia run: SirRescued phase set on dungeon completion."));
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("Melodia run: NotifySirRescued rejected (phase=%d)."),
				static_cast<int32>(Flow->Phase));
		}
	}
}

void AMelodiaDungeonRunCoordinator::HandleRunDefeated()
{
	SetRoomExitLocked(true);
	if (RunSubsystem)
	{
		RunSubsystem->EndRun(false);
		FMelodiaRunHistoryEntry Entry;
		Entry.RunSeed = RunSubsystem->RunSeed;
		Entry.FinalStageIndex = RunSubsystem->CurrentStageIndex;
		Entry.EndlessDepth = RunSubsystem->EndlessDepth;
		Entry.bCompletedStructuredRun = false;
		if (Persistence)
		{
			Persistence->AppendRunHistory(Entry);
			Persistence->ClearRunCheckpoint();
			Persistence->SaveProfile();
		}
	}
	PresentDefeatSummary();
	UE_LOG(LogTemp, Log, TEXT("Melodia run: dungeon defeat - summary presented."));
}

void AMelodiaDungeonRunCoordinator::SetRoomExitLocked_Implementation(const bool bLocked)
{
	if (!IsValid(ActiveRoomExit) && !ResolveActiveRoomExit())
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia coordinator '%s' cannot %s room exit: no unique active exit."),
			*GetName(), bLocked ? TEXT("lock") : TEXT("unlock"));
		return;
	}
	ActiveRoomExit->SetLocked(bLocked);
}

bool AMelodiaDungeonRunCoordinator::ResolveActiveRoomExit()
{
	if (IsValid(ActiveRoomExit))
	{
		return true;
	}

	int32 CandidateCount = 0;
	AMelodiaRoomExit* Candidate = nullptr;
	for (TActorIterator<AMelodiaRoomExit> It(GetWorld()); It; ++It)
	{
		if (IsActorInAuthoritativeRoom(*It) && (It->Coordinator == this || !It->Coordinator))
		{
			++CandidateCount;
			Candidate = *It;
		}
	}
	if (CandidateCount != 1)
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia coordinator '%s' expected exactly one owned room exit; found %d."),
			*GetName(), CandidateCount);
		return false;
	}
	ActiveRoomExit = Candidate;
	if (!ActiveRoomExit->Coordinator)
	{
		ActiveRoomExit->Coordinator = this;
	}
	return true;
}

bool AMelodiaDungeonRunCoordinator::ResolveActiveRoomEntrance(const bool bLogFailure)
{
	if (IsValid(ActiveRoomEntrance))
	{
		return true;
	}

	int32 TotalCount = 0;
	int32 PrimaryCount = 0;
	AMelodiaRoomEntrance* OnlyCandidate = nullptr;
	AMelodiaRoomEntrance* PrimaryCandidate = nullptr;
	for (TActorIterator<AMelodiaRoomEntrance> It(GetWorld()); It; ++It)
	{
		if (!IsActorInAuthoritativeRoom(*It)) continue;
		++TotalCount;
		OnlyCandidate = *It;
		if (It->bPrimaryRunEntrance)
		{
			++PrimaryCount;
			PrimaryCandidate = *It;
		}
	}
	if (PrimaryCount == 1)
	{
		ActiveRoomEntrance = PrimaryCandidate;
		return true;
	}
	if (PrimaryCount == 0 && TotalCount == 1)
	{
		ActiveRoomEntrance = OnlyCandidate;
		return true;
	}
	if (bLogFailure)
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia coordinator '%s' expected one primary generated-room entrance; found %d primary among %d total. Player was not moved."),
			*GetName(), PrimaryCount, TotalCount);
	}
	return false;
}

void AMelodiaDungeonRunCoordinator::SetPlayerTransitionLocked(const bool bLocked)
{
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
	{
		if (bLocked)
		{
			PC->SetIgnoreMoveInput(true);
			PC->SetIgnoreLookInput(true);
		}
		else
		{
			// Release only the lock acquired by this coordinator. ResetIgnore* would
			// clear locks owned by menus, cinematics, or other gameplay systems.
			PC->SetIgnoreMoveInput(false);
			PC->SetIgnoreLookInput(false);
		}
	}
}

void AMelodiaDungeonRunCoordinator::CheckpointCurrentStage()
{
	if (Persistence)
	{
		Persistence->OnOperationCompleted.AddUniqueDynamic(this, &AMelodiaDungeonRunCoordinator::OnPersistenceOperation);
		Persistence->SaveRunCheckpoint();
	}
}

void AMelodiaDungeonRunCoordinator::OnPersistenceOperation(FName Operation, bool bSuccess)
{
	UE_LOG(LogTemp, Log, TEXT("Melodia persistence: %s %s."), *Operation.ToString(), bSuccess ? TEXT("succeeded") : TEXT("FAILED"));
}

bool AMelodiaDungeonRunCoordinator::ResolveArchetype()
{
	if (RunArchetype.IsNull() || !RunSubsystem) return false;
	const UMelodiaRunArchetypeDefinition* Archetype = RunArchetype.LoadSynchronous();
	if (!Archetype) return false;
	TArray<FText> Errors;
	if (!Archetype->ValidateDefinition(Errors))
	{
		for (const FText& Error : Errors)
		{
			UE_LOG(LogTemp, Warning, TEXT("Melodia archetype validation error: %s"), *Error.ToString());
		}
		return false;
	}
	RunSubsystem->ApplyArchetype(Archetype);
	return true;
}
