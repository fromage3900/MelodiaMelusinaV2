// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include <GameFramework/Character.h>
#include <GameplayTagContainer.h>

#include "ACFRiderComponent.generated.h"

/* Delegate that broadcasts when the riding state changes.*/
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnRidingStateChanged, bool, bIsRiding);

/* ACFRiderComponent is responsible for managing riding mechanics within the ACF system.
 It allows characters to mount and dismount from rideable entities*/
UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent))
class MOUNTSYSTEM_API UACFRiderComponent : public UActorComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UACFRiderComponent();

    /**
     * Event triggered when the riding state changes (e.g., mount or dismount).
     *
     * Listeners can bind to this event in Blueprints to react when the character mounts or dismounts.
     */
    UPROPERTY(BlueprintAssignable)
    FOnRidingStateChanged OnRidingStateChanged;

    /**
     * Checks if the character is currently riding a mount.
     *
     * @return true if the character is mounted, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = "ACF|Rider")
    FORCEINLINE bool IsRiding() const { return bIsRiding; }

    /**
     * Initiates the mounting process. Runs on the server to ensure proper network replication.
     *
     * @param mount The mountable component to be mounted.
     */
    UFUNCTION(Server, Reliable, WithValidation, BlueprintCallable, Category = "ACF|Rider")
    void StartMount(class UACFMountableComponent* mount);

    /**
     * Initiates the dismounting process. Runs on the server for proper synchronization.
     *
     * @param dismountPoint (Optional) The location where the character should dismount. Defaults to NAME_None.
     */
    UFUNCTION(Server, Reliable, WithValidation, BlueprintCallable, Category = "ACF|Rider")
    void StartDismount(const FName& dismountPoint = NAME_None);

    /**
     * Retrieves the Pawn (character or entity) currently being ridden.
     *
     * @return A pointer to the APawn currently being used as a mount.
     */
    UFUNCTION(BlueprintPure, Category = "ACF|Rider")
    class APawn* GetMount() const;

    /**
     * Retrieves the mountable component associated with the current mount.
     *
     * @return A pointer to the UACFMountableComponent of the current mount.
     */
    UFUNCTION(BlueprintPure, Category = "ACF|Rider")
    class UACFMountableComponent* GetMountComp() const
    {
        return Mount;
    }

    /**
     * Retrieves the gameplay tag representing the type of mount being ridden.
     *
     * @return The FGameplayTag that identifies the mount type.
     */
    UFUNCTION(BlueprintPure, Category = "ACF|Rider")
    FGameplayTag GetMountTypeTag() const;

    UFUNCTION(BlueprintPure, Category = "ACF|Rider")
    ACharacter* GetCharacterOwner() const;

    void SetCharacterOwner(TObjectPtr<ACharacter> val) { charOwner = val; }

protected:
    // Called when the game starts
    virtual void BeginPlay() override;

    UPROPERTY(SaveGame, Replicated, ReplicatedUsing = OnRep_IsRiding)
    bool bIsRiding = false;

private:
    void HandlePossession();
    void FinishDismount(const FName& dismountPoint = NAME_None);

    void Internal_DetachFromMount();

    UFUNCTION()
    void OnRep_Mount();

    UPROPERTY(ReplicatedUsing = OnRep_Mount)
    TObjectPtr<UACFMountableComponent> Mount;

    TObjectPtr<class UACFGroupAIComponent> groupOwner;

    UPROPERTY()
    TObjectPtr<ACharacter> charOwner;

    UFUNCTION()
    void OnRep_IsRiding();

    void Internal_Ride(bool inIsRiding);

    void Internal_AttachToMount();

    void Internal_Mount();

    void Internal_SetMountCollisionsEnabled(const bool bMounted);
};
