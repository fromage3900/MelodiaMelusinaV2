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

	/**
	 * "Hair that listens": peak sideways sway force (cm/s) the hair receives on each
	 * beat, alternating left/right between beats and scaled by the music pulse. Zero
	 * in rests, so the hair settles on its own simulation between phrases.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Hair|Music", meta=(ClampMin="0"))
	float MusicSwayForce = 40.0f;

	/** Upward lift (cm/s) on the beat, scaled by the music pulse. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Hair|Music", meta=(ClampMin="0"))
	float MusicLiftForce = 15.0f;

protected:
	virtual void OnRegister() override;
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void OnUnregister() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType,
		FActorComponentTickFunction* ThisTickFunction) override;

private:
	void BindEditorSourceMesh();
	void BindToOwnerMesh();
	void RestoreOwnerMeshReference();

	/**
	 * Adds this frame's music-driven one-shot Kawaii force. Runs on the game thread
	 * so the music clock is never read from the animation worker; Kawaii itself
	 * stays owned by the hair AnimBlueprint.
	 */
	void ApplyMusicForce();

	/** Beat phase last frame; a wrap marks a new beat and flips the sway side. */
	float LastMusicBeatPhase = 0.0f;
	bool bMusicSwayRight = false;

	/**
	 * Hair AnimBP class, resolved in the constructor but NOT installed there.
	 *
	 * Installing the anim instance in the constructor makes the AnimBP tick from
	 * the first frame, while SourceMeshComponent is assigned in BindToOwnerMesh()
	 * -- which BeginPlay deliberately defers one tick so the battle adapter's mesh
	 * swap completes first. Those intervening frames ticked the graph with a null
	 * source mesh. The class is cached here and installed in BindToOwnerMesh(), so
	 * the game graph has no instance to tick until the same call stack that
	 * populates its source mesh runs. Editor worlds do not install it either:
	 * BindEditorSourceMesh() only writes SourceMeshComponent when this AnimBP is
	 * already instanced.
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
