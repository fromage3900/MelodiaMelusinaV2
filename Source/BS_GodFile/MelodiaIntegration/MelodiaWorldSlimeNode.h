#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaWorldSlimeNode.generated.h"

class APawn;
class UMelodiaHybridEncounterComponent;
class USphereComponent;
class UStaticMeshComponent;

/**
 * One sandbox target for Flow and Sequence. This actor owns one HP value and
 * remains in the world across presentation changes. Damage arrives only as an
 * already resolved final value; it contains no stock or rhythm damage math.
 */
UCLASS(Blueprintable)
class BS_GODFILE_API AMelodiaWorldSlimeNode : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaWorldSlimeNode();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Hybrid")
	TObjectPtr<UStaticMeshComponent> SlimeMesh;

	/** Proximity/targeting only. Overlap never applies damage. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Hybrid")
	TObjectPtr<USphereComponent> HitVolume;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Hybrid")
	TObjectPtr<UMelodiaHybridEncounterComponent> HybridEncounter;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Hybrid", meta=(ClampMin="1.0"))
	float MaxHP = 25.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Hybrid")
	float CurrentHP = 25.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Hybrid")
	bool bIsDead = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Hybrid")
	int32 KillCount = 0;

	UFUNCTION(BlueprintPure, Category="Melodia|Hybrid")
	bool IsPlayerInTargetRange(const APawn* PlayerPawn) const;

	/** Sink for a final number supplied by the stock resolver. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Hybrid")
	void ApplyWorldDamage(float FinalDamage);

	virtual float TakeDamage(float DamageAmount, struct FDamageEvent const& DamageEvent,
		class AController* EventInstigator, AActor* DamageCauser) override;

protected:
	virtual void BeginPlay() override;

private:
	void Die();
};
