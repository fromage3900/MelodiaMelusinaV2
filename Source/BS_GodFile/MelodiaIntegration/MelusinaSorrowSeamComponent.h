#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelusinaSorrowSeamComponent.generated.h"

class UMaterialInstanceDynamic;
class UMaterialParameterCollection;

/**
 * Presentation-only Sorrow Seam veil driver.
 * Reads MPC_Melodia_Palette scalars (DreadPresence/Dissonance/BeatPulse) and
 * lerps MI_Fabric_Melusina_SorrowSeam params. No combat/traversal/save authority.
 * 0 at rest = byte-identical (all lerps gated on >KINDA_SMALL_NUMBER).
 */
UCLASS(ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class BS_GODFILE_API UMelusinaSorrowSeamComponent : public UActorComponent
{
	GENERATED_BODY()
public:
	UMelusinaSorrowSeamComponent();
	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** Sheen when the world is unhealed. Matches specs/melusina_sorrow_seam.v1.json. */
	static constexpr float PristineSheen = 0.18f;
	/** Sheen once challenge.first_resonance_echo is completed. */
	static constexpr float HealedSheen = 0.32f;

	UPROPERTY(EditAnywhere, Category="SorrowSeam")
	TObjectPtr<UMaterialParameterCollection> PaletteMPC = nullptr;

	// MID created from MI_Fabric_Melusina_SorrowSeam at runtime; applied to Trail/Shawl slots via wardrobe morph if needed.
	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> SorrowSeamMID = nullptr;

	/** FInterpTo speed for the mend lerp. 1.5 reaches pristine->healed in ~1.5s. */
	UPROPERTY(EditAnywhere, Category="SorrowSeam", meta=(ClampMin="0.0", ClampMax="10.0"))
	float MendLerpSpeed = 1.5f;

	// Idempotent heal flag check — read-only: if challenge.first_resonance_echo.completed is set, lerp to pristine.
	bool IsWorldHealed() const;

private:
	float CurrentSheen = PristineSheen;
	float TargetSheen = PristineSheen;

	/**
	 * Set once ApplyToMID has scanned the owner's material slots. Without this the scan
	 * re-runs every tick (8 GetMaterial calls plus string compares) for the whole session
	 * whenever no Sorrow Seam material is bound, which is the current default.
	 */
	bool bMIDResolveAttempted = false;

	void ApplyToMID();
};
