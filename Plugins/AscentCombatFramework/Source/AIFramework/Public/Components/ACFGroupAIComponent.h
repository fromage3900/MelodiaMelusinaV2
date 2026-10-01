// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFAITypes.h"
#include "Actors/ACFCharacter.h"
#include "CoreMinimal.h"
#include <Components/PrimitiveComponent.h>
#include <Components/SceneComponent.h>
#include <Components/SplineComponent.h>
#include <GameplayTagContainer.h>
#include "ACFBaseGroupComponent.h"
#include "Components/ActorComponent.h"

#include "ACFGroupAIComponent.generated.h"

struct FAISpawnInfo;
class FPrimitiveSceneProxy;
struct FStreamableHandle;
class AACFCharacter;



/**
 * * Component responsible for managing AI groups in ACF.
 */
UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent))
class AIFRAMEWORK_API UACFGroupAIComponent : public UACFBaseGroupComponent {
	GENERATED_BODY()

public:
	/**
	 * * Default constructor.
	 */
	UACFGroupAIComponent();

protected:
	/**
	 * * Called when the game starts.
	 */
	virtual void BeginPlay() override;

	/**
	 * * Sets internal references for AI management.
	 */
	virtual void SetReferences();

	virtual void OnUnregister() override;
	virtual void OnRegister() override;

	/**
	 * * Whether the AI group is currently engaged in combat.
	 */
	UPROPERTY(BlueprintReadOnly, Replicated, Category = ACF)
	bool bInBattle;

	/**
	* * The maximum number of simultaneous AI agents allowed in the group.
	*/
	UPROPERTY(EditAnywhere, Savegame, BlueprintReadOnly, Category = "ACF|Spawn")
	int32 MaxSimultaneousAgents = 20;
protected:


	/**
	 * * The group name used for UI representation.
	 */
	UPROPERTY(EditAnywhere, Category = "ACF|AI Config")
	FName GroupName = "Default Group Name";

	/**
	 * * Whether to override individual agent perception settings.
	 */
	UPROPERTY(EditAnywhere, Category = "ACF|AI Config")
	bool bOverrideAgentPerception = true;

	/**
	 * * Whether to alert other team members upon engagement.
	 */
	UPROPERTY(EditAnywhere, Category = "ACF|AI Config")
	bool bAlertOtherTeamMembers = true;

	/**
	 * * Whether to override the individual agent team settings.
	 */
	UPROPERTY(EditAnywhere, Category = "ACF|AI Config")
	bool bOverrideAgentTeam = true;


	/**
	 * * The default AI state for the group when spawned.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|AI Config")
	FGameplayTag DefaultAiState;



	/**
	 * * Default offset for AI spawning locations.
	 */
	UPROPERTY(EditAnywhere, Category = "ACF|Spawn")
	FVector2D DefaultSpawnOffset;

	/**
	 * * List of AI characters to spawn in the group.
	 */
	UPROPERTY(EditAnywhere, SaveGame, meta = (TitleProperty = "AIClassBP"), BlueprintReadWrite, Category = "ACF|Spawn")
	TArray<FAISpawnInfo> AIToSpawn;

	/**
	 * * The leader of the AI group.
	 */
	UPROPERTY(Replicated, BlueprintReadOnly, Category = ACF)
	TObjectPtr<class AActor> groupLead;

	virtual void OnComponentLoaded_Implementation() override;

	virtual void OnChildDeath(const AACFCharacter* character) override;

public:
	/**
	* * Sets the battle state of the group.
	* @param inBattle True to engage the group in battle, false otherwise.
	* @param newTarget The target to engage if in battle.
	*/
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetInBattle(bool inBattle, AActor* newTarget);

	/**
	 * * Checks if the group is currently engaged in battle.
	 * @return True if in battle, false otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE bool IsInBattle() const { return bInBattle; }

	/**
	 * * Retrieves the list of AI to spawn.
	 * @return An array containing the AI spawn information.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	TArray<FAISpawnInfo> GetAIToSpawn() const { return AIToSpawn; }

	/**
	 * * Retrieves the nearest AI agent to a given location.
	 * @param location The target location.
	 * @return Pointer to the closest AI agent.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	class AACFCharacter* GetAgentNearestTo(const FVector& location) const;


	/**
	 * * Removes an agent from the group.
	 * @param character Pointer to the agent to be removed.
	 * @return True if successfully removed, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	bool RemoveAgentFromGroup(AACFCharacter* character);

	/**
	 * * Retrieves all agents in the group.
	 * @param outAgents Output parameter containing the list of agents.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void GetGroupAgents(TArray<FAIAgentsInfo>& outAgents) const { outAgents = AICharactersInfo; }

	/**
	 * * Adds an AI to the spawn list from a class reference.
	 * @param charClass The class of the AI to be added.
	 * @return True if successfully added, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	bool AddAIToSpawnFromClass(const TSubclassOf<AACFCharacter>& charClass);

	/**
	 * * Adds an AI to the spawn list.
	 * @param spawnInfo The AI spawn information.
	 * @return True if successfully added, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	bool AddAIToSpawn(const FAISpawnInfo& spawnInfo);

	/**
	 * * Removes an AI from the spawn list by class reference.
	 * @param charClass The class of the AI to be removed.
	 * @return True if successfully removed, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	bool RemoveAIToSpawn(const TSubclassOf<AACFCharacter>& charClass);

	/**
	 * * Removes an AI from the spawn list by full unit data.
	 * @param unit The unit data to remove.
	 * @return True if successfully removed, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	bool RemoveAIToSpawnUnit(const FBaseUnit& unit);

	/**
	 * * Replaces the list of AI to spawn with a new list.
	 * @param newAIs The new list of AI spawn information.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void ReplaceAIToSpawn(const TArray<FAISpawnInfo>& newAIs);


	/**
	 * * Retrieves the enemy group associated with this group.
	 * @return A pointer to the enemy group component.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	class UACFGroupAIComponent* GetEnemyGroup() const { return enemyGroup; }

	/**
	 * * Retrieves the leader of the group.
	 * @return A pointer to the group leader actor.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	class AActor* GetGroupLead() const { return groupLead; }

	/**
	 * * Calculates and retrieves the centroid position of the group.
	 * @return The centroid location of the group.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FVector GetGroupCentroid() const;

	/**
	 * * Requests a new target for an AI agent.
	 * @param requestSender The AI controller requesting a new target.
	 * @return A pointer to the new target character.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	class AACFCharacter* RequestNewTarget(const AACFAIController* requestSender);

	/**
	 * * Sends a command to all companions in the group.
	 * @param command The gameplay tag representing the command to be executed.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	void SendCommandToCompanions(FGameplayTag command);

	/**
	 * * Despawns the AI group.
	 * @param bUpdateAIToSpawn Whether to update the AI spawn list.
	 * @param actionToTriggerOnDyingAgent Optional action tag for dying agents.
	 * @param lifespawn Time before despawn is completed.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	void DespawnGroup(const bool bUpdateAIToSpawn = true, FGameplayTag actionToTriggerOnDyingAgent = FGameplayTag(), float lifespawn = .2f);

	/**
	 * * Checks if other team members should be alerted.
	 * @return True if alerting is enabled, false otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	bool GetAlertOtherTeamMembers() const { return bAlertOtherTeamMembers; }

	/**
	 * * Sets whether other team members should be alerted.
	 * @param val True to enable alerting, false to disable.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetAlertOtherTeamMembers(bool val) { bAlertOtherTeamMembers = val; }


	/**
	 * * Gets the total number of AI configured to spawn.
	 * @return The total AI count to be spawned.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	int32 GetTotalAIToSpawnCount() const;


	/**
	 * * Adds an existing character to the AI group.
	 * @param character Pointer to the character to be added.
	 * @return True if successfully added, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	bool AddExistingCharacterToGroup(AACFCharacter* character);

	/**
	 * * Reinitializes a given AI agent.
	 * @param character Pointer to the AI agent to be reinitialized.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void ReInitAgent(AACFCharacter* character);


	/**
	 * * Enables or disables multiple spawns for this group.
	 * @param bEnabled True to allow multiple spawns, false to disable.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetCanSpawnMultitpleTimes(bool bEnabled) { bCanSpawnMultitpleTimes = bEnabled; }

	/**
	 * * Retrieves the maximum number of simultaneous agents.
	 * @return The maximum number of agents allowed.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	int32 GetMaxSimultaneousAgents() const { return MaxSimultaneousAgents; }

	/**
	 * * Sets the maximum number of simultaneous agents.
	 * @param val The new maximum number of agents.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetMaxSimultaneousAgents(int32 val) { MaxSimultaneousAgents = val; }

	/**
	 * * Retrieves the group's name.
	 * @return The name of the group.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FName GetGroupName() const { return GroupName; }

	/**
	 * * Checks if the group is currently spawned.
	 * @return True if the group is spawned, false otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	bool IsGroupSpawned() const { return bAlreadySpawned; }

	/**
	 * * Sets the group's name.
	 * @param val The new name for the group.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetGroupName(FName val) { GroupName = val; }

	/**
 * * Checks if multiple spawns are allowed for this group.
 * @return True if multiple spawns are enabled, false otherwise.
 */
	UFUNCTION(BlueprintPure, Category = ACF)
	bool CanSpawnMultitpleTimes() const { return bCanSpawnMultitpleTimes; }


	/**
	 * * Initializes AI agents within the group.
	 */
	virtual void InitAgents() override;


	//RPC VERSION FOR MULTIPLAYER!

	UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
	void ServerAddCharacterToGroup(AACFCharacter* character);

	UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
	void ServerRemoveCharacterFromGroup(AACFCharacter* character);

	UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
	void ServerAddAIToSpawn(const FAISpawnInfo& spawnInfo);

	virtual void Internal_SpawnGroup() override;

	//END RPC!
#if WITH_EDITORONLY_DATA
	/** Editor-only capsules for visualizing and editing spawn points */
	UPROPERTY(Transient)
	TArray<TObjectPtr<UCapsuleComponent>> SpawnPreviewCapsules;
#endif

#if WITH_EDITOR
	virtual void PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent) override;
	virtual void PostEditComponentMove(bool bFinished) override;

	/** Rebuilds preview capsules from AIToSpawn array */
	void RebuildSpawnPreviewCapsules();

	/** Updates AIToSpawn transforms from capsule positions */
	void SyncSpawnInfoFromCapsules();

#endif


protected: 

	virtual uint8 AddAgentToGroup(const FAISpawnInfo& spawnInfo);
	virtual void InitAgent(FAIAgentsInfo& agent, int32 childIndex) override;

	FAISpawnInfo BuildSpawnInfoFromAgent(const FAIAgentsInfo& agent) const;
	void StoreSpawnInfoForAgent(FAIAgentsInfo& agent, const FAISpawnInfo& spawnInfo) const;
	FAISpawnInfo BuildSpawnInfoFromCharacter(AACFCharacter* character) const;

	void SetEnemyGroup(UACFGroupAIComponent* inEnemyGroup);


	virtual void OnAIAssetsLoaded() override;
private:


	void Internal_SendCommandToAgents(FGameplayTag command);

	UPROPERTY()
	TObjectPtr<class UACFGroupAIComponent> enemyGroup;




};
