// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFActionCondition.h"
#include "ACFCCTypes.h"
#include "Actors/ACFCharacter.h"
#include "CoreMinimal.h"
#include "Data/ACFCharacterDataAsset.h"
#include <Engine/DataTable.h>
#include <GameplayTagContainer.h>
#include "ACFTask.h"
#include "ACFAITypes.generated.h"

class UContextualAnimSceneAsset;
class AACFSplinePath;
class AAIController;
class AController;

/**
 *
 */

UENUM(BlueprintType)
enum class EAgentRotation : uint8
{
	EGroupForward = 0 UMETA(DisplayName = "Group Forward"),
	EGroupCenter = 1 UMETA(DisplayName = "Look at Group Center")
};

UENUM(BlueprintType)
enum class EPatrolType : uint8
{
	EFollowSpline = 0 UMETA(DisplayName = "Follow Spline"),
	ERandomPoint = 1 UMETA(DisplayName = "Random Point In Range"),
};

UENUM(BlueprintType)
enum class EAICombatState : uint8
{
	EMeleeCombat = 0 UMETA(DisplayName = "Melee Attacks"),
	EChaseTarget = 1 UMETA(DisplayName = "Chase Target"),
	ERangedCombat = 2 UMETA(DisplayName = "Ranged Attacks"),
	EStudyTarget = 3 UMETA(DisplayName = "Studytarget"),
	EFlee = 4 UMETA(DisplayName = "Flee Away"),
};

UENUM(BlueprintType)
enum class EBattleState : uint8
{
	EExploration UMETA(DisplayName = "Exploration"),
	EBattle UMETA(DisplayName = "Battle"),
};

USTRUCT(BlueprintType)
struct FAIAgentsInfo
{
	GENERATED_BODY()

public:
	FAIAgentsInfo()
	{
		AICharacter = nullptr;
		charLevel = 1;
		characterClass = AACFCharacter::StaticClass();
	};

	//   FAIAgentsInfo(class AACFCharacter* inChar, class AACFAIController* inContr);

	FAIAgentsInfo(class AACFCharacter* inCharr);

	FORCEINLINE bool operator==(const FAIAgentsInfo& Other) const
	{
		return this->AICharacter == Other.AICharacter;
	}

	FORCEINLINE bool operator!=(const FAIAgentsInfo& Other) const
	{
		return this->AICharacter != Other.AICharacter;
	}

	FORCEINLINE bool operator==(const AACFCharacter* Other) const
	{
		return this->AICharacter == Other;
	}

	FORCEINLINE bool operator!=(const AACFCharacter* Other) const
	{
		return this->AICharacter != Other;
	}

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
	TObjectPtr<class AACFCharacter> AICharacter;

	UPROPERTY(SaveGame)
	TSubclassOf<AACFCharacter> characterClass;

	UPROPERTY(SaveGame)
	FName Guid;

	UPROPERTY(SaveGame)
	int32 charLevel;

	UPROPERTY(SaveGame)
	TSoftObjectPtr<UACFCharacterDataAsset> AIConfig;

	UPROPERTY(SaveGame)
	TSoftClassPtr<AACFCharacter> AIClassBP;

	UPROPERTY(SaveGame)
	int32 AILevel = 1;

	UPROPERTY(SaveGame)
	FTransform SpawnTransform;

	UPROPERTY(SaveGame)
	TObjectPtr<AACFSplinePath> PatrolPath;

	UPROPERTY(SaveGame)
	bool bHasSpawnInfo = false;

	TObjectPtr<class AACFAIController> GetController() const;
};

USTRUCT(BlueprintType)
struct FCommandChances : public FTableRowBase
{
	GENERATED_BODY()

public:
	FCommandChances()
	{
		Condition = nullptr;
	}

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
	FGameplayTag CommandTag;

	UPROPERTY(EditAnywhere, Instanced, BlueprintReadOnly, Category = ACF)
	class UACFActionCondition* Condition;
};

USTRUCT(BlueprintType)
struct FAICombatStateConfig
{
	GENERATED_BODY()

public:
	FAICombatStateConfig()
		: Conditions()
	{
		CombatState = EAICombatState::EMeleeCombat;
	};

	FAICombatStateConfig(const EAICombatState inCombatState, float inChance, const ELocomotionState& inState)
		: Conditions()
	{
		TriggerChancePercentage = inChance;
		LocomotionState = inState;

		CombatState = inCombatState;
	}

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	EAICombatState CombatState;

	UPROPERTY(EditAnywhere, Instanced, BlueprintReadOnly, Category = ACF)
	TArray<class UACFActionCondition*> Conditions;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	float TriggerChancePercentage = 75.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	ELocomotionState LocomotionState = ELocomotionState::EWalk;

	UACFDistanceActionCondition* GetDistanceBasedCondition() const
	{
		for (const auto& condition : Conditions)
		{
			UACFDistanceActionCondition* distanceCond = Cast<UACFDistanceActionCondition>(condition);
			if (distanceCond)
			{
				return distanceCond;
			}
		}
		return nullptr;
	}

	FORCEINLINE bool operator==(const EAICombatState& Other) const
	{
		return this->CombatState == Other;
	}

	FORCEINLINE bool operator!=(const EAICombatState& Other) const
	{
		return this->CombatState != Other;
	}

	FORCEINLINE bool operator==(const FAICombatStateConfig& Other) const
	{
		return this->CombatState == Other.CombatState;
	}

	FORCEINLINE bool operator!=(const FAICombatStateConfig& Other) const
	{
		return this->CombatState != Other.CombatState;
	}
};

USTRUCT(BlueprintType)
struct FConditions : public FActionChances
{
	GENERATED_BODY()

public:
	FConditions()
	{
		Condition = nullptr;
	}

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Instanced, Category = ACF)
	class UACFActionCondition* Condition;
};

USTRUCT(BlueprintType)
struct FBaseUnit {
	GENERATED_BODY()

public:
	FBaseUnit() {
		AIConfig = nullptr;
		AILevel = 1;
	};

	FBaseUnit(const TSubclassOf<AACFCharacter>& inClass)
	{
		AIClassBP = TSoftClassPtr<AACFCharacter>(inClass.Get());
		AIConfig = nullptr;
		AILevel = 1;
	}

	FBaseUnit(const TSoftClassPtr<AACFCharacter>& inClass)
	{
		AIClassBP = inClass;
		AIConfig = nullptr;
		AILevel = 1;
	}

	UPROPERTY(EditAnywhere, SaveGame, BlueprintReadWrite, Category = ACF)
	TSoftObjectPtr<UACFCharacterDataAsset> AIConfig;

	UPROPERTY(EditAnywhere, SaveGame, BlueprintReadWrite, Category = ACF)
	TSoftClassPtr<AACFCharacter> AIClassBP;

	UPROPERTY(EditAnywhere, SaveGame, BlueprintReadWrite, Category = ACF)
	int32 AILevel;

	FORCEINLINE bool operator==(const FBaseUnit& Other) const
	{
		return this->AIClassBP == Other.AIClassBP
			&& this->AIConfig == Other.AIConfig
			&& this->AILevel == Other.AILevel;
	}

	FORCEINLINE bool operator!=(const FBaseUnit& Other) const
	{
		return !(*this == Other);
	}

	FORCEINLINE bool operator==(const TSoftClassPtr<AACFCharacter>& Other) const
	{
		return this->AIClassBP == Other;
	}

	FORCEINLINE bool operator!=(const TSoftClassPtr<AACFCharacter>& Other) const
	{
		return this->AIClassBP != Other;
	}

	FORCEINLINE bool operator==(const TSubclassOf<AACFCharacter>& Other) const
	{
		return this->AIClassBP == TSoftClassPtr<AACFCharacter>(Other.Get());
	}

	FORCEINLINE bool operator!=(const TSubclassOf<AACFCharacter>& Other) const
	{
		return !(*this == Other);
	}
};

USTRUCT(BlueprintType)
struct FAISpawnInfo : public FBaseUnit
{
	GENERATED_BODY()

	FAISpawnInfo()
	{
		AIClassBP = AACFCharacter::StaticClass();
		SpawnTransform = FTransform();
	};

	FAISpawnInfo(const TSubclassOf<class AACFCharacter> classToSpawn)
	{
		AIClassBP = classToSpawn;
		SpawnTransform = FTransform();
	}

	FAISpawnInfo(const TSubclassOf<class AACFCharacter> classToSpawn, const FTransform& relativePos)
	{
		AIClassBP = classToSpawn;
		SpawnTransform = relativePos;
	}

	FAISpawnInfo(const FBaseUnit& baseUnit)
	{
		AIClassBP = baseUnit.AIClassBP;
		AIConfig = baseUnit.AIConfig;
		AILevel = baseUnit.AILevel;
		SpawnTransform = FTransform();
	}

	UPROPERTY(EditAnywhere, SaveGame, meta = (MakeEditWidget), BlueprintReadWrite, Category = ACF)
	FTransform SpawnTransform;

	UPROPERTY(EditAnywhere, SaveGame, BlueprintReadWrite, Category = ACF)
	TObjectPtr<AACFSplinePath> PatrolPath;

	FORCEINLINE bool operator==(const FAISpawnInfo& Other) const
	{
		return static_cast<const FBaseUnit&>(*this) == static_cast<const FBaseUnit&>(Other);
	}

	FORCEINLINE bool operator!=(const FAISpawnInfo& Other) const
	{
		return !(*this == Other);
	}

	FORCEINLINE bool operator==(const FBaseUnit& Other) const
	{
		return static_cast<const FBaseUnit&>(*this) == Other;
	}

	FORCEINLINE bool operator!=(const FBaseUnit& Other) const
	{
		return !(*this == Other);
	}

	FORCEINLINE bool operator==(const TSubclassOf<AACFCharacter>& Other) const
	{
		return static_cast<const FBaseUnit&>(*this) == Other;
	}

	FORCEINLINE bool operator!=(const TSubclassOf<AACFCharacter>& Other) const
	{
		return !(*this == Other);
	}
};

USTRUCT(BlueprintType)
struct FWaveConfig
{
	GENERATED_BODY()

public:
	FWaveConfig()
	{
		GroupSpawner = nullptr;
		secondsDelayToNextWave = 1.f;
	}

	/*The spawner to be used for this wave */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
	TSoftObjectPtr<class AACFAIGroupSpawner> GroupSpawner;

	/*The Agents To Be Used For This Wave. Overrides default spawner configuration*/
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
	TArray<FAISpawnInfo> WaveAgentsOverride;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
	float secondsDelayToNextWave;

	void AddAIToSpawn(const TSubclassOf<AACFCharacter>& charClass, int32 totalNumber = 1)
	{
		for (int32 index = 0; index < totalNumber; index++)
		{
			WaveAgentsOverride.Add(FAISpawnInfo(charClass));
		}
	}

	void RemoveAIToSpawn(const TSubclassOf<AACFCharacter>& charClass, int32 totalNumber = 1)
	{
		for (int32 index = 0; index < totalNumber; index++)
		{
			if (WaveAgentsOverride.Contains(charClass))
			{
				WaveAgentsOverride.Remove(charClass);
			}
		}
	}
};

USTRUCT(BlueprintType)
struct FACFAITicket
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = ACF)
	AActor* Target;

	UPROPERTY(BlueprintReadOnly, Category = ACF)
	AController* AIController;

	UPROPERTY(BlueprintReadOnly, Category = ACF)
	float TimeRemaining;

	FACFAITicket()
		: Target(nullptr)
		, AIController(nullptr)
		, TimeRemaining(0.f)
	{
	}

	FACFAITicket(AActor* InTarget, AController* InController, float InTime)
		: Target(InTarget)
		, AIController(InController)
		, TimeRemaining(InTime)
	{
	}

	FORCEINLINE bool operator==(const AController* OtherController) const
	{
		return AIController == OtherController;
	}

	FORCEINLINE bool operator!=(const AController* OtherController) const
	{
		return AIController != OtherController;
	}
};

// LEGACY, now we only use tags
UENUM(BlueprintType)
enum class EAIState : uint8
{
	EPatrol = 0 UMETA(DisplayName = "Patrol"),
	EBattle = 1 UMETA(DisplayName = "Combat"),
	EFollowLeader = 2 UMETA(DisplayName = "Follow Lead Actor"),
	EReturnHome = 3 UMETA(DisplayName = "Return Home"),
	EWait = 4 UMETA(DisplayName = "Wait"),
};

namespace ACF
{
	const FName AIWait = TEXT("AIState.Wait");
	const FName AIPatrol = TEXT("AIState.Patrol");
	const FName AICombat = TEXT("AIState.Combat");
	const FName AIReturnHome = TEXT("AIState.ReturnHome");
	const FName AIFollowLead = TEXT("AIState.FollowLead");
	const FName AIRoutine = TEXT("AIState.Routine");
}

/**
* AI Routine
*/

USTRUCT(BlueprintType)
struct FRoutineTime
{
	GENERATED_BODY()

	/** 0..23 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|RoutineTime",
		meta = (ClampMin = "0", ClampMax = "23", UIMin = "0", UIMax = "23"))
	uint8 Hour = 9;

	/** 0..59 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|RoutineTime",
		meta = (ClampMin = "0", ClampMax = "59", UIMin = "0", UIMax = "59"))
	uint8 Minute = 0;

	/** Returns minutes since midnight [0..1439] */
	int32 ToMinutesSinceMidnight() const { return static_cast<int32>(Hour) * 60 + static_cast<int32>(Minute); }

	/** Friendly "HH:MM" */
	FString ToStringHHMM() const { return FString::Printf(TEXT("%02d:%02d"), Hour, Minute); }

	/** Build from minutes [0..1439] */
	static FRoutineTime FromMinutes(int32 Minutes)
	{
		Minutes = FMath::Clamp(Minutes, 0, 1439);
		FRoutineTime Result;
		Result.Hour = static_cast<uint8>(Minutes / 60);
		Result.Minute = static_cast<uint8>(Minutes % 60);
		return Result;
	}
};

USTRUCT(BlueprintType)
struct FAIRoutineTask
{
	GENERATED_BODY()

public:

	FAIRoutineTask()
	{
		EntryGuid = FGuid::NewGuid();
	}

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Routine")
	FRoutineTime TaskTime;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Instanced, Category = "ACF|Routine")
	UACFTask* RoutineTask = nullptr;

	/** Stable unique id for this entry (used instead of array index). */
	UPROPERTY(BlueprintReadOnly, Meta = (IgnoreForMemberInitializationTest), Category = "ACF|Routine")
	FGuid EntryGuid;
};

UCLASS()
class AIFRAMEWORK_API UACFAITypes : public UObject
{
	GENERATED_BODY()
};
