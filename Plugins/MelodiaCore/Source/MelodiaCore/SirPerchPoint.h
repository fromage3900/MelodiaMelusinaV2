#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SirPerchPoint.generated.h"

class UStaticMeshComponent;
class USceneComponent;

/**
 * Authored landing spot for Sir Melodious (D1: authored perches, not arbitrary
 * geometry scanning). A perch carries where the bird's origin sits and which
 * way he faces, so he settles on a rail instead of sliding off a collision
 * edge, and designers can drop one anywhere - a fence, a bell tree, a roof.
 *
 * The optional glint component is a designer-assigned visual cue. It ships
 * with no mesh on purpose: the class stays asset-free and the BP child decides
 * whether a perch reads in-world.
 */
UCLASS(Blueprintable)
class MELODIACORE_API ASirPerchPoint : public AActor
{
	GENERATED_BODY()

public:
	ASirPerchPoint();

	/** Offset from the actor origin to the spot Sir's origin rests at. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Perch")
	FVector LandingOffset = FVector(0.0, 0.0, 0.0);

	/** When false the perch keeps the bird's current facing. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Perch")
	bool bFaceAlongPerch = true;

	/** Facing applied when bFaceAlongPerch is set. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Perch")
	FRotator PerchFacing = FRotator(0.0, 0.0, 0.0);

	/** Optional in-world read of "you can land here". No mesh by default. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Perch")
	TObjectPtr<UStaticMeshComponent> Glint;

	UFUNCTION(BlueprintPure, Category="Melodia|Perch")
	FVector GetLandingLocation() const;

	UFUNCTION(BlueprintPure, Category="Melodia|Perch")
	FRotator GetLandingRotation() const;
};
