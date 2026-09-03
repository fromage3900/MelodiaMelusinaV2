#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaPersonaTypes.h"
#include "MelodiaPersonaSubsystem.generated.h"

class UMelodiaNarrativeSubsystem;
class UMelodiaExternalJRPGBridgeSubsystem;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaQuestStateChanged, FName, QuestId, EMelodiaQuestState, State);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaSocialStatChanged, FName, StatId, int32, NewValue);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaEquipmentRequested, FName, UnitId, FName, EquipmentId);

/**
 * Save-backed Persona-lite read model and integration facade.
 * Stock JRPG Blueprints remain authoritative for combat, inventory, equipment application and UI.
 */
UCLASS()
class BS_GODFILE_API UMelodiaPersonaSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	UFUNCTION(BlueprintPure, Category="Melodia|Persona", meta=(WorldContext="WorldContextObject"))
	static UMelodiaPersonaSubsystem* Get(const UObject* WorldContextObject);

	UPROPERTY(BlueprintAssignable, Category="Melodia|Persona|Quest")
	FMelodiaQuestStateChanged OnQuestStateChanged;

	UPROPERTY(BlueprintAssignable, Category="Melodia|Persona|Stats")
	FMelodiaSocialStatChanged OnSocialStatChanged;

	/** Stock equipment graph consumes this request and remains authoritative. */
	UPROPERTY(BlueprintAssignable, Category="Melodia|Persona|Equipment")
	FMelodiaEquipmentRequested OnEquipmentRequested;

	UFUNCTION(BlueprintPure, Category="Melodia|Persona|Combat")
	TArray<FMelodiaAbilityDefinition> GetAbilitiesForLevel(int32 Level) const;

	UFUNCTION(BlueprintPure, Category="Melodia|Persona|Equipment")
	TArray<FMelodiaEquipmentDefinition> GetEquipmentDefinitions() const;

	UFUNCTION(BlueprintCallable, Category="Melodia|Persona|Equipment")
	bool RequestEquip(FName UnitId, FName EquipmentId);

	UFUNCTION(BlueprintPure, Category="Melodia|Persona|Quest")
	TArray<FMelodiaQuestDefinition> GetAvailableQuests() const;

	UFUNCTION(BlueprintPure, Category="Melodia|Persona|Quest")
	EMelodiaQuestState GetQuestState(FName QuestId) const;

	UFUNCTION(BlueprintCallable, Category="Melodia|Persona|Quest")
	bool AcceptQuest(FName QuestId);

	UFUNCTION(BlueprintCallable, Category="Melodia|Persona|Quest")
	bool CompleteQuest(FName QuestId);

	/** Reads through the canonical narrative record, so stats survive a reload. */
	UFUNCTION(BlueprintPure, Category="Melodia|Persona|Stats")
	int32 GetSocialStat(FName StatId) const;

	UFUNCTION(BlueprintCallable, Category="Melodia|Persona|Stats")
	int32 AddSocialStat(FName StatId, int32 Delta);

	/**
	 * The project's one quest-gating predicate: is content requiring this quest
	 * currently available?  An empty quest ID is always available.
	 *
	 * Minimap markers and Orrery travel destinations ask the same question, so
	 * they must share this answer rather than each implementing the rule.
	 */
	UFUNCTION(BlueprintPure, Category="Melodia|Persona|Quest")
	bool IsGatedContentAvailable(FName RequiredQuestId) const;

	UFUNCTION(BlueprintPure, Category="Melodia|Persona|Minimap")
	TArray<FMelodiaMinimapMarkerDefinition> GetVisibleMinimapMarkers() const;

private:
	const FMelodiaQuestDefinition* FindQuest(FName QuestId) const;
	bool IsQuestComplete(FName QuestId) const;
	void RefreshMinimapWidgets() const;

	UFUNCTION()
	void HandleNarrativeQuest(FName QuestId);

	/** Narrative owns the atomic write; Persona only refreshes its read-model/UI. */
	UFUNCTION()
	void HandleNarrativeQuestStateCommitted(FName QuestId, bool bCompleted);

	/** Narrative validated the intent and its allowlist; Persona owns the clamp and the broadcast. */
	UFUNCTION()
	void HandleSocialStatRequested(FName StatId, int32 Delta);

	/**
	 * Applies an allowlisted dialogue/quest reward.
	 *
	 * UMelodiaNarrativeSubsystem::GrantDialogueReward consumes the id via
	 * ConsumeOnce BEFORE broadcasting, so the reward is already spent by the time
	 * this runs -- consume-first is the idempotence guard and is correct, but it
	 * means an unhandled broadcast burns the reward permanently. This handler is
	 * what stops that: it either equips the mapped item or logs loudly.
	 */
	UFUNCTION()
	void HandleRewardRequested(FName RewardId);

	/** Observes stock battle presentation only; it never owns battle, damage, or quest state. */
	UFUNCTION()
	void HandleJRPGBattleStarted(FName EncounterId);

	UFUNCTION()
	void HandleJRPGBattleEnded(uint8 BattleResult);

	/** Resolves typed Persona equipment IDs into stock JRPG classes and invokes its canonical controller equip function. */
	UFUNCTION()
	void HandleEquipmentRequested(FName UnitId, FName EquipmentId);

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaPersonaContent> Content;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaNarrativeSubsystem> Narrative;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaExternalJRPGBridgeSubsystem> JRPGBridge;

	FName ActiveBridgeEncounterId;

	// Social stats deliberately have no member here. They live on
	// FMelodiaNarrativeRecord, the project's single persistence seam; a local
	// copy would be a second source of truth that silently drops on reload.
};
