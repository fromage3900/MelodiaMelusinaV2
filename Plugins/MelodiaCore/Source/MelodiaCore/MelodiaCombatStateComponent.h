// Native reactive combat state for Melodia battle actors.
// Ported from MelodiaMelusina_PROD to MelodiaCore plugin (UE 5.8).

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaSpellTypes.h"
#include "MelodiaAfflictionTypes.h"
#include "MelodiaCombatStateComponent.generated.h"

// QUARANTINED LANE (Decision 016, 2026-07-30): this class is not part of the
// shipping authority (second battle stack). Guards below block NEW Blueprints/placements; existing
// content references still resolve. Do not re-enable without a logged decision.
UCLASS(ClassGroup=(Melodia), NotBlueprintable, NotPlaceable, HideDropdown)
class MELODIACORE_API UMelodiaCombatStateComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaCombatStateComponent();

	// --- Ultimate gauge ---
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Combat")
	float UltimateGauge = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Combat")
	float UltimateMax = 100.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	bool bUltimateReady = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	float LastUltimateDamage = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	int32 UltimateActivationCount = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	int32 TotalUltimateActivationCount = 0;

	// --- Skill points ---
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Combat")
	int32 SkillPoints = 3;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Combat")
	int32 SkillPointMax = 5;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	int32 LastSkillPointDelta = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	int32 BasicActivationCount = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	int32 SkillActivationCount = 0;

	// --- Command sequencing ---
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	int32 CommandSequence = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	int32 ActiveTurnOrderIndex = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	FString LastCommandName;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	FString EnemyIntentName = TEXT("Waiting");

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	float EnemyIntentPower = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	bool bUltimateInterruptWindow = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	int32 UltimateInterruptCount = 0;

	// --- Enemy toughness / break ---
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Combat")
	float EnemyToughness = 100.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Combat")
	float EnemyToughnessMax = 100.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	float LastToughnessDamage = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	bool bEnemyBroken = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	int32 EnemyBreakCount = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	int32 TotalEnemyBreakCount = 0;

	// --- Break follow-up ---
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	bool bBreakFollowUpAvailable = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	bool bBreakFollowUpConsumed = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	float LastFollowUpBonusDamage = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	int32 BreakFollowUpAvailableCount = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	int32 BreakFollowUpConsumedCount = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	int32 TotalBreakFollowUpConsumedCount = 0;

	// --- Enemy turn delay ---
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	int32 EnemyTurnDelayStacks = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	int32 LastEnemyTurnDelay = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	int32 EnemyTurnDelayApplyCount = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	int32 TotalEnemyTurnDelayApplyCount = 0;

	// --- Party vitals ---
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Combat")
	float PartyHP = 100.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Combat")
	float PartyMaxHP = 100.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Combat")
	EMelodiaSpellElement EnemyElement = EMelodiaSpellElement::Tide;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Combat")
	EMelodiaSpellElement EquippedKeyElement = EMelodiaSpellElement::Forte;

	/** The extra weakness bonus only applies once the matching harmonic key is actually equipped. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Combat")
	bool bHasHarmonicKeyEquipped = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Combat")
	bool bCompanionActive = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	float LastPartyDamageTaken = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	int32 EnemyTurnCount = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Combat")
	bool bUltimateUsedThisBattle = false;

	// --- Functions ---
	UFUNCTION(BlueprintCallable, Category="Melodia|Combat")
	float ApplyPartyDamage(float Damage);
	float AddUltimateGauge(float Delta);

	UFUNCTION(BlueprintCallable, Category="Melodia|Combat")
	void ResetUltimateGauge();

	UFUNCTION(BlueprintCallable, Category="Melodia|Combat")
	void RecordUltimateActivated(float Damage);

	UFUNCTION(BlueprintCallable, Category="Melodia|Combat")
	int32 AddSkillPoints(int32 Delta);

	UFUNCTION(BlueprintCallable, Category="Melodia|Combat")
	bool SpendSkillPoints(int32 Cost);

	UFUNCTION(BlueprintPure, Category="Melodia|Combat")
	bool CanSpendSkillPoints(int32 Cost) const;

	UFUNCTION(BlueprintCallable, Category="Melodia|Combat")
	void ResetActionEconomy(bool bResetPartyResources = true);

	UFUNCTION(BlueprintCallable, Category="Melodia|Combat")
	void EquipHarmonicKey(EMelodiaSpellElement NewKeyElement);

	UFUNCTION(BlueprintCallable, Category="Melodia|Combat")
	void RecordCommandState(const FString& CommandName, const FString& IntentName, float IntentPower, bool bUltimateWindow, bool bUltimateInterrupt);

	UFUNCTION(BlueprintCallable, Category="Melodia|Combat")
	bool ApplyEnemyToughnessDamage(float Damage);

	UFUNCTION(BlueprintCallable, Category="Melodia|Combat")
	void OpenBreakFollowUpWindow();

	UFUNCTION(BlueprintCallable, Category="Melodia|Combat")
	bool ConsumeBreakFollowUp(float BonusDamage);

	UFUNCTION(BlueprintCallable, Category="Melodia|Combat")
	int32 ApplyEnemyTurnDelay(int32 DelayAmount);

	UFUNCTION(BlueprintCallable, Category="Melodia|Combat")
	int32 ConsumeEnemyTurnDelay();

	UFUNCTION(BlueprintCallable, Category="Melodia|Combat")
	void ResetEnemyToughness(bool bResetPartyHP = true);

	// --- Afflictions ---
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Afflictions")
	TArray<FMelodiaAfflictionEntry> ActiveAfflictions;

	UFUNCTION(BlueprintCallable, Category="Melodia|Afflictions")
	void ApplyAffliction(EMelodiaSpellElement Element);

	UFUNCTION(BlueprintCallable, Category="Melodia|Afflictions")
	void TickAfflictions();

	UFUNCTION(BlueprintCallable, Category="Melodia|Afflictions")
	void ClearAfflictions();

	UFUNCTION(BlueprintPure, Category="Melodia|Afflictions")
	float GetAfflictionTickDamageTotal() const;

	// --- Modifiers ---
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Modifiers")
	TArray<FMelodiaModifierEntry> ActiveModifiers;

	UFUNCTION(BlueprintCallable, Category="Melodia|Modifiers")
	void ApplyModifier(FName ModifierId, EMelodiaModifierStat Stat, EMelodiaModifierOp Op, float Value, int32 DurationTurns, EMelodiaModifierStacking Stacking, int32 MaxStacks);

	UFUNCTION(BlueprintCallable, Category="Melodia|Modifiers")
	void TickModifiers();

	UFUNCTION(BlueprintPure, Category="Melodia|Modifiers")
	float EvaluateModifier(EMelodiaModifierStat Stat, float BaseValue) const;

	UFUNCTION(BlueprintCallable, Category="Melodia|Modifiers")
	void ClearModifiers();
};
