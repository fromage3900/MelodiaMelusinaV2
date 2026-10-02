// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ACFGroupAIComponent.h"
#include "CoreMinimal.h"
#include "Game/ACFDamageType.h"

#include "ACFCompanionGroupAIComponent.generated.h"

/**
 * Companion Group AI Component responsible for managing a group of companion AI members.
 * Handles experience distribution, distance-based despawn logic, and update timing.
 */
UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent))
class AIFRAMEWORK_API UACFCompanionGroupAIComponent : public UACFGroupAIComponent {
	GENERATED_BODY()

public:
	UACFCompanionGroupAIComponent() {};

	/**
   * Adds experience points to all companions in the group.
   * @param Exp - Amount of experience to add to each companion.
   */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void AddExpToTheGroup(int32 Exp);

	/**
	* Enables or disables automatic despawn when companions are too far from the group leader.
	* @param bDespawn - If true, companions will despawn when exceeding MaxDistanceFromLead.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetDespawnIfTooDistanceFromLead(bool bDespawn);

	/**
	  * Checks whether companions should despawn when too far from the leader.
	  * @return True if despawn on distance is enabled.
	  */
	UFUNCTION(BlueprintPure, Category = ACF)
	bool GetDespawnIfTooDistanceFromLead() const
	{
		return bDespawnIfTooDistanceFromLead;
	}


	/**
	  * Returns the maximum allowed distance from the leader before despawn occurs.
	  * @return Maximum distance from the leader.
	  */
	UFUNCTION(BlueprintPure, Category = ACF)
	float GetMaxDistanceFromLead() const { return MaxDistanceFromLead; }

	/**
	 * Sets the maximum allowed distance from the leader before despawn occurs.
	 * @param val - New maximum distance from the leader.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetMaxDistanceFromLead(float val) { MaxDistanceFromLead = val; }

	/**
	* Returns the update interval used for distance checks and AI updates.
	* @return Time interval between updates.
	*/
	UFUNCTION(BlueprintPure, Category = ACF)
	float GetUpdateTime() const { return UpdateTime; }

	/**
	 * Sets the update interval used for distance checks and AI updates.
	 * @param val - New update interval in seconds.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetUpdateTime(float val) { UpdateTime = val; }

protected:
	/** Initializes component references and dependencies. */
	virtual void SetReferences() override;

	/** Whether companions should despawn when exceeding the maximum distance from the leader. */
	UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category = "ACF ")
	bool bDespawnIfTooDistanceFromLead = false;

	/** Maximum distance from the leader before despawn occurs. Only editable if despawn is enabled. */
	UPROPERTY(BlueprintReadWrite, meta = (EditCondition = "bDespawnIfTooDistanceFromLead"), EditDefaultsOnly, Category = "ACF ")
	float MaxDistanceFromLead = 3000.f;

	/** Time interval used to update distance checks and AI logic. Only editable if despawn is enabled. */
	UPROPERTY(BlueprintReadWrite, meta = (EditCondition = "bDespawnIfTooDistanceFromLead "), EditDefaultsOnly, Category = "ACF ")
	float UpdateTime = 1.f;

	virtual void BeginPlay() override;

	void StartUpdateCentroid();

	void StopUpdateCentroid();

private:
	UPROPERTY()
	class AController* contr;

	UFUNCTION()
	void HandleLeadGetHit(const FACFDamageEvent& damage);

	UFUNCTION()
	void HandleLeadHits(const FACFDamageEvent& damage);

	UFUNCTION()
	void HandlePossessedCharacterChanged(const class AACFCharacter* _char);

	UFUNCTION()
	void UpdateCentroid();

	FTimerHandle UpdateTimer;

	bool bUpdating;
};
