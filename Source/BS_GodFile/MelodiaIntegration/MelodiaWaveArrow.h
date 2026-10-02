#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaWaveArrow.generated.h"
class USphereComponent;
class UStaticMeshComponent;
class UProjectileMovementComponent;
class UNiagaraComponent;
class UMelodiaWaveHarpCombatComponent;

/** A moving collision/visual object. It never calculates or stores damage. */
UCLASS()
class BS_GODFILE_API AMelodiaWaveArrow final : public AActor
{
 GENERATED_BODY()
public:
 AMelodiaWaveArrow();
 void Launch(UMelodiaWaveHarpCombatComponent* Source, const FVector& Direction);
 UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<USphereComponent> Collision;
 UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UStaticMeshComponent> Visual;
 UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UProjectileMovementComponent> Movement;
 UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TObjectPtr<UNiagaraComponent> Trail;
 UPROPERTY(BlueprintReadOnly) bool bConsumed = false;
private:
 UFUNCTION() void HandleHit(UPrimitiveComponent* Component, AActor* Other,
  UPrimitiveComponent* OtherComponent, FVector Impulse, const FHitResult& Hit);
 UFUNCTION() void HandleOverlap(UPrimitiveComponent* Component, AActor* Other,
  UPrimitiveComponent* OtherComponent, int32 BodyIndex, bool bFromSweep, const FHitResult& Hit);
 void Consume(AActor* Other);
 TWeakObjectPtr<UMelodiaWaveHarpCombatComponent> Shooter;
};
