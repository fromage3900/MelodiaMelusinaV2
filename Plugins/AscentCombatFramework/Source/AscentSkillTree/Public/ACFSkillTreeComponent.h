// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFSkillTypes.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "Graph/ACFSkillTreeGraph.h"

#include "ACFSkillTreeComponent.generated.h"

class UACFSkillTreeGraph;
class UACFBaseSkillNode;
class UACFGASAttributesComponent;
class UACFAbilitySystemComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnActiveSkillsChanged);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnSkillPointsChanged, int32, NewSkillPoints);

USTRUCT(BlueprintType)
struct FSkillLevelData
{
	GENERATED_BODY()

	UPROPERTY(SaveGame)
	FGuid SkillId;

	UPROPERTY(SaveGame)
	int32 CurrentLevel;

	FSkillLevelData() : SkillId(FGuid()), CurrentLevel(0) {}
	FSkillLevelData(const FGuid& InId, int32 InLevel) : SkillId(InId), CurrentLevel(InLevel) {}
};

UENUM(BlueprintType)
enum class ECanUnlockSkillResult : uint8
{
	SkillUnlocked				UMETA(DisplayName = "Skill unlocked"),
	SkillUpgraded				UMETA(DisplayName = "Skill upgraded"),
	InvalidAttributeComponent	UMETA(DisplayName = "Invalid attribute component"),
	InvalidInputParameters		UMETA(DisplayName = "Invalid SkillTree Tag or Skill ID"),
	SkillTreeNotFound			UMETA(DisplayName = "Skill tree not found"),
	SkillNodeNotFound			UMETA(DisplayName = "Skill node not found"),
	AlreadyAtMaxLevel			UMETA(DisplayName = "Skill Already at max Level"),
	InsufficientSkillPoints		UMETA(DisplayName = "Insufficient skill points"),
	InsufficientCharacterLevel	UMETA(DisplayName = "Insufficient character level"),
	ParentNodesNotActive		UMETA(DisplayName = "Precedent skills Not Unlocked")
};


/**
*Component that manages the unlocking and tracking of skills within one or more skill trees.
* Handles applying skill effects to the owning ability system comp.
*/
UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class ASCENTSKILLTREE_API UACFSkillTreeComponent : public UActorComponent {
	GENERATED_BODY()

public:
	UACFSkillTreeComponent();

	/**
	 * Unlocks or upgrades a skill from the given skill tree on the server using the node's unique GUID.
	 * If the skill is new, it applies its effects. If it's an upgrade, it increments its level.
	 *
	 * @param SkillTreeTag The skill tree to use for the lookup.
	 * @param SkillNodeId The unique GUID identifying the skill node to unlock/upgrade.
	 */
	UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
	void UnlockSkillFromTree(const FGameplayTag& SkillTreeTag, const FGuid& SkillNodeId);

	/**
	 * Checks if a skill can be unlocked or upgraded based on requirements (level, skill points, parent nodes, max level).
	 *
	 * @param SkillTreeTag The skill tree to use for the lookup.
	 * @param SkillNodeId The unique GUID identifying the skill node to check.
	 * @return True if the skill can be unlocked or upgraded.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	bool CanUnlockSkill(const FGameplayTag& SkillTreeTag, const FGuid& SkillNodeId, ECanUnlockSkillResult& OutResult);

	/**
	 * Adds the specified amount of skill points to the character.
	 * @param SkillPointsToAdd - Amount of skill points to add.
	 */
	UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
	void AddSkillPoints(int32 SkillPointsToAdd);

	/**
	 * Returns a skill node based on the provided skill tree tag and node GUID.
	 * @param SkillTreeTag - Tag identifying the skill tree.
	 * @param SkillNodeId - GUID identifying the skill node within the tree.
	 * @return The corresponding skill node if found.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	UACFBaseSkillNode* GetSkillByIds(const FGameplayTag& SkillTreeTag, const FGuid& SkillNodeId) const;

	/**
	 * Returns the skill tree graph associated with the provided tag.
	 * @param SkillTreeTag - Tag of the skill tree to retrieve.
	 * @return Pointer to the skill tree graph if found.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	UACFSkillTreeGraph* GetSkillTreeByTag(const FGameplayTag& SkillTreeTag) const;

	/**
	 * Returns all the skill trees.
	 * @return All the skill trees.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	TArray<UACFSkillTreeGraph*> GetSkillTrees() const {
		return SkillTrees;
	}

	/**
	 * Checks whether the specified skill node is currently active (level 1 or higher) using its GUID.
	 * @param SkillNodeId - GUID of the skill node to check.
	 * @return True if the skill is active.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	bool IsSkillActive(const FGuid& SkillNodeId) const;

	/**
	 * Gets the current level of an unlocked skill.
	 * @param SkillNodeId - GUID of the skill node to check.
	 * @return The current level (0 if not unlocked).
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	int32 GetSkillCurrentLevel(const FGuid& SkillNodeId) const;

	/**
	 * Removes an active skill by GUID, deactivating its effects and clearing its ability handle.
	 * This does not refund skill points.
	 *
	 * @param SkillTreeTag The skill tree the skill originally came from (used for internal lookup).
	 * @param SkillNodeId The GUID identifying the skill node to remove from the active list.
	 */
	UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
	void RemoveSkill(const FGameplayTag& SkillTreeTag, const FGuid& SkillNodeId);

	/**
	 * Removes all currently active skills, deactivates all granted abilities and effects,
	 * clears internal tracking, and refunds all spent skill points based on their purchased levels.
	 */
	UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
	void Respec();

	UFUNCTION(BlueprintPure,Category = ACF)
	int32 GetSkillPoints() const { return SkillPoints; }

	void SetSkillPoints(int32 val) { SkillPoints = val; }
protected:
	// Current list of active skills (replicated)
	UPROPERTY(BlueprintReadOnly, ReplicatedUsing = OnRep_ActiveSkills, SaveGame, Category = ACF)
	FSkillSaveContainer ActiveSkills;

	// Map of active skill GUIDs to their current level
	UPROPERTY(BlueprintReadOnly, ReplicatedUsing = OnRep_SkillLevels, SaveGame, Category = ACF)
	TArray<FSkillLevelData> SkillLevels;

	// Current available skill points
	UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, ReplicatedUsing = OnRep_SkillPoints, SaveGame, Category = ACF)
	int32 SkillPoints = 2;

	// Maps skill node GUIDs to their ability and effect handles
	UPROPERTY(BlueprintReadOnly, Category = ACF)
	TMap<FGuid, FAbilityHandlers> SkillHandlers;

	// List of all available skill trees
	UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = ACF)
	TArray<UACFSkillTreeGraph*> SkillTrees;

	// Called when ActiveSkills changes (rep notify or after modification)
	UPROPERTY(BlueprintAssignable, Category = "ACF|Skills")
	FOnActiveSkillsChanged OnActiveSkillsChanged;

	// Called when SkillPoints changes
	UPROPERTY(BlueprintAssignable, Category = "ACF|Skills")
	FOnSkillPointsChanged OnSkillPointsChanged;

	UFUNCTION()
	void OnRep_ActiveSkills()
	{
		BroadcastActiveSkillsChanged();
	}

	UFUNCTION()
	void OnRep_SkillLevels()
	{
		BroadcastActiveSkillsChanged();
	}

	UFUNCTION()
	void OnRep_SkillPoints()
	{
		BroadcastSkillPointsChanged();
	}

	void BroadcastSkillPointsChanged()
	{
		OnSkillPointsChanged.Broadcast(SkillPoints);
	}

	void BroadcastActiveSkillsChanged()
	{
		SynchTrees();
		OnActiveSkillsChanged.Broadcast();
	}

	virtual void BeginPlay() override;

	void SynchTrees();
	bool Internal_RemoveSkill(const FGameplayTag& SkillTreeTag, const FGuid& SkillNodeId);

	TObjectPtr<UACFGASAttributesComponent> AttributeComp;
	TObjectPtr<UACFAbilitySystemComponent> AbilityComp;
};