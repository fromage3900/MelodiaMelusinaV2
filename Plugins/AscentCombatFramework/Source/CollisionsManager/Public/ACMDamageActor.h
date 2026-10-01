// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACMCollisionManagerComponent.h"
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "ACMDamageActor.generated.h"

UCLASS(BlueprintType, Blueprintable, Category = ACM)
class COLLISIONSMANAGER_API AACMDamageActor : public AActor {
    GENERATED_BODY()

public:
    // Sets default values for this actor's properties
    AACMDamageActor();

    UPROPERTY(BlueprintAssignable, Category = ACM)
    FOnActorDamaged OnActorDamaged;

    UFUNCTION(BlueprintCallable, Category = ACM)
    void SetupCollisions(AActor* inOwner);

    UFUNCTION(BlueprintPure, Category = ACM)
    AActor* GetActorOwner() const
    {
        return ActorOwner;
    }

    UFUNCTION(BlueprintCallable, Category = ACM)
    void StartDamageTraces();

    UFUNCTION(BlueprintCallable, Category = ACM)
    void StopDamageTraces();

    UFUNCTION(BlueprintCallable, Category = ACM)
    void StartAreaDamage(float radius = 100.f, float damageInterval = 1.5f);

    UFUNCTION(BlueprintCallable, Category = ACM)
    void StopAreaDamage();

    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE class UACMCollisionManagerComponent* GetCollisionsComponent() const { return CollisionComp; }

    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE class UInterpToMovementComponent* GetMovementComponent() const { return MovementComp; }

    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE class UMeshComponent* GetMesh() const { return MeshComp; }

protected:
    UFUNCTION(BlueprintNativeEvent, Category = ACM)
    void OnSetup(AActor* new0wner);
    virtual void OnSetup_Implementation(AActor* new0wner);

    // Called when the game starts or when spawned
    virtual void BeginPlay() override;

    virtual void EndPlay(EEndPlayReason::Type end) override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, DisplayName = "Mesh Component", Category = ACF)
    TObjectPtr<class UMeshComponent> MeshComp;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, DisplayName = "ACF Collisions ManagerComp", Category = ACF)
    TObjectPtr<class UACMCollisionManagerComponent> CollisionComp;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, DisplayName = "Movement Comp", Category = ACF)
    TObjectPtr<class UInterpToMovementComponent> MovementComp;

    UPROPERTY(BlueprintReadWrite, Category = ACM, meta = (ExposeOnSpawn = true))
    AActor* ActorOwner;

private:
    UFUNCTION()
    void HandleDamagedActor(AActor* damagedActor);
};
