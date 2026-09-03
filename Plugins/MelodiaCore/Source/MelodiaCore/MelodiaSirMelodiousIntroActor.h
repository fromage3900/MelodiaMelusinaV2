#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaSirMelodiousIntroActor.generated.h"

class USkeletalMeshComponent;
class USceneComponent;
class USphereComponent;
class UPointLightComponent;
class UPrimitiveComponent;
class AActor;
struct FHitResult;

/**
 * Authored first-room presentation of Sir Melodious. It owns the reunion beat
 * but intentionally defers companion movement and flight to a later controller.
 */
UCLASS(Blueprintable)
class MELODIACORE_API AMelodiaSirMelodiousIntroActor : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaSirMelodiousIntroActor();

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UFUNCTION()
	void HandleReunionOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Melodia|Sir Melodious")
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Melodia|Sir Melodious")
	TArray<TObjectPtr<USkeletalMeshComponent>> PresentationMeshes;

	/** One-shot approach volume that records Sir's first reunion with Melusina. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Melodia|Resonance")
	TObjectPtr<USphereComponent> ReunionTrigger;

	/** Dormant until Melusina reaches Sir; a small authored cue for the reunion. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Melodia|Resonance")
	TObjectPtr<UPointLightComponent> ReunionLight;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Resonance")
	bool bEnableReunionBeat = true;

	/** Number of AMelodiaExplorationPoint actors the player must visit (via
	 * UMelodiaOpeningFlowSubsystem::NotifyExplorationPointVisited) before the
	 * reunion beat is allowed to fire. 0 = no gate, the original ungated behaviour
	 * -- existing placements of this actor are unaffected unless authored otherwise. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Opening|Exploration", meta=(ClampMin="0"))
	int32 RequiredExplorationPoints = 0;

	/** Bedroom-only second beat: Sir flies through the window into Dreamstate. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Opening|Departure")
	bool bDepartAfterReunion = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Opening|Departure", meta=(ClampMin="0.0"))
	float DepartureDelaySeconds = 1.25f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Opening|Departure", meta=(ClampMin="0.1"))
	float DepartureDurationSeconds = 1.8f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Opening|Departure")
	FVector DepartureOffset = FVector(650.0f, 0.0f, 260.0f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Opening|Departure", meta=(AllowedClasses="/Script/Engine.World"))
	FName DepartureDestinationLevel = TEXT("/Game/EnvSandbox/Environments/L_KaleidoNave");

	/** Dissonance procs from actual distance to Sir as he flies away, not a fixed
	 * trigger volume - "losing power because she's away from her companion."
	 * Fractions of DepartureOffset's length (0-1). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Opening|Departure", meta=(ClampMin="0.0", ClampMax="1.0"))
	float StrainDistanceRatio = 0.35f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Opening|Departure", meta=(ClampMin="0.0", ClampMax="1.0"))
	float RuptureDistanceRatio = 0.75f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Opening|Departure", meta=(ClampMin="0.0", ClampMax="1.0"))
	float MinSongcraftScalar = 0.2f;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Opening|Departure")
	bool BeginWindowDeparture();

private:
	void HandleDepartureDelayElapsed();
	void UpdateDissonanceFromDistance(const FVector& SirLocation) const;
	bool bReunionTriggered = false;
	bool bDepartureActive = false;
	bool bDepartureCompleted = false;
	float DepartureElapsed = 0.0f;

	/** DepartureDurationSeconds resolved once at BeginWindowDeparture() -- through
	 * UMelodiaPacingSubsystem if a profile is authored, else a copy of the field
	 * above. Tick() reads this, never the authored field, so the arc's duration
	 * cannot change mid-flight even if the pacing profile is edited live in PIE. */
	float ResolvedDepartureDurationSeconds = 0.0f;
	FVector DepartureStartLocation = FVector::ZeroVector;
	FTimerHandle DepartureDelayHandle;
};
