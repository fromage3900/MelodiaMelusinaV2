// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved

#pragma once



#include "CoreMinimal.h"
#include "Interfaces/ACFInteractableInterface.h"
#include "ItemActors/ACFEquippableActor.h"
#include "Items/ACFProjectile.h"
#include <Components/StaticMeshComponent.h>

#include "ACFProjectileActor.generated.h"

class UACFProjectile;
class UStaticMesh;

/**
 *
 */
UCLASS()
class INVENTORYSYSTEM_API AACFProjectileActor : public AACFEquippableActor, public IACFInteractableInterface {
    GENERATED_BODY()

public:
    AACFProjectileActor();
    /**
     * Returns the projectile movement component used to simulate the projectile's physics.
     * @return Pointer to UProjectileMovementComponent
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE class UProjectileMovementComponent* GetProjectileMovementComp()
    {
        return ProjectileMovementComp;
    }

    /**
     * Gets the static mesh asset used by the projectile.
     * @return Pointer to UStaticMesh
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE class UStaticMesh* GetStaticMesh() { return MeshComp->GetStaticMesh(); }

    /**
     * Gets the static mesh component of the projectile.
     * @return Pointer to UStaticMeshComponent
     */
    FORCEINLINE class UStaticMeshComponent* GetMeshComponent() const { return MeshComp; }

    /**
     * Gets the collision manager component used for hit detection and response.
     * @return Pointer to UACMCollisionManagerComponent
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE class UACMCollisionManagerComponent* GetCollisionComp() const { return CollisionComp; }

    /**
     * Checks whether this projectile should be dropped upon the owner's death.
     * @return True if droppable, false otherwise
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE bool ShouldBeDroppedOnDeath() const
    {
        return bDroppableWhenAttached;
    }

    /**
     * Returns the chance (0–100) that the projectile will be dropped on death.
     * @return Drop percentage value
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE float GetDropOnDeathPercentage() const
    {
        return DropRatePercentage;
    }

    /**
     * Initializes the projectile with the owning pawn. Typically called before firing.
     * @param inOwner The pawn who owns and fires the projectile
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetupProjectile(class APawn* inOwner);

    /**
     * Activates the projectile's damage logic, enabling hit registration.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void ActivateDamage();

    /**
     * Attaches the projectile to a hit surface, optionally marking it as pickable.
     * @param HitResult The result of the hit that caused the attachment
     * @param inPickable Whether the projectile should be pickable after attachment
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void AttachToHit(const FHitResult& HitResult, bool inPickable);

    UFUNCTION(BlueprintPure, Category = ACF)
    UACFProjectile* GetProjectileDefinition() const
    {
        return Cast<UACFProjectile>(GetItemDefinition());
    }

    virtual void InitItemActor(APawn* inOwner, UACFItem* inItemDefinition) override;

protected:
    // Called when the game starts or when spawned
    virtual void BeginPlay() override;

    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category = "ACF|Projectile")
    float ProjectileLifespan = 5.f;

    /* If this projectile must destroy itself on hit or attach to the actor hit*/
    UPROPERTY(EditDefaultsOnly, Category = "ACF|Projectile")
    EProjectileHitPolicy HitPolicy;

    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = "HitPolicy == EProjectileHitPolicy::DestroyOnHit"), Category = "ACF|Projectile")
    FImpactFX ImpactEffect;

    UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, meta = (EditCondition = "HitPolicy == EProjectileHitPolicy::AttachOnHit"), Category = "ACF|Projectile")
    float AttachedLifespan = 10.f;

    /* If this is set to true when this projectile is attached to an acfcharacter and
    this character dies, the projectile can be dropped as world item*/
    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = "HitPolicy == EProjectileHitPolicy::AttachOnHit"), Category = "ACF|Projectile")
    bool bDroppableWhenAttached = true;

    /* When attached to an adversary, the chance that this item will be dropped when it dies*/
    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = "HitPolicy == EProjectileHitPolicy::AttachOnHit"), Category = "ACF|Projectile")
    float DropRatePercentage = 100.f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
    TObjectPtr<class USphereComponent> SphereComp;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
    TObjectPtr<class UStaticMeshComponent> MeshComp;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
    TObjectPtr<class UProjectileMovementComponent> ProjectileMovementComp;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
    TObjectPtr<class UACMCollisionManagerComponent> CollisionComp;

    // INTERACTION INTERFACE
    /* called when player interact with object of this class */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    void OnInteractedByPawn(class APawn* Pawn, const FString& interactionType = "");

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    bool CanBeInteracted(class APawn* Pawn);

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    FText GetInteractableName();
    // END INTERACTION INTERFACE

    virtual void OnRep_ItemOwner() override;
private:
    UPROPERTY(Replicated)
    bool bIsFlying;

    UPROPERTY(Replicated)
    bool bPickable;

    UPROPERTY(ReplicatedUsing = OnRep_ProjDefinitionClass)
    TSubclassOf<UACFItem> projDefinitionClass;

    UFUNCTION()
    void OnRep_ProjDefinitionClass();

    UFUNCTION()
    void HandleAttackHit(const FHitResult& HitResult);

    UFUNCTION()
    void HandleProjectileHit(UPrimitiveComponent* HitComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, FVector NormalImpulse, const FHitResult& Hit);

    
    void MakeStatic();
    void PlayImpact(const FHitResult& HitResult);

    bool bImpacted = false;
};
