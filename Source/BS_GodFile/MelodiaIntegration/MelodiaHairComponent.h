#pragma once

#include "CoreMinimal.h"
#include "Components/SkeletalMeshComponent.h"
#include "MelodiaHairComponent.generated.h"

/**
 * Presentation-only Melusina hair component for character classes that cannot
 * inherit AMelodiaSmokeCharacter's native WaterHairMesh. It attaches to the
 * owning Character mesh and supplies that mesh to the hair AnimBP's Copy Pose
 * input; Kawaii Physics remains owned by the hair AnimBlueprint.
 */
UCLASS(ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaHairComponent final : public USkeletalMeshComponent
{
	GENERATED_BODY()

public:
	UMelodiaHairComponent();

	// REMOVED 2026-07-31: FallbackAttachCorrection / bForceAttachCorrection.
	//
	// These applied a corrective transform to the hair at BeginPlay. They are gone,
	// not deprecated -- this component no longer rotates or offsets the hair under
	// any circumstance. If the hair sits wrong, fix it in the rig or in the authored
	// component transform, where it is visible in the viewport, instead of in a
	// runtime correction that only manifests on Play.

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void OnUnregister() override;

private:
	void BindToOwnerMesh();
	void RestoreOwnerMeshReference();

	/**
	 * Hair AnimBP class, resolved in the constructor but NOT installed there.
	 *
	 * Installing the anim instance in the constructor makes the AnimBP tick from
	 * the first frame, while SourceMeshComponent is only assigned in
	 * BindToOwnerMesh() -- which BeginPlay deliberately defers one tick so the
	 * battle adapter's mesh swap completes first. Those intervening frames ticked
	 * the graph with a null source mesh. The class is cached here and installed in
	 * BindToOwnerMesh(), so the graph has no instance to tick until the same call
	 * stack that populates its source mesh runs.
	 */
	UPROPERTY()
	TSubclassOf<UAnimInstance> HairAnimClass;

	/** The stock mechanics mesh redirected on this instance, if any. */
	TWeakObjectPtr<USkeletalMeshComponent> OriginalMechanicsMesh;

	/** The visible mesh installed into the stock SkeletalMesh property. */
	TWeakObjectPtr<USkeletalMeshComponent> RedirectedPresentationMesh;

	/** Original render state restored when the battle unit is torn down. */
	bool bOriginalMechanicsMeshWasVisible = true;
	bool bOriginalMechanicsMeshWasHiddenInGame = false;
};
