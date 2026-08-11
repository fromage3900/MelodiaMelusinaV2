#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaRoguelikeAuthorityTypes.h"
#include "MelodiaSpellTypes.h"
#include "MelodiaRoguelikePersistence.generated.h"

USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaRunHistoryEntry
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|History") int32 SchemaVersion = 1;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|History") int32 RunSeed = 0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|History") int32 FinalStageIndex = 0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|History") int32 EndlessDepth = 0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|History") int64 Score = 0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|History") float DurationSeconds = 0.0f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|History") bool bCompletedStructuredRun = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|History") bool bExtracted = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|History") TArray<FName> RewardIds;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|History") FDateTime FinishedAtUtc;
};

// QUARANTINED LANE (Decision 016, 2026-07-30): this class is not part of the
// shipping authority (deferred roguelike). Guards below block NEW Blueprints/placements; existing
// content references still resolve. Do not re-enable without a logged decision.
UCLASS(NotBlueprintable, NotPlaceable, HideDropdown)
class MELODIACORE_API UMelodiaRoguelikeProfileSaveGame : public USaveGame
{
	GENERATED_BODY()
public:
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Profile") int32 SchemaVersion = 1;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Profile") TArray<FName> DiscoveredDefinitionIds;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Profile") TArray<FName> UnlockedCosmeticIds;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Profile") TArray<FName> NarrativeMemoryIds;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Profile") TMap<FName, FString> Settings;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Profile") int64 DurableCurrency = 0;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Profile") int32 CompanionBond = 0;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Profile") TArray<FName> EntitlementCache;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Profile") FDateTime SavedAtUtc;
};

UCLASS()
class MELODIACORE_API UMelodiaRoguelikeRunCheckpointSaveGame : public USaveGame
{
	GENERATED_BODY()
public:
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Run Checkpoint") int32 SchemaVersion = 1;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Run Checkpoint") FMelodiaRunSnapshot Snapshot;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Run Checkpoint") float PartyHP = 100.0f;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Run Checkpoint") float PartyMaxHP = 100.0f;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Run Checkpoint") int32 SkillPoints = 3;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Run Checkpoint") int32 SkillPointMax = 5;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Run Checkpoint") float UltimateGauge = 0.0f;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Run Checkpoint") EMelodiaSpellElement KeyElement = EMelodiaSpellElement::Forte;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Run Checkpoint") bool bHarmonicKeyEquipped = false;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Run Checkpoint") FDateTime SavedAtUtc;
};

UCLASS()
class MELODIACORE_API UMelodiaRoguelikeRunHistorySaveGame : public USaveGame
{
	GENERATED_BODY()
public:
	UPROPERTY(BlueprintReadOnly, Category="Melodia|History") int32 SchemaVersion = 1;
	UPROPERTY(BlueprintReadOnly, Category="Melodia|History") TArray<FMelodiaRunHistoryEntry> Entries;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaRoguelikePersistenceCompleted, FName, Operation, bool, bSuccess);

UCLASS()
class MELODIACORE_API UMelodiaRoguelikePersistenceSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	UFUNCTION(BlueprintPure, Category="Melodia|Persistence", meta=(WorldContext="WorldContextObject"))
	static UMelodiaRoguelikePersistenceSubsystem* Get(const UObject* WorldContextObject);

	UFUNCTION(BlueprintCallable, Category="Melodia|Persistence")
	void SaveProfile();

	UFUNCTION(BlueprintCallable, Category="Melodia|Persistence")
	void LoadProfile();

	UFUNCTION(BlueprintCallable, Category="Melodia|Persistence")
	void SaveRunCheckpoint();

	UFUNCTION(BlueprintCallable, Category="Melodia|Persistence")
	void LoadRunCheckpoint();

	UFUNCTION(BlueprintCallable, Category="Melodia|Persistence")
	bool ClearRunCheckpoint();

	UFUNCTION(BlueprintCallable, Category="Melodia|Persistence")
	void SaveRunHistory();

	UFUNCTION(BlueprintCallable, Category="Melodia|Persistence")
	void LoadRunHistory();

	UFUNCTION(BlueprintCallable, Category="Melodia|Persistence")
	void AppendRunHistory(const FMelodiaRunHistoryEntry& Entry);

	UFUNCTION(BlueprintPure, Category="Melodia|Persistence")
	bool HasRunCheckpoint() const;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Persistence")
	TObjectPtr<UMelodiaRoguelikeProfileSaveGame> CachedProfile;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Persistence")
	TObjectPtr<UMelodiaRoguelikeRunHistorySaveGame> CachedHistory;

	UPROPERTY(BlueprintAssignable, Category="Melodia|Persistence")
	FMelodiaRoguelikePersistenceCompleted OnOperationCompleted;

private:
	void HandleSaveComplete(const FString& SlotName, int32 UserIndex, bool bSuccess);
	void HandleProfileLoaded(const FString& SlotName, int32 UserIndex, USaveGame* Loaded);
	void HandleCheckpointLoaded(const FString& SlotName, int32 UserIndex, USaveGame* Loaded);
	void HandleHistoryLoaded(const FString& SlotName, int32 UserIndex, USaveGame* Loaded);
	static FString ProfileSlot() { return TEXT("MelodiaProfile_v1"); }
	static FString CheckpointSlot() { return TEXT("MelodiaRunCheckpoint_v1"); }
	static FString HistorySlot() { return TEXT("MelodiaRunHistory_v1"); }
};
