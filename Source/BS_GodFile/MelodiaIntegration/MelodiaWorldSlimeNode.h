#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaHybridEncounterComponent.h"
#include "MelodiaWorldSlimeNode.generated.h"

class APawn;
class UMaterialInstanceDynamic;
class UNiagaraComponent;
class UNiagaraSystem;
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

	/** Existing stock authored stat/skill definitions. Defaults are stat views;
	 * no unit is spawned and their HP is never used as encounter state. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Hybrid|Stock")
	TSubclassOf<AActor> StockAttackerDefinition;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Hybrid|Stock")
	TSubclassOf<AActor> StockDefenderDefinition;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Hybrid|Stock")
	TSubclassOf<AActor> StockSkillDefinition;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Hybrid|Stock", meta=(ClampMin="0"))
	int32 StockPureDamage = 0;

	/** Ring held around the target while its figure is locked. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Hybrid|FX")
	TSoftObjectPtr<UNiagaraSystem> LockSystem = TSoftObjectPtr<UNiagaraSystem>(FSoftObjectPath(TEXT("/Game/Melodia/VFX/NS_Melusina_Sigil.NS_Melusina_Sigil")));

	/** Played once as a phrase opens. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Hybrid|FX")
	TSoftObjectPtr<UNiagaraSystem> SequenceSystem = TSoftObjectPtr<UNiagaraSystem>(FSoftObjectPath(TEXT("/Game/Melodia/VFX/NS_Melusina_StarPop.NS_Melusina_StarPop")));

	/** The FLIP splash, once per phrase, when the figure is released back into Flow. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Hybrid|FX")
	TSoftObjectPtr<UNiagaraSystem> ReleaseSystem = TSoftObjectPtr<UNiagaraSystem>(FSoftObjectPath(TEXT("/Game/Melodia/VFX/NS_Melusina_Splash.NS_Melusina_Splash")));

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

	/** The Chladni figure clears as Flow tunes the target and rings at lock. */
	UFUNCTION()
	void HandleResonanceChanged(float ResonanceNormalized, bool bLocked);

	UFUNCTION()
	void HandlePresentationModeChanged(EMelodiaHybridPresentationMode Mode, AActor* Target);

	void PlayOnce(const TSoftObjectPtr<UNiagaraSystem>& System) const;

	UPROPERTY(Transient)
	TObjectPtr<UNiagaraComponent> LockFx;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> ResonanceMaterial;

	/** The material's authored ChladniIntensity, reached at lock. */
	float LockedChladniIntensity = 0.0f;
};
