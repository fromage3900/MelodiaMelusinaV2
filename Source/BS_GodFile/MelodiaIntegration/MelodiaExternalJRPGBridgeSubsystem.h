#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaExternalJRPGBridgeSubsystem.generated.h"

class AActor;
class UGameInstance;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaExternalJRPGBattleStarted, FName, EncounterId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaExternalJRPGBattleEnded, uint8, BattleResult);

/** Routes exploration encounters to one tagged stock battle actor; stock battle code remains authoritative. */
UCLASS()
class BS_GODFILE_API UMelodiaExternalJRPGBridgeSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
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

	UFUNCTION(BlueprintPure, Category = "Melodia|JRPG Bridge")
	bool IsJRPGBattleActive() const { return IsValid(ActiveBattleActor); }

	UFUNCTION(BlueprintPure, Category = "Melodia|JRPG Bridge")
	FName GetActiveEncounterId() const { return ActiveEncounterId; }

private:
	UFUNCTION()
	void HandleBattleOver(uint8 BattleResult);
	UFUNCTION()
	void HandleNarrativeBattleRequested(FName EncounterId);

	void UnbindActiveBattle();
	UPROPERTY(Transient)
	TObjectPtr<AActor> ActiveBattleActor;

	UPROPERTY(Transient)
	TObjectPtr<class UMelodiaNarrativeSubsystem> NarrativeSubsystem;

	FName ActiveEncounterId;
};
