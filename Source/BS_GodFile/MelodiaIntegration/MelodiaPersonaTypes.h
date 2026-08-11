#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MelodiaPersonaTypes.generated.h"

UENUM(BlueprintType)
enum class EMelodiaQuestState : uint8
{
	Locked,
	Available,
	Active,
	Completed
};

UENUM(BlueprintType)
enum class EMelodiaMinimapMarkerType : uint8
{
	Objective,
	NPC,
	Encounter,
	Exit,
	SavePoint
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaAbilityDefinition
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName AbilityId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(MultiLine=true))
	FText Description;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName StockSkillAssetId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName Element;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	int32 MPCost = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	int32 UnlockLevel = 1;
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaEquipmentDefinition
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName EquipmentId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName StockItemAssetId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName Slot;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	int32 AttackBonus = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	int32 DefenseBonus = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	int32 MagicBonus = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	int32 SpeedBonus = 0;
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaQuestDefinition
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName QuestId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName GiverNPCId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(MultiLine=true))
	FText Objective;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName PrerequisiteQuestId;

	/** Optional Persona-lite stat gate. Empty means no social-stat requirement. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName RequiredSocialStatId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="0"))
	int32 RequiredSocialStatValue = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName CompletionFlagId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName RewardId;
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaMinimapMarkerDefinition
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName MarkerId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName ActorTag;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FText Label;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	EMelodiaMinimapMarkerType Type = EMelodiaMinimapMarkerType::Objective;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName RequiredQuestId;
};

UCLASS(BlueprintType)
class BS_GODFILE_API UMelodiaPersonaContent : public UDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Persona|Combat")
	TArray<FMelodiaAbilityDefinition> Abilities;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Persona|Equipment")
	TArray<FMelodiaEquipmentDefinition> Equipment;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Persona|Quests")
	TArray<FMelodiaQuestDefinition> Quests;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Persona|Minimap")
	TArray<FMelodiaMinimapMarkerDefinition> MinimapMarkers;

	/**
	 * Allowlisted reward id -> EquipmentId that granting it should equip.
	 *
	 * Explicit rather than derived from a name convention: reward ids and
	 * equipment ids are authored independently (melodia_reward_tuning_fork vs
	 * melodia_tuning_fork), and a string transform would silently mis-resolve
	 * the moment either side is renamed. A reward with no entry here is a
	 * narrative-only reward -- it is still consumed exactly once, and
	 * UMelodiaPersonaSubsystem logs that nothing was equipped.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Persona|Equipment")
	TMap<FName, FName> RewardEquipment;
};
