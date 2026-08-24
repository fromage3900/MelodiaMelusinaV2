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

	UPROPERTY(EditAnywhere, Category="SorrowSeam")
	TObjectPtr<UMaterialParameterCollection> PaletteMPC = nullptr;

	// MID created from MI_Fabric_Melusina_SorrowSeam at runtime; applied to Trail/Shawl slots via wardrobe morph if needed.
	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> SorrowSeamMID = nullptr;

	UPROPERTY(EditAnywhere, Category="SorrowSeam", meta=(ClampMin="0.0", ClampMax="1.0"))
	float MendLerpSpeed = 1.5f;

	// Idempotent heal flag check — read-only: if challenge.first_resonance_echo.completed is set, lerp to pristine.
	bool IsWorldHealed() const;

private:
	float CurrentSheen = 0.18f; // default pristine sheen for Sorrow Seam
	float TargetSheen = 0.18f;
	void ApplyToMID();
};
