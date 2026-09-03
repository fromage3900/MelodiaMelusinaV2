// NPC Character Definition for Melodia ΓÇö extends enemy system with character data
// Includes skeletal mesh, materials, animation blueprint, and interaction config

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MelodiaEnemyDefinition.h"
#include "MelodiaNPCDefinition.generated.h"

UENUM(BlueprintType)
enum class ENPCBehaviorType : uint8
{
	Stationary UMETA(DisplayName = "Stationary"),
	Patrol UMETA(DisplayName = "Patrol"),
	Wander UMETA(DisplayName = "Wander"),
	Schedule UMETA(DisplayName = "Schedule"),
	Event UMETA(DisplayName = "Event")
};

USTRUCT(BlueprintType)
struct FMelodiaNPCOutfitPiece
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Outfit")
	FName SlotName = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Outfit")
	FName PieceId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Outfit")
	TSoftObjectPtr<USkeletalMesh> SkeletalMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Outfit")
	TSoftObjectPtr<UMaterialInterface> MaterialOverride;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Outfit")
	bool bRequired = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Outfit")
	FName CompatibleArchetype = NAME_None;
};

USTRUCT(BlueprintType)
struct FMelodiaNPCInteractionConfig
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Interaction")
	FName InteractionType = NAME_None; // "Dialogue", "Shop", "Battle", "Photo", "Quest"

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Interaction")
	FName DialogueTree = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Interaction")
	TArray<FName> ShopInventory;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Interaction")
	FName BattleEnemyId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Interaction")
	FName Difficulty = FName(TEXT("Normal"));

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Interaction")
	TArray<FName> BattleRewards;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Interaction")
	FName PhotoPoseSet = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Interaction")
	FName ShopType = NAME_None; // "healing_items", "cosmetics"

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Interaction")
	bool bQuestGiver = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Interaction")
	TArray<FName> Tips;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Interaction")
	bool bTimeSensitive = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Interaction")
	FName QuestChain = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Interaction")
	int32 QuestStep = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Interaction")
	FName PhotoReward = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Interaction")
	FName UnlockRequirement = NAME_None;
};

USTRUCT(BlueprintType)
struct FMelodiaNPCScheduleEntry
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Schedule")
	FString TimeOfDay = "06:00"; // HH:MM 24-hour

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Schedule")
	FVector Location = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Schedule")
	FRotator Rotation = FRotator::ZeroRotator;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Schedule")
	FName AnimationState = NAME_None;
};

USTRUCT(BlueprintType)
struct FMelodiaNPCAffinityReward
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Affinity")
	int32 RequiredAffinityLevel = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Affinity")
	FName RewardId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Affinity")
	FText RewardDescription;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Affinity")
	FName RewardType = NAME_None; // "OutfitVariant", "Pose", "Dialogue", "Item"
};

USTRUCT(BlueprintType)
struct FMelodiaNPCDefinition
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC")
	FName NPCId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC")
	FText DisplayName = FText::FromString(TEXT("NPC"));

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC")
	FName Archetype = NAME_None; // "SakuraDreamer", "CosmicWeaver", "MirageDancer"

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC")
	FText Description;

	// Visual
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Visual")
	TSoftObjectPtr<USkeletalMesh> BaseSkeletalMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Visual")
	TSoftClassPtr<UAnimInstance> AnimationBlueprint;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Visual")
	TArray<FMelodiaNPCOutfitPiece> OutfitPieces;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Visual")
	TSoftObjectPtr<UMaterialParameterCollection> NPCMaterialParams;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Visual")
	FName OutfitVariant = NAME_None;

	// Animation Personality
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Animation")
	FName IdleSet = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Animation")
	FName WalkStyle = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Animation")
	FName RunStyle = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Animation")
	TArray<FName> InteractionGestures;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Animation")
	TArray<FName> FacialExpressions;

	// AI Behavior
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|AI")
	ENPCBehaviorType BehaviorType = ENPCBehaviorType::Stationary;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|AI")
	FName PatrolPath = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|AI")
	float WanderRadius = 500.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|AI")
	TArray<FMelodiaNPCScheduleEntry> Schedule;

	// Interaction
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Interaction")
	FMelodiaNPCInteractionConfig InteractionConfig;

	// Battle (if applicable)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Battle")
	FName BattleEnemyId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Battle")
	FName BattleDifficulty = FName(TEXT("Normal"));

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Battle")
	TArray<FName> BattleRewards;

	// Progression
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Progression")
	TArray<FMelodiaNPCAffinityReward> AffinityRewards;

	// Spawning
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Spawning")
	TArray<FName> SpawnZones;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Spawning")
	FString SpawnLevelPath;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Spawning")
	float SpawnWeight = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Spawning")
	int32 MinPlayerLevel = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC|Spawning")
	int32 MaxPlayerLevel = 50;
};

/**
 * DataAsset containing catalog of NPC definitions for the world.
 * Extends the enemy system with character-specific data for exploration/interaction.
 */
UCLASS(BlueprintType)
class MELODIACORE_API UMelodiaNPCDataAsset : public UDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|NPC")
	TArray<FMelodiaNPCDefinition> NPCs;

	UFUNCTION(BlueprintPure, Category = "Melodia|NPC")
	bool FindNPCById(FName NPCId, FMelodiaNPCDefinition& OutNPC) const;

	UFUNCTION(BlueprintPure, Category = "Melodia|NPC")
	FMelodiaNPCDefinition GetNPCByIndex(int32 Index) const;

	UFUNCTION(BlueprintPure, Category = "Melodia|NPC")
	TArray<FMelodiaNPCDefinition> GetNPCsByArchetype(FName Archetype) const;

	UFUNCTION(BlueprintPure, Category = "Melodia|NPC")
	TArray<FMelodiaNPCDefinition> GetNPCsByZone(FName ZoneName) const;

	/** Built-in demo NPCs matching the 10 NPC pilot. */
	UFUNCTION(BlueprintPure, Category = "Melodia|NPC")
	static TArray<FMelodiaNPCDefinition> GetDemoNPCs();
};
