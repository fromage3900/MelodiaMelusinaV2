// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFCCTypes.h"
#include "Animation/ACFAnimTypes.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "Components/ACFDamageHandlerComponent.h"
#include "Components/ACFEquipmentComponent.h"
#include "Components/CapsuleComponent.h"
#include "CoreMinimal.h"
#include "Game/ACFDamageType.h"
#include "Game/ACFTypes.h"
#include "GameFramework/Character.h"
#include "ALSSavableInterface.h"
#include "Interfaces/ACFEntityInterface.h"
#include "Interfaces/ACFInteractableInterface.h"
#include <AbilitySystemInterface.h>
#include <GenericTeamAgentInterface.h>

#include "ACFCharacter.generated.h"

class USkeletalMeshComponent;
class UAbilitySystemComponent;
class UACFTeamComponent;
class UAIPerceptionStimuliSourceComponent;
class UCCMFadeableActorComponent;
class UACFCharacterInitializerComponent;

enum class EActionPriority : uint8;
enum class EDamageZone : uint8;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnCharacterFullyInitialized);

// DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDamageInflicted, class AActor*, damageReceiver);

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnCrouchStateChanged, bool, isCrouched);


DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnCombatTypeChanged, ECombatType, CombatType);

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDeathEvent, AACFCharacter*, self);

UCLASS()
class ASCENTCOMBATFRAMEWORK_API AACFCharacter : public ACharacter,
	public IGenericTeamAgentInterface,
	public IACFEntityInterface,
	public IAbilitySystemInterface,
	public IALSSavableInterface {
	GENERATED_BODY()

public:
	/** Default constructor for the character */
	AACFCharacter(const FObjectInitializer& ObjectInitializer);

	/**
	 * * Gets whether fall damage is enabled.
	 *
	 * @return True if fall damage is enabled, false otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	bool GetEnableFallDamage() const { return bEnableFallDamage; }

	/**
	 * * Sets whether fall damage is enabled.
	 *
	 * @param val True to enable fall damage, false to disable it.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetEnableFallDamage(bool val) { bEnableFallDamage = val; }

	/**
	 * Resets the fall-height reference to the character's current Z position.
	 * Call this when a glider (or any ability that slows descent) activates so that
	 * the fall-damage distance is measured from the glider activation point instead
	 * of from the original jump/walk-off point.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF | Fall")
	void ResetFallHeight() { ZFalling = GetActorLocation().Z; }

	/**
	 * * Gets whether an action should be triggered upon landing.
	 *
	 * @return True if an action should be triggered upon landing, false otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	bool GetTriggerActionOnLand() const { return bTriggerActionOnLand; }

	/**
	 * * Sets whether an action should be triggered upon landing.
	 *
	 * @param val True to trigger an action upon landing, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetTriggerActionOnLand(bool val) { bTriggerActionOnLand = val; }

	bool GetAutoInit() const { return bAutoInit; }
	void SetAutoInit(bool val) { bAutoInit = val; }
protected:
	// Called after properties have been initialized
	virtual void PostInitProperties() override;

	// Called when the game ends
	virtual void EndPlay(EEndPlayReason::Type reason) override;

	// Handles replication before network sync
	void PreReplication(IRepChangedPropertyTracker& ChangedPropertyTracker);

	// Called before components are initialized
	virtual void PreInitializeComponents() override;

	// Called when the game starts or when spawned
	virtual void BeginPlay() override;

	// Updates movement base
	virtual void SetBase(FMovementBaseInterfaceData* MovementBaseInterfaceData, FName BoneName, bool bNotifyActor) override;

	// Handles movement mode changes
	virtual void OnMovementModeChanged(EMovementMode prevMovementMde, uint8 PreviousCustomMode = 0) override;

	// Handles landing logic
	virtual void Landed(const FHitResult& Hit) override;

	/** Character name displayed in UI */
	UPROPERTY(EditAnyWhere, SaveGame, Category = "ACF")
	FText CharacterName;

	/** Portrait name displayed in UI */
	UPROPERTY(EditAnyWhere, SaveGame, Category = "ACF")
	UTexture2D* CharacterPortrait;

	/** Mapping of bone names to damage zones */
	UPROPERTY(EditAnyWhere, BlueprintReadWrite, Category = "ACF")
	TMap<FName, EDamageZone> BoneNameToDamageZoneMap;

	UPROPERTY(EditAnyWhere, BlueprintReadWrite, Category = "ACF")
	bool bAutoInit = true;

	/** Determines if fall damage is active */
	UPROPERTY(EditAnywhere, Category = "ACF | Fall")
	bool bEnableFallDamage = true;

	/** Threshold fall distance for damage */
	UPROPERTY(EditAnywhere, Category = "ACF | Fall")
	float FallDamageDistanceThreshold = 200.f;

	/** Curve defining fall damage based on distance */
	UPROPERTY(EditAnywhere, Category = "ACF | Fall")
	class UCurveFloat* FallDamageByFallDistance;

	/** Determines if an action should be triggered upon landing */
	UPROPERTY(EditAnywhere, Category = "ACF | Fall")
	bool bTriggerActionOnLand = true;

	/** Fall height required to trigger an action */
	UPROPERTY(EditAnywhere, meta = (EditCondition = "bTriggerActionOnLand"), Category = "ACF | Fall")
	float FallHeightToTriggerAction = 300.f;

	/** Action tag to trigger upon landing */
	UPROPERTY(EditAnywhere, meta = (EditCondition = "bTriggerActionOnLand"), Category = "ACF | Fall")
	FGameplayTag ActionsToTriggerOnLand;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = Camera, meta = (AllowPrivateAccess = "true"))
	class UCameraComponent* CameraComponent;

	/** Component for managing abilities in ACF */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, DisplayName = "ACF Ability System Comp", Category = ACF)
	TObjectPtr<class UACFAbilitySystemComponent> ActionsComp;

	/** Component for character movement in ACF */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, DisplayName = "ACF Character Movement Comp", Category = ACF)
	TObjectPtr<class UACFCharacterMovementComponent> LocomotionComp;

	/** Component for managing statistics in ACF */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, DisplayName = "ACF Statistics Comp", Category = ACF)
	TObjectPtr<class UARSStatisticsComponent> StatisticsComp;

	/** Component for managing collisions in ACF */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, DisplayName = "ACF Collisions Manager Comp", Category = ACF)
	TObjectPtr<class UACMCollisionManagerComponent> CollisionComp;

	/** Component for managing equipment and inventory in ACF */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, DisplayName = "ACF Equipment & Inventory Comp", Category = ACF)
	TObjectPtr<class UACFEquipmentComponent> EquipmentComp;

	/** Component for managing visual and sound effects in ACF */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, DisplayName = "ACF VFX & SFX Comp", Category = ACF)
	TObjectPtr<class UACFEffectsManagerComponent> EffetsComp;

	/** Component for handling damage in ACF */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, DisplayName = "ACF Damage Handler Comp", Category = ACF)
	TObjectPtr<class UACFDamageHandlerComponent> DamageHandlerComp;

	/** Component handling the character's ragdoll physics and death animations */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, DisplayName = "ACF Ragdoll Comp", Category = ACF)
	TObjectPtr<class UACFRagdollComponent> RagdollComp;

	/** Component for data-driven character initialization from a UACFCharacterDataAsset */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, DisplayName = "ACF Character Initializer Comp", Category = ACF)
	TObjectPtr<UACFCharacterInitializerComponent> InitializerComp;

	/** Component for handling motion warping mechanics */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, DisplayName = "ACF Motion Warp Comp", Category = ACF)
	TObjectPtr<class UMotionWarpingComponent> MotionWarpComp;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, DisplayName = "ACF Team Comp", Category = ACF)
	TObjectPtr<UACFTeamComponent> TeamComponent;

	/** Component for applying camera effects such as fade in/out */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, DisplayName = "ACF Material Overrides Comp", Category = ACF)
	TObjectPtr<UCCMFadeableActorComponent> FadeComp;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, DisplayName = "ACF Stimuli Comp", Category = ACF)
	TObjectPtr<UAIPerceptionStimuliSourceComponent> StimuliSource;


	/** Audio component responsible for handling sound playback */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
	TObjectPtr<class UAudioComponent> AudioComp;

	/** Event triggered when the character dies */
	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	void OnCharacterDeath();
	virtual void OnCharacterDeath_Implementation();

	/** Calculates fall damage based on the fall distance */
	UFUNCTION(BlueprintCallable, Category = ACF)
	float GetFallDamageFromDistance(float fallDistance);

	/** Initializes character components post-creation */
	virtual void PostInitializeComponents() override;

	virtual void CalcCamera(float DeltaTime, FMinimalViewInfo& OutResult) override;

	/** Current combat type of the character */
	UPROPERTY(Replicated, BlueprintReadOnly, Category = "ACF")
	ECombatType CombatType = ECombatType::EUnarmed;

	/** Death type behavior of the character */
	UPROPERTY(EditDefaultsOnly, Category = "ACF | Death")
	EDeathType DeathType = EDeathType::EDeathAction;

	/** Whether the character should automatically be destroyed upon death */
	UPROPERTY(EditDefaultsOnly, Category = "ACF | Death")
	bool bAutoDestroyOnDeath = false;

	/** Time before the character is destroyed after death */
	UPROPERTY(EditDefaultsOnly, meta = (EditCondition = "bAutoDestroyOnDeath"), Category = "ACF | Death")
	float DestroyTimeOnDeath = 2.f;

	/** Whether the character's capsule should be disabled upon death */
	UPROPERTY(EditDefaultsOnly, Category = "ACF | Death")
	bool bDisableCapsuleOnDeath = true;

	virtual UAbilitySystemComponent* GetAbilitySystemComponent() const override;

	/** Attempts to make the character jump */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void TryJump();

public:
	/**
	 * * Sets the character's immortality status.
	 *
	 * @param inImmortal True to make the character immortal, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetIsImmortal(bool inImmortal)
	{
		GetDamageHandlerComponent()->SetIsImmortal(inImmortal);
	}

	/**
	 * * Checks if the character is immortal.
	 *
	 * @return True if the character is immortal, false otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	bool IsImmortal() const
	{
		return GetDamageHandlerComponent()->GetIsImmortal();
	}

	/**
	 * * Takes damage and applies it to the character.
	 *
	 * @param Damage The amount of damage to apply.
	 * @param DamageEvent The event that caused the damage.
	 * @param EventInstigator The controller responsible for the damage.
	 * @param DamageCauser The actor that caused the damage.
	 * @return The amount of damage actually applied.
	 */
	virtual float TakeDamage(float Damage, FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser) override;

	/**
	 * * Makes the character crouch.
	 *
	 * @param bClientSimulation True if the crouch is simulated on the client.
	 */
	virtual void Crouch(bool bClientSimulation = false) override;

	/**
	 * * Makes the character uncrouch.
	 *
	 * @param bClientSimulation True if the uncrouch is simulated on the client.
	 */
	virtual void UnCrouch(bool bClientSimulation = false) override;

	/**
	 * * Called when the actor is loaded.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
	void OnActorLoaded();
	virtual void OnActorLoaded_Implementation();

	/**
	 * * Called when the actor is saved.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
	void OnActorSaved();
	virtual void OnActorSaved_Implementation();

	//~ Begin IALSSavableInterface (minimal, mirrors AACFWorldItem's pattern)
	/** Components whose SaveGame data must be persisted (stats, death flag, equipment). */
	virtual TArray<UActorComponent*> GetComponentsToSave_Implementation() const override;
	/**
	 * Load hook, invoked consistently by every restore path: full world-load
	 * (GFinishLoad -> ExecuteFunctionsOnSavableActor) and per-actor WPActors auto-reload
	 * (UALSLoadAndSaveSubsystem::LoadActor -> FullDeserializeActor). Forwards to
	 * OnActorLoaded, or destroys the corpse if the actor was saved dead.
	 */
	virtual void OnLoaded_Implementation() override;
	//~ End IALSSavableInterface

	/**
	 * If the actor was restored dead, destroys it and its equipped items instantly
	 * instead of trying to replay death visuals (see .cpp for why).
	 */
	void DestroyIfLoadedDead();

	/**
	 * * Checks if the entity is alive.
	 *
	 * @return True if the entity is alive, false otherwise.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
	bool IsEntityAlive() const;
	virtual bool IsEntityAlive_Implementation() const override
	{
		return IsAlive();
	}

	/**
	 * * Gets the extent radius of the entity.
	 *
	 * @return The extent radius of the entity.
	 */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
	float GetEntityExtentRadius() const;
	virtual float GetEntityExtentRadius_Implementation() const
	{
		return GetCapsuleComponent()->GetScaledCapsuleRadius();
	}
	// END ACF ENTITY INTERFACE

	/**
	 * * Gets the combat team of the character.
	 *
	 * @return The combat team of the character.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FGameplayTag GetCombatTeam() const;

	/**
	 * * Checks if the target is an enemy.
	 *
	 * @param target The target to check.
	 * @return True if the target is an enemy, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	bool IsMyEnemy(AACFCharacter* target) const;

	/**
	 * * Gets the death type of the character.
	 *
	 * @return The death type of the character.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	EDeathType GetDeathType() const
	{
		return DeathType;
	}

	/**
	 * * Sets the death type of the character.
	 *
	 * @param inDeathType The death type to set.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetDeathType(EDeathType inDeathType)
	{
		DeathType = inDeathType;
	}

	/**
	 * * Gets the damage zone by bone name.
	 *
	 * @param BoneName The name of the bone.
	 * @return The damage zone associated with the bone name.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	EDamageZone GetDamageZoneByBoneName(FName BoneName) const;

	/**
	 * * Gets the collision channels of enemies.
	 *
	 * @return An array of collision channels of enemies.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	TArray<TEnumAsByte<ECollisionChannel>> GetEnemiesCollisionChannel() const;

	/**
	 * * Checks if the character is ranged.
	 *
	 * @return True if the character is ranged, false otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE bool IsRanged() const
	{
		return CombatType == ECombatType::ERanged;
	}

	/**
	 * * Checks if the character can be ranged.
	 *
	 * @return True if the character can be ranged, false otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	bool CanBeRanged() const;

	/**
	 * * Called to bind functionality to input.
	 *
	 * @param PlayerInputComponent The input component to bind.
	 */
	virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;

	UFUNCTION(BlueprintImplementableEvent, Category = ACF)
	void SetupPlayerInputComponentBP(UInputComponent* PlayerInputComponent);

	/**
	 * * Gets the walk speed of the character.
	 *
	 * @return The walk speed of the character.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	float GetWalkSpeed() const;

	/**
	 * * Gets the jog speed of the character.
	 *
	 * @return The jog speed of the character.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	float GetJogSpeed() const;

	/**
	 * * Gets the sprint speed of the character.
	 *
	 * @return The sprint speed of the character.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	float GetSprintSpeed() const;

	/**
	 * * Triggers an action.
	 *
	 * @param Action The action to trigger.
	 * @param Priority The priority of the action.
	 * @param canBeStored True if the action can be stored, false otherwise.
	 * @param contextString The context string for the action.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void TriggerAction(FGameplayTag Action, EActionPriority Priority, bool canBeStored = false);

	/**
	 * * Forces an action.
	 *
	 * @param Action The action to force.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void ForceAction(FGameplayTag Action);

	/**
	 * * Gets the current action state.
	 *
	 * @return The current action state.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FGameplayTag GetCurrentActionState() const;

	/**
	 * * Gets the target of the character.
	 *
	 * @return The target of the character.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	AActor* GetTarget() const;

	/**
	 * * Sets the character name.
	 *
	 * @param inCharacterName The name to set.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetCharacterName(const FText& inCharacterName)
	{
		CharacterName = inCharacterName;
	}

	/**
	 * * Sets the character Portrait.
	 *
	 * @param inCharacterPortrait The Portrait to set.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetCharacterPortrait(UTexture2D* inCharacterPortrait)
	{
		CharacterPortrait = inCharacterPortrait;
	}

	/**
	* * Get the character Portrait.
	*/
	UFUNCTION(BlueprintCallable, Category = ACF)
	UTexture2D* GetCharacterPortrait() { return CharacterPortrait; }


	/**
	 * * Destroys the character.
	 *
	 * @param lifeSpan The lifespan before destruction.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	void DestroyCharacter(float lifeSpan = 0.2);

	/**
	 * * Gets the main mesh of the character.
	 *
	 * @return The main mesh of the character.
	 */
	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	USkeletalMeshComponent* GetMainMesh() const;
	virtual USkeletalMeshComponent* GetMainMesh_Implementation() const;

	/**
	 * * Gets the ACF character movement component.
	 *
	 * @return The ACF character movement component.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE class UACFCharacterMovementComponent* GetACFCharacterMovementComponent() const { return LocomotionComp; }

	/**
	 * * Gets the actions component.
	 *
	 * @return The actions component.
	 */
	UFUNCTION(BlueprintPure, DisplayName = "GetActionsAbilityComponent", Category = ACF)
	FORCEINLINE class UACFAbilitySystemComponent* GetActionsComponent() const { return ActionsComp; }

	/**
	 * * Gets the statistics component.
	 *
	 * @return The statistics component.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE class UARSStatisticsComponent* GetStatisticsComponent() const { return StatisticsComp; }

	/**
	 * * Gets the leveling component.
	 *
	 * @return The leveling component.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE class UARSLevelingComponent* GetLevelingComponent() const { return StatisticsComp; }

	/**
	 * * Gets the equipment component.
	 *
	 * @return The equipment component.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE class UACFEquipmentComponent* GetEquipmentComponent() const { return EquipmentComp; }

	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE UACFCharacterInitializerComponent* GetInitializerComponent() const { return InitializerComp; }

	/**
	 * * Gets the collisions component.
	 *
	 * @return The collisions component.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE class UACMCollisionManagerComponent* GetCollisionsComponent() const { return CollisionComp; }

	/**
	 * * Gets the damage handler component.
	 *
	 * @return The damage handler component.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE class UACFDamageHandlerComponent* GetDamageHandlerComponent() const { return DamageHandlerComp; }

	// Gets the ragdoll component
	/**
	 * * Gets the ragdoll component.
	 *
	 * @return The ragdoll component.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE class UACFRagdollComponent* GetRagdollComponent() const { return RagdollComp; }

	// Gets the motion warp component
	/**
	 * * Gets the motion warp component.
	 *
	 * @return The motion warp component.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE class UMotionWarpingComponent* GetMotionWarpComponent() const { return MotionWarpComp; }

	// Gets the materials override component
	/**
	 * * Gets the materials override component.
	 *
	 * @return The materials override component.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE class UCCMFadeableActorComponent* GetMaterialsOverrideComp() const { return FadeComp; }

	// Gets the targeting component
	/**
	 * * Gets the targeting component.
	 *
	 * @return The targeting component.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	class UATSBaseTargetComponent* GetTargetingComponent() const;

	// Checks if the character is alive
	/**
	 * * Checks if the character is alive.
	 *
	 * @return True if the character is alive, false otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	bool IsAlive() const;

	/**
	 * * Gets the character name.
	 *
	 * @return The character name.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE FText GetCharacterName() const { return CharacterName; }

	/**
	 * * Gets the audio component.
	 *
	 * @return The audio component.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE class UAudioComponent* GetAudioComp() const { return AudioComp; }

	/**
	 * * Gets the combat type of the character.
	 *
	 * @return The combat type of the character.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE ECombatType GetCombatType() const { return CombatType; }

	/**
	 * * Gets the current moveset.
	 *
	 * @return The current moveset.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FGameplayTag GetCurrentMoveset() const;

	/**
	 * * Gets the ACF animation instance.
	 *
	 * @return The ACF animation instance.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	class UACFAnimInstance* GetACFAnimInstance() const;

	/**
	 * * Gets the current maximum speed of the character.
	 *
	 * @return The current maximum speed of the character.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	float GetCurrentMaxSpeed() const;

	/**
	 * * Gets the last damage information.
	 *
	 * @return The last damage information.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FACFDamageEvent GetLastDamageInfo() const;

	/**
	 * * Checks if the character is dead.
	 *
	 * @return True if the character is dead, false otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE bool GetIsDead() const { return !IsAlive(); }

	/**
	 * * Kills the character instantly.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	void KillCharacter();

	/**
	 * * Revives the character with a specified amount of health.
	 *
	 * @param normalizedHealthToGrant The amount of health to grant upon revival.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	void ReviveCharacter(float normalizedHealthToGrant = 1.f);

	/**
	 * * Gets the relative target direction.
	 *
	 * @param targetActor The target actor.
	 * @return The relative target direction.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	EACFDirection GetRelativeTargetDirection(const AActor* targetActor) const;

	/**
	 * * Activates damage handling with specified channels.
	 *
	 * @param damageActType The type of damage activation.
	 * @param traceChannels The trace channels to use for damage handling.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void ActivateDamage(const EDamageActivationType& damageActType, const TArray<FName>& traceChannels);

	/**
	 * * Deactivates damage handling.
	 *
	 * @param damageActType The type of damage activation.
	 * @param traceChannels The trace channels to use for damage handling.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void DeactivateDamage(const EDamageActivationType& damageActType, const TArray<FName>& traceChannels);

	/**
	 * * Switches the moveset.
	 *
	 * @param moveType The moveset to switch to.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	void SwitchMoveset(FGameplayTag moveType);

	/**
	 * * Switches the Actions set.
	 *
	 * @param moveType The moveset actions to switch to.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	void SwitchMovesetActions(FGameplayTag moveType);

	/**
	 * * Switches the overlay.
	 *
	 * @param overlayTag The overlay to switch to.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	void SwitchOverlay(FGameplayTag overlayTag);

	/*+DELEGATES*/

	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnCombatTypeChanged OnCombatTypeChanged;

	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnCharacterFullyInitialized OnCharacterFullyInitialized;

	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnCrouchStateChanged OnCrouchStateChanged;

	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnDeathEvent OnDeath;

	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnDamageReceived OnDamageReceived;

	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnDamageInflicted OnDamageInflicted;

	/// <summary>
	/// /Combat Team Interface
	/// </summary>

	// IACFEntityInterface - Main implementation (source of truth)
	virtual FGameplayTag GetEntityCombatTeam_Implementation() const override;
	virtual void AssignTeamToEntity_Implementation(FGameplayTag inCombatTeam) override;

	// IGenericTeamAgentInterface - Read from TeamComponent
	virtual FGenericTeamId GetGenericTeamId() const override;
	virtual void SetGenericTeamId(const FGenericTeamId& TeamID) override;
	virtual ETeamAttitude::Type GetTeamAttitudeTowards(const AActor& Other) const override;

	/// <summary>
	/// /End Combat Team Entity
	/// </summary>

private:
	bool bInitialized = false;

	float ZFalling = -1.f;

	UFUNCTION()
	void HandleDamageReceived(const FACFDamageEvent& damageReceived);

	UFUNCTION()
	void HandleDamageInflicted(const FACFDamageEvent& damage);


	UFUNCTION()
	void SetupCollisionManager();

	UFUNCTION()
	void HandleCharacterDeath();

	UFUNCTION()
	void InitializeCharacter();

	UFUNCTION()
	void HandleEquipmentChanged(const FEquipment& equipment);

	UFUNCTION()
	void OnRep_ReplicatedAcceleration();

	UPROPERTY(Transient, ReplicatedUsing = OnRep_ReplicatedAcceleration)
	FReplicatedAcceleration ReplicatedAcceleration;
};
