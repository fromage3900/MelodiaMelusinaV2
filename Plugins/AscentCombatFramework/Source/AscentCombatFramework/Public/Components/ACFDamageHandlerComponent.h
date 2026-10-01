// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFCoreTypes.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "Game/ACFDamageCalculation.h"
#include "Game/ACFDamageType.h"
#include "Game/ACFTypes.h"
#include "GameFramework/DamageType.h"

#include "ACFDamageHandlerComponent.generated.h"

// Forward declarations
struct FACFDamageEvent;
class UACFDamageCalculation;
struct FOnAttributeChangeData;
class UGameplayEffect;

// Delegates for broadcasting damage-related events
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnCharacterDeath);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDamageReceived, const FACFDamageEvent&, damageReceived);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDamageInflicted, const FACFDamageEvent&, damageInflicted);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDamageAvoided, const FGameplayTag&, avoidingAction);
/**
 * * Damage handler component for Ascent Combat Framework (ACF).
 *
 * This component manages damage handling, including receiving and inflicting damage,
 * team-based collision setup, and character death/revival mechanics.
 */
UCLASS(Blueprintable, ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class ASCENTCOMBATFRAMEWORK_API UACFDamageHandlerComponent : public UActorComponent {
	GENERATED_BODY()

public:
	/**
	 * * Constructor - Sets default values for this component.
	 */
	UACFDamageHandlerComponent();

	/**
	 * * Retrieves the last recorded damage event received by this actor.
	 *
	 * @return The last received damage event.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE FACFDamageEvent GetLastDamageInfo() const { return LastDamageReceived; }



	/**
	 * * Event triggered when the actor receives damage.
	 */
	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnDamageReceived OnDamageReceived;

	/**
	 * * Event triggered when the actor successfully inflicts damage on another entity.
	 */
	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnDamageInflicted OnDamageInflicted;

	/**
	* * Event triggered when the actor successfully avoid a damage because of dodge, block, parry, etc.
	*/
	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnDamageAvoided OnDamageAvoided;

	/**
	 * * Event triggered when the owning actor dies.
	 */
	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnCharacterDeath OnOwnerDeath;

	/**
	 * * Handles point-based damage received from a specific hit location.
	 *
	 * This function processes direct impact damage, such as projectiles or melee attacks.
	 *
	 * @param Damage The amount of damage taken.
	 * @param DamageType The type of damage received.
	 * @param HitLocation The world-space location where the damage occurred.
	 * @param HitNormal The normal vector at the impact location.
	 * @param HitComponent The component that was hit.
	 * @param BoneName The bone that was hit (for skeletal meshes).
	 * @param ShotFromDirection The direction from which the shot or attack originated.
	 * @param InstigatedBy The controller responsible for the attack.
	 * @param DamageCauser The actor that caused the damage.
	 * @param HitInfo Additional hit information.
	 * @return The actual amount of damage applied after calculations.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	float TakePointDamage(float Damage, const class UDamageType* DamageType, FVector HitLocation, FVector HitNormal,
		class UPrimitiveComponent* HitComponent, FName BoneName, FVector ShotFromDirection,
		class AController* InstigatedBy, AActor* DamageCauser, const FHitResult& HitInfo);

	/**
	 * * Applies generic damage to the actor.
	 *
	 * Used for non-point-based damage, such as explosions, poison, or area-of-effect (AOE) attacks.
	 *
	 * @param damageReceiver The actor receiving damage.
	 * @param Damage The amount of damage applied.
	 * @param DamageEvent Details of the damage event.
	 * @param EventInstigator The controller responsible for the damage.
	 * @param DamageCauser The actor that caused the damage.
	 * @return The actual amount of damage applied.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	float TakeDamage(AActor* damageReceiver, float Damage, FDamageEvent const& DamageEvent,
		class AController* EventInstigator, class AActor* DamageCauser);

	/**
	 * * Checks whether the actor is still alive.
	 *
	 * @return True if the actor is alive, false if dead.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	bool GetIsAlive() const { return bIsAlive; }

	/**
	 * * Revives the actor, restoring health and resetting any necessary state.
	 *
	 * Can be used for player respawns or reviving AI companions.
	 */
	UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
	void Revive();

	/**
	 * * Gets the combat team of this actor.
	 *
	 * @return The actor's team affiliation.
	 */
	FGameplayTag GetCombatTeam() const;

	/**
	 * * Sets the character's immortality status.
	 *
	 * @param inImmortal True to make the character immortal, false otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	bool GetIsImmortal() const { return bIsImmortal; }

	/**
	 * * Checks if the character is immortal.
	 *
	 * @return True if the character is immortal, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetIsImmortal(bool val) { bIsImmortal = val; }

protected:
	/**
	 * * Called when the game starts or when the component is spawned.
	 */
	virtual void BeginPlay() override;

	UPROPERTY()
	bool bIsImmortal;

	/**
	 * * Determines whether to use a blocking collision channel for damage detection.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	bool bUseBlockingCollisionChannel = false;

	/**
	 * * The class used for calculating damage.
	 *
	 * Determines how damage is processed based on specific game rules.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
	TSubclassOf<UACFDamageCalculation> DamageCalculatorClass;

	/**
	 * * Defines automated responses when the actor is hit.
	 *
	 * Can be used for triggering actions like dodging, parrying, counterattacking, or playing hit animations.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
	TArray<FOnHitActionChances> HitResponseActions;

private:
	/**
	 * * Constructs and processes damage received by this actor.
	 */
	void ConstructDamageReceived(AActor* DamagedActor, float Damage, class AController* InstigatedBy, FVector HitLocation,
		class UPrimitiveComponent* FHitComponent, FName BoneName, FVector ShotFromDirection,
		TSubclassOf<UDamageType> DamageType, AActor* DamageCauser);

	/**
	 * * The instance of the damage calculator used for processing damage.
	 */
	UPROPERTY()
	TObjectPtr<UACFDamageCalculation> DamageCalculator;

	/**
	 * * Stores the last received damage event for reference.
	 */
	UPROPERTY(ReplicatedUsing = OnRep_LastDamageReceived)
	FACFDamageEvent LastDamageReceived;

	UFUNCTION()
	void OnRep_LastDamageReceived();

	/**
	 * * Handles logic when a health stat reaches zero
	 */
	UFUNCTION()
	void HandleStatReachedZero();

	/**
	 * * Tracks whether the actor is currently alive.
	 *
	 * Marked as Savegame and Replicated for persistence across sessions.
	 */
	UPROPERTY(Savegame, ReplicatedUsing = OnRep_IsAlive)
	bool bIsAlive = true;

	UFUNCTION()
	void OnRep_IsAlive();
	/**
	 * * Ensures that initialization is only performed once.
	 */
	bool bInit = false;
};
