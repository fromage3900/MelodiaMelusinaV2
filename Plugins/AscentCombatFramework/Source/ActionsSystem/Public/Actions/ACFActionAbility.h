// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFActionTypes.h"
#include "Animation/AnimMontage.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include <Abilities/GameplayAbility.h>
#include <GameplayTagContainer.h>
#include "ACFGameplayAbility.h"

#include "ACFActionAbility.generated.h"

class UAnimMontage;
class UARSStatisticsComponent;

/**
 *
 * A specialized Gameplay Ability used in ACF to represent animated abilities.
 * When triggered, it plays an animation montage and automatically ends when the montage finishes.
 * This class encapsulates logic for warp reproduction, animation-driven execution flow,
 * and optional substate and effect hooks.
 *
 */
UCLASS(Blueprintable, BlueprintType)
class ACTIONSSYSTEM_API UACFActionAbility : public UACFGameplayAbility {
	GENERATED_BODY()



public:
	UACFActionAbility();

	// GETTERS & SETTERS//
	/**
	 * Sets a new configuration for the action.
	 * @param newConfig The new action configuration to assign.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetActionConfig(const FActionConfig& newConfig);


	/**
	 * Ends the action explicitly. Doesn't stop animation, but handles logic reset.
	 * @param bCancelled If true, the action was interrupted or cancelled.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	virtual void ExitAction(bool bCancelled = false);


protected:

	/*If this action allows physical rotation during the animation*/
	UPROPERTY(EditAnywhere, Category = ACF)
	bool bAllowPhysicalRotation = false;

	/**
	 * Called on the server when the action is successfully triggered.
	 */
	UFUNCTION(BlueprintNativeEvent, DisplayName = "ServerAbilityStarted", Category = ACF)
	void OnActionStarted();

	/**
	 * Called on the clients when the action is successfully triggered.
	 */
	UFUNCTION(BlueprintNativeEvent, DisplayName = "ClientAbilityStarted", Category = ACF)
	void ClientsOnActionStarted();

	/**
	 * Called on the server when the action finishes.
	 * Usually triggered by montage ending if BindActionToAnimation is true.
	 */
	UFUNCTION(BlueprintNativeEvent, DisplayName = "ServerEndAbility", Category = ACF)
	void OnActionEnded();

	/**
	 * Called on the clients when the action finishes.
	 */
	UFUNCTION(BlueprintNativeEvent, DisplayName = "ClientEndAbility", Category = ACF)
	void ClientsOnActionEnded();

	/**
	 * Deprecated. Use CanActivateAbility() instead.
	 * Custom logic for determining whether this action can be executed.
	 * @param owner Optional character context.
	 * @return True if the action can be executed.
	 */
	UFUNCTION(BlueprintNativeEvent, meta = (DeprecatedFunction, DeprecationMessage = "Use CanActivateAbility() instead"), Category = ACF)
	bool CanExecuteAction(class ACharacter* owner = nullptr) const;
	/**
	 * Client-side handler for notable points.
	 */
	UFUNCTION(BlueprintNativeEvent, DisplayName = "ClientNotablePoint", Category = ACF)
	void ClientsOnNotablePointReached();

	/**
	 * Sets the montage reproduction strategy.
	 * @param reproType The reproduction type to use.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetMontageReproductionType(EMontageReproductionType reproType);


	//**GAMEPLAY ABILITY OVERRIDE **/
	virtual void PreActivate(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo,
		const FGameplayAbilityActivationInfo ActivationInfo, FOnGameplayAbilityEnded::FDelegate* OnGameplayAbilityEndedDelegate, const FGameplayEventData* TriggerEventData) override;
	virtual void ActivateAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo,
		const FGameplayAbilityActivationInfo ActivationInfo, const FGameplayEventData* TriggerEventData) override;
	virtual void EndAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo,
		const FGameplayAbilityActivationInfo ActivationInfo, bool bReplicateEndAbility, bool bWasCancelled) override;
	virtual bool CanActivateAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo,
		const FGameplayTagContainer* SourceTags = nullptr, const FGameplayTagContainer* TargetTags = nullptr, OUT FGameplayTagContainer* OptionalRelevantTags = nullptr)
		const override;
	virtual void HandleGameplayEventReceived(FGameplayEventData Payload) override;

	//COOLDOWNS
	virtual bool CommitAbilityCooldown(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo, const FGameplayAbilityActivationInfo ActivationInfo, const bool ForceCooldown, OUT FGameplayTagContainer* OptionalRelevantTags = nullptr) override;
	virtual void ApplyCooldown(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo, const FGameplayAbilityActivationInfo ActivationInfo) const override;
	virtual const FGameplayTagContainer* GetCooldownTags() const;
	virtual bool CheckCooldown(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo, OUT FGameplayTagContainer* OptionalRelevantTags = nullptr) const override;
	bool UsingDefaultCooldown() const;


	bool bBindActionToAnimation = true;

	/*
	 * Set to true when the ExitAction notify fires on the server.
	 * Used to coordinate late-arriving combo input RPCs with the exit flow.
	 * When a combo input arrives and bExitRequested is true, the action exits immediately
	 * instead of waiting for the montage to finish. This fixes the multiplayer race condition
	 * where StoreAbilityInBuffer RPC arrives between ExitNotify and montage end.
	 */
	bool bExitRequested = false;

	virtual void Internal_OnActivated(class UACFAbilitySystemComponent* actionmanger, class UAnimMontage* inAnimMontage);
	virtual void Internal_OnDeactivated();
	virtual void HandleMontageFinished() override;
	virtual void HandleMontageInterrupted() override;
private:



	bool bOldAllowPhysicsRotation;

	FGameplayTagContainer cooldownTags;


};
