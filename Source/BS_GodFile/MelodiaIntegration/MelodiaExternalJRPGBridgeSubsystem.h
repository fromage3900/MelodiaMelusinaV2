#pragma once

#include "CoreMinimal.h"
#include "MelodiaNarrativeTypes.h"
#include "MelodiaRhythmCombatTypes.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "UObject/ObjectKey.h"
#include "MelodiaExternalJRPGBridgeSubsystem.generated.h"

class AActor;
class UGameInstance;
class UMelodiaHybridEncounterComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaExternalJRPGBattleStarted, FName, EncounterId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaExternalJRPGBattleEnded, uint8, BattleResult);

/** Routes exploration encounters to one tagged stock battle actor; stock battle code remains authoritative. */
UCLASS()
class BS_GODFILE_API UMelodiaExternalJRPGBridgeSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	UMelodiaExternalJRPGBridgeSubsystem();

	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/** Explicit accessor used by runtime probes and Blueprint integration. */
	UFUNCTION(BlueprintPure, Category = "Melodia|JRPG Bridge")
	static UMelodiaExternalJRPGBridgeSubsystem* GetGameInstanceSubsystem(UGameInstance* GameInstance);

	UPROPERTY(BlueprintAssignable, Category = "Melodia|JRPG Bridge|Presentation")
	FMelodiaExternalJRPGBattleStarted OnJRPGBattleStarted;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|JRPG Bridge|Presentation")
	FMelodiaExternalJRPGBattleEnded OnJRPGBattleEnded;

	UFUNCTION(BlueprintCallable, Category = "Melodia|JRPG Bridge")
	bool StartTaggedJRPGBattle(FName EncounterId);

	/** Route one completed world encounter through the existing typed narrative outcome. */
	bool CompleteWorldEncounter(UMelodiaHybridEncounterComponent* Encounter, EMelodiaBattleResult Result);

	/** Bind stock combat-stat objects (live units or authored class defaults).
	 * They supply stats only: their HP is never read or written by this route.
	 * CalculateDamage remains the existing stock Blueprint function. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Hybrid")
	bool BindWorldDamageResolver(UMelodiaHybridEncounterComponent* Encounter,
		UObject* StockAttacker, UObject* StockDefenderStats, UObject* StockSkill, int32 PureDamage = 0);

	void UnbindWorldDamageResolver(UMelodiaHybridEncounterComponent* Encounter);

	/** FLOW uses the same stock resolver with identity rhythm scaling. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Hybrid")
	bool ResolveWorldFlowAttack(UMelodiaHybridEncounterComponent* Encounter);

	UFUNCTION(BlueprintPure, Category = "Melodia|JRPG Bridge")
	bool IsJRPGBattleActive() const { return IsValid(ActiveBattleActor); }

	UFUNCTION(BlueprintPure, Category = "Melodia|JRPG Bridge")
	FName GetActiveEncounterId() const { return ActiveEncounterId; }

private:
	UFUNCTION()
	void HandleBattleOver(uint8 BattleResult);
	UFUNCTION()
	void HandleNarrativeBattleRequested(FName EncounterId);
	UFUNCTION()
	void HandleWorldEffectRequested(AActor* Target, const FMelodiaRhythmEffectRequest& Request);

	struct FWorldDamageBinding
	{
		TWeakObjectPtr<UMelodiaHybridEncounterComponent> Encounter;
		TWeakObjectPtr<UObject> Attacker;
		TWeakObjectPtr<UObject> DefenderStats;
		TWeakObjectPtr<UObject> Skill;
		int32 PureDamage = 0;
	};
	bool InvokeStockDamageResolver(const FWorldDamageBinding& Binding, double Multiplier, int32& OutDamage);
	TMap<FObjectKey, FWorldDamageBinding> WorldDamageBindings;
	bool bResolvingStockDamage = false;

	void UnbindActiveBattle();
	bool HasUniqueWorldEncounter(const UMelodiaHybridEncounterComponent* Encounter, FName EncounterId) const;
	UPROPERTY(Transient)
	TObjectPtr<AActor> ActiveBattleActor;

	UPROPERTY(Transient)
	TObjectPtr<class UMelodiaNarrativeSubsystem> NarrativeSubsystem;

	FName ActiveEncounterId;
};
