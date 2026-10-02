// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFEquipmentComponent.h"
#include "ACFItemTypes.h"
#include "ACMTypes.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "Items/ACFWeapon.h"
#include <Components/MeshComponent.h>

#include "ACFShootingComponent.generated.h"

struct FImpactFX;
/**
 * Called when the current ammo in magazine or total ammo changes.
 *
 * @param currentAmmoInMagazine Current number of bullets in the magazine.
 * @param totalAmmo Total number of bullets available including reserve.
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnCurrentAmmoChanged, int32, currentAmmoInMagazine, int32, totalMagazineSize);

/**
 * Called when a shot is fired.
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnShoot);

/**
 * Atomic snapshot of the ammo state. Magazine and total are replicated together
 * inside a single property so clients always observe a consistent pair, instead
 * of recomputing the total from the equipment/inventory (which replicate on a
 * different component and can race with the magazine value).
 */
USTRUCT(BlueprintType)
struct FACFAmmoState {
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    int32 MagazineAmmo = 0;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    int32 TotalAmmo = 0;
};

/**
 * Component that handles shooting logic, ammo management, and shooting-related events.
 */
UCLASS(Blueprintable, ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class INVENTORYSYSTEM_API UACFShootingComponent : public UActorComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UACFShootingComponent();

    /**
     * Removes one ammo from the current magazine.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void RemoveAmmo(int32 count = 1);

    /**
     * Initializes the shooting component on the server, associating it with an owner Pawn and a shooting mesh.
     *
     * @param inOwner The Pawn that owns this shooting component.
     * @param inMesh The mesh component used for shooting.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetupShootingComponent(class APawn* inOwner, class UMeshComponent* inMesh);

    /**
     * Reinitializes the shooting component with a new owner, mesh, start socket, and shooting effects.
     *
     * @param inOwner The new owner Pawn.
     * @param inMesh The mesh used for shooting.
     * @param inStartSocket The name of the socket from which projectiles are fired.
     * @param inShootingFX The visual effect to play when shooting.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void ReinitializeShootingComponent(class APawn* inOwner, class UMeshComponent* inMesh, FName inStartSocket)
    {
        shootingMesh = inMesh;
        characterOwner = inOwner;
        ProjectileStartSocket = inStartSocket;
    }

    /**
     * Returns the projectile speed.
     *
     * @return The speed at which projectiles are fired.
   
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE float GetProjectileSpeed() const { return ProjectileShotSpeed; }  */

    /**
     * Fires a projectile at a specified target with optional deviation, charge, and projectile override.
     *
     * @param target The actor to shoot at.
     * @param randomDeviation The angle deviation applied to the shot.
     * @param charge The charge multiplier affecting the shot.
     * @param projectileOverride Optionally override the default projectile class.
     * @param socketOverride Optionally override the socket used for firing.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void ShootAtActor(const AActor* target, float randomDeviation = 5.f, float charge = 1.f, TSubclassOf<class UACFProjectile> projectileOverride = nullptr, const FName socketOverride = NAME_None);

    /**
     * Fires a projectile in a specific direction with optional charge and projectile override.
     *
     * @param direction The direction to fire towards.
     * @param charge The charge multiplier affecting the shot.
     * @param projectileOverride Optionally override the default projectile class.
     * @param socketOverride Optionally override the socket used for firing.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void ShootAtDirection(const FRotator& direction, float charge = 1.f, TSubclassOf<class UACFProjectile> projectileOverride = nullptr, const FName socketOverride = NAME_None);

    /**
     * Shoots a projectile based on shooting type and target type.
     *
     * @param SourcePawn The pawn initiating the shot.
     * @param type The type of shooting logic to apply.
     * @param targetType The type of target to aim at.
     * @param charge The charge multiplier affecting the shot.
     * @param projectileOverride Optionally override the default projectile class.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void Shoot(APawn* SourcePawn, EShootingType type, EShootTargetType targetType, float charge = 1.f, TSubclassOf<class UACFProjectile> projectileOverride = nullptr);

    /**
     * Fires a projectile at a specified target with optional deviation, charge, and projectile override.
     *
     * @param target The actor to shoot at.
     * @param randomDeviation The angle deviation applied to the shot.
     * @param outResult the hitresult of the swipe trace
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    bool SwipeTraceShootAtActor(const AActor* target, FHitResult& outResult, float randomDeviation = 5.f, float swipeRadius = 1.f);

    /**
     * Performs a swipe trace shooting action in a given direction with a delay.
     *
     * @param start The start location of the trace.
     * @param targetType how to calculate the direction to perform the trace
     * @param outResult the hitresult of the swipe trace
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    bool SwipeTraceShoot(APawn* SourcePawn, EShootTargetType targetType, FHitResult& outResult, float swipeRadius = 1.f);

    /**
     * Performs a swipe trace shooting action in a given direction with a delay.
     *
     * @param start The start location of the trace.
     * @param direction The direction in which to perform the trace.
     * @param outResult the hitresult of the swipe trace
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    bool SwipeTraceShootAtDirection(const FVector& start, const FVector& direction, FHitResult& outResult, float swipeRadius = 1.f);

    /**
     * Reduces the ammo magazine count by a specified amount.
     *
     * @param amount The number of bullets to remove from the magazine.
     */
    UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
    void ReduceAmmoMagazine(int32 amount = 1);

    /**
     * Reloads the weapon, refilling the magazine.
     * If bTryToEquipAmmo is true, it will attempt to equip ammo from inventory.
     *
     * @param bTryToEquipAmmo Whether to try equipping ammo from inventory.
     */
    UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
    void Reload(bool bTryToEquipAmmo = true);

    /**
     * Attempts to equip ammo from the inventory.
     *
     * @return True if ammo was successfully equipped, false otherwise.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    bool TryEquipAmmoFromInventory();

    /**
     * Checks if the weapon can shoot.
     *
     * @return True if shooting is currently allowed.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool CanShoot() const;

    /**
     * Checks if the specified projectile type can be used.
     *
     * @param projectileClass The projectile class to check.
     * @return True if the projectile is allowed.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool CanUseProjectile(const TSubclassOf<UACFProjectile>& projectileClass) const;

    /**
     * Checks if the weapon needs a reload.
     *
     * @return True if the magazine is empty or partially empty and ammo is available.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool NeedsReload() const;

    /**
     * Checks if the magazine is full.
     *
     * @return True if the magazine is at full capacity.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool IsFullMagazine() const
    {
        return currentMagazine == AmmoMagazine;
    }

    /**
     * Attempts to retrieve an allowed ammo type from the inventory.
     *
     * @param outAmmoSlot The inventory item slot to be filled with valid ammo.
     * @return True if a compatible ammo was found.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool TryGetAllowedAmmoFromInventory(FInventoryItem& outAmmoSlot) const;

    /**
     * Returns the world position of the shooting socket.
     *
     * @return The world location of the projectile start socket.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FVector GetShootingSocketPosition() const
    {
        return shootingMesh->GetSocketLocation(ProjectileStartSocket);
    }

    /**
     * Returns the name of the socket from which projectiles are fired.
     *
     * @return The socket name used to spawn projectiles.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FName GetProjectileStartSocketName() const
    {
        return ProjectileStartSocket;
    }

    /**
     * Sets the socket name from which projectiles should be fired.
     *
     * @param newSocket The new socket name to use.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetProjectileStartSocketName(FName newSocket)
    {
        ProjectileStartSocket = newSocket;
    }

    /**
     * Returns the mesh component associated with shooting.
     *
     * @return The mesh component used for shooting logic.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE UMeshComponent* GetShootingMesh() const
    {
        return shootingMesh;
    }

    /**
     * Returns the list of allowed projectile types.
     *
     * @return An array of projectile classes allowed for use.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE TArray<TSubclassOf<UACFProjectile>> GetAllowedProjectiles() const
    {
        return AllowedProjectiles;
    }

    /**
     * Returns the total magazine capacity.
     *
     * @return The maximum number of bullets the magazine can hold.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE int32 GetAmmoMagazine() const
    {
        return AmmoMagazine;
    }

    /**
     * Returns the total count of equipped ammo.
     *
     * @return The number of bullets currently equipped (excluding magazine).
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    int32 GetTotalEquippedAmmoCount() const;

    /**
     * Returns the current amount of ammo in the magazine.
     *
     * @return The number of bullets currently loaded in the magazine.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE int32 GetCurrentAmmoInMagazine() const
    {
        return currentMagazine;
    }

    /**
     * Returns the total ammo count available (including in magazine and inventory).
     *
     * @return The total amount of usable ammo.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    int32 GetTotalAmmoCount() const;

    /**
     * Checks whether the weapon uses a magazine system.
     *
     * @return True if the magazine system is enabled.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool GetUseMagazine() const { return bUseMagazine; }

    /**
     * Attempts to retrieve an ammo slot from equipped items.
     *
     * @param outSlot The equipped item slot that will contain the ammo if found.
     * @return True if an ammo slot was successfully retrieved.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool TryGetAmmoSlot(FEquippedItem& outSlot) const;

    /**
     * Attempts to retrieve an ammo slot from the inventory.
     *
     * @param outSlot The item slot that will contain the ammo if found.
     * @return True if an ammo slot was successfully retrieved.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool TryGetAmmoInventorySlot(FInventoryItem& outSlot) const;

    /**
     * Enables or disables the magazine system.
     *
     * @param val Set to true to enable the magazine system, false to disable it.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetUseMagazine(bool val) { bUseMagazine = val; }

    /* Delegate triggered when the current ammo count changes */
    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnCurrentAmmoChanged OnCurrentAmmoChanged;

    /* Delegate triggered when a projectile is shot */
    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnShoot OnProjectileShoot;

protected:
    // Called when the game starts
    virtual void BeginPlay() override;

    /*Socket in the provided mesh the projectile starts from*/
    UPROPERTY(EditAnywhere, Category = "ACF")
    FName ProjectileStartSocket = "ProjectileStart";

    /*If shooting should check for Ammos*/
    UPROPERTY(EditDefaultsOnly, Category = "ACF|Ammo")
    bool bConsumeAmmo = true;

    /*The equipment slot that will be checked to consume Ammos when shooting*/
    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = "bConsumeAmmo"), Category = "ACF|Ammo")
    FGameplayTag AmmoSlot;

    /*Projectiles allowed to be used with this component*/
    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = "bConsumeAmmo"), Category = "ACF|Ammo")
    TArray<TSubclassOf<class UACFProjectile>> AllowedProjectiles;

    /*If this is set to true means that this weapon will need to be Reload every time his ammo in
    magazine are 0 to continue shooting. */
    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = "bConsumeAmmo"), Category = "ACF|Ammo")
    bool bUseMagazine = false;

    /*The number of projectile to be shot before reloading*/
    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = "bUseMagazine"), Category = "ACF|Ammo")
    int32 AmmoMagazine = 10;

    /*The default projectile class to be shot*/
    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = "bConsumeAmmo == false"), Category = "ACF|Ammo")
    TSubclassOf<class UACFProjectile> ProjectileClassBP;

    /*Distance at which the trace is done*/
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "ACF|SwipeTrace Shoot Config")
    float ShootRange = 3500.f;

private:
    UPROPERTY()
    TObjectPtr<UMeshComponent> shootingMesh;

    UPROPERTY(Replicated)
    TObjectPtr<APawn> characterOwner;

    /** Server-side working value of the current magazine. On clients it is kept
     *  in sync from the replicated AmmoState snapshot (see OnRep_AmmoState). */
    int32 currentMagazine = 0;

    /** Magazine + total ammo replicated together as one atomic snapshot, so the
     *  client never reads a half-updated state across two components. */
    UPROPERTY(ReplicatedUsing = OnRep_AmmoState)
    FACFAmmoState AmmoState;

    UFUNCTION()
    void OnRep_AmmoState();

    /** Authority only: rebuild the replicated AmmoState from the current
     *  magazine and the inventory total, then broadcast locally (listen server). */
    void UpdateAmmoState();

    void Internal_Shoot(const FTransform& spawnTransform, const FVector& ShotDirection, float charge, TSubclassOf<class UACFProjectile> inProjClass);

    UFUNCTION(NetMulticast, Reliable)
    void Internal_SetupComponent(class APawn* inOwner, class UMeshComponent* inMesh);

    class UACFEquipmentComponent* TryGetEquipment() const;

    TSubclassOf<UACFItem> GetBestProjectileToShoot() const;
};
