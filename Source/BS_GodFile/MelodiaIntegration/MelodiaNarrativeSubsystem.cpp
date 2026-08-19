#include "MelodiaNarrativeSubsystem.h"
#include "UObject/UnrealType.h"

#include "MelodiaIntegrationConfig.h"
#include "MelodiaOllamaValidation.h"
#include "MelodiaWaterGameplaySubsystem.h"
#include "Core/QuillscriptAsset.h"
#include "Core/QuillscriptInterpreter.h"
#include "Core/QuillscriptSubsystem.h"
#include "Widgets/DialogBox.h"
#include "Serialization/MemoryReader.h"
#include "Serialization/MemoryWriter.h"

namespace
{
	constexpr TCHAR IntentPrefix[] = TEXT("melodia:");
	constexpr TCHAR PersistentVariablePrefix[] = TEXT("melodia_");

	bool IsPersistentQuillVariable(const FName Name)
	{
		return Name.ToString().StartsWith(PersistentVariablePrefix, ESearchCase::IgnoreCase);
	}

	bool ParseBool(const FString& Value, bool& OutValue)
	{
		if (Value.Equals(TEXT("true"), ESearchCase::IgnoreCase) || Value == TEXT("1"))
		{
			OutValue = true;
			return true;
		}
		if (Value.Equals(TEXT("false"), ESearchCase::IgnoreCase) || Value == TEXT("0"))
		{
			OutValue = false;
			return true;
		}
		return false;
	}
}

UMelodiaNarrativeSubsystem* UMelodiaNarrativeSubsystem::GetMelodiaNarrativeSubsystem(const UObject* WorldContextObject)
{
	if (!IsValid(WorldContextObject) || !WorldContextObject->GetWorld())
	{
		return nullptr;
	}

	UGameInstance* GameInstance = WorldContextObject->GetWorld()->GetGameInstance();
	return GameInstance ? GameInstance->GetSubsystem<UMelodiaNarrativeSubsystem>() : nullptr;
}

void UMelodiaNarrativeSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	if (!Config)
	{
		Config = LoadObject<UMelodiaIntegrationConfig>(nullptr, TEXT("/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig.DA_MelodiaIntegrationConfig"));
		if (!Config)
		{
			UE_LOG(LogTemp, Error, TEXT("Melodia integration config is missing: /Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig"));
		}
	}
	if (UQuillscriptSubsystem* Quill = GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>())
	{
		Quill->OnNotified.AddUniqueDynamic(this, &ThisClass::HandleQuillNotification);
		Quill->OnScriptPlay.AddUniqueDynamic(this, &ThisClass::HandleQuillScriptPlay);
	}
}

void UMelodiaNarrativeSubsystem::Deinitialize()
{
	if (const UGameInstance* GI = GetGameInstance())
	{
		if (UQuillscriptSubsystem* Quill = GI->GetSubsystem<UQuillscriptSubsystem>())
		{
			Quill->OnNotified.RemoveDynamic(this, &ThisClass::HandleQuillNotification);
			Quill->OnScriptPlay.RemoveDynamic(this, &ThisClass::HandleQuillScriptPlay);
		}
	}
	ActiveInterpreter.Reset();
	Super::Deinitialize();
}

bool UMelodiaNarrativeSubsystem::Reject(const FString& Intent, const EMelodiaIntentFailure Failure)
{
	UE_LOG(LogTemp, Warning, TEXT("Melodia intent rejected: %s (%d)"), *Intent, static_cast<int32>(Failure));
	OnIntentRejected.Broadcast(Intent, Failure);
	return false;
}

bool UMelodiaNarrativeSubsystem::IsAllowed(const TSet<FName>& Allowlist, const FName Id, const FString& Intent)
{
	if (Id.IsNone())
	{
		return false;
	}

	if (Allowlist.Contains(Id))
	{
		return true;
	}

#if !UE_BUILD_SHIPPING
	if (Config && Config->bRelaxedAllowlistInEditor)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_RELAXED_ALLOWLIST: Allowing unregistered ID '%s' for intent: %s"), *Id.ToString(), *Intent);
		Config->DiscoveredUnregisteredIds.Add(Id);
		return true;
	}
#endif

	return Reject(Intent, EMelodiaIntentFailure::UnknownIdentifier);
}

bool UMelodiaNarrativeSubsystem::ConsumeOnce(TArray<FName>& ConsumedIds, const FName Id, const FString& Intent)
{
	if (ConsumedIds.Contains(Id))
	{
		return Reject(Intent, EMelodiaIntentFailure::Duplicate);
	}
	ConsumedIds.Add(Id);
	return true;
}

bool UMelodiaNarrativeSubsystem::StartBattle(const FName EncounterId)
{
	const FString Intent = FString::Printf(TEXT("StartBattle(%s)"), *EncounterId.ToString());
	if (!Config || !IsAllowed(Config->EncounterIds, EncounterId, Intent))
	{
		return false;
	}
	if (!PendingEncounterId.IsNone())
	{
		return Reject(Intent, EMelodiaIntentFailure::Busy);
	}
	if (!ActiveInterpreter.IsValid())
	{
		return Reject(Intent, EMelodiaIntentFailure::MissingRuntime);
	}

	PendingEncounterId = EncounterId;
	bBattleCompletionConsumed = false;
	ActiveInterpreter->Stop();
	OnBattleRequested.Broadcast(EncounterId);
	return true;
}

bool UMelodiaNarrativeSubsystem::CompleteQuest(const FName QuestId)
{
	const FString Intent = FString::Printf(TEXT("CompleteQuest(%s)"), *QuestId.ToString());
	if (!Config || !IsAllowed(Config->QuestIds, QuestId, Intent))
	{
		return false;
	}

	// Quest notifications use one documented verb, but acceptance and completion
	// are separate state transitions. Keep the legacy quest:<id> key for the
	// acceptance edge, then consume a distinct completion key only after Persona
	// has made the quest active. Both edges remain independently idempotent.
	const bool bQuestWasActive = NarrativeRecord.ActiveQuestIds.Contains(QuestId);
	const FName ConsumedQuestIntent = bQuestWasActive
		? FName(*FString::Printf(TEXT("quest-complete:%s"), *QuestId.ToString()))
		: FName(*FString::Printf(TEXT("quest:%s"), *QuestId.ToString()));
	// Reject a genuine repeat before doing any work -- this is the idempotence guard.
	if (NarrativeRecord.ConsumedIntentIds.Contains(ConsumedQuestIntent))
	{
		return Reject(Intent, EMelodiaIntentFailure::Duplicate);
	}

	OnQuestRequested.Broadcast(QuestId);

	// Consume only if a listener actually moved the quest. Persona writes both
	// edges back through SetQuestActive, so ActiveQuestIds is the authoritative
	// record of whether the transition happened -- no flag needed to observe it.
	//
	// This ordering matters: a quest whose prerequisite is unmet is Locked, so
	// Persona no-ops. Consuming before the broadcast burned the intent anyway, and
	// because ConsumedIntentIds is SaveGame-flagged the burn survived reloads --
	// the quest could never be accepted later even once its prerequisite was met.
	const bool bQuestIsActive = NarrativeRecord.ActiveQuestIds.Contains(QuestId);
	if (bQuestIsActive == bQuestWasActive)
	{
		UE_LOG(LogTemp, Verbose,
			TEXT("MELODIA_QUEST intent '%s' produced no transition; leaving it unconsumed so it can be retried."),
			*Intent);
		return false;
	}

	NarrativeRecord.ConsumedIntentIds.Add(ConsumedQuestIntent);
	return true;
}

bool UMelodiaNarrativeSubsystem::SetQuestActive(const FName QuestId, const bool bActive)
{
	const FString Intent = FString::Printf(TEXT("SetQuestActive(%s)"), *QuestId.ToString());
	if (!Config || !IsAllowed(Config->QuestIds, QuestId, Intent))
	{
		return false;
	}

	if (bActive)
	{
		NarrativeRecord.ActiveQuestIds.AddUnique(QuestId);
	}
	else
	{
		NarrativeRecord.ActiveQuestIds.Remove(QuestId);
	}
	return true;
}

bool UMelodiaNarrativeSubsystem::SetNarrativeFlag(const FName FlagId, const bool Value)
{
	const FString Intent = FString::Printf(TEXT("SetNarrativeFlag(%s)"), *FlagId.ToString());
	if (!Config || !IsAllowed(Config->NarrativeFlagIds, FlagId, Intent))
	{
		return false;
	}
	NarrativeRecord.Flags.Add(FlagId, Value);
	if (UQuillscriptSubsystem* Quill = GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>())
	{
		Quill->GetVariables().Add(FlagId, FText::FromString(Value ? TEXT("on") : TEXT("off")));
	}
	OnFlagChanged.Broadcast(FlagId, Value);
	return true;
}

bool UMelodiaNarrativeSubsystem::RequestTravel(const FName LevelId)
{
	const FString Intent = FString::Printf(TEXT("RequestTravel(%s)"), *LevelId.ToString());
	if (!Config || !IsAllowed(Config->TravelLevelIds, LevelId, Intent))
	{
		return false;
	}
	OnTravelRequested.Broadcast(LevelId);
	return true;
}

bool UMelodiaNarrativeSubsystem::GrantDialogueReward(const FName RewardId)
{
	const FString Intent = FString::Printf(TEXT("GrantDialogueReward(%s)"), *RewardId.ToString());
	if (!Config || !IsAllowed(Config->DialogueRewardIds, RewardId, Intent) ||
		!ConsumeOnce(NarrativeRecord.ConsumedRewardIds, RewardId, Intent))
	{
		return false;
	}
	OnRewardRequested.Broadcast(RewardId);
	return true;
}

bool UMelodiaNarrativeSubsystem::IsWorldChallengeCompleted(
	const FName ChallengeId,
	const FName CompletionFlagId) const
{
	return !ChallengeId.IsNone()
		&& !CompletionFlagId.IsNone()
		&& Config
		&& Config->WorldChallengeIds.Contains(ChallengeId)
		&& Config->NarrativeFlagIds.Contains(CompletionFlagId)
		&& NarrativeRecord.Flags.FindRef(CompletionFlagId);
}

EMelodiaContentCommitResult UMelodiaNarrativeSubsystem::CommitWorldChallenge(
	const FName ChallengeId,
	const FName CompletionFlagId,
	const FName RewardId,
	const FName CompletionIntentId,
	EMelodiaContentCommitFailure& OutFailure)
{
	OutFailure = EMelodiaContentCommitFailure::None;
	const FString Intent = FString::Printf(TEXT("CommitWorldChallenge(%s)"), *ChallengeId.ToString());

	auto RejectContent = [this, &OutFailure, &Intent](
		const EMelodiaContentCommitFailure Failure,
		const EMelodiaIntentFailure IntentFailure,
		const EMelodiaContentCommitResult Result = EMelodiaContentCommitResult::Rejected)
	{
		OutFailure = Failure;
		Reject(Intent, IntentFailure);
		return Result;
	};

	if (ChallengeId.IsNone() || CompletionFlagId.IsNone()
		|| RewardId.IsNone() || CompletionIntentId.IsNone())
	{
		return RejectContent(EMelodiaContentCommitFailure::InvalidId, EMelodiaIntentFailure::UnknownIdentifier);
	}
	if (!Config)
	{
		return RejectContent(EMelodiaContentCommitFailure::AuthorityUnavailable, EMelodiaIntentFailure::MissingRuntime);
	}
	if (!Config->WorldChallengeIds.Contains(ChallengeId))
	{
		return RejectContent(EMelodiaContentCommitFailure::UnknownChallenge, EMelodiaIntentFailure::UnknownIdentifier);
	}
	if (!Config->NarrativeFlagIds.Contains(CompletionFlagId))
	{
		return RejectContent(EMelodiaContentCommitFailure::UnknownFlag, EMelodiaIntentFailure::UnknownIdentifier);
	}
	if (!Config->DialogueRewardIds.Contains(RewardId))
	{
		return RejectContent(EMelodiaContentCommitFailure::UnknownReward, EMelodiaIntentFailure::UnknownIdentifier);
	}

	const bool bIntentConsumed = NarrativeRecord.ConsumedIntentIds.Contains(CompletionIntentId);
	const bool bCompletionSet = NarrativeRecord.Flags.FindRef(CompletionFlagId);
	const bool bRewardConsumed = NarrativeRecord.ConsumedRewardIds.Contains(RewardId);
	if (bIntentConsumed)
	{
		if (bCompletionSet && bRewardConsumed)
		{
			return EMelodiaContentCommitResult::AlreadyApplied;
		}
		return RejectContent(
			EMelodiaContentCommitFailure::InconsistentState,
			EMelodiaIntentFailure::IncompatibleSave,
			EMelodiaContentCommitResult::InconsistentState);
	}
	if (bRewardConsumed)
	{
		return RejectContent(
			EMelodiaContentCommitFailure::RewardAlreadyConsumed,
			EMelodiaIntentFailure::Duplicate,
			EMelodiaContentCommitResult::InconsistentState);
	}
	if (bCompletionSet)
	{
		return RejectContent(
			EMelodiaContentCommitFailure::CompletionAlreadySet,
			EMelodiaIntentFailure::Duplicate,
			EMelodiaContentCommitResult::InconsistentState);
	}

	// All validation is complete before the first canonical field is changed.
	// Broadcasts happen only after the three record mutations are committed.
	NarrativeRecord.Flags.Add(CompletionFlagId, true);
	NarrativeRecord.ConsumedIntentIds.Add(CompletionIntentId);
	NarrativeRecord.ConsumedRewardIds.Add(RewardId);
	if (UQuillscriptSubsystem* Quill = GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>())
	{
		Quill->GetVariables().Add(CompletionFlagId, FText::FromString(TEXT("on")));
	}
	OnFlagChanged.Broadcast(CompletionFlagId, true);
	OnRewardRequested.Broadcast(RewardId);
	UE_LOG(LogTemp, Log, TEXT("Melodia world challenge committed: challenge=%s flag=%s reward=%s intent=%s"),
		*ChallengeId.ToString(), *CompletionFlagId.ToString(), *RewardId.ToString(), *CompletionIntentId.ToString());
	return EMelodiaContentCommitResult::Applied;
}

bool UMelodiaNarrativeSubsystem::IsStateAnchorApplied(
	const FName AnchorId,
	const FName PersistenceKey,
	const FName ApplyIntentId) const
{
	return !AnchorId.IsNone()
		&& !PersistenceKey.IsNone()
		&& !ApplyIntentId.IsNone()
		&& Config
		&& Config->StateAnchorIds.Contains(AnchorId)
		&& NarrativeRecord.ConsumedIntentIds.Contains(ApplyIntentId);
}

EMelodiaContentCommitResult UMelodiaNarrativeSubsystem::ApplyStateAnchor(
	const FName AnchorId,
	const FName PersistenceKey,
	const TArray<FMelodiaStateAnchorOperation>& Operations,
	const FName ApplyIntentId,
	EMelodiaContentCommitFailure& OutFailure)
{
	OutFailure = EMelodiaContentCommitFailure::None;
	const FString Intent = FString::Printf(TEXT("ApplyStateAnchor(%s,%s)"),
		*AnchorId.ToString(), *PersistenceKey.ToString());

	auto RejectContent = [this, &OutFailure, &Intent](
		const EMelodiaContentCommitFailure Failure,
		const EMelodiaIntentFailure IntentFailure,
		const EMelodiaContentCommitResult Result = EMelodiaContentCommitResult::Rejected)
	{
		OutFailure = Failure;
		Reject(Intent, IntentFailure);
		return Result;
	};

	if (AnchorId.IsNone() || PersistenceKey.IsNone() || ApplyIntentId.IsNone() || Operations.IsEmpty())
	{
		return RejectContent(EMelodiaContentCommitFailure::InvalidId, EMelodiaIntentFailure::UnknownIdentifier);
	}
	if (!Config)
	{
		return RejectContent(EMelodiaContentCommitFailure::AuthorityUnavailable, EMelodiaIntentFailure::MissingRuntime);
	}
	if (!Config->StateAnchorIds.Contains(AnchorId))
	{
		return RejectContent(EMelodiaContentCommitFailure::UnknownAnchor, EMelodiaIntentFailure::UnknownIdentifier);
	}

	TSet<FName> SeenTargets;
	bool bAnyPositiveOperationAlreadyApplied = false;
	bool bAllOperationsMatchForReplay = true;
	for (const FMelodiaStateAnchorOperation& Operation : Operations)
	{
		if (Operation.TargetId.IsNone() || SeenTargets.Contains(Operation.TargetId))
		{
			return RejectContent(EMelodiaContentCommitFailure::InvalidId, EMelodiaIntentFailure::UnknownIdentifier);
		}
		SeenTargets.Add(Operation.TargetId);

		bool bCurrentValue = false;
		switch (Operation.Type)
		{
		case EMelodiaStateAnchorOperationType::SetNarrativeFlag:
			if (!Config->NarrativeFlagIds.Contains(Operation.TargetId))
			{
				return RejectContent(EMelodiaContentCommitFailure::UnknownFlag, EMelodiaIntentFailure::UnknownIdentifier);
			}
			bCurrentValue = NarrativeRecord.Flags.FindRef(Operation.TargetId);
			break;
		case EMelodiaStateAnchorOperationType::SetQuestActive:
			if (!Config->QuestIds.Contains(Operation.TargetId))
			{
				return RejectContent(EMelodiaContentCommitFailure::UnknownQuest, EMelodiaIntentFailure::UnknownIdentifier);
			}
			bCurrentValue = NarrativeRecord.ActiveQuestIds.Contains(Operation.TargetId);
			break;
		default:
			return RejectContent(EMelodiaContentCommitFailure::UnsupportedOperation, EMelodiaIntentFailure::UnknownIntent);
		}
		// A false operation is a valid no-op against a default/absent field, so it
		// cannot prove that a prior anchor applied it. True operations can prove
		// partial application and are therefore used for the fail-closed check.
		const bool bOperationMatchesForReplay = !Operation.bValue || bCurrentValue;
		bAllOperationsMatchForReplay &= bOperationMatchesForReplay;
		bAnyPositiveOperationAlreadyApplied |= Operation.bValue && bCurrentValue;
	}

	const bool bIntentConsumed = NarrativeRecord.ConsumedIntentIds.Contains(ApplyIntentId);
	if (bIntentConsumed)
	{
		if (bAllOperationsMatchForReplay)
		{
			return EMelodiaContentCommitResult::AlreadyApplied;
		}
		return RejectContent(
			EMelodiaContentCommitFailure::InconsistentState,
			EMelodiaIntentFailure::IncompatibleSave,
			EMelodiaContentCommitResult::InconsistentState);
	}
	if (bAnyPositiveOperationAlreadyApplied)
	{
		return RejectContent(
			EMelodiaContentCommitFailure::InconsistentState,
			EMelodiaIntentFailure::IncompatibleSave,
			EMelodiaContentCommitResult::InconsistentState);
	}

	// The complete operation list has been validated before this transaction
	// mutates the canonical record. The intent journal is the idempotency key.
	for (const FMelodiaStateAnchorOperation& Operation : Operations)
	{
		switch (Operation.Type)
		{
		case EMelodiaStateAnchorOperationType::SetNarrativeFlag:
			NarrativeRecord.Flags.Add(Operation.TargetId, Operation.bValue);
			break;
		case EMelodiaStateAnchorOperationType::SetQuestActive:
			if (Operation.bValue)
			{
				NarrativeRecord.ActiveQuestIds.AddUnique(Operation.TargetId);
			}
			else
			{
				NarrativeRecord.ActiveQuestIds.Remove(Operation.TargetId);
			}
			break;
		default:
			// Exhaustively validated above; keep the switch defensive if the enum grows.
			return RejectContent(EMelodiaContentCommitFailure::UnsupportedOperation, EMelodiaIntentFailure::UnknownIntent);
		}
	}
	NarrativeRecord.ConsumedIntentIds.Add(ApplyIntentId);
	for (const FMelodiaStateAnchorOperation& Operation : Operations)
	{
		if (Operation.Type == EMelodiaStateAnchorOperationType::SetNarrativeFlag)
		{
			if (UQuillscriptSubsystem* Quill = GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>())
			{
				Quill->GetVariables().Add(Operation.TargetId,
					FText::FromString(Operation.bValue ? TEXT("on") : TEXT("off")));
			}
			OnFlagChanged.Broadcast(Operation.TargetId, Operation.bValue);
		}
	}
	UE_LOG(LogTemp, Log, TEXT("Melodia state anchor committed: anchor=%s key=%s intent=%s operations=%d"),
		*AnchorId.ToString(), *PersistenceKey.ToString(), *ApplyIntentId.ToString(), Operations.Num());
	return EMelodiaContentCommitResult::Applied;
}

bool UMelodiaNarrativeSubsystem::GrantDialogueSocialStat(const FName IntentId, const FName StatId, const int32 Delta)
{
	const FString Intent = FString::Printf(TEXT("GrantDialogueSocialStat(%s,%s,%d)"),
		*IntentId.ToString(), *StatId.ToString(), Delta);
	if (IntentId.IsNone() || !Config || !IsAllowed(Config->SocialStatIds, StatId, Intent))
	{
		return false;
	}

	// Idempotent per authored choice, not per stat/delta pair. Two different
	// dialogue beats may both award Harmony +1, while replaying either beat after
	// resume/load remains a no-op.
	const FName ConsumedKey(*FString::Printf(TEXT("social-stat:%s"), *IntentId.ToString()));
	if (!ConsumeOnce(NarrativeRecord.ConsumedIntentIds, ConsumedKey, Intent))
	{
		return false;
	}

	OnSocialStatRequested.Broadcast(StatId, Delta);
	return true;
}

bool UMelodiaNarrativeSubsystem::CompleteBattle(const EMelodiaBattleResult Result)
{
	if (PendingEncounterId.IsNone() || bBattleCompletionConsumed)
	{
		return Reject(TEXT("CompleteBattle"), EMelodiaIntentFailure::Duplicate);
	}
	if (!ActiveInterpreter.IsValid())
	{
		return Reject(TEXT("CompleteBattle"), EMelodiaIntentFailure::MissingRuntime);
	}

	bBattleCompletionConsumed = true;
	const FName CompletedEncounter = PendingEncounterId;
	PendingEncounterId = NAME_None;
	const bool bWon = Result == EMelodiaBattleResult::Victory;
	const FName BattleWonFlag(TEXT("melodia_battle_won"));
	if (Config && Config->NarrativeFlagIds.Contains(BattleWonFlag))
	{
		NarrativeRecord.Flags.Add(BattleWonFlag, bWon);
		OnFlagChanged.Broadcast(BattleWonFlag, bWon);
	}

	// Quill owns presentation branching, while the typed enum and persistent
	// narrative record remain authoritative here. Mirror only the terminal result
	// needed by the resumed script; do not expose battle objects or controllers.
	FString ResultValue;
	switch (Result)
	{
	case EMelodiaBattleResult::Victory:
		ResultValue = TEXT("victory");
		break;
	case EMelodiaBattleResult::Defeat:
		ResultValue = TEXT("defeat");
		break;
	case EMelodiaBattleResult::Fled:
		ResultValue = TEXT("fled");
		break;
	default:
		ResultValue = TEXT("unavailable");
		break;
	}
	if (UQuillscriptSubsystem* Quill = GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>())
	{
		Quill->GetVariables().Add(TEXT("melodia_battle_result"), FText::FromString(ResultValue));
	}

	UE_LOG(LogTemp, Log, TEXT("MELUSINA_LOOP_BATTLE_COMPLETED encounter=%s result=%s"), *CompletedEncounter.ToString(), *ResultValue);
	OnBattleCompleted.Broadcast(CompletedEncounter, Result);
	ResumeQuillOnce();
	return true;
}

bool UMelodiaNarrativeSubsystem::AbortPendingBattle(const FString& Reason)
{
	if (PendingEncounterId.IsNone())
	{
		return false;
	}
	if (!ActiveInterpreter.IsValid())
	{
		return Reject(TEXT("AbortPendingBattle"), EMelodiaIntentFailure::MissingRuntime);
	}

	const FName AbortedEncounter = PendingEncounterId;
	PendingEncounterId = NAME_None;
	bBattleCompletionConsumed = true;
	if (UQuillscriptSubsystem* Quill = GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>())
	{
		Quill->GetVariables().Add(TEXT("melodia_battle_result"), FText::FromString(TEXT("unavailable")));
	}
	UE_LOG(LogTemp, Error, TEXT("MELUSINA_LOOP_BATTLE_ABORTED encounter=%s reason=%s"),
		*AbortedEncounter.ToString(), *Reason);
	OnBattleAborted.Broadcast(AbortedEncounter, Reason);
	ResumeQuillOnce();
	return true;
}

bool UMelodiaNarrativeSubsystem::MigrateRecord(FMelodiaNarrativeRecord& Record)
{
	if (Record.Version == FMelodiaNarrativeRecord::CurrentVersion)
	{
		return true;
	}

	// A record from a newer build cannot be safely downgraded; refuse rather
	// than load it partially.
	if (Record.Version > FMelodiaNarrativeRecord::CurrentVersion)
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia narrative record version %d is newer than this build (%d); refusing to load."),
			Record.Version, FMelodiaNarrativeRecord::CurrentVersion);
		return false;
	}

	// Step the record forward one version at a time so a save can cross several
	// schema changes in one load.
	while (Record.Version < FMelodiaNarrativeRecord::CurrentVersion)
	{
		switch (Record.Version)
		{
		case 1:
			// 1 -> 2 added SocialStats, BondRanks, PhaseIndex and SpawnContext.
			// All four default correctly for a pre-version-2 save: no stats were
			// ever persisted, so an empty map is the truthful value.
			Record.Version = 2;
			break;

		case 2:
			// 2 -> 3 added OwnedCosmeticIds, EquippedCosmeticIds, LastPullUnixSeconds
			// (Decision 043, MelodiaWardrobe plugin). All three default correctly for
			// a pre-version-3 save: no cosmetics were ever persisted, so empty
			// containers and zero timestamp are the truthful values. The migration
			// is a no-op on data; the version stamp is the only thing that changes.
			Record.Version = 3;
			break;

		case 3:
			// 3 -> 4 added the logical water/platform snapshot. Older saves have
			// no water gameplay state, so the reflected default is authoritative.
			Record.WaterGameplayState = FMelodiaWaterGameplaySaveData();
			Record.Version = 4;
			break;

		default:
			UE_LOG(LogTemp, Warning, TEXT("Melodia narrative record version %d has no migration path."), Record.Version);
			return false;
		}
	}

	UE_LOG(LogTemp, Log, TEXT("Melodia narrative record migrated to version %d."), Record.Version);
	return true;
}

bool UMelodiaNarrativeSubsystem::RestoreNarrativeRecord(const FMelodiaNarrativeRecord& Record)
{
	FMelodiaNarrativeRecord Migrated = Record;
	if (!MigrateRecord(Migrated))
	{
		ResetNarrativeRecord();
		return Reject(TEXT("RestoreNarrativeRecord"), EMelodiaIntentFailure::IncompatibleSave);
	}

	NarrativeRecord = Migrated;
	if (UMelodiaWaterGameplaySubsystem* WaterGameplay = GetGameInstance()->GetSubsystem<UMelodiaWaterGameplaySubsystem>())
	{
		WaterGameplay->RestoreSaveState(NarrativeRecord.WaterGameplayState);
	}
	RestorePersistentQuillVariables();
	return true;
}

int32 UMelodiaNarrativeSubsystem::GetSocialStat(FName StatId) const
{
	const int32* Found = NarrativeRecord.SocialStats.Find(StatId);
	return Found ? *Found : 0;
}

int32 UMelodiaNarrativeSubsystem::AddSocialStat(FName StatId, int32 Delta)
{
	if (StatId.IsNone())
	{
		return 0;
	}

	int32& Value = NarrativeRecord.SocialStats.FindOrAdd(StatId);
	Value = FMath::Max(0, Value + Delta);
	return Value;
}

int32 UMelodiaNarrativeSubsystem::GetBondRank(FName BondId) const
{
	const int32* Found = NarrativeRecord.BondRanks.Find(BondId);
	return Found ? *Found : 0;
}

int32 UMelodiaNarrativeSubsystem::SetBondRank(FName BondId, int32 Rank)
{
	if (BondId.IsNone())
	{
		return 0;
	}

	// Ranks only ever advance; a lower value is treated as a no-op so a
	// mis-ordered dialogue cannot walk a bond backwards.
	int32& Value = NarrativeRecord.BondRanks.FindOrAdd(BondId);
	Value = FMath::Max(Value, Rank);
	return Value;
}

int32 UMelodiaNarrativeSubsystem::AdvancePhase()
{
	return ++NarrativeRecord.PhaseIndex;
}

FName UMelodiaNarrativeSubsystem::GetSpawnContext(FName MapId) const
{
	const FName* Found = NarrativeRecord.SpawnContext.Find(MapId);
	return Found ? *Found : NAME_None;
}

bool UMelodiaNarrativeSubsystem::SetSpawnContext(FName MapId, FName SpawnTag)
{
	if (MapId.IsNone())
	{
		return false;
	}

	NarrativeRecord.SpawnContext.Add(MapId, SpawnTag);
	return true;
}

void UMelodiaNarrativeSubsystem::ResetNarrativeRecord()
{
	NarrativeRecord = FMelodiaNarrativeRecord();
	PendingEncounterId = NAME_None;
	bBattleCompletionConsumed = false;
	if (UQuillscriptSubsystem* Quill = GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>())
	{
		Quill->GetVariables().Remove(TEXT("melodia_battle_result"));
	}
}

bool UMelodiaNarrativeSubsystem::SyncNarrativeRecordToSave(UObject* JRPGSaveObject)
{
	if (!IsValid(JRPGSaveObject))
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia narrative save sync rejected: save object is invalid."));
		return false;
	}

	CapturePersistentQuillVariables();
	if (UMelodiaWaterGameplaySubsystem* WaterGameplay = GetGameInstance()->GetSubsystem<UMelodiaWaterGameplaySubsystem>())
	{
		WaterGameplay->CaptureSaveState(NarrativeRecord.WaterGameplayState);
	}

	FStructProperty* RecordProperty = FindFProperty<FStructProperty>(JRPGSaveObject->GetClass(), TEXT("melodiaNarrativeRecord"));
	if (!RecordProperty || RecordProperty->Struct != FMelodiaNarrativeRecord::StaticStruct())
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia narrative save sync rejected: canonical save has no compatible melodiaNarrativeRecord field."));
		return false;
	}

	FMelodiaNarrativeRecord* Destination = RecordProperty->ContainerPtrToValuePtr<FMelodiaNarrativeRecord>(JRPGSaveObject);
	if (!Destination)
	{
		return false;
	}

	*Destination = NarrativeRecord;
	return true;
}

void UMelodiaNarrativeSubsystem::CapturePersistentQuillVariables()
{
	if (UQuillscriptSubsystem* Quill = GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>())
	{
		NarrativeRecord.QuillPersistentData.Reset();
		FMemoryWriter QuillWriter(NarrativeRecord.QuillPersistentData, true);
		Quill->SerializeQuillscriptData(QuillWriter);

		NarrativeRecord.QuillVariables.Empty();
		for (const TPair<FName, FText>& Variable : Quill->GetVariables())
		{
			if (IsPersistentQuillVariable(Variable.Key))
			{
				NarrativeRecord.QuillVariables.Add(Variable.Key, Variable.Value);
			}
		}
	}
}

void UMelodiaNarrativeSubsystem::RestorePersistentQuillVariables()
{
	if (UQuillscriptSubsystem* Quill = GetGameInstance()->GetSubsystem<UQuillscriptSubsystem>())
	{
		if (!NarrativeRecord.QuillPersistentData.IsEmpty())
		{
			FMemoryReader QuillReader(NarrativeRecord.QuillPersistentData, true);
			Quill->DeserializeQuillscriptData(QuillReader);
		}

		TMap<FName, FText>& RuntimeVariables = Quill->GetVariables();
		if (NarrativeRecord.QuillPersistentData.IsEmpty())
		{
			// Compatibility lane for saves written before the full Quill payload
			// was added. These saves still restore namespaced authored state.
			for (auto It = RuntimeVariables.CreateIterator(); It; ++It)
			{
				if (IsPersistentQuillVariable(It.Key()))
				{
					It.RemoveCurrent();
				}
			}
			RuntimeVariables.Append(NarrativeRecord.QuillVariables);
		}

		for (const TPair<FName, bool>& Flag : NarrativeRecord.Flags)
		{
			RuntimeVariables.Add(Flag.Key, FText::FromString(Flag.Value ? TEXT("on") : TEXT("off")));
		}
	}
}

bool UMelodiaNarrativeSubsystem::RestoreNarrativeRecordFromSave(UObject* JRPGSaveObject)
{
	if (!IsValid(JRPGSaveObject))
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia narrative load rejected: save object is invalid."));
		return false;
	}

	FStructProperty* RecordProperty = FindFProperty<FStructProperty>(JRPGSaveObject->GetClass(), TEXT("melodiaNarrativeRecord"));
	if (!RecordProperty || RecordProperty->Struct != FMelodiaNarrativeRecord::StaticStruct())
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia narrative load rejected: canonical save has no compatible melodiaNarrativeRecord field."));
		return false;
	}

	const FMelodiaNarrativeRecord* Source = RecordProperty->ContainerPtrToValuePtr<FMelodiaNarrativeRecord>(JRPGSaveObject);
	return Source && RestoreNarrativeRecord(*Source);
}

#if WITH_EDITOR
bool UMelodiaNarrativeSubsystem::CompileQuillSource(UQuillscriptAsset* QuillAsset, const FString& SourceCode)
{
	if (!IsValid(QuillAsset) || SourceCode.IsEmpty())
	{
		return false;
	}

	QuillAsset->Modify();
	QuillAsset->SetContent(SourceCode);
	QuillAsset->MarkPackageDirty();
	return true;
}
#endif

void UMelodiaNarrativeSubsystem::HandleQuillScriptPlay(AQuillscriptInterpreter* Interpreter)
{
	if (!IsValid(Interpreter))
	{
		ActiveInterpreter.Reset();
		UE_LOG(LogTemp, Error, TEXT("MELUSINA_LOOP_QUILL_PLAY rejected: interpreter is invalid."));
		return;
	}

	ActiveInterpreter = Interpreter;

	// Quill creates its managed widgets before broadcasting OnScriptPlay, but
	// dialogue content is initialized later by PlayDialogueBox(). Do not force
	// visibility or cursor state here: that can expose an empty widget, override
	// authored script input settings, or outlive a script that ends immediately.
	const UDialogBox* DialogBox = Interpreter->GetDialogBox();
	UE_LOG(LogTemp, Log,
		TEXT("MELUSINA_LOOP_QUILL_PLAY interpreter=%s dialog=%s in_viewport=%s"),
		*Interpreter->GetName(),
		*GetNameSafe(DialogBox),
		DialogBox && DialogBox->IsInViewport() ? TEXT("true") : TEXT("false"));
}

bool UMelodiaNarrativeSubsystem::ResumeQuillOnce()
{
	if (AQuillscriptInterpreter* Interpreter = ActiveInterpreter.Get())
	{
		UE_LOG(LogTemp, Log, TEXT("MELUSINA_LOOP_QUILL_RESTORE interpreter=%s"), *Interpreter->GetName());
		Interpreter->Restore();
		UE_LOG(LogTemp, Log, TEXT("MELUSINA_LOOP_QUILL_NEXT interpreter=%s"), *Interpreter->GetName());
		Interpreter->Next();
		return true;
	}

	return Reject(TEXT("ResumeQuill"), EMelodiaIntentFailure::MissingRuntime);
}

void UMelodiaNarrativeSubsystem::HandleQuillNotification(FString Message)
{
	if (!Message.StartsWith(IntentPrefix, ESearchCase::IgnoreCase))
	{
		return;
	}

	UE_LOG(LogTemp, Log, TEXT("MELUSINA_LOOP_QUILL_NOTIFY message=%s"), *Message);

	FString Context = Message;
	if (Config)
	{
		FString State = GetWorldStateForValidation();
		if (!State.IsEmpty())
		{
			Context = FString::Printf(TEXT("%s [STATE: %s]"), *Message, *State);
		}
	}

	// Async Ollama validation, logging-only and non-gating (Decision 016/009:
	// this must never block or alter the intent path). The helper logs
	// MELODIA_Ollama_Validation with the verdict; fire-and-forget.
	MelodiaOllamaValidation::ValidateMessageAsync(Context, [this, Message](bool bValid, const FString& RawReply)
	{
		if (!bValid && Config && Config->bStrictAiValidation)
		{
			UE_LOG(LogTemp, Error, TEXT("MELODIA_STRICT_AI_REJECT intent=%s"), *Message);
			Reject(Message, EMelodiaIntentFailure::UnknownIntent);
		}
	});

	TArray<FString> Parts;
	Message.ParseIntoArray(Parts, TEXT(":"), true);
	if (Parts.Num() < 3)
	{
		Reject(Message, EMelodiaIntentFailure::UnknownIntent);
		return;
	}

	const FString& Verb = Parts[1];
	const FName Id(*Parts[2]);

	typedef void (UMelodiaNarrativeSubsystem::*FVerbHandler)(const FName, const TArray<FString>&, const FString&);
	static TMap<FString, FVerbHandler> Handlers;
	if (Handlers.Num() == 0)
	{
		Handlers.Add(TEXT("battle"), &UMelodiaNarrativeSubsystem::HandleBattleVerb);
		Handlers.Add(TEXT("quest"), &UMelodiaNarrativeSubsystem::HandleQuestVerb);
		Handlers.Add(TEXT("flag"), &UMelodiaNarrativeSubsystem::HandleFlagVerb);
		Handlers.Add(TEXT("travel"), &UMelodiaNarrativeSubsystem::HandleTravelVerb);
		Handlers.Add(TEXT("reward"), &UMelodiaNarrativeSubsystem::HandleRewardVerb);
		Handlers.Add(TEXT("stat"), &UMelodiaNarrativeSubsystem::HandleStatVerb);
		Handlers.Add(TEXT("item"), &UMelodiaNarrativeSubsystem::HandleItemVerb);
	}

	if (FVerbHandler* Handler = Handlers.Find(Verb.ToLower()))
	{
		(this->**Handler)(Id, Parts, Message);
	}
	else
	{
		Reject(Message, EMelodiaIntentFailure::UnknownIntent);
	}
}

FString UMelodiaNarrativeSubsystem::GetWorldStateForValidation() const
{
	if (!Config) return TEXT("");

	TArray<FString> StateParts;
	
	// Add location
	if (UWorld* World = GetWorld())
	{
		StateParts.Add(FString::Printf(TEXT("Location=%s"), *World->GetMapName()));
	}

	// Add Social Stats
	if (NarrativeRecord.SocialStats.Num() > 0)
	{
		FString StatsStr = TEXT("Stats(");
		for (const auto& Stat : NarrativeRecord.SocialStats)
		{
			StatsStr += FString::Printf(TEXT("%s:%d,"), *Stat.Key.ToString(), Stat.Value);
		}
		StatsStr.RemoveFromEnd(TEXT(","));
		StatsStr += TEXT(")");
		StateParts.Add(StatsStr);
	}

	// Add active quests
	if (NarrativeRecord.ActiveQuestIds.Num() > 0)
	{
		StateParts.Add(FString::Printf(TEXT("QuestsActive=%d"), NarrativeRecord.ActiveQuestIds.Num()));
	}

	return FString::Join(StateParts, TEXT("; "));
}

void UMelodiaNarrativeSubsystem::HandleBattleVerb(const FName Id, const TArray<FString>& Parts, const FString& Message)
{
	StartBattle(Id);
}

void UMelodiaNarrativeSubsystem::HandleQuestVerb(const FName Id, const TArray<FString>& Parts, const FString& Message)
{
	CompleteQuest(Id);
}

void UMelodiaNarrativeSubsystem::HandleFlagVerb(const FName Id, const TArray<FString>& Parts, const FString& Message)
{
	if (Parts.Num() == 4)
	{
		bool Value = false;
		ParseBool(Parts[3], Value) ? SetNarrativeFlag(Id, Value) : Reject(Message, EMelodiaIntentFailure::UnknownIntent);
	}
	else
	{
		Reject(Message, EMelodiaIntentFailure::UnknownIntent);
	}
}

void UMelodiaNarrativeSubsystem::HandleTravelVerb(const FName Id, const TArray<FString>& Parts, const FString& Message)
{
	RequestTravel(Id);
}

void UMelodiaNarrativeSubsystem::HandleRewardVerb(const FName Id, const TArray<FString>& Parts, const FString& Message)
{
	GrantDialogueReward(Id);
}

void UMelodiaNarrativeSubsystem::HandleStatVerb(const FName Id, const TArray<FString>& Parts, const FString& Message)
{
	// Syntax: melodia:stat:<IntentId>:<StatId>:<Delta>
	// Id is the authored intent id; the stat and delta follow it. Routing through
	// GrantDialogueSocialStat keeps the allowlist check and the per-intent
	// ConsumeOnce guard on the one path, so a Quill resume or a save reload
	// replaying the same beat is a no-op instead of a second grant.
	if (Parts.Num() != 5)
	{
		Reject(Message, EMelodiaIntentFailure::UnknownIntent);
		return;
	}

	const FName StatId(*Parts[3]);
	int32 Delta = 0;
	LexFromString(Delta, *Parts[4]);

	GrantDialogueSocialStat(Id, StatId, Delta);
}

void UMelodiaNarrativeSubsystem::HandleItemVerb(const FName Id, const TArray<FString>& Parts, const FString& Message)
{
	// Syntax: melodia:item:give:<ItemId>:<Count>
	if (Parts.Num() == 5 && Parts[2].Equals(TEXT("give"), ESearchCase::IgnoreCase))
	{
		const FName ItemId(*Parts[3]);
		int32 Count = 0;
		LexFromString(Count, *Parts[4]);
		
		if (Count > 0)
		{
			UE_LOG(LogTemp, Log, TEXT("MELUSINA_LOOP_ITEM_GRANT id=%s count=%d"), *ItemId.ToString(), Count);
			// For now, we log and could broadcast an event or call a wallet/inventory subsystem.
			// This demonstrates multi-parameter verb support.
		}
		else
		{
			Reject(Message, EMelodiaIntentFailure::UnknownIntent);
		}
	}
	else
	{
		Reject(Message, EMelodiaIntentFailure::UnknownIntent);
	}
}
