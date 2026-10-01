// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFActionTypes.h"
#include "ACFRiderComponent.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include <GameplayTagContainer.h>

#include "ACFMountableComponent.generated.h"

class ACharacter;
class APawn;
class UACFMountPointComponent;

// Delegate that broadcasts when the mount state changes.
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnMountedStateChanged, bool, inIsMounted);

/**
 * Component that allows an actor to be mountable by a character.
 * Handles mounting logic
 */
UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent))
class MOUNTSYSTEM_API UACFMountableComponent : public UActorComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UACFMountableComponent();

    /**
     * Returns the pawn that owns this component.
     *
     * @return The APawn that owns this component.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE class APawn* GetPawnOwner() const
    {
        return pawnOwner;
    }

    /**
     * Begins the mount process with the given rider.
     *
     * @param inRider The character attempting to mount this actor.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void StartMount(class ACharacter* inRider);

    /**
     * Stops the mounting process and dismounts the rider.
     * Executed on the server.
     *
     * @param dismountPoint Optional socket name to use as dismount location.
     */
    UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
    void StopMount(FName dismountPoint = NAME_None);

    /**
     * Triggers an action on the rider while mounted.
     *
     * @param ActionState The tag identifying the action to trigger.
     * @param Priority The priority of the action.
     * @param bCanBeStored Whether the action can be stored if not executable immediately.
     */
    UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
    void TriggerActionOnRider(FGameplayTag ActionState, EActionPriority Priority = EActionPriority::ELow, bool bCanBeStored = false);

    /**
     * Releases a previously triggered sustained action on the rider.
     *
     * @param actionTag The tag identifying the sustained action to release.
     */
    UFUNCTION(BlueprintCallable,  Server, Reliable, Category = ACF)
    void ReleaseSustainedActionOnRider(FGameplayTag actionTag);

    /**
     * Returns the name of the socket used as the mount point.
     *
     * @return The name of the socket to attach the rider.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FName GetMountPoint() const
    {
        return MountPointSocket;
    }

    /**
     * Returns the world-space transform of the mount point socket used for attaching the rider.
     *
     * @return The transform of the mount point socket if valid, otherwise the owner's transform.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FTransform GetMountPointTransform() const;

    /**
     * Returns the dismount point component associated with a given socket/tag name.
     *
     * @param dismountPoint The name of the dismount point to retrieve (optional).
     * @return A pointer to the UACFMountPointComponent matching the given name, or nullptr.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    class UACFMountPointComponent* GetDismountPoint(const FName& dismountPoint = NAME_None) const;

    /**
     * Returns the mesh component used for attaching the rider.
     * Uses the override if set, otherwise attempts to infer from the owner.
     *
     * @return A pointer to the mesh component to use for mounting.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    UMeshComponent* GetMountMesh() const;

    /**
     * Sets a custom mesh component to be used as the rider attachment point.
     *
     * @param inMountMeshOverride The mesh to use for mounting instead of the default.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetMountMesh(UMeshComponent* inMountMeshOverride)
    {
        mountMeshOverride = inMountMeshOverride;
    }

    /**
     * Returns whether this actor is currently mounted by a rider.
     *
     * @return True if mounted, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE bool IsMounted() const
    {
        return bIsMounted;
    }

    /**
     * Returns the gameplay tag representing the type of this mount.
     *
     * @return The mount type tag.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FGameplayTag GetMountTag() const
    {
        return MountTypeTag;
    }

    /**
     * Returns the action tag associated with mounting this actor.
     *
     * @return The gameplay tag used for the mount action.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FGameplayTag GetMountActionTag() const
    {
        return MountActionTag;
    }

    /**
     * Returns the character currently mounted on this actor.
     *
     * @return The character riding this actor, or nullptr if none.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE class ACharacter* GetRider() const
    {
        return rider;
    }

    /**
     * Returns the owning pawn of this mount.
     *
     * @return The pawn that owns this mount component.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE class APawn* GetMountOwner() const
    {
        return GetPawnOwner();
    }

    /**
     * Returns whether the rider needs to possess the mount pawn when mounting.
     *
     * @return True if possession is required, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE bool NeedsPossession() const
    {
        return bPossessMount;
    }

    /**
     * Checks whether this mount is currently available for mounting.
     *
     * @return True if no rider is currently assigned.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE bool CanBeMounted() const
    {
        return !rider;
    }

    /**
     * Returns the team of the mount's owner, used for faction or AI logic.
     *
     * @return The team this mount belongs to.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FGameplayTag GetOwnerTeam() const;

    /**
     * Finds the closest socket or tag name of a mount point to the given world location.
     *
     * @param location The world-space location to compare.
     * @return The name of the nearest mount point socket.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    FName GetNearestMountPointTag(const FVector& location) const;

    /**
     * Finds the closest UACFMountPointComponent to the given world location.
     *
     * @param location The world-space location to compare.
     * @return The nearest mount point component, or nullptr if none found.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    UACFMountPointComponent* GetNearestMountPoint(const FVector& location) const;

    /**
     * Delegate called whenever the mounted state changes.
     */
    UPROPERTY(BlueprintAssignable, Category = "ACF")
    FOnMountedStateChanged OnMountedStateChanged;

protected:
    // Whether the actor is currently mounted by a rider (replicated and saved).
    UPROPERTY(SaveGame, Replicated, ReplicatedUsing = OnRep_IsMounted)
    bool bIsMounted = false;

    // Gameplay tag defining the type of mount (e.g., horse, vehicle).
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    FGameplayTag MountTypeTag;

    // Action tag used to trigger the mount animation or state.
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    FGameplayTag MountActionTag;

    // Name of the socket where the rider is attached when mounting.
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    FName MountPointSocket;

    // Default socket used for dismounting if no custom point is specified.
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    FName DefaultDismountPoint;

    // If true, the rider will take possession of the mount pawn.
    UPROPERTY(EditAnywhere, Category = ACF)
    bool bPossessMount = true;

    // Sets the internal mount state and handles side effects.
    virtual void SetMounted(bool inMounted);

    // Sets the current rider reference internally.
    void SetRider(ACharacter* inRider)
    {
        rider = inRider;
    }

    // The character currently riding this actor (replicated).
    UPROPERTY(Replicated)
    ACharacter* rider;

    friend UACFRiderComponent;

protected:
    // Called when the game starts
    virtual void BeginPlay() override;

private:
    UFUNCTION()
    void OnRep_IsMounted();

private:
    TObjectPtr<APawn> pawnOwner;

    TObjectPtr<UMeshComponent> mountMeshOverride;
};
