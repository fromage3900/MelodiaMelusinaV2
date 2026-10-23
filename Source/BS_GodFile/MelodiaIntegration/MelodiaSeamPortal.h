#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MultiWorldHandle.h"
#include "MelodiaSeamPortal.generated.h"

class UBoxComponent;
class ACharacter;
class UMaterialInterface;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaSeamCrossed, AActor*, Traveller);

/**
 * Runtime half of the Escher kit (HF/escher_kit.py, escher_bend.py, escher_graph.py): a trigger volume that applies a SEAM to a character that crosses it.
 *
 *   NewLocation = Pivot + Roll * (Location - Pivot) + Translation        (roll first, then translate)
 *   NewRotation = Roll * Rotation          velocity = Roll * velocity
 *   gravity     = Roll * gravity           (UCharacterMovementComponent::SetGravityDirection) when the roll is not the identity
 *
 * A Penrose-style seam is a pure translation (e.g. 0,0,-952 cm). A gravity-bend seam is a 90 degree roll about the lip line (pivot = a point on the lip,
 * axis = the lip axis, no translation: the lip is fixed by the roll, so the surface is continuous). The numbers come straight from the Houdini-side manifests
 * (seam.transform / seam.roll), converted to Unreal's frame by the spawner; ComputeSeam is pure math so it can be tested against them.
 *
 * The volume only fires when the traveller is moving across it (velocity . CrossingDirection > 0) and then ignores that traveller for CooldownSeconds,
 * so a pawn that lands inside a paired seam is not bounced back. Gameplay-affecting (it moves the pawn) but it writes no narrative state.
 *
 * Cross-world crossings are NOT done here: when DestinationWorld is valid and TransitionMaterial is set, the portal is only a presenter. It hands the
 * traveller to UMultiWorldSeamTransition (the MultiWorld plugin owns the world switch and the transition FX) and applies no seam math.
 */
UCLASS(Blueprintable)
class BS_GODFILE_API AMelodiaSeamPortal : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaSeamPortal();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Melodia|Seam")
	TObjectPtr<UBoxComponent> Trigger;

	/** Translation (cm, world) applied AFTER the roll. Penrose-style seams use only this. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Seam")
	FVector TranslationCm = FVector::ZeroVector;

	/** World axis the roll turns about (right-hand rule). Ignored when RollDegrees is 0. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Seam")
	FVector RollAxis = FVector(0.0, 1.0, 0.0);

	/** Roll in degrees. 90 = a convex lip: gravity turns with the surface. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Seam", meta = (ClampMin = "-180.0", ClampMax = "180.0"))
	float RollDegrees = 0.0f;

	/** Point (world, cm) the roll pivots about; when bPivotIsActorLocation it is this actor's location. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Seam")
	FVector PivotCm = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Seam")
	bool bPivotIsActorLocation = true;

	/** The seam fires only when the traveller's velocity has a positive component along this world direction (default: the actor's forward). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Seam")
	FVector CrossingDirection = FVector::ForwardVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Seam")
	bool bRequireCrossingDirection = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Seam", meta = (ClampMin = "0.0"))
	float CooldownSeconds = 0.6f;

	/** Set at runtime from UMultiWorldManager. Valid + TransitionMaterial => hand off to MultiWorld instead of the in-world seam. */
	UPROPERTY(BlueprintReadWrite, Category = "Melodia|Seam|MultiWorld")
	FMultiWorldHandle DestinationWorld;

	/** A User Interface domain material built on MultiWorld_SeamTransition_MF (e.g. MW_ST_CrossFading_PPM). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Seam|MultiWorld")
	TObjectPtr<UMaterialInterface> TransitionMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Seam|MultiWorld", meta = (ClampMin = "0.0"))
	float TransitionSeconds = 1.0f;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Seam")
	FMelodiaSeamCrossed OnSeamCrossed;

	/** Pure math: where a body at (Location, Rotation) ends up. Exposed so tests can compare it with the Houdini-side seam. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Seam")
	void ComputeSeam(const FVector& Location, const FQuat& Rotation, FVector& OutLocation, FQuat& OutRotation) const;

	/** Apply the seam to a character now (ignores the crossing-direction test; honours the cooldown only when bUseCooldown). Returns true if applied. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Seam")
	bool ApplySeam(ACharacter* Traveller, bool bUseCooldown = false);

protected:
	virtual void BeginPlay() override;

private:
	UFUNCTION()
	void HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	FQuat RollQuat() const;

	TMap<TWeakObjectPtr<AActor>, double> LastCrossed;
};
