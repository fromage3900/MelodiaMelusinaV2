// Authoritative battle encounter orchestrator.
// Adapted from MelodiaMelusina_PROD ΓÇö JRPG template bridge replaced with direct CombatState wiring.

#pragma once

#include "CoreMinimal.h"
#include "Engine/TimerHandle.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaBattleTypes.h"
#include "MelodiaRhythmExecutionComponent.h"
#include "MelodiaSongSkillLibrary.h"
#include "MelodiaBattleSession.generated.h"

class UMelodiaCombatStateComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaOnBattlePhaseChanged, EMelodiaBattlePhase, NewPhase, EMelodiaBattlePhase, PreviousPhase);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaOnEncounterEnded, EMelodiaEncounterResult, Result);

/** Aggregated tallies for the results screen (WBP_Battle_Results). */
USTRUCT(BlueprintType)
struct FMelodiaBattleResultsSummary
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session")
	EMelodiaEncounterResult Result = EMelodiaEncounterResult::None;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session")
	FText Rank;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session")
	float Score = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session")
	int32 MaxCombo = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session")
	int32 PerfectCount = 0;

	/** Non-perfect hits (Great + Good). */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session")
	int32 HitCount = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session")
	int32 MissCount = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session")
	int32 TotalNotes = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session")
	float DamageDealt = 0.0f;
};

/**
 * GameInstance subsystem ΓÇö authoritative encounter lifecycle.
 * Phase machine: None ΓåÆ AwaitingPlayerCommand ΓåÆ RhythmExecution ΓåÆ EnemyTurn ΓåÆ Victory/Defeat/Fled.
 */
UCLASS()
class MELODIACORE_API UMelodiaBattleSession : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	UFUNCTION(BlueprintPure, Category="Melodia|Battle Session", meta=(WorldContext="WorldContextObject"))
	static UMelodiaBattleSession* Get(const UObject* WorldContextObject);

	// --- Phase queries ---
	UFUNCTION(BlueprintPure, Category="Melodia|Battle Session")
	EMelodiaBattlePhase GetBattlePhase() const { return BattlePhase; }

	UFUNCTION(BlueprintPure, Category="Melodia|Battle Session")
	bool IsEncounterActive() const;

	UFUNCTION(BlueprintPure, Category="Melodia|Battle Session")
	bool IsAwaitingPlayerCommand() const;

	UFUNCTION(BlueprintPure, Category="Melodia|Battle Session")
	bool IsRhythmExecutionActive() const;

	UFUNCTION(BlueprintPure, Category="Melodia|Battle Session")
	bool CanSubmitBasicCommand() const;

	UFUNCTION(BlueprintPure, Category="Melodia|Battle Session")
	bool CanSubmitSkillCommand(FName SkillId) const;

	UFUNCTION(BlueprintPure, Category="Melodia|Battle Session")
	bool CanSubmitUltimateCommand() const;

	UFUNCTION(BlueprintPure, Category="Melodia|Battle Session")
	bool CanSubmitFleeCommand() const;

	// --- Encounter lifecycle ---
	UFUNCTION(BlueprintCallable, Category="Melodia|Battle Session")
	bool BeginEncounter(const FMelodiaEncounterDefinition& Encounter);

	UFUNCTION(BlueprintCallable, Category="Melodia|Battle Session")
	bool SubmitBasicCommand();

	UFUNCTION(BlueprintCallable, Category="Melodia|Battle Session")
	bool SubmitSkillCommand(FName SkillId);

	UFUNCTION(BlueprintCallable, Category="Melodia|Battle Session")
	bool SubmitUltimateCommand();

	UFUNCTION(BlueprintCallable, Category="Melodia|Battle Session")
	bool SubmitFleeCommand();

	UFUNCTION(BlueprintCallable, Category="Melodia|Battle Session")
	bool ConfirmVictoryReward();

	/** Restore health carried between encounters. Returns the amount actually restored. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Battle Session|Persistent Party")
	float RestorePersistentPartyHealth(float Amount);

	UFUNCTION(BlueprintCallable, Category="Melodia|Battle Session|Persistent Party")
	int32 RestorePersistentSkillPoints(int32 Amount);

	/** Absolute restore of the Persistent Party block from a loaded save. Does not
	 * touch BattlePhase or any live-encounter state. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Battle Session|Persistent Party")
	void RestorePersistentPartyState(float HP, float MaxHP, int32 SkillPoints, int32 SkillPointMax,
		float UltimateGauge, EMelodiaSpellElement KeyElement, bool bHarmonicKeyEquipped);

	// --- Rhythm execution notifications ---
	void NotifyRhythmExecutionStarted();
	void NotifyRhythmExecutionFinished(const FMelodiaRhythmExecutionResult& Result);

	// --- Delegates ---
	UPROPERTY(BlueprintAssignable, Category="Melodia|Battle Session")
	FMelodiaOnBattlePhaseChanged OnBattlePhaseChanged;

	UPROPERTY(BlueprintAssignable, Category="Melodia|Battle Session")
	FMelodiaOnEncounterEnded OnEncounterEnded;

	// --- Accessors ---
	UFUNCTION(BlueprintPure, Category="Melodia|Battle Session")
	AActor* GetBattleController() const { return ActiveBattleController; }

	UFUNCTION(BlueprintPure, Category="Melodia|Battle Session")
	UMelodiaCombatStateComponent* GetCombatState() const;

	UFUNCTION(BlueprintPure, Category="Melodia|Battle Session")
	EMelodiaEncounterResult GetLastEncounterResult() const { return LastEncounterResult; }

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session")
	EMelodiaHUDMode HUDMode = EMelodiaHUDMode::Exploration;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session")
	int32 CommandSubmitCount = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session")
	int32 EncounterPhaseLogCount = 0;

	/** Persistent combo across the entire encounter (resets on Miss) */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session")
	int32 SessionCombo = 0;

	/** Highest combo achieved this encounter */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session")
	int32 SessionMaxCombo = 0;

	/** Cumulative score for the encounter */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session")
	float SessionScore = 0.0f;

	/** Aggregated results for the encounter (drives WBP_Battle_Results). */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session")
	FMelodiaBattleResultsSummary LastBattleResults;

	UFUNCTION(BlueprintPure, Category="Melodia|Battle Session")
	const FMelodiaBattleResultsSummary& GetLastBattleResults() const { return LastBattleResults; }

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session")
	FString LastEncounterPhaseLogEntry;

	// --- Enemy HP (direct state, no reflection bridge needed) ---
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Battle Session")
	float EnemyHP = 300.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Battle Session")
	float EnemyMaxHP = 300.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Battle Session")
	float EnemyBaseDamage = 15.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Battle Session")
	int32 EnemySpeed = 80;

	// --- Action Value turn economy (GS-003): lowest accumulated AV acts next ---
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Battle Session|Turn Economy", meta=(ClampMin="1"))
	int32 PlayerBaseSpeed = 100;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session|Turn Economy")
	int32 PlayerAV = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session|Turn Economy")
	int32 EnemyAV = 0;

	/** Player speed after Speed modifiers (HasteDance etc.); feeds AV costs. */
	UFUNCTION(BlueprintPure, Category="Melodia|Battle Session|Turn Economy")
	int32 GetEffectivePlayerSpeed() const;

	/** Times the ultimate fired as an AV interrupt this encounter (GS-004). */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session|Turn Economy")
	int32 UltimateInterruptCount = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session")
	FName ActiveEnemyId = NAME_None;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session")
	FText ActiveEnemyIntentName;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session")
	float ActiveEnemyIntentDamage = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session")
	float ActiveEnemyBPM = 128.0f;

	// --- Staged enemy-turn pacing (seconds) ---
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Battle Session|Pacing")
	float EnemyTelegraphDuration = 0.4f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Battle Session|Pacing")
	float EnemyAttackAnimDuration = 0.6f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Battle Session|Pacing")
	float EnemyPostImpactDuration = 0.35f;

	/** Disable to restore the original instant while-loop resolution. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Battle Session|Pacing")
	bool bStageEnemyTurns = true;

	/** Party values intentionally carried from one encounter trigger to the next. */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session|Persistent Party")
	float PersistentPartyHP = 100.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session|Persistent Party")
	float PersistentPartyMaxHP = 100.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session|Persistent Party")
	int32 PersistentSkillPoints = 3;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session|Persistent Party")
	int32 PersistentSkillPointMax = 5;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session|Persistent Party")
	float PersistentUltimateGauge = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session|Persistent Party")
	EMelodiaSpellElement PersistentEquippedKeyElement = EMelodiaSpellElement::Forte;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Battle Session|Persistent Party")
	bool bPersistentHarmonicKeyEquipped = false;

private:
	void SetBattlePhase(EMelodiaBattlePhase NewPhase);
	void SyncHUDMode();
	void EndEncounter(EMelodiaEncounterResult Result);
	void ExecuteEnemyTurn();
	void RunEnemyAVCatchUp();

	// --- Staged enemy turns (P5/HSR pacing; math identical to the immediate path) ---
	/** Telegraph -> attack-anim -> impact -> recompute, timer-paced. Falls back to the
	 * immediate while-loop when no world/timer manager is available (headless tests). */
	void BeginStagedEnemyTurns();
	void StagedEnemyTelegraph();
	void StagedEnemyImpact();
	void FinishStagedEnemyTurns();
	/** ExecuteEnemyTurn minus phase-set + intent presentation (those fire at telegraph). */
	void ResolveEnemyAction();
	bool ShouldEnemyActAgain(int32 ActionsTaken) const;
	void PushBackEnemyAV(float AvFraction);
	bool ResolveRhythmExecutionResult(const FMelodiaRhythmExecutionResult& Result);
	bool CheckVictoryOrDefeat();
	void UpdateSessionCombo(const FMelodiaRhythmExecutionResult& Result);
	void HydrateCombatStateFromPersistentParty(UMelodiaCombatStateComponent& CombatState);
	void StorePersistentPartyFromCombatState(const UMelodiaCombatStateComponent& CombatState);
	void NotifyPlayerCommandPresentation(FName CommandId, EMelodiaRhythmGrade RhythmGrade) const;
	void NotifyPlayerVictoryPresentation() const;
	void NotifyPlayerDefeatPresentation() const;
	void NotifyEnemyIntentPresentation() const;
	void NotifyEnemyHitPresentation(float Damage, EMelodiaRhythmGrade RhythmGrade) const;
	void NotifyEnemyBrokenPresentation() const;
	void NotifyEnemyDefeatedPresentation() const;

	UPROPERTY()
	TObjectPtr<AActor> ActiveBattleController = nullptr;

	UPROPERTY()
	FMelodiaEncounterDefinition ActiveEncounter;

	EMelodiaBattlePhase BattlePhase = EMelodiaBattlePhase::None;
	EMelodiaEncounterResult LastEncounterResult = EMelodiaEncounterResult::None;
	bool bPersistentPartyStateInitialized = false;

	// staged enemy-turn state
	FTimerHandle EnemyStageTimer;
	int32 StagedActionsTaken = 0;
	bool bStagedSequenceRunning = false;

	// defeat presentation: hold the Defeat phase briefly before teardown
	FTimerHandle DefeatTimer;
	void FinishDefeat();

	// ultimate choreography: camera/dilation beat, damage lands after
	FTimerHandle UltTimer;
	float PendingUltimateDamage = 0.0f;
	void ApplyUltimateDamage();
};
