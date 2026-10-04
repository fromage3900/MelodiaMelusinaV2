#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Engine/DataAsset.h"
#include "MelodiaSeasonalVariantComponent.generated.h"

class UInstancedStaticMeshComponent;
class UMaterialInstanceDynamic;
class UMaterialInterface;
class UStaticMesh;

UENUM(BlueprintType)
enum class EMelodiaSeason : uint8
{
	Spring,
	Summer,
	Autumn,
	Winter
};

UENUM(BlueprintType)
enum class EMelodiaSeasonSource : uint8
{
	/** Month/Day read from the level's Ultra Dynamic Sky actor. Falls back to Manual when none is found. */
	UltraDynamicSky,
	/** SeasonPosition below. */
	Manual
};

/** One season's look for a biome. Tonal first; mesh swaps are optional instance changes. */
USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaSeasonLook
{
	GENERATED_BODY()

	/** Colour the biome leans toward this season. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Season")
	FLinearColor Tint = FLinearColor::White;

	/** 0 = authored colour, 1 = fully Tint. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Season", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float TintStrength = 0.35f;

	/** Replace an instanced mesh by another while this season dominates (source -> replacement). Instances are kept. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Season")
	TMap<TSoftObjectPtr<UStaticMesh>, TSoftObjectPtr<UStaticMesh>> MeshSwaps;
};

/** Per-biome seasonal data: four looks (Spring, Summer, Autumn, Winter) plus which material parameters carry colour. */
UCLASS(BlueprintType)
class BS_GODFILE_API UMelodiaSeasonalProfile : public UDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Season")
	FName BiomeId = NAME_None;

	/** Index = EMelodiaSeason. Fewer than four entries fall back to the last one. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Season")
	TArray<FMelodiaSeasonLook> Looks;

	/** Vector parameters nudged toward the season tint. A parameter a material lacks is skipped. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Season")
	TArray<FName> TintParameterNames = { FName(TEXT("BaseTint")), FName(TEXT("MelodiaWindRevealTint")) };

	/** Instanced meshes (or their actor) carrying this tag react. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Season")
	FName ReactiveTag = TEXT("MelodiaSeasonal");

	/** Audio hue strobe: the vector parameter that carries the strobing colour (flower master: wind-reveal tint). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Audio Hue")
	FName HueTintParameter = TEXT("MelodiaWindRevealTint");

	/** Scalar that sets how strongly the tint is revealed (0 = natural albedo). Raised on the beat. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Audio Hue")
	FName HueAmountParameter = TEXT("MelodiaWindResponse");

	/** Scalar that adds emissive glow on the beat (flower master: wind emissive boost). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Audio Hue")
	FName HueEmissiveParameter = TEXT("MelodiaWindEmissiveBoost");

	/** Scalar (turns, 0 = authored colour) that rotates the whole albedo hue. Driven by the strobe when the material has it. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Audio Hue")
	FName HueShiftParameter = TEXT("MelodiaHueShift");
};

/**
 * Seasonal biome variants. Reads the season from Ultra Dynamic Sky (Month/Day) or a manual position and
 * tints / swaps the instanced meshes of one biome accordingly. Presentation only: it creates per-component
 * material instances and restores the authored materials and meshes at EndPlay; it writes no MPC and owns
 * no audio. Season position runs 0 = start of spring, 1 = summer, 2 = autumn, 3 = winter (wraps at 4).
 */
UCLASS(ClassGroup = (Melodia), meta = (BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaSeasonalVariantComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaSeasonalVariantComponent();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Season")
	TObjectPtr<UMelodiaSeasonalProfile> Profile;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Season")
	EMelodiaSeasonSource Source = EMelodiaSeasonSource::UltraDynamicSky;

	/** Used when Source is Manual (or no sky is found). 0 spring, 1 summer, 2 autumn, 3 winter. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Season", meta = (ClampMin = "0.0", ClampMax = "4.0"))
	float SeasonPosition = 0.0f;

	/** Southern hemisphere shifts the calendar by half a year. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Season")
	bool bSouthernHemisphere = false;

	/** Seasons per second the displayed position may move (1.0 = a full season in one second). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Season", meta = (ClampMin = "0.01"))
	float TransitionSpeed = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Season")
	bool bAffectAllInstancedMeshes = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Season", meta = (ClampMin = "100"))
	float Radius = 40000.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Season", meta = (ClampMin = "1"))
	int32 MaxComponents = 400;

	/**
	 * Strobe the tracked foliage through the hue wheel from the shared audio lanes (MPC_Melodia_Palette, which OSC
	 * writes): each beat steps the hue by the golden-ratio conjugate, bass/beat raise the reveal amount and glow,
	 * treble nudges the hue. Reads the palette only; writes only the tracked material instances.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Audio Hue")
	bool bAudioHueStrobe = false;

	/** 1 = full colour wheel, 0 = hold the season tint's hue. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Audio Hue", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float HueRange = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Audio Hue", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float HueSaturation = 0.85f;

	/** Added to the authored reveal amount at full beat/bass (result is clamped to 0..1). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Audio Hue", meta = (ClampMin = "0.0"))
	float HueAmountGain = 0.8f;

	/** Multiplies the authored emissive boost: 1 + gain * pulse. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Audio Hue", meta = (ClampMin = "0.0"))
	float HueEmissiveGain = 1.5f;

	/** Share of the strobing colour taken from the season tint (0 = pure strobe). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Audio Hue", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float SeasonTintShare = 0.2f;

	/** Scales the albedo hue rotation the strobe applies through HueShiftParameter (1 = the full hue offset, 0 = off). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Audio Hue", meta = (ClampMin = "0.0", ClampMax = "2.0"))
	float HueShiftStrength = 1.0f;

	UFUNCTION(BlueprintPure, Category = "Melodia|Season")
	float GetDisplayedSeasonPosition() const { return DisplayedPosition; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Season")
	EMelodiaSeason GetDominantSeason() const;

private:
	struct FTrackedComp
	{
		TWeakObjectPtr<UInstancedStaticMeshComponent> Comp;
		TArray<TWeakObjectPtr<UMaterialInterface>> OriginalMaterials;
		TWeakObjectPtr<UStaticMesh> OriginalMesh;
	};

	/** One MID per distinct source material, shared by every component that uses it (a field has ~20, not ~230). */
	struct FSharedMID
	{
		TWeakObjectPtr<UMaterialInstanceDynamic> MID;
		/** Authored value per tint parameter; alpha < 0 marks "parameter absent". */
		TArray<FLinearColor> BaseColors;
		float BaseAmount = -1.0f;
		float BaseEmissive = -1.0f;
		bool bHasHueShift = false;
		FLinearColor BaseHueTint = FLinearColor(0.0f, 0.0f, 0.0f, -1.0f);
	};

	float ResolveTargetPosition();
	bool ReadSkyDate(int32& OutMonth, int32& OutDay);
	void Rescan();
	void Track(UInstancedStaticMeshComponent* Comp);
	void RestoreAll();
	void Apply();
	void ApplyMaterialParams();
	bool bStrobeWasOn = false;
	void TickAudioHue(float DeltaSeconds, class UMaterialParameterCollectionInstance* Palette);
	FSharedMID* GetOrCreateShared(UMaterialInterface* Original);

	TArray<FTrackedComp> Tracked;
	TMap<TWeakObjectPtr<UMaterialInterface>, FSharedMID> Shared;

	UPROPERTY(Transient)
	TObjectPtr<class UMaterialParameterCollection> PaletteMPC;

	float HueIndex = 0.0f;
	float LastBeatPulse = 0.0f;
	float StrobeHue = 0.0f;
	float HueOffsetTurns = 0.0f;
	float BeatEnergy = 0.0f;
	float BassSmoothed = 0.0f;
	float TrebleSmoothed = 0.0f;
	float AudioTimer = 0.0f;
	FLinearColor SeasonTintNow = FLinearColor::White;
	float SeasonStrengthNow = 0.0f;
	TWeakObjectPtr<AActor> SkyActor;
	float DisplayedPosition = 0.0f;
	float AppliedPosition = -1.0f;
	float RescanTimer = 0.0f;
	float PollTimer = 0.0f;
	float CachedTarget = 0.0f;
	bool bInitialised = false;
};
