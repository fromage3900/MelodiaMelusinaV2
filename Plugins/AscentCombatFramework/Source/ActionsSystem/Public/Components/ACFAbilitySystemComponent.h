// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFAbilitySet.h"
#include "ACFActionTypes.h"
#include "ARSStatisticsComponent.h"
#include "ARSTypes.h"
#include "Actions/ACFActionsSet.h"
#include "CoreMinimal.h"
#include <AbilitySystemComponent.h>
#include <Engine/DataTable.h>
#include <GameplayTagContainer.h>

#include "ACFAbilitySystemComponent.generated.h"

class UACFActionAbility;
class UARSStatisticsComponent;
class ACharacter;
class UAnimInstance;
class UACFAbilitySet;
class UACFGameplayAbility;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnActionStarted, FGameplayTag, abilityTag);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnActionEnded, FGameplayTag, abilityTag);

/*
 * Component that extends UAbilitySystemComponent to manage modular action abilities.
 * Handles action triggering, priority logic, ability buffering, and moveset-based ability granting.
 */
UCLASS(ClassGroup = (ACF), DisplayName = "ACF Ability Component", Blueprintable, meta = (BlueprintSpawnableComponent))
class ACTIONSSYSTEM_API UACFAbilitySystemComponent : public UAbilitySystemComponent {
	GENERATED_BODY()

public:
	// Sets default values for this component's properties
	UACFAbilitySystemComponent();

public:
	/*
	 * Tries to trigger the action with the provided tag.
	 * @param ActionState The tag of the action to trigger.
	 * @param Priority Priority level of the action.
	 * @param bCanBeStored If true, the action will be stored if it can't be executed immediately.
	 * @return True if the action was successfully triggered.
	 */
	UFUNCTION(BlueprintCallable, DisplayName = "TriggerActionAbility", Category = ACF)
	bool TriggerAction(UPARAM(DisplayName = "AbilityTag", Meta = (Categories = "Actions,Ability")) FGameplayTag ActionState, EActionPriority Priority = EActionPriority::ELow, bool bCanBeStored = false);

	/*
 * Tries to trigger the action with the provided tag.
 * @param ActionState The tag of the action to trigger.
 * @param Payload The payload data to pass to the ability.
 * @param Priority Priority level of the action.
 * @param bCanBeStored If true, the action will be stored if it can't be executed immediately.
 * @return True if the action was successfully triggered.
 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Actions")
	bool TriggerActionWithPayload(UPARAM(DisplayName = "AbilityTag", Meta = (Categories = "Actions,Ability")) FGameplayTag AbilityTag, const FACFAbilityPayload& Payload, EActionPriority Priority /*= EActionPriority::ELow*/, bool bCanBeStored /*= false*/);

	/*
	 * Triggers a basic ability using its tag.
	 * @param abilityTag The tag of the ability to trigger.
	 * @return True if triggered successfully.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	bool TriggerAbility(UPARAM(DisplayName = "AbilityTag", Meta = (Categories = "Actions,Ability")) FGameplayTag abilityTag);

	/*
	 * Grants an entire ability set, optionally associated with a moveset tag.
	 * @param abilitySet The ability set to grant.
	 * @param movesetTag Optional tag to associate with the granted set.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void GrantAbilitySet(UACFAbilitySet* abilitySet, FGameplayTag movesetTag = FGameplayTag());

	/*
	 * Removes abilities associated with a specific moveset tag.
	 * @param movesetTag The tag used to identify abilities to remove.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void RemoveAbilitySetByTag(const FGameplayTag& movesetTag);

	/*
	 * Removes a specific ability set, optionally scoped by moveset tag.
	 * @param abilitySet The ability set to remove.
	 * @param movesetTag Optional tag to match.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void RemoveAbilitySet(const UACFAbilitySet* abilitySet, FGameplayTag movesetTag = FGameplayTag());

	/** Returns the default ability set used when no moveset is active. */
	UFUNCTION(BlueprintPure, Category = ACF)
	UACFAbilitySet* GetDefaultAbilitySet() const { return DefaultAbilitySet; }

	/** Returns the map of moveset tags to their ability sets. */
	UFUNCTION(BlueprintPure, Category = ACF)
	const TMap<FGameplayTag, UACFAbilitySet*>& GetMovesetAbilities() const { return MovesetAbilities; }

	/*
	 * Grants a single ability from a configuration struct.
	 * @param abilitySet The configuration of the ability.
	 * @param movesetTag Optional tag for context.
	 * @return The handle of the granted ability.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	FGameplayAbilitySpecHandle GrantAbility(const FAbilityConfig& ability, FGameplayTag movesetTag = FGameplayTag());

	/*
	 * Grants an action-type ability from a config.
	 * @param abilitySet The action ability configuration.
	 * @param movesetTag Optional tag for context.
	 * @return The handle of the granted ability.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	FGameplayAbilitySpecHandle GrantACFAbility(const FActionAbilityConfig& abilitySet, FGameplayTag movesetTag = FGameplayTag());

	/*
	 * Sends a gameplay event to all active abilities.
	 * @param gameplayEvent The tag of the event to trigger.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void TriggerGameplayEvent(const FGameplayTag& gameplayEvent);

	//**  GETTERS  **//

	/*
	 * Retrieves the ability object associated with the specified tag.
	 * @param abilityTag The gameplay tag of the ability.
	 * @return The matching UGameplayAbility instance.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	UGameplayAbility* GetAbilityByTag(const FGameplayTag& abilityTag) const;

	/*
	 * Retrieves ability configuration data from a set by tag.
	 * @param abilityTag The gameplay tag of the ability.
	 * @param outAction The output config structure for the found action.
	 * @return True if found.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	bool GetAbilityFromAbilitySet(const FGameplayTagContainer& abilityTagContainer, FActionAbilityConfig& outAction) const;

	bool GetAbilityFromAbilitySet(const FGameplayTag& abilityTag, FActionAbilityConfig& outAction) const;

	/*
	 * Gets the runtime instance of an ability by handle.
	 * @param abilityHandle The handle of the ability.
	 * @return The active UGameplayAbility instance.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	UGameplayAbility* GetAbilityInstance(const FGameplayAbilitySpecHandle& abilityHandle) const;

	/*
	 * Checks whether the current action tag matches a given state.
	 * @param state The state tag to compare.
	 * @return True if matches.
	 */
	UFUNCTION(BlueprintPure, DisplayName = "IsPerforminAbility", Category = ACF)
	FORCEINLINE bool IsInActionState(FGameplayTag state) const { return CurrentAbilityTag == state; }

	/*
	 * Checks if an action is currently being performed.
	 * @return True if performing an action.
	 */
	UFUNCTION(BlueprintPure, DisplayName = "IsPerforminAnyActionAbility", Category = ACF)
	FORCEINLINE bool IsPerformingAction() const { return bIsPerformingAction; }


	/*
	 * Gets the priority of the currently executing action.
	 * @return The priority as an EActionPriority enum.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	EActionPriority GetCurrentActionPriority() const { return (EActionPriority)CurrentPriority; }

	/*
	 * Returns the last activated action instance.
	 * @return Pointer to the last UACFActionAbility.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	UACFGameplayAbility* GetLastActivatedAbility() const { return LastActivatedAbility; }

	/*
	 * Converts an ability tag to its corresponding handle.
	 * @param abilityTag The gameplay tag of the ability.
	 * @return The corresponding ability spec handle.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	FGameplayAbilitySpecHandle FromAbilityTagToHandle(const FGameplayTag& abilityTag) const;

	/*
	 * Returns the ability handle matching the ability and moveset tag.
	 * @param abilityTag The gameplay tag of the ability.
	 * @param abilitySetTag The tag identifying the ability set.
	 * @return The handle to the corresponding ability spec.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	FGameplayAbilitySpecHandle GetAbilityHandle(const FGameplayTag& abilityTag, const FGameplayTag abilitySetTag) const;
	/*
	 * Returns the currently active moveset actions tag.
	 * @return The current moveset tag.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE FGameplayTag GetCurrentMovesetActionsTag() const { return currentMovesetActionsTag; }

	/*
	 * Returns the current action tag being performed.
	 * @return The current action tag.
	 */
	UFUNCTION(BlueprintPure, DisplayName = "GetCurrentAbilityTag", Category = ACF)
	FGameplayTag GetCurrentActionTag() const;

	// END GETTERS

	/*
	 * Updates the current moveset tag and grants appropriate abilities.
	 * @param movesetActionsTag The tag representing the moveset.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	void SetMovesetActions(const FGameplayTag& movesetActionsTag);
	/*
	 * Disables action buffering.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void StopStoringActions() { bCanStoreAction = false; }

	/*
	 * Enables action buffering.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void StartStoringActions() { bCanStoreAction = true; }

	/*
	 * Prevents new actions from being triggered.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void LockActionsTrigger();

	/*
	 * Allows actions to be triggered again.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void UnlockActionsTrigger() { bIsLocked = false; }

	/*
	 * Stores an ability in the buffer to be executed when the current one ends.
	 * Runs locally (no RPC): the combo continuation is re-triggered as a predicted
	 * ability activation carrying the requested combo counter in its payload.
	 * @param Action The tag of the ability to store.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void StoreAbilityInBuffer(const FGameplayTag& Action);

	/*
	 * Returns the stored action tag, if any.
	 * @return The stored action tag.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE FGameplayTag GetStoredAction() const { return StoredAction; }

	/*
	 * Checks if an action is currently stored.
	 * @return True if an action is buffered.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE bool HasStoredActions() const { return StoredAction != FGameplayTag(); }

	/*
	 * Checks whether a given action tag is executable based on internal rules.
	 * @param Action The tag of the action to check.
	 * @return True if executable.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	bool CanExecuteAbility(FGameplayTag Action) const;

	/*
	 * Checks whether a given ability handle is executable.
	 * @param handle The ability handle to check.
	 * @return True if executable.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	bool CanExecuteAbilityByHandle(const FGameplayAbilitySpecHandle& handle) const;

	/*
	 * Releases a sustained action by ending its montage and terminating it.
	 * @param actionTag The tag of the action to release.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void ReleaseSustainedAction(FGameplayTag actionTag);

	/*
	 * Event triggered when an ability starts.
	 */
	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnActionStarted OnAbilityStartedEvent;

	/*
	 * Event triggered when an ability ends.
	 */
	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnActionEnded OnAbilityFinishedEvent;

	/*
	 * Returns the currently performing action instance.
	 * @return Pointer to the current UACFActionAbility instance.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE class UACFActionAbility* GetCurrentAction() const { return PerformingAction; }

	/*
	 * Exits the current active action.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void ExitCurrentAction();

	void GrantInitialAbilities();
	virtual void OnAbilityStarted(TObjectPtr<UACFGameplayAbility> ability);
	virtual void OnAbilityEnded(TObjectPtr<UACFGameplayAbility> ability);

	void EvaluateBuffer();

	/*Combo Counters*/
	void SetComboCounter(const FGameplayTag& comboTag, int32 value);

	UFUNCTION(Blueprintpure, Category = ACF)
	int32 GetComboCount(const FGameplayTag& comboTag) const;

	void ResetComboCount(const FGameplayTag& comboTag);
	/*END Combo Counters*/


	void SetCurrentPriority(const int32 newPriority);

	void SetPendingPriority(const int32 newPriority);
private:
	bool LaunchAbility(const FGameplayAbilitySpecHandle& handle, const EActionPriority priority);

	bool LaunchAbilityWithPayload(
		const FGameplayAbilitySpecHandle& handle,
		const EActionPriority priority,
		const FGameplayEventData* OptionalEventData);

	// Internal function with optional payload
	bool Internal_TriggerAction(
		FGameplayTag abilityTag,
		EActionPriority Priority,
		bool bCanBeStored,
		const FGameplayEventData* OptionalEventData = nullptr);

	TObjectPtr<ACharacter> CharacterOwner;


	UPROPERTY(Replicated)
	bool bIsPerformingAction;

	UPROPERTY()
	TObjectPtr<UACFActionAbility> PerformingAction;

	UPROPERTY()
	TObjectPtr<UACFGameplayAbility> LastActivatedAbility;

	UPROPERTY()
	FActionState CurrentActionState;

	UPROPERTY(Replicated)
	FGameplayTag CurrentAbilityTag;

	/**
	 * Buffered action tag. NOT replicated: each machine buffers locally. The owning client
	 * buffers its own input and re-triggers the next combo step as a predicted activation
	 * (carrying the combo counter in the payload); replicating this would let the server's
	 * empty value clobber the client's local buffer before it is consumed.
	 */
	UPROPERTY()
	FGameplayTag StoredAction;

	UPROPERTY(Replicated)
	int32 CurrentPriority;

	UPROPERTY(Replicated)
	FGameplayTag currentMovesetActionsTag;

	/**
	 * Per-tag combo step counter. NOT replicated: the client predicts it locally and the
	 * value it wants is carried to the server inside the ability payload
	 * (FACFAbilityPayload::ComboCounter) on the predicted activation, so both sides select
	 * the same montage section without replication or extra RPCs.
	 */
	UPROPERTY()
	TArray<FComboCounter> ComboCounters;

	UPROPERTY(Replicated)
	bool bIsLocked = false;

	int32 PendingPriority;
	bool bCanStoreAction = true;
	TObjectPtr<UARSStatisticsComponent> StatisticComp;

	/* Private Functions*/
	void PrintStateDebugInfo(bool bIsEntring);

protected:
	friend class UACFGameplayAbility;
	friend class UACFActionAbility;

	// Called when the game starts
	virtual void BeginPlay() override;



	UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = ACF)
	bool bPrintDebugInfo = false;

	UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = ACF)
	bool bAutoInit = false;

	/*The Actions set to be used for this character*/
	UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = ACF)
	UACFAbilitySet* DefaultAbilitySet;

	/*The ActionsSet to be used when a specific moveset is applied*/
	UPROPERTY(BlueprintReadOnly, meta = (Categories = "Moveset"), EditDefaultsOnly, Category = ACF)
	TMap<FGameplayTag, UACFAbilitySet*> MovesetAbilities;

};
