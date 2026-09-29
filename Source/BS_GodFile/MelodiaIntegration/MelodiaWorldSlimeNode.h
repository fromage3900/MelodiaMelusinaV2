// Hybrid-combat spike: world-resolved slime node (sandbox only).
//
// WORLD_PROJECTED_TURNS shape (Jev-live): the trigger/HP/death/respawn loop is
// real; the damage NUMBER is a documented stub (SpikeScalarStub) standing in
// for the stock skill/grade scalar until the STOCK_BRIDGE lands. Do not ship
// this scalar — the bridge replaces it with UseSkillWithRhythm output.
// Stock keeps owning damage numbers; this actor only owns HP location.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaWorldSlimeNode.generated.h"

class UStaticMeshComponent;
class USphereComponent;

/**
 * One-hit world slime node for the hybrid spike. Lives in sandbox maps only
 * (MelodiaIntegrationMap). Overlap with the player resolves a world hit in
 * place — no scene change, no battle map. Death hides the node and respawns
 * on a timer; kills are counted for proof reads.
 */
UCLASS(Blueprintable)
class BS_GODFILE_API AMelodiaWorldSlimeNode : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaWorldSlimeNode();

	/** Slime body. Mesh is assigned in the BP child (sandbox presentation). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|HybridSpike")
	TObjectPtr<UStaticMeshComponent> SlimeMesh = nullptr;

	/** Contact volume that resolves the world hit. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|HybridSpike")
	TObjectPtr<USphereComponent> HitVolume = nullptr;

	/** HP owned by the world actor (location), not by battle units. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|HybridSpike")
	float MaxHP = 25.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|HybridSpike")
	float CurrentHP = 25.0f;

	/** DOCUMENTED STUB: stands in for the stock skill/grade scalar. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|HybridSpike")
	float SpikeScalarStub = 1.0f;

	/** Base world-hit damage before the scalar. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|HybridSpike")
	float SpikeBaseDamage = 25.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|HybridSpike")
	float RespawnSeconds = 10.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|HybridSpike")
	bool bIsDead = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|HybridSpike")
	int32 KillCount = 0;

	/** Bridge entry point: applies FinalDamage the way the stock bridge will. */
	UFUNCTION(BlueprintCallable, Category="Melodia|HybridSpike")
	void ApplyWorldDamage(float FinalDamage);

	/** Contact resolve: one hit at the stubbed scalar (spike behavior). */
	UFUNCTION(BlueprintCallable, Category="Melodia|HybridSpike")
	void ResolveContactHit();

protected:
	virtual void BeginPlay() override;

	UFUNCTION()
	void OnHitOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

private:
	void Die();
	void Respawn();

	FTimerHandle RespawnTimer;
};
