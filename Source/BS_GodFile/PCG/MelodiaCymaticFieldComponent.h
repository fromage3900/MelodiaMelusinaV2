#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaCymaticFieldComponent.generated.h"

class UInstancedStaticMeshComponent;

/**
 * Cymatic field -> geometry. Lifts and pulses instanced meshes (PCG output) with the Chladni standing wave
 * and expanding "hit" ripples. Presentation only: it never writes an MPC and never owns audio.
 *
 * Reads the shared field from UWorldFieldBus (published by UMelodiaCymaticsSubsystem from the palette),
 * so it follows OSC/TD audio when the bridge is live and the C++ beat/combat values otherwise.
 *
 * Place on a trigger/volume actor. Which meshes react:
 *   - instanced mesh components (or their actor) tagged ReactiveTag -- for PCG, add the tag to the
 *     Static Mesh Spawner's ISM descriptor ComponentTags -- or every ISM inside ReactRadius when
 *     bReactToAllInstancedMeshes is set.
 * A hit is a ripple from a world point: a Pawn overlapping the owner, a beat edge (bHitOnBeat), or TriggerHit().
 * Each hit also resolves a Great command on UMelodiaRhythmReactivitySubsystem so materials, flowers and the
 * ocean pulse and TD receives the beat out over OSC (the same path the piano keys use).
 */
UCLASS(ClassGroup = (Melodia), meta = (BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaCymaticFieldComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaCymaticFieldComponent();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** Start a ripple at a world position. Strength 0..1. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Cymatics")
	void TriggerHit(FVector WorldOrigin, float Strength = 1.0f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Cymatics|Targets")
	FName ReactiveTag = TEXT("MelodiaCymatic");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Cymatics|Targets")
	bool bReactToAllInstancedMeshes = false;

	/** Only instances within this distance (cm) of the owner react. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Cymatics|Targets", meta = (ClampMin = "100"))
	float ReactRadius = 8000.0f;

	/** Budget across all tracked components; extra instances are left at rest. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Cymatics|Targets", meta = (ClampMin = "1"))
	int32 MaxInstances = 6000;

	/** Side length (cm) of one Chladni plate tile in world space. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Cymatics|Wave", meta = (ClampMin = "100"))
	float PlateSizeCm = 6000.0f;

	/** Peak vertical lift (cm) from the standing wave at full drive. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Cymatics|Wave")
	float MaxLiftCm = 35.0f;

	/** Fractional scale gain at full drive on an antinode. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Cymatics|Wave")
	float ScalePulse = 0.15f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Cymatics|Ripple")
	float RippleSpeedCmPerSec = 1400.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Cymatics|Ripple", meta = (ClampMin = "10"))
	float RippleWidthCm = 350.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Cymatics|Ripple", meta = (ClampMin = "0.1"))
	float RippleLifeSec = 2.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Cymatics|Ripple")
	float RippleLiftCm = 60.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Cymatics|Hits")
	bool bHitOnPawnOverlap = true;

	/** Fire a ripple from the owner on each beat edge. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Cymatics|Hits")
	bool bHitOnBeat = false;

	/** Resolve a Great command on the reactivity subsystem per hit (palette pulse + OSC out). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Cymatics|Hits")
	bool bNotifyReactivity = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Cymatics|Performance", meta = (ClampMin = "1", ClampMax = "120"))
	float UpdateHz = 30.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Cymatics|Performance", meta = (ClampMin = "0.5"))
	float RescanIntervalSec = 3.0f;

private:
	struct FTracked
	{
		TWeakObjectPtr<UInstancedStaticMeshComponent> Comp;
		TArray<FTransform> Rest;
		TArray<FTransform> Scratch;
	};

	struct FRipple
	{
		FVector Origin = FVector::ZeroVector;
		float Age = 0.0f;
		float Strength = 1.0f;
	};

	UFUNCTION()
	void HandleOwnerOverlap(AActor* OverlappedActor, AActor* OtherActor);

	void Rescan();
	void RestoreAll();
	void Apply(float DeltaSeconds);

	TArray<FTracked> Tracked;
	TArray<FRipple> Ripples;
	float RescanTimer = 0.0f;
	float UpdateTimer = 0.0f;
	float LastBeatPulse = 0.0f;
};
