// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Interfaces/ACFInteractableInterface.h"

#include "ACFStorage.generated.h"

class UACFInteractableComponent;
class UACFStorageComponent;
class USceneComponent;
class USkeletalMeshComponent;

/**
 * Generic interactable storage actor.
 *
 * Components:
 *  - UStaticMeshComponent          : visual representation of the storage prop
 *  - UACFInteractableComponent     : registers the actor as interactable and triggers
 *                                    the configured ability tag on the interacting pawn
 *  - UACFStorageComponent          : holds the stored items
 *
 * All interface callbacks are exposed as BlueprintNativeEvent so child Blueprints
 * (e.g. ACF_Chest_BP, ACF_Deposit_BP) can override the interaction logic without
 * needing a dedicated C++ subclass.
 */
UCLASS(Blueprintable, ClassGroup = (ACF), meta = (DisplayName = "ACF Storage"))
class CRAFTINGSYSTEM_API AACFStorage : public AActor, public IACFInteractableInterface
{
    GENERATED_BODY()

public:
    AACFStorage();

    // ── IACFInteractableInterface ─────────────────────────────────────────────

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    void OnInteractedByPawn(class APawn* Pawn, const FString& interactionType = "");
    virtual void OnInteractedByPawn_Implementation(class APawn* Pawn, const FString& interactionType = "") override;

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    void OnLocalInteractedByPawn(class APawn* Pawn, const FString& interactionType = "");
    virtual void OnLocalInteractedByPawn_Implementation(class APawn* Pawn, const FString& interactionType = "") override;

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    void OnInteractableRegisteredByPawn(class APawn* Pawn);
    virtual void OnInteractableRegisteredByPawn_Implementation(class APawn* Pawn) override;

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    void OnInteractableUnregisteredByPawn(class APawn* Pawn);
    virtual void OnInteractableUnregisteredByPawn_Implementation(class APawn* Pawn) override;

    // ── Getters ───────────────────────────────────────────────────────────────

    UFUNCTION(BlueprintPure, Category = "ACF|Storage")
    FORCEINLINE UACFStorageComponent* GetStorageComponent() const { return StorageComponent; }

    UFUNCTION(BlueprintPure, Category = "ACF|Storage")
    FORCEINLINE UACFInteractableComponent* GetInteractableComponent() const { return InteractableComponent; }

protected:
    // ── Components ────────────────────────────────────────────────────────────

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<USkeletalMeshComponent> StorageMesh;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<UACFInteractableComponent> InteractableComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<UACFStorageComponent> StorageComponent;


};
