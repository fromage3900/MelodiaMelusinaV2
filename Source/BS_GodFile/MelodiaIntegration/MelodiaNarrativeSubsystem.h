#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaNarrativeTypes.h"
#include "MelodiaNarrativeSubsystem.generated.h"

class AQuillscriptInterpreter;
class UQuillscriptAsset;
class UMelodiaIntegrationConfig;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaBattleRequested, FName, EncounterId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaQuestRequested, FName, QuestId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaTravelRequested, FName, LevelId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaRewardRequested, FName, RewardId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaFlagChanged, FName, FlagId, bool, Value);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaSocialStatRequested, FName, StatId, int32, Delta);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaIntentRejected, FString, Intent, EMelodiaIntentFailure, Failure);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaBattleCompleted, FName, EncounterId, EMelodiaBattleResult, Result);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaBattleAborted, FName, EncounterId, FString, Reason);

UCLASS()
class BS_GODFILE_API UMelodiaNarrativeSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	UFUNCTION(BlueprintPure, Category = "Melodia|Integration", meta = (WorldContext = "WorldContextObject"))
	static UMelodiaNarrativeSubsystem* GetMelodiaNarrativeSubsystem(const UObject* WorldContextObject);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Integration")
	TObjectPtr<UMelodiaIntegrationConfig> Config;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Integration")
	FMelodiaBattleRequested OnBattleRequested;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Integration")
	FMelodiaQuestRequested OnQuestRequested;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Integration")
	FMelodiaTravelRequested OnTravelRequested;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Integration")
	FMelodiaRewardRequested OnRewardRequested;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Integration")
	FMelodiaFlagChanged OnFlagChanged;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Integration")
	FMelodiaIntentRejected OnIntentRejected;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Integration")
	FMelodiaBattleCompleted OnBattleCompleted;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Integration")
	FMelodiaBattleAborted OnBattleAborted;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Integration")
	bool StartBattle(FName EncounterId);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Integration")
	bool CompleteQuest(FName QuestId);

	/** Persists quest acceptance in the canonical narrative record. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Integration")
	bool SetQuestActive(FName QuestId, bool bActive);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Integration")
	bool SetNarrativeFlag(FName FlagId, bool Value);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Integration")
	bool RequestTravel(FName LevelId);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Integration")
	bool GrantDialogueReward(FName RewardId);

	/** Read-only completion query for a data-driven world challenge. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Integration|World Challenge")
	bool IsWorldChallengeCompleted(FName ChallengeId, FName CompletionFlagId) const;

	/**
	 * Atomically commits a world-challenge completion, consumed intent, and
	 * allowlisted reward. Blueprint children must use this transaction rather
	 * than calling SetNarrativeFlag and GrantDialogueReward independently.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Integration|World Challenge")
	EMelodiaContentCommitResult CommitWorldChallenge(
		FName ChallengeId,
		FName CompletionFlagId,
		FName RewardId,
		FName CompletionIntentId,
		EMelodiaContentCommitFailure& OutFailure);

	/** Read-only canonical state query for a generic stable-key StateAnchor. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Integration|State Anchor")
	bool IsStateAnchorApplied(FName AnchorId, FName PersistenceKey, FName ApplyIntentId) const;

	/**
	 * Applies an allowlisted StateAnchor operation list once through the
	 * narrative record. Invalid or partially-applied transactions make no
	 * canonical mutation.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Integration|State Anchor")
	EMelodiaContentCommitResult ApplyStateAnchor(
		FName AnchorId,
		FName PersistenceKey,
		const TArray<FMelodiaStateAnchorOperation>& Operations,
		FName ApplyIntentId,
		EMelodiaContentCommitFailure& OutFailure);

	/**
	 * Raises a Persona-lite social stat from an allowlisted dialogue choice
	 * (Decision 018 -- dialogue is the only source).
	 *
	 * Applied once per authored intent ID: that stable ID is recorded in
	 * ConsumedIntentIds, so a Quill resume or reloaded save cannot double-apply
	 * this choice while a different authored beat may raise the same stat.
	 * StatId remains independently validated against the social-stat allowlist.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Integration")
	bool GrantDialogueSocialStat(FName IntentId, FName StatId, int32 Delta);

	/** Persona listens here; this subsystem validates but does not own stat semantics. */
	UPROPERTY(BlueprintAssignable, Category = "Melodia|Integration")
	FMelodiaSocialStatRequested OnSocialStatRequested;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Integration")
	bool CompleteBattle(EMelodiaBattleResult Result);

	/**
	 * Releases a pending encounter after an integration failure without fabricating a
	 * battle result.
	 *
	 * BlueprintCallable because the Fled/torn-down path has no other way out: without
	 * it a battle that ends unexpectedly leaves PendingEncounterId set and the
	 * subsystem Busy forever, and no Blueprint could clear it.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Integration")
	bool AbortPendingBattle(const FString& Reason);

	UFUNCTION(BlueprintPure, Category = "Melodia|Integration")
	bool IsBattlePending() const { return !PendingEncounterId.IsNone(); }

	UFUNCTION(BlueprintPure, Category = "Melodia|Integration")
	FName GetPendingEncounterId() const { return PendingEncounterId; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Integration|Save")
	FMelodiaNarrativeRecord GetNarrativeRecord() const { return NarrativeRecord; }

	UFUNCTION(BlueprintCallable, Category = "Melodia|Integration|Save")
	bool RestoreNarrativeRecord(const FMelodiaNarrativeRecord& Record);

	/**
	 * Upgrades a record written by an older build to CurrentVersion in place.
	 *
	 * Returns false only when the record cannot be upgraded (it is newer than
	 * this build, or from a version with no migration path), in which case the
	 * caller must refuse the load rather than silently discarding player state.
	 *
	 * New fields that default sensibly need no migration case -- they simply
	 * arrive zeroed. Add a case only when old data must be transformed.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Integration|Save")
	static bool MigrateRecord(UPARAM(ref) FMelodiaNarrativeRecord& Record);

	// --- Persona-lite persistent state -------------------------------------
	// These live on the narrative record because it is the project's single
	// persistence seam. Systems that own their semantics (Persona, travel) read
	// and write through here instead of holding a transient copy.

	UFUNCTION(BlueprintPure, Category = "Melodia|Integration|Persona")
	int32 GetSocialStat(FName StatId) const;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Integration|Persona")
	int32 AddSocialStat(FName StatId, int32 Delta);

	UFUNCTION(BlueprintPure, Category = "Melodia|Integration|Persona")
	int32 GetBondRank(FName BondId) const;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Integration|Persona")
	int32 SetBondRank(FName BondId, int32 Rank);

	UFUNCTION(BlueprintPure, Category = "Melodia|Integration|Persona")
	int32 GetPhaseIndex() const { return NarrativeRecord.PhaseIndex; }

	UFUNCTION(BlueprintCallable, Category = "Melodia|Integration|Persona")
	int32 AdvancePhase();

	UFUNCTION(BlueprintPure, Category = "Melodia|Integration|Travel")
	FName GetSpawnContext(FName MapId) const;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Integration|Travel")
	bool SetSpawnContext(FName MapId, FName SpawnTag);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Integration|Save")
	void ResetNarrativeRecord();

	/** Copies the approved narrative record into the canonical JRPG save object. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Integration|Save")
	bool SyncNarrativeRecordToSave(UObject* JRPGSaveObject);

	/** Restores the approved narrative record from the canonical JRPG save object. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Integration|Save")
	bool RestoreNarrativeRecordFromSave(UObject* JRPGSaveObject);

#if WITH_EDITOR
	/** Reparse authored Quill source so SourceCode and compiled Statements remain synchronized. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Integration|Editor")
	static bool CompileQuillSource(UQuillscriptAsset* QuillAsset, const FString& SourceCode);
#endif

	/** Returns a descriptive string of the current world state for AI validation. */
	FString GetWorldStateForValidation() const;

	/**
	 * Entry point for a Quill notification message.
	 *
	 * UFUNCTION is REQUIRED: Initialize binds this with AddUniqueDynamic, and a
	 * dynamic delegate can only bind reflected functions. Without it the bind
	 * silently fails at runtime (ensure: "Unable to bind delegate to
	 * 'HandleQuillNotification'") and EVERY melodia: intent -- battle, travel,
	 * reward, stat, quest, flag -- never reaches this subsystem.
	 */
	UFUNCTION()
	void HandleQuillNotification(FString Message);

private:
	void HandleBattleVerb(const FName Id, const TArray<FString>& Parts, const FString& Message);
	void HandleQuestVerb(const FName Id, const TArray<FString>& Parts, const FString& Message);
	void HandleFlagVerb(const FName Id, const TArray<FString>& Parts, const FString& Message);
	void HandleTravelVerb(const FName Id, const TArray<FString>& Parts, const FString& Message);
	void HandleRewardVerb(const FName Id, const TArray<FString>& Parts, const FString& Message);
	void HandleStatVerb(const FName Id, const TArray<FString>& Parts, const FString& Message);
	void HandleItemVerb(const FName Id, const TArray<FString>& Parts, const FString& Message);

	/** UFUNCTION required -- bound via AddUniqueDynamic alongside HandleQuillNotification. */
	UFUNCTION()
	void HandleQuillScriptPlay(AQuillscriptInterpreter* Interpreter);

	bool Reject(const FString& Intent, EMelodiaIntentFailure Failure);
	bool IsAllowed(const TSet<FName>& Allowlist, FName Id, const FString& Intent);
	bool ConsumeOnce(TArray<FName>& ConsumedIds, FName Id, const FString& Intent);
	bool ResumeQuillOnce();
	void CapturePersistentQuillVariables();
	void RestorePersistentQuillVariables();

	UPROPERTY(Transient)
	TWeakObjectPtr<AQuillscriptInterpreter> ActiveInterpreter;

	UPROPERTY(Transient)
	FName PendingEncounterId;

	UPROPERTY(Transient)
	bool bBattleCompletionConsumed = false;

	UPROPERTY()
	FMelodiaNarrativeRecord NarrativeRecord;
};
