// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "ACFActionTypes.h"

#include "Abilities/GameplayAbility.h"
#include "Abilities/GameplayAbilityTypes.h"
#include "GameFramework/Character.h"
#include "ACFGameplayAbility.generated.h"

class UARSStatisticsComponent;

/**
 *
 * A specialized Gameplay Ability used in ACF to represent abilities.
 *
 */
UCLASS(Blueprintable, BlueprintType, DefaultToInstanced, EditInlineNew)
class ACTIONSSYSTEM_API UACFGameplayAbility : public UGameplayAbility
{
	GENERATED_BODY()


public:
	//Default Constructor
	UACFGameplayAbility();

	/**
	 * Returns the current action configuration for this action.
	 * @return A copy of the current FActionConfig struct.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FActionConfig GetActionConfig() const
	{
		return ActionConfig;
	}

	/**
	 * Assigns a new animation montage for this action.
	* @param newMontage The animation montage to use.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetAnimMontage(UAnimMontage* newMontage);

	/**
	 * Returns the animation montage used for this action.
	 * @return A pointer to the animation montage asset.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	UAnimMontage* GetAnimMontage() const
	{
		return animMontage;
	}

	/**
	 * Gets the gameplay tag associated with this action.
	 * @return The FGameplayTag identifying this action.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FGameplayTag GetActionTag() const
	{
		return GetTriggeringTag();
	}

	/**
	* Returns the play rate of the animation montage.
	* @return Animation playback speed multiplier.
	*/
	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	float GetPlayRate() const;

	/**
	 * Returns the play rate of the animation montage.
	 * @return Animation playback speed multiplier.
	 */
	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	UAnimMontage* GetMontage() const;

	/**
	* Plays any gameplay effects or visual/audio effects related to this action.
	*/
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
	void PlayEffects();

	/**
	* Starts the execution of the action, including animation playback.
	*/
	UFUNCTION(BlueprintCallable, Category = ACF)
	void ExecuteAction();

	/** Returns the spec handle for this ability instance. */
	UFUNCTION(BlueprintCallable, BlueprintPure, Category = "ACF")
	FGameplayAbilitySpecHandle GetSpecHandle() const
	{
		return GetCurrentAbilitySpecHandle();
	}

	UFUNCTION(BlueprintPure, Category = "ACF|Payload")
	FACFAbilityPayload GetTriggerPayload() const
	{
		return StoredPayload;
	}

	UFUNCTION(BlueprintPure, Category = "ACF|Payload")
	bool HasValidPayload() const
	{
		return StoredPayload.bIsValid;
	}

	UFUNCTION(BlueprintPure, Category = "ACF|Payload")
	FGameplayTag GetTriggeringTag() const { return TriggeringTag; }

	UFUNCTION(BlueprintPure, Category = "ACF")
	TArray<FStatisticValue> GetDefaultAbilityCost() const { return ActionConfig.ActionCost; }

protected:

	/**
	* Gets the name of the montage section to play.
	* @return The section name to be played.
	*/
	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	FName GetMontageSectionName();

	/**
	* Returns the action manager component associated with this ability.
	*
	* @return Pointer to the UACFAbilitySystemComponent.
	*/
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE UACFAbilitySystemComponent* GetACFAbilityComponent() const { return ACFAbilityComponent; }



	/**
	* Fills warp reproduction info when montage type is set to Warp.
	* @param outWarpInfo Output parameter to fill with warp data.
	*/
	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	void GetWarpInfo(FACFWarpReproductionInfo& outWarpInfo);

	/**
	 * Gets the transform to be used for the warp target.
	 * Only called if MontageReproductionType is set to Warp.
	 * @return The transform of the warp target.
	 */
	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	FTransform GetWarpTransform();

	/**
	 * Gets the component used as warp target.
	 * Only called if MontageReproductionType is set to Warp.
	 * @return The scene component to warp to.
	 */
	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	class USceneComponent* GetWarpTargetComponent();

	/**
	 * Called when a notable point in the animation is reached (via ACFNotifyAction).
	 */
	UFUNCTION(BlueprintNativeEvent, DisplayName = "NotablePointReached", Category = ACF)
	void OnNotablePointReached();

	/**
	* Called when a gameplay event tied to this action is received.
	* @param eventTag The tag of the received gameplay event.
	 */
	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	void OnGameplayEventReceived(const FGameplayTag eventTag);

	/**
	 * Called by the ability system when a buffered input arrives and no ability is currently active.
	 * This handles the multiplayer race condition where StoreAbilityInBuffer RPC arrives
	 * after the current ability has already ended (due to network lag).
	 * Override in combo actions to advance the combo counter for late-arriving inputs.
	 * @param inputTag The tag of the buffered input action.
	 */
	virtual void OnBufferedInputReceived(const FGameplayTag& inputTag) {}

	/**
	* Called when a gameplay event tied to this action is received.
	* @param eventTag The tag of the received gameplay event.
	*/
	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	void OnMontageFinished(bool bInterrupted);

	/** Called when the ability system is initialized with a pawn avatar. */
	UFUNCTION(BlueprintImplementableEvent, Category = ACF, DisplayName = "OnPawnAvatarSet")
	void K2_OnPawnAvatarSet();

	/**
	 * Returns the character that owns this ability.
	 *
	 * @return Pointer to the owning ACharacter.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE ACharacter* GetCharacterOwner() const { return CharacterOwner; }


	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
	FActionConfig ActionConfig;

	UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = ACF)
	UAnimMontage* animMontage;


	UPROPERTY(BlueprintReadWrite, Category = ACF)
	FACFMontageInfo MontageInfo;

	UPROPERTY(BlueprintReadOnly, Category = ACF)
	FGameplayTag TriggeringTag;

	UPROPERTY(BlueprintReadOnly, Category = "ACF|Payload")
	FACFAbilityPayload StoredPayload;

	bool IsFullyInit() const;
	void PlayCurrentMontage();

	UWorld* GetWorld() const override { return GetCharacterOwner() ? GetCharacterOwner()->GetWorld() : nullptr; }

	//**GAMEPLAY ABILITY OVERRIDE **/
	virtual void PreActivate(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo,
		const FGameplayAbilityActivationInfo ActivationInfo, FOnGameplayAbilityEnded::FDelegate* OnGameplayAbilityEndedDelegate, const FGameplayEventData* TriggerEventData) override;
	virtual void ExtractPayloadFromEvent(const FGameplayEventData* TriggerEventData);
	virtual void ActivateAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo,
		const FGameplayAbilityActivationInfo ActivationInfo, const FGameplayEventData* TriggerEventData) override;
	virtual void EndAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo,
		const FGameplayAbilityActivationInfo ActivationInfo, bool bReplicateEndAbility, bool bWasCancelled) override;
	virtual bool CheckCost(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo, OUT FGameplayTagContainer* OptionalRelevantTags = nullptr) const;
	virtual void OnAvatarSet(const FGameplayAbilityActorInfo* ActorInfo, const FGameplayAbilitySpec& Spec) override;
	virtual void ApplyCost(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo, const FGameplayAbilityActivationInfo ActivationInfo) const override;
	virtual float GetCooldownTimeRemaining(const FGameplayAbilityActorInfo* ActorInfo) const override;

	//Ability Data
	FGameplayAbilityActorInfo actorInfo;
	FGameplayAbilityActivationInfo activationInfo;
	FGameplayAbilitySpecHandle selfHandle;

	// Init Value From a Template Action
	virtual void InitAbility();

	UFUNCTION()
	virtual void HandleMontageFinished();

	UFUNCTION()
	virtual void HandleMontageInterrupted();

	UPROPERTY()
	TObjectPtr<UARSStatisticsComponent> StatisticComp;

	UFUNCTION()
	virtual void HandleGameplayEventReceived(FGameplayEventData Payload);

	/* Deprecated: use GetCharacterOwner() instead */
	UPROPERTY(BlueprintReadOnly, Category = ACF)
	TObjectPtr<ACharacter> CharacterOwner;

	bool bIsExecutingAction = false;
	bool bAutoCommit = true;
	void PrepareMontageInfo();

	UPROPERTY()
	TObjectPtr<class UACFAbilitySystemComponent> ACFAbilityComponent;

	friend UACFAbilitySystemComponent;
private:

	void InitWarp();
	void UpdateWarp();

	FActiveGameplayEffectHandle executionEffect;
	bool bFullyInit;



};
