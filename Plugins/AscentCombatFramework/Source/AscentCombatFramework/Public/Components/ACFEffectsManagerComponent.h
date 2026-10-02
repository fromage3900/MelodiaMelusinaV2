// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ACFAbilitySystemComponent.h"
#include "Components/ACFCharacterMovementComponent.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "Game/ACFDamageType.h"
#include <Engine/EngineTypes.h>

#include "ACFEffectsManagerComponent.generated.h"

class UACFEffectsConfigDataAsset;

/**
 * Component responsible for managing and triggering FX (particles, sounds, decals)
 * based on gameplay events such as footsteps, damage reactions, and terrain interaction.
 * Typically attached to characters or actors that require contextual visual/audio feedback.
 */
UCLASS(Blueprintable, ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class ASCENTCOMBATFRAMEWORK_API UACFEffectsManagerComponent : public UActorComponent {
	GENERATED_BODY()

public:

	// Sets default values for this component's properties
	UACFEffectsManagerComponent();


	/**
	 * Triggers footstep visual and audio effects for the given bone, if valid.
	 *
	 * @param footBone The name of the foot bone to emit the FX from. If None, defaults to auto-selection.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void TriggerFootstepFX(FName footBone = NAME_None);

	/**
	 * Returns the physical surface type the character is currently standing on.
	 *
	 * @return The current terrain surface (e.g., grass, rock, water).
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	EPhysicalSurface GetCurrentTerrain();

	/**
	 * Called when the character receives a damage event with impact data.
	 *
	 * @param damageEvent Struct containing the full impact information (e.g., hit direction, instigator, damage type).
	 */
	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	void OnDamageImpactReceived(const FACFDamageEvent& damageEvent);
	virtual void OnDamageImpactReceived_Implementation(const FACFDamageEvent& damageEvent);

	/**
	 * Plays the visual and audio feedback for receiving damage, such as particles, sounds, and decals.
	 *
	 * @param damageEvent The data describing the hit and damage information.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void PlayHitReactionEffect(const FACFDamageEvent& damageEvent);

	/**
	* Plays the visual and audio feedback for avoiding a damage, such as particles, sounds, and decals.
	*
	* @param reactiveEventTag The gameplaytag describing the avoided event (hit/avoided).
	*/
	UFUNCTION(BlueprintCallable, Category = ACF)
	void PlayDamageAvoidedEffect(const FGameplayTag& reactiveEventTag);

	/**
	 * Attempts to retrieve the configured FX (particle, sound, etc.) for a given hit reaction and damage type.
	 *
	 * @param HitRection The gameplay tag identifying the type of reaction (e.g., light_hit, heavy_hit).
	 * @param DamageType The specific subclass of UDamageType that caused the hit.
	 * @param outFX Output parameter receiving the FX if a match is found.
	 * @return True if a matching FX configuration was found, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	bool TryGetDamageFX(const FGameplayTag& HitRection, const TSubclassOf<class UDamageType>& DamageType, FBaseFX& outFX);

	/**
	 * Attempts to retrieve the configured FX for a damage-avoided reaction (e.g. parry, dodge).
	 * Uses the effect data asset's DamageAvoidedEffects map keyed by the given tag.
	 *
	 * @param avoidedTag The gameplay tag identifying the avoided reaction (from the effect).
	 * @param outFX Output parameter receiving the FX if a match is found.
	 * @return True if a matching FX was found in CharacterEffectsConfig->DamageAvoidedEffects, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	bool TryGetDamageAvoidedFX(const FGameplayTag& avoidedTag, FBaseFX& outFX);

	/**
	 * Returns the noise value that should be emitted based on the character's current locomotion state.
	 *
	 * @return The scalar value of noise emitted (used for AI perception).
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	float GetNoiseToEmitForCurrentLocomotionState() const;

	/**
	 * Returns the noise value associated with a specific locomotion state.
	 *
	 * @param locState The locomotion state to evaluate (e.g., walking, sprinting, crouching).
	 * @return The scalar noise value to emit for that state.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	float GetNoiseToEmitByLocomotionState(ELocomotionState locState) const;

	UFUNCTION(BlueprintPure, Category = ACF)
	UACFEffectsConfigDataAsset* GetCharacterEffectsConfig() const { return CharacterEffectsConfig; }

	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetCharacterEffectsConfig(UACFEffectsConfigDataAsset* val);

protected:
	virtual void BeginPlay() override;

	/** Bone name used as fallback for hit/impact FX attachment when no bone is provided. */
	UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = ACF)
	FName DefaultHitBoneName = "pelvis";

	/** Gameplay cue tag executed when this character receives damage (hit reaction FX). Uses effect config DamageEffectsByHitReaction. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACF, meta = (Categories = "GameplayCue"))
	FGameplayTag DefaultHitCue;

	/** Gameplay cue tag executed when this character avoids damage (e.g. parry/dodge). Uses effect config DamageAvoidedEffects. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACF, meta = (Categories = "GameplayCue"))
	FGameplayTag DefaultAvoidedCue;

	/** Data asset defining footsteps, damage FX and damage-avoided FX (Effect Data Asset). Replicated to clients. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACF, ReplicatedUsing = OnRep_CharacterEffectsConfig)
	class UACFEffectsConfigDataAsset* CharacterEffectsConfig;

	/** Length of the downward trace used to detect terrain surface under the character (for footstep surface type). */
	UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = "ACF| Footstep")
	float TraceLengthByActorLocation = 200.f;

	/** Noise emitted while moving; used for AI perception. Keys: locomotion state (walk/jog/sprint). */
	UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = "ACF| Footstep")
	TMap<ELocomotionState, float> FootstepNoiseByLocomotionState;

	/** Noise emitted while moving when crouched; used for AI perception. */
	UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = "ACF| Footstep")
	TMap<ELocomotionState, float> FootstepNoiseByLocomotionStateWhenCrouched;

	/** Cached reference to the owning character. */
	UPROPERTY(BlueprintReadOnly, Category = ACF)
	ACharacter* CharacterOwner;

	/** Server RPC: request playing an attached effect on this character (replicated to clients). */
	UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
	void PlayEffectAttached(const FActionEffect& attachedFX);

	/** Server RPC: request stopping a previously attached effect. */
	UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
	void StopEffectAttached(const FActionEffect& attachedFX);

	/** Multicast: actually spawns the attached FX on clients. */
	UFUNCTION(NetMulticast, Reliable)
	void ClientsPlayEffectAttached(const FActionEffect& attachedFX);

private:
	/** Bound to ACFDamageHandlerComponent::OnDamageReceived; triggers hit reaction cue and OnDamageImpactReceived. */
	UFUNCTION()
	void HandleDamageReceived(const FACFDamageEvent& damageEvent);

	/** Multicast: stops and destroys the components for an attached effect. */
	UFUNCTION(NetMulticast, Reliable)
	void ClientsStopEffectAttached(const FActionEffect& attachedFX);

	/** Called when CharacterEffectsConfig is replicated to this client. */
	UFUNCTION()
	void OnRep_CharacterEffectsConfig();

	/** Tracks currently active attached FX by their GUID for later stop. */
	TMap<FGuid, FAttachedComponents> ActiveFX;
};
