#include "MelodiaRoguelikeRunSubsystem.h"

// Runtime-only implementation; editor Python is intentionally not a dependency.

#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "MelodiaBattleSession.h"
#include "MelodiaRoguelikeDefinitions.h"
#include "RoomData.h"

UMelodiaRoguelikeRunSubsystem* UMelodiaRoguelikeRunSubsystem::Get(const UObject* WorldContextObject)
{
	const UWorld* World = WorldContextObject ? WorldContextObject->GetWorld() : nullptr;
	return World && World->GetGameInstance()
		? World->GetGameInstance()->GetSubsystem<UMelodiaRoguelikeRunSubsystem>()
		: nullptr;
}

void UMelodiaRoguelikeRunSubsystem::StartNewRun(const int32 Seed)
{
	RunSeed = Seed;
	CurrentStageIndex = 0;
	RandomStream.Initialize(RunSeed);
	PendingRewards.Reset();
	AcquiredRewardIds.Reset();
	SongPowerMultiplier = 1.0f;
	RecoveryMultiplier = 1.0f;
	Dissonance = 0.0f;
	HeartMelodyTokensConsumed = 0;
	SwirlMelodyTokensConsumed = 0;
	bSirMelodiousAvailable = false;
	bEncounterResultRecorded = false;
	bRewardCommitted = false;
	SetPhase(EMelodiaRunPhase::Generating);
	SetLifecyclePhase(EMelodiaRunLifecyclePhase::Generating);
	BuildCurrentStage();
}

void UMelodiaRoguelikeRunSubsystem::BuildCurrentStage()
{
	// Build pool arrays from archetype when available, else use hardcoded defaults
	TArray<FName> StageIds = { TEXT("Grove"), TEXT("ResonantBridge"), TEXT("DissonantClearing"), TEXT("MemoryCache"), TEXT("Crescendo") };
	TArray<FName> EnemyIds = { TEXT("CrystalShard"), TEXT("StoneGolem"), TEXT("VoidWraith"), TEXT("FireDrake") };
	TArray<FName> RoomDataIds = { TEXT("RD_MelodiaGrove_V1"), TEXT("RD_MelodiaGrove_V2"), TEXT("RD_MelodiaGrove_V1"), TEXT("RD_MelodiaGrove_V2"), TEXT("RD_MelodiaGrove_V1") };

	if (ResolvedArchetype)
	{
		if (ResolvedArchetype->Rooms.Num() > 0)
		{
			StageIds.Reset();
			RoomDataIds.Reset();
			for (const TSoftObjectPtr<UMelodiaRoomDefinition>& RoomPtr : ResolvedArchetype->Rooms)
			{
				if (const UMelodiaRoomDefinition* Room = RoomPtr.LoadSynchronous())
				{
					if (const URoomData* RoomData = Room->RoomData.LoadSynchronous())
					{
						const FName RoomDataId = RoomData->GetFName();
						const bool bPhysicallyValidatedRoom = RoomDataId == FName(TEXT("RD_MelodiaGrove_V1"))
							|| RoomDataId == FName(TEXT("RD_MelodiaGrove_V2"));
						if (bPhysicallyValidatedRoom)
						{
							StageIds.Add(Room->StableId);
							RoomDataIds.Add(RoomDataId);
						}
						else
						{
							UE_LOG(LogTemp, Warning,
								TEXT("Melodia excluded RoomData '%s' from runtime selection because it has not passed the physical entrance/exit contract."),
								*RoomDataId.ToString());
						}
					}
				}
			}
		}
		if (ResolvedArchetype->Encounters.Num() > 0)
		{
			EnemyIds.Reset();
			for (const TSoftObjectPtr<UMelodiaRoguelikeEncounterDefinition>& EncPtr : ResolvedArchetype->Encounters)
			{
				if (const UMelodiaRoguelikeEncounterDefinition* Enc = EncPtr.LoadSynchronous())
					EnemyIds.Add(Enc->EnemyId);
			}
		}
	}

	if (StageIds.IsEmpty() || RoomDataIds.IsEmpty() || StageIds.Num() != RoomDataIds.Num())
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia archetype resolved to no physically validated rooms; using the authored core fallback pool."));
		StageIds = { TEXT("Grove"), TEXT("ResonantBridge"), TEXT("DissonantClearing"), TEXT("MemoryCache"), TEXT("Crescendo") };
		RoomDataIds = { TEXT("RD_MelodiaGrove_V1"), TEXT("RD_MelodiaGrove_V2"), TEXT("RD_MelodiaGrove_V1"), TEXT("RD_MelodiaGrove_V2"), TEXT("RD_MelodiaGrove_V1") };
	}
	if (EnemyIds.IsEmpty())
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia archetype resolved to no loadable encounters; using the authored core fallback pool."));
		EnemyIds = { TEXT("CrystalShard"), TEXT("StoneGolem"), TEXT("VoidWraith"), TEXT("FireDrake") };
	}
	AuthoritativeStage = FMelodiaAuthoritativeStageRecipe();
	bFallbackRecipeActive = false;
	AuthoritativeStage.StageIndex = CurrentStageIndex;
	AuthoritativeStage.ActIndex = bStructuredMode && StructuredStagesPerAct > 0 ? CurrentStageIndex / StructuredStagesPerAct : 0;
	AuthoritativeStage.EndlessDepth = EndlessDepth;
	AuthoritativeStage.StageSeed = DeriveSeed(RunSeed, CurrentStageIndex, 0x53544147u);
	AuthoritativeStage.TopologySeed = DeriveSeed(RunSeed, CurrentStageIndex, 0x544f504fu);
	AuthoritativeStage.RoomSeed = DeriveSeed(RunSeed, CurrentStageIndex, 0x524f4f4du);
	AuthoritativeStage.EnemySeed = DeriveSeed(RunSeed, CurrentStageIndex, 0x454e454du);
	AuthoritativeStage.RewardSeed = DeriveSeed(RunSeed, CurrentStageIndex, 0x52455744u);
	AuthoritativeStage.MutatorSeed = DeriveSeed(RunSeed, CurrentStageIndex, 0x4d555441u);
	AuthoritativeStage.CosmeticSeed = DeriveSeed(RunSeed, CurrentStageIndex, 0x434f534du);

	FRandomStream RoomStream(AuthoritativeStage.RoomSeed);
	FRandomStream EnemyStream(AuthoritativeStage.EnemySeed);
	const bool bThreshold = CurrentStageIndex == 0 && !bEndlessMode;
	const bool bFinalStage = !bEndlessMode && StagesPerDungeon > 0 && CurrentStageIndex >= StagesPerDungeon - 1;
	const int32 RoomChoiceIndex = static_cast<int32>(static_cast<uint32>(AuthoritativeStage.RoomSeed) % StageIds.Num());
	AuthoritativeStage.StageId = bThreshold ? FName(TEXT("SakuraThreshold")) : StageIds[RoomChoiceIndex];
	AuthoritativeStage.RoomDefinitionId = AuthoritativeStage.StageId;

	// A resolved archetype owns the exact RoomData reference. Until one is assigned,
	// use only the two host-compatible rooms proven by the room/entrance audits.
	AuthoritativeStage.RoomDataId = bThreshold ? FName(TEXT("RD_MelodiaGrove_V2")) : RoomDataIds[RoomChoiceIndex];

	AuthoritativeStage.EnemyId = bThreshold ? FName(TEXT("SakuraPhantom"))
		: bFinalStage ? FName(TEXT("CosmicSentinel"))
		: EnemyIds[static_cast<uint32>(AuthoritativeStage.EnemySeed) % EnemyIds.Num()];
	AuthoritativeStage.EncounterId = FName(*FString::Printf(TEXT("Encounter_%s"), *AuthoritativeStage.EnemyId.ToString()));
	AuthoritativeStage.DifficultyTier = bEndlessMode ? 1 + EndlessDepth / 6 : 1 + AuthoritativeStage.ActIndex;
	AuthoritativeStage.RewardPoolId = Dissonance >= 50.0f ? FName(TEXT("DissonanceHigh")) : FName(TEXT("CoreMixed"));
	AuthoritativeStage.DissonanceProfileId = Dissonance >= 75.0f ? FName(TEXT("Critical")) : Dissonance >= 40.0f ? FName(TEXT("Medium")) : FName(TEXT("Low"));
	AuthoritativeStage.CompanionRequirement = EMelodiaCompanionRequirement::Resonance;

	CurrentStage.StageIndex = CurrentStageIndex;
	CurrentStage.StageSeed = AuthoritativeStage.StageSeed;
	CurrentStage.StageId = AuthoritativeStage.StageId;
	CurrentStage.EnemyId = AuthoritativeStage.EnemyId;
	OnStageRecipeReady.Broadcast(CurrentStage);
	UE_LOG(LogTemp, Log, TEXT("Melodia authoritative recipe v%d: act %d stage %d depth %d %s / %s (stage %d room %d enemy %d reward %d cosmetic %d)"),
		AuthoritativeStage.SchemaVersion, AuthoritativeStage.ActIndex, CurrentStageIndex, EndlessDepth,
		*AuthoritativeStage.StageId.ToString(), *AuthoritativeStage.EnemyId.ToString(),
		AuthoritativeStage.StageSeed, AuthoritativeStage.RoomSeed, AuthoritativeStage.EnemySeed,
		AuthoritativeStage.RewardSeed, AuthoritativeStage.CosmeticSeed);
}

bool UMelodiaRoguelikeRunSubsystem::RecordEncounterResult(const EMelodiaEncounterResult Result)
{
	if (Phase != EMelodiaRunPhase::Encounter || bEncounterResultRecorded)
	{
		return false;
	}

	bEncounterResultRecorded = true;
	if (Result == EMelodiaEncounterResult::Victory)
	{
		if (!bEndlessMode && CurrentStageIndex >= StagesPerDungeon - 1)
		{
			bSirMelodiousAvailable = true;
			SetPhase(EMelodiaRunPhase::Complete);
			SetLifecyclePhase(bStructuredMode ? EMelodiaRunLifecyclePhase::EndlessOffer : EMelodiaRunLifecyclePhase::RunSummary);
			OnRunCompleted.Broadcast();
			return true;
		}
		BuildRewardCandidates();
		SetPhase(EMelodiaRunPhase::RewardChoice);
		SetLifecyclePhase(EMelodiaRunLifecyclePhase::RewardChoice);
		OnRewardCandidatesReady.Broadcast(PendingRewards);
	}
	else if (Result == EMelodiaEncounterResult::Defeat)
	{
		SetPhase(EMelodiaRunPhase::Defeated);
		SetLifecyclePhase(EMelodiaRunLifecyclePhase::Defeated);
		OnRunDefeated.Broadcast();
	}
	else
	{
		bEncounterResultRecorded = false;
		SetPhase(EMelodiaRunPhase::Exploring);
		SetLifecyclePhase(EMelodiaRunLifecyclePhase::Exploring);
	}
	return true;
}

bool UMelodiaRoguelikeRunSubsystem::NotifyEncounterStarted()
{
	if (Phase != EMelodiaRunPhase::Exploring)
	{
		return false;
	}
	bEncounterResultRecorded = false;
	SetPhase(EMelodiaRunPhase::Encounter);
	SetLifecyclePhase(EMelodiaRunLifecyclePhase::Encounter);
	return true;
}

void UMelodiaRoguelikeRunSubsystem::BuildRewardCandidates()
{
	PendingRewards.Reset();
	FRandomStream RewardStream(AuthoritativeStage.RewardSeed);
	const float PowerMagnitude = RewardStream.FRandRange(0.10f, 0.18f);
	const float RecoveryMagnitude = RewardStream.FRandRange(0.12f, 0.22f);
	const float BargainMagnitude = RewardStream.FRandRange(0.22f, 0.35f);

	FMelodiaRunRewardCandidate Power;
	Power.RewardId = TEXT("ResonantCrescendo");
	Power.DisplayName = FText::FromString(TEXT("Resonant Crescendo"));
	Power.Type = EMelodiaRunRewardType::SongPower;
	Power.Magnitude = PowerMagnitude;
	PendingRewards.Add(Power);

	FMelodiaRunRewardCandidate Recovery;
	if (CurrentStageIndex == 0)
	{
		Recovery.RewardId = TEXT("HeartMelodyToken");
		Recovery.DisplayName = FText::FromString(TEXT("Heart Melody Token - consume to restore 30 HP"));
		Recovery.Type = EMelodiaRunRewardType::Recovery;
		Recovery.Magnitude = RecoveryMagnitude;
	}
	else
	{
		Recovery.RewardId = TEXT("SwirlMelodyToken");
		Recovery.DisplayName = FText::FromString(TEXT("Swirl Melody Token - consume to restore 2 SP"));
		Recovery.Type = EMelodiaRunRewardType::SkillPointRegen;
		Recovery.Magnitude = 2.0f;
	}
	PendingRewards.Add(Recovery);

	FMelodiaRunRewardCandidate Bargain;
	Bargain.RewardId = TEXT("CrimsonOvertone");
	Bargain.DisplayName = FText::FromString(TEXT("Crimson Overtone"));
	Bargain.Type = EMelodiaRunRewardType::DissonantBargain;
	Bargain.Magnitude = BargainMagnitude;
	Bargain.DissonanceCost = 15.0f;
	PendingRewards.Add(Bargain);
}

bool UMelodiaRoguelikeRunSubsystem::SelectReward(const int32 CandidateIndex)
{
	if (Phase != EMelodiaRunPhase::RewardChoice || bRewardCommitted || !PendingRewards.IsValidIndex(CandidateIndex))
	{
		return false;
	}

	const FMelodiaRunRewardCandidate Reward = PendingRewards[CandidateIndex];
	bRewardCommitted = true;
	AcquiredRewardIds.Add(Reward.RewardId);
	if (Reward.Type == EMelodiaRunRewardType::Recovery)
	{
		++HeartMelodyTokens;
		ConsumeHeartMelodyToken();
	}
	else if (Reward.Type == EMelodiaRunRewardType::SkillPointRegen)
	{
		++SwirlMelodyTokens;
		ConsumeSwirlMelodyToken();
	}
	else
	{
		SongPowerMultiplier += Reward.Magnitude;
		Dissonance = FMath::Clamp(Dissonance + Reward.DissonanceCost, 0.0f, 100.0f);
	}
	PendingRewards.Reset();
	OnRewardSelected.Broadcast(Reward);
	SetPhase(EMelodiaRunPhase::Transitioning);
	SetLifecyclePhase(EMelodiaRunLifecyclePhase::TransitionReady);
	return true;
}

bool UMelodiaRoguelikeRunSubsystem::ConsumeHeartMelodyToken()
{
	if (HeartMelodyTokens <= 0)
	{
		return false;
	}
	UMelodiaBattleSession* Session = GetGameInstance() ? GetGameInstance()->GetSubsystem<UMelodiaBattleSession>() : nullptr;
	if (!Session)
	{
		return false;
	}
	if (Session->PersistentPartyHP >= Session->PersistentPartyMaxHP)
	{
		return false;
	}
	--HeartMelodyTokens;
	++HeartMelodyTokensConsumed;
	Session->RestorePersistentPartyHealth(30.0f);
	return true;
}

int32 UMelodiaRoguelikeRunSubsystem::GrantHeartMelodyTokens(const int32 Amount)
{
	if (Amount > 0)
	{
		HeartMelodyTokens += Amount;
	}
	return HeartMelodyTokens;
}

void UMelodiaRoguelikeRunSubsystem::RestoreDurableTokens(const int32 SavedHeartTokens, const int32 SavedSwirlTokens)
{
	HeartMelodyTokens = FMath::Max(0, SavedHeartTokens);
	SwirlMelodyTokens = FMath::Max(0, SavedSwirlTokens);
}

bool UMelodiaRoguelikeRunSubsystem::ConsumeSwirlMelodyToken()
{
	if (SwirlMelodyTokens <= 0)
	{
		return false;
	}
	UMelodiaBattleSession* Session = GetGameInstance() ? GetGameInstance()->GetSubsystem<UMelodiaBattleSession>() : nullptr;
	if (!Session || Session->PersistentSkillPoints >= Session->PersistentSkillPointMax)
	{
		return false;
	}
	--SwirlMelodyTokens;
	++SwirlMelodyTokensConsumed;
	Session->RestorePersistentSkillPoints(2);
	return true;
}

bool UMelodiaRoguelikeRunSubsystem::AdvanceStage()
{
	if (Phase != EMelodiaRunPhase::Transitioning || !bRewardCommitted)
	{
		return false;
	}
	++CurrentStageIndex;
	if (bEndlessMode) { ++EndlessDepth; }
	bEncounterResultRecorded = false;
	bRewardCommitted = false;
	// GS-006: enter Generating before broadcasting the recipe so a synchronous
	// generation-complete callback is never dropped by the phase guard.
	SetPhase(EMelodiaRunPhase::Generating);
	SetLifecyclePhase(EMelodiaRunLifecyclePhase::Generating);
	BuildCurrentStage();
	return true;
}

void UMelodiaRoguelikeRunSubsystem::NotifyGenerationComplete(const bool bSucceeded)
{
	if (Phase != EMelodiaRunPhase::Generating)
	{
		return;
	}
	SetPhase(bSucceeded ? EMelodiaRunPhase::Exploring : EMelodiaRunPhase::Inactive);
	SetLifecyclePhase(bSucceeded ? EMelodiaRunLifecyclePhase::Exploring : EMelodiaRunLifecyclePhase::RecoverableFailure);
}

void UMelodiaRoguelikeRunSubsystem::EndRun(const bool bCompleted)
{
	PendingRewards.Reset();
	SetPhase(bCompleted ? EMelodiaRunPhase::Complete : EMelodiaRunPhase::Inactive);
	SetLifecyclePhase(bCompleted ? EMelodiaRunLifecyclePhase::RunSummary : EMelodiaRunLifecyclePhase::Inactive);
}

void UMelodiaRoguelikeRunSubsystem::SetPhase(const EMelodiaRunPhase NewPhase)
{
	if (Phase == NewPhase)
	{
		return;
	}
	const EMelodiaRunPhase Previous = Phase;
	Phase = NewPhase;
	OnRunPhaseChanged.Broadcast(NewPhase, Previous);
}

void UMelodiaRoguelikeRunSubsystem::StartStructuredRun(const int32 Seed, const int32 Acts, const int32 StagesPerAct)
{
	bStructuredMode = true;
	bEndlessMode = false;
	StructuredActCount = FMath::Max(1, Acts);
	StructuredStagesPerAct = FMath::Max(1, StagesPerAct);
	StagesPerDungeon = StructuredActCount * StructuredStagesPerAct;
	EndlessDepth = 0;
	StartNewRun(Seed);
	SetLifecyclePhase(EMelodiaRunLifecyclePhase::Generating);
}

bool UMelodiaRoguelikeRunSubsystem::ContinueEndless()
{
	if (!bStructuredMode || bEndlessMode || Phase != EMelodiaRunPhase::Complete)
	{
		return false;
	}
	bEndlessMode = true;
	EndlessDepth = 1;
	++CurrentStageIndex;
	bEncounterResultRecorded = false;
	bRewardCommitted = false;
	SetPhase(EMelodiaRunPhase::Generating);
	SetLifecyclePhase(EMelodiaRunLifecyclePhase::Generating);
	BuildCurrentStage();
	return true;
}

bool UMelodiaRoguelikeRunSubsystem::RestartRun()
{
	if (bStructuredMode)
	{
		StartStructuredRun(RunSeed, StructuredActCount, StructuredStagesPerAct);
	}
	else
	{
		StartNewRun(RunSeed);
	}
	return true;
}

bool UMelodiaRoguelikeRunSubsystem::RecordGenerationResult(const bool bSucceeded)
{
	if (Phase != EMelodiaRunPhase::Generating)
	{
		return false;
	}
	NotifyGenerationComplete(bSucceeded);
	return true;
}

bool UMelodiaRoguelikeRunSubsystem::ActivateDeterministicFallbackRecipe()
{
	if (Phase != EMelodiaRunPhase::Generating || bFallbackRecipeActive)
	{
		return false;
	}
	bFallbackRecipeActive = true;
	AuthoritativeStage.StageId = TEXT("FallbackSafe");
	AuthoritativeStage.RoomDefinitionId = TEXT("MelodiaGrove");
	AuthoritativeStage.RoomDataId = TEXT("RD_MelodiaGrove_V1");
	AuthoritativeStage.MutatorIds.AddUnique(TEXT("GenerationFallback"));
	CurrentStage.StageId = AuthoritativeStage.StageId;
	OnStageRecipeReady.Broadcast(CurrentStage);
	UE_LOG(LogTemp, Warning, TEXT("Melodia activated deterministic fallback recipe for stage %d."), CurrentStageIndex);
	return true;
}

void UMelodiaRoguelikeRunSubsystem::ApplyArchetype(const UMelodiaRunArchetypeDefinition* Archetype)
{
	if (!Archetype) return;
	ResolvedArchetype = const_cast<UMelodiaRunArchetypeDefinition*>(Archetype);
	bStructuredMode = true;
	bEndlessMode = false;
	StructuredActCount = FMath::Max(1, Archetype->ActCount);
	StructuredStagesPerAct = FMath::Max(1, Archetype->StagesPerAct);
	StagesPerDungeon = StructuredActCount * StructuredStagesPerAct;
	UE_LOG(LogTemp, Log, TEXT("Melodia archetype '%s' applied: %dx%d, %d rooms, %d encounters."),
		*Archetype->StableId.ToString(), StructuredActCount, StructuredStagesPerAct,
		Archetype->Rooms.Num(), Archetype->Encounters.Num());
}

void UMelodiaRoguelikeRunSubsystem::SetCompanionState(const bool bPresent, const bool bResonance, const bool bPlayable, const int32 Bond)
{
	bCompanionPresent = bPresent;
	bResonanceAvailable = bPresent && bResonance;
	bCompanionPlayable = bPresent && bPlayable;
	CompanionBond = FMath::Max(0, Bond);
	bSirMelodiousAvailable = bCompanionPresent;
}

FMelodiaRunSnapshot UMelodiaRoguelikeRunSubsystem::ExportSnapshot() const
{
	FMelodiaRunSnapshot Snapshot;
	Snapshot.RunSeed = RunSeed;
	Snapshot.CurrentStageIndex = CurrentStageIndex;
	Snapshot.EndlessDepth = EndlessDepth;
	Snapshot.Phase = LifecyclePhase;
	Snapshot.CurrentStage = AuthoritativeStage;
	Snapshot.AcquiredRewardIds = AcquiredRewardIds;
	for (const FMelodiaRunRewardCandidate& Candidate : PendingRewards)
	{
		Snapshot.PendingRewardIds.Add(Candidate.RewardId);
		Snapshot.PendingRewardTypes.Add(static_cast<uint8>(Candidate.Type));
		Snapshot.PendingRewardMagnitudes.Add(Candidate.Magnitude);
		Snapshot.PendingRewardDissonanceCosts.Add(Candidate.DissonanceCost);
	}
	Snapshot.bEncounterResultRecorded = bEncounterResultRecorded;
	Snapshot.bRewardCommitted = bRewardCommitted;
	Snapshot.bFallbackRecipeActive = bFallbackRecipeActive;
	Snapshot.SongPowerMultiplier = SongPowerMultiplier;
	Snapshot.RecoveryMultiplier = RecoveryMultiplier;
	Snapshot.Dissonance = Dissonance;
	Snapshot.HeartMelodyTokens = HeartMelodyTokens;
	Snapshot.SwirlMelodyTokens = SwirlMelodyTokens;
	Snapshot.bStructuredMode = bStructuredMode;
	Snapshot.bEndlessMode = bEndlessMode;
	Snapshot.StructuredActCount = StructuredActCount;
	Snapshot.StructuredStagesPerAct = StructuredStagesPerAct;
	Snapshot.StagesPerDungeon = StagesPerDungeon;
	Snapshot.bCompanionPresent = bCompanionPresent;
	Snapshot.bResonanceAvailable = bResonanceAvailable;
	Snapshot.bCompanionPlayable = bCompanionPlayable;
	Snapshot.CompanionBond = CompanionBond;
	return Snapshot;
}

bool UMelodiaRoguelikeRunSubsystem::ImportSnapshot(const FMelodiaRunSnapshot& Snapshot)
{
	const int32 PendingCount = Snapshot.PendingRewardIds.Num();
	const bool bPendingArraysMatch =
		Snapshot.PendingRewardTypes.Num() == PendingCount
		&& Snapshot.PendingRewardMagnitudes.Num() == PendingCount
		&& Snapshot.PendingRewardDissonanceCosts.Num() == PendingCount;
	const bool bPhaseValid =
		static_cast<uint8>(Snapshot.Phase) <= static_cast<uint8>(EMelodiaRunLifecyclePhase::RecoverableFailure);
	const bool bStructuredShapeValid = !Snapshot.bStructuredMode
		|| (Snapshot.StructuredActCount > 0
			&& Snapshot.StructuredStagesPerAct > 0
			&& Snapshot.StagesPerDungeon == Snapshot.StructuredActCount * Snapshot.StructuredStagesPerAct);
	const bool bScalarsValid =
		FMath::IsFinite(Snapshot.SongPowerMultiplier) && Snapshot.SongPowerMultiplier >= 0.0f
		&& FMath::IsFinite(Snapshot.RecoveryMultiplier) && Snapshot.RecoveryMultiplier >= 0.0f
		&& FMath::IsFinite(Snapshot.Dissonance);

	if (Snapshot.SchemaVersion != 1
		|| Snapshot.CurrentStage.SchemaVersion != 1
		|| Snapshot.RunSeed < 0
		|| Snapshot.CurrentStageIndex < 0
		|| Snapshot.EndlessDepth < 0
		|| Snapshot.CurrentStage.StageIndex != Snapshot.CurrentStageIndex
		|| !bPendingArraysMatch
		|| !bPhaseValid
		|| !bStructuredShapeValid
		|| !bScalarsValid)
	{
		return false;
	}

	TArray<FMelodiaRunRewardCandidate> ImportedPendingRewards;
	ImportedPendingRewards.Reserve(PendingCount);
	for (int32 Index = 0; Index < PendingCount; ++Index)
	{
		if (Snapshot.PendingRewardIds[Index].IsNone()
			|| Snapshot.PendingRewardTypes[Index] > static_cast<uint8>(EMelodiaRunRewardType::DissonantBargain)
			|| !FMath::IsFinite(Snapshot.PendingRewardMagnitudes[Index])
			|| !FMath::IsFinite(Snapshot.PendingRewardDissonanceCosts[Index]))
		{
			return false;
		}

		FMelodiaRunRewardCandidate Candidate;
		Candidate.RewardId = Snapshot.PendingRewardIds[Index];
		Candidate.DisplayName = FText::FromName(Candidate.RewardId);
		Candidate.Type = static_cast<EMelodiaRunRewardType>(Snapshot.PendingRewardTypes[Index]);
		Candidate.Magnitude = Snapshot.PendingRewardMagnitudes[Index];
		Candidate.DissonanceCost = Snapshot.PendingRewardDissonanceCosts[Index];
		ImportedPendingRewards.Add(Candidate);
	}

	// Commit only after every serialized field has passed validation. A corrupt
	// checkpoint must never leave a partially mutated live run behind.
	RunSeed = Snapshot.RunSeed;
	CurrentStageIndex = Snapshot.CurrentStageIndex;
	EndlessDepth = Snapshot.EndlessDepth;
	LifecyclePhase = Snapshot.Phase;
	switch (LifecyclePhase)
	{
	case EMelodiaRunLifecyclePhase::Generating:
	case EMelodiaRunLifecyclePhase::RecoverableFailure:
		Phase = EMelodiaRunPhase::Generating;
		break;
	case EMelodiaRunLifecyclePhase::Exploring:
		Phase = EMelodiaRunPhase::Exploring;
		break;
	case EMelodiaRunLifecyclePhase::Encounter:
		Phase = EMelodiaRunPhase::Encounter;
		break;
	case EMelodiaRunLifecyclePhase::RewardChoice:
		Phase = EMelodiaRunPhase::RewardChoice;
		break;
	case EMelodiaRunLifecyclePhase::TransitionReady:
		Phase = EMelodiaRunPhase::Transitioning;
		break;
	case EMelodiaRunLifecyclePhase::Defeated:
		Phase = EMelodiaRunPhase::Defeated;
		break;
	case EMelodiaRunLifecyclePhase::StructuredComplete:
	case EMelodiaRunLifecyclePhase::EndlessOffer:
	case EMelodiaRunLifecyclePhase::RunSummary:
		Phase = EMelodiaRunPhase::Complete;
		break;
	default:
		Phase = EMelodiaRunPhase::Inactive;
		break;
	}

	AuthoritativeStage = Snapshot.CurrentStage;
	CurrentStage.StageIndex = AuthoritativeStage.StageIndex;
	CurrentStage.StageSeed = AuthoritativeStage.StageSeed;
	CurrentStage.StageId = AuthoritativeStage.StageId;
	CurrentStage.EnemyId = AuthoritativeStage.EnemyId;
	AcquiredRewardIds = Snapshot.AcquiredRewardIds;
	PendingRewards = MoveTemp(ImportedPendingRewards);
	bEncounterResultRecorded = Snapshot.bEncounterResultRecorded;
	bRewardCommitted = Snapshot.bRewardCommitted;
	bFallbackRecipeActive = Snapshot.bFallbackRecipeActive;
	SongPowerMultiplier = Snapshot.SongPowerMultiplier;
	RecoveryMultiplier = Snapshot.RecoveryMultiplier;
	Dissonance = FMath::Clamp(Snapshot.Dissonance, 0.0f, 100.0f);
	HeartMelodyTokens = FMath::Max(0, Snapshot.HeartMelodyTokens);
	SwirlMelodyTokens = FMath::Max(0, Snapshot.SwirlMelodyTokens);
	bStructuredMode = Snapshot.bStructuredMode;
	bEndlessMode = Snapshot.bEndlessMode;
	StructuredActCount = Snapshot.StructuredActCount;
	StructuredStagesPerAct = Snapshot.StructuredStagesPerAct;
	StagesPerDungeon = Snapshot.StagesPerDungeon;
	bCompanionPresent = Snapshot.bCompanionPresent;
	bResonanceAvailable = Snapshot.bCompanionPresent && Snapshot.bResonanceAvailable;
	bCompanionPlayable = Snapshot.bCompanionPresent && Snapshot.bCompanionPlayable;
	CompanionBond = FMath::Max(0, Snapshot.CompanionBond);
	bSirMelodiousAvailable = bCompanionPresent;
	RandomStream.Initialize(RunSeed);
	return true;
}

void UMelodiaRoguelikeRunSubsystem::ResetTransientRunState(const int32 Seed)
{
	PendingRewards.Reset();
	AcquiredRewardIds.Reset();
	bEncounterResultRecorded = false;
	bRewardCommitted = false;
}

void UMelodiaRoguelikeRunSubsystem::SetLifecyclePhase(const EMelodiaRunLifecyclePhase NewPhase)
{
	LifecyclePhase = NewPhase;
}

int32 UMelodiaRoguelikeRunSubsystem::DeriveSeed(const int32 Seed, const int32 StageIndex, const uint32 Salt)
{
	uint32 Value = static_cast<uint32>(Seed);
	Value ^= static_cast<uint32>(StageIndex) + 0x9e3779b9u + (Value << 6) + (Value >> 2);
	Value ^= Salt + 0x9e3779b9u + (Value << 6) + (Value >> 2);
	Value ^= Value >> 16;
	Value *= 0x7feb352du;
	Value ^= Value >> 15;
	Value *= 0x846ca68bu;
	Value ^= Value >> 16;
	return static_cast<int32>(Value & 0x7fffffffu);
}
