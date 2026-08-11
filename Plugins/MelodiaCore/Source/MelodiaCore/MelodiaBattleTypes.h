// Shared battle session types ΓÇö kernel phases, encounter payload, HUD modes.
// Ported from MelodiaMelusina_PROD to MelodiaCore plugin (UE 5.8).

#pragma once

#include "CoreMinimal.h"
#include "MelodiaBattleTypes.generated.h"

UENUM(BlueprintType)
enum class EMelodiaBattlePhase : uint8
{
	None UMETA(DisplayName = "None"),
	AwaitingPlayerCommand UMETA(DisplayName = "Awaiting Player Command"),
	RhythmExecution UMETA(DisplayName = "Rhythm Execution"),
	EnemyTurn UMETA(DisplayName = "Enemy Turn"),
	Victory UMETA(DisplayName = "Victory"),
	Defeat UMETA(DisplayName = "Defeat"),
	Fled UMETA(DisplayName = "Fled")
};

UENUM(BlueprintType)
enum class EMelodiaHUDMode : uint8
{
	Exploration UMETA(DisplayName = "Exploration"),
	BattleCompact UMETA(DisplayName = "Battle Compact"),
	BattleHighway UMETA(DisplayName = "Battle Highway"),
	Victory UMETA(DisplayName = "Victory"),
	Defeat UMETA(DisplayName = "Defeat")
};

UENUM(BlueprintType)
enum class EMelodiaEncounterResult : uint8
{
	None UMETA(DisplayName = "None"),
	Victory UMETA(DisplayName = "Victory"),
	Defeat UMETA(DisplayName = "Defeat"),
	Fled UMETA(DisplayName = "Fled")
};

/** Payload passed from encounter triggers into the battle session. */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaEncounterDefinition
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Battle")
	TObjectPtr<AActor> BattleController = nullptr;

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Battle")
	TObjectPtr<AActor> BattleData = nullptr;

	/** Optional presentation-only enemy actor. Combat authority remains in the session. */
	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Battle")
	TObjectPtr<AActor> EnemyActor = nullptr;

	/** Optional named enemy from MelodiaEnemyDefinition; level scaling remains the fallback. */
	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Battle")
	FName EnemyId;

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Battle")
	int32 EncounterLevel = 1;

	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Battle")
	FText EncounterDisplayName;
};
