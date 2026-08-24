#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MelodiaResonanceGardenData.generated.h"

class UMaterialInterface;

/** Quality tier used by the fur selection contract. */
UENUM(BlueprintType)
enum class EMelodiaFurBackendKind : uint8
{
	NativeGroom UMETA(DisplayName="Native Groom"),
	ShellCard UMETA(DisplayName="Shell / Card"),
	Impostor UMETA(DisplayName="Impostor"),
	ExternalAdapter UMETA(DisplayName="External Adapter")
};

/** One distance band in the deterministic fur fallback ladder. */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaFurLodBand
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Fur")
	float MinDistance = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Fur")
	float MaxDistance = 400.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Fur")
	EMelodiaFurBackendKind Backend = EMelodiaFurBackendKind::NativeGroom;

	bool Contains(const float Distance) const
	{
		return Distance >= MinDistance && Distance < MaxDistance;
	}
};

/** Reusable fur contract shared by companions and future cute-animal families. */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaFurProfile
{
	GENERATED_BODY()

	FMelodiaFurProfile();

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Fur")
	FName ProfileId = FName(TEXT("Fur_Default"));

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Fur")
	TArray<FMelodiaFurLodBand> LODBands;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Fur|Assets")
	FName GroomAssetTag = FName(TEXT("Groom_Hero"));

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Fur|Assets")
	FName ShellAssetTag = FName(TEXT("FurShell_Mid"));

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Fur|Assets")
	FName CardAssetTag = FName(TEXT("FurCards_Far"));

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Fur|Materials")
	TSoftObjectPtr<UMaterialInterface> HeroMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Fur|Materials")
	TSoftObjectPtr<UMaterialInterface> FallbackMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Fur")
	float WoolClumpScale = 0.65f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Fur")
	float SheenResponse = 0.45f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Fur")
	bool bSupportsSimulation = true;

	bool IsValid(FText* OutError = nullptr) const;
};

/** The Melusina-owned visual identity shared by character, companion, world and web evidence. */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaStyleGenome
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Style")
	FName GenomeId = FName(TEXT("ResonanceGarden"));

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Style|Palette")
	FLinearColor PrimaryColor = FLinearColor(0.92f, 0.72f, 0.83f, 1.0f);

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Style|Palette")
	FLinearColor SecondaryColor = FLinearColor(0.65f, 0.82f, 0.92f, 1.0f);

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Style|Palette")
	FLinearColor AccentColor = FLinearColor(1.0f, 0.88f, 0.55f, 1.0f);

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Style|Materials")
	FName MaterialFamily = FName(TEXT("M_Master_Toon_Universal"));

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Style|Materials")
	TSoftObjectPtr<UMaterialInterface> MaterialMaster;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Style|Materials", meta=(ClampMin="0.0", ClampMax="1.0"))
	float Sheen = 0.55f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Style|Materials", meta=(ClampMin="0.0", ClampMax="1.0"))
	float Iridescence = 0.25f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Style|Materials", meta=(ClampMin="0.0", ClampMax="1.0"))
	float Sparkle = 0.18f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Style|Materials", meta=(ClampMin="0.0", ClampMax="1.0"))
	float Bloom = 0.22f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Style|Music")
	FName MusicMotif = FName(TEXT("petal_fan"));

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Style|Music", meta=(ClampMin="0.0", ClampMax="2.0"))
	float RhythmSensitivity = 0.75f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Style|World")
	TArray<FName> HabitatTags;

	bool IsValid(FText* OutError = nullptr) const;
};

UCLASS(BlueprintType)
class MELODIACORE_API UMelodiaStyleGenomeAsset : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Style")
	FMelodiaStyleGenome Genome;

	virtual FPrimaryAssetId GetPrimaryAssetId() const override;
};

UCLASS()
class MELODIACORE_API UMelodiaFurLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category="Melodia|Fur")
	static EMelodiaFurBackendKind SelectBackendForDistance(const FMelodiaFurProfile& Profile, float Distance);
};
