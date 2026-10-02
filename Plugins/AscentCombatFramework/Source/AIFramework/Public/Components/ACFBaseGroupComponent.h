// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "ACFAITypes.h"
#include "GameplayTagContainer.h"
#include "Components/SceneComponent.h"
#include "ACFBaseGroupComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAgentDeath, const AACFCharacter*, character);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnAllAgentDeath);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnAgentsSpawned);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnAgentsChanged);

/**
 * * Base Component responsible for managing AI groups in ACF.
 */
UCLASS(ClassGroup = (ACF))
class AIFRAMEWORK_API UACFBaseGroupComponent : public USceneComponent
{
	GENERATED_BODY()

public:
	/**
	 * * Default constructor.
	 */
	UACFBaseGroupComponent();


protected:

	/**
	 * * The combat team the AI group belongs to.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (Categories = "Teams"), Category = "ACF|AI Config")
	FGameplayTag CombatTeam;

	/**
	** Whether the group can spawn multiple times.
	*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Spawn")
	bool bCanSpawnMultitpleTimes = false;

	/**
	* * List of AI agents currently in the group.
	*/
	UPROPERTY(SaveGame, Replicated)
	TArray<FAIAgentsInfo> AICharactersInfo;


	/**
	 * * Called when the component is fully loaded.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
	void OnComponentLoaded();


	/**
	 * * Called when before the component is Saved.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
	void OnComponentSaved();

	/**
	 * * Called when an AI character in the group dies.
	 * @param character Pointer to the deceased AI character.
	*/
	UFUNCTION()
	virtual void OnChildDeath(const AACFCharacter* character);



public:
	/**
	 * * Event triggered when an AI agent in the group dies.
	 */
	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnAgentDeath OnAgentDeath;

	/**
	 * * Event triggered when all AI agents in the group are dead.
	 */
	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnAllAgentDeath OnAllAgentDeath;

	/**
	 * * Event triggered when AI agents are spawned in the group.
	 */
	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnAgentsSpawned OnAgentsSpawned;

	/**
	 * * Event triggered when AI agents are despawned.
	 */
	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnAgentsSpawned OnAgentsDespawned;

	/**
	 * * Event triggered when AI agents change in the group.
	 */
	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnAgentsChanged OnAgentsChanged;



	/**
	 * * Retrieves the combat team of the group.
	 * @return The combat team enum value.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FGameplayTag GetCombatTeam() const;

	/**
	 * * Retrieves the total number of agents in the group.
	 * @return The number of agents in the group.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE int32 GetGroupSize() const { return AICharactersInfo.Num(); }


	/**
	 * * Retrieves an agent by its index in the group.
	 * @param index The index of the agent.
	 * @param outAgent Output parameter containing the agent's information.
	 * @return True if the agent was found, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	bool GetAgentByIndex(int32 index, FAIAgentsInfo& outAgent) const;

	/**
	* * Gets the total number of agents currently spawned.
	* @return The current agent count.
	*/
	UFUNCTION(BlueprintPure, Category = ACF)
	int32 GetTotalAgentsCount() const { return AICharactersInfo.Num(); }


	/**
	 * * Checks if a given character is already part of the group.
	 * @param character Pointer to the character.
	 * @return True if the character is in the group, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	bool IsAlreadyInGroup(const AACFCharacter* character) const { return AICharactersInfo.Contains(character); }

	/**
	 * * Spawns the AI group.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	virtual void SpawnGroup();

	UFUNCTION()
	virtual void OnAIAssetsLoaded();

protected:
	// Handle for managing async loading
	TSharedPtr<FStreamableHandle> StreamableHandle;

	UFUNCTION()
	void HandleAgentDeath(class AACFCharacter* agent);

	UPROPERTY(SaveGame)
	bool bAlreadySpawned = false;

	virtual void Internal_SpawnGroup();
	virtual void InitAgents();
	virtual void InitAgent(FAIAgentsInfo& agent, int32 childIndex);



};
