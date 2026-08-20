// MelodiaNPR — toon shading parameters and the runtime material applier.
//
// Decision 037: PPV / toon-outline lane split — MooaToon owns the outline algorithm.
// Decision 044: the outfit algorithm is re-hosted in MelodiaWardrobe; this module is
// the rendering half only.
//
// The applier deliberately drives a UMaterialInstanceDynamic rather than deriving from
// UMaterialInstanceConstant. UMaterialInstanceConstant lives in UnrealEd, so a class
// derived from it cannot exist in a packaged build — which would break the
// `package_launch` gate. A MID works in both editor and cooked builds.

#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "MelodiaToonMaterial.generated.h"

class UMaterialInstanceDynamic;
class UMaterialInterface;

/** Toon shading parameters for Melusina. */
USTRUCT(BlueprintType)
struct MELODIANPR_API FMelodiaToonParams
{
	GENERATED_BODY()

	/** Rim lighting intensity (0.0 - 1.0). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Toon")
	float RimIntensity = 1.0f;

	/** Rim falloff distance. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Toon")
	float RimFalloff = 2.0f;

	/** Shadow thickness via SDF threshold. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Toon")
	float SdfThreshold = 0.5f;

	/** Outline width (pixels). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Toon")
	float OutlineWidth = 1.0f;

	/** Outline color. FLinearColor, not FColor — material vector parameters are linear. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Toon")
	FLinearColor OutlineColor = FLinearColor::White;

	/** Base color tint. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Toon")
	FLinearColor BaseTint = FLinearColor::White;

	/** Metallic input override (0.0 - 1.0). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Toon")
	float Metallic = 0.0f;

	/** Roughness input override (0.0 - 1.0). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Toon")
	float Roughness = 0.5f;
};

/**
 * Applies FMelodiaToonParams to a dynamic material instance.
 *
 * Scaffold: parameter names below are the contract this expects on the toon master.
 * If the master material uses different names, fix them here rather than adding a
 * translation layer.
 */
UCLASS(BlueprintType)
class MELODIANPR_API UMelodiaToonMaterial : public UObject
{
	GENERATED_BODY()

public:
	/** Create the dynamic instance this applier drives. Must be called before ApplyToonParams. */
	UFUNCTION(BlueprintCallable, Category = "Toon")
	UMaterialInstanceDynamic* InitializeFrom(UMaterialInterface* SourceMaterial);

	/** Push toon params onto the dynamic instance. No-op if not initialized. */
	UFUNCTION(BlueprintCallable, Category = "Toon")
	void ApplyToonParams(const FMelodiaToonParams& Params);

	/** Set which outfit layer is visible (modular clothing index). */
	UFUNCTION(BlueprintCallable, Category = "Outfit")
	void SetOutfitLayer(int32 LayerIndex);

	/** Current outfit layer index. */
	UFUNCTION(BlueprintPure, Category = "Outfit")
	int32 GetOutfitLayer() const;

private:
	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> ToonInstance = nullptr;

	UPROPERTY(Transient)
	int32 OutfitLayer = 0;
};
