#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaLightReactorComponent.generated.h"

class ULightComponent;

/** Which shared lane drives a mapping. All are read from MPC_Melodia_Palette (the single audio/event surface). */
UENUM(BlueprintType)
enum class EMelodiaLightSource : uint8
{
	Bass,
	Mid,
	Treble,
	BeatPulse,
	RhythmPulse,
	Sparkle,
	/** Decaying pulse of the last Quantum draw (UMelodiaQuantumDrawSubsystem). */
	QuantumPulse,
	/** Normalized winner index of the last Quantum draw -- a held value, not a pulse. */
	QuantumChoice,
	/** Chladni tension from UWorldFieldBus. */
	CymaticTension
};

/** Which light parameter a mapping scales or blends. */
UENUM(BlueprintType)
enum class EMelodiaLightTarget : uint8
{
	/** Intensity = Base * (1 + Amount * Source). */
	Intensity,
	/** Attenuation radius (local lights) = Base * (1 + Amount * Source). */
	AttenuationRadius,
	/** Source radius (point/spot/rect) = Base * (1 + Amount * Source): softer, larger glow. */
	SourceRadius,
	/** Volumetric scattering intensity = Base * (1 + Amount * Source). */
	VolumetricScattering,
	/** Colour moves from the authored colour toward Tint by Amount * Source (Tint = Quantum reaction colour when bTintFromQuantum). */
	ColorToTint,
	/** Colour temperature (K) = Base + Amount * 1000 * Source. */
	Temperature
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaLightLane
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Light Lane")
	EMelodiaLightSource Source = EMelodiaLightSource::BeatPulse;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Light Lane")
	EMelodiaLightTarget Target = EMelodiaLightTarget::Intensity;

	/** Signed scale. 1.0 on Intensity doubles the light at full source. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Light Lane")
	float Amount = 0.5f;

	/** Seconds to rise toward a higher source value. 0 = instant. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Light Lane", meta = (ClampMin = "0"))
	float AttackSec = 0.02f;

	/** Seconds to fall toward a lower source value. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Light Lane", meta = (ClampMin = "0"))
	float ReleaseSec = 0.25f;

	/** ColorToTint only: use the last Quantum draw's reaction colour as the tint. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Light Lane")
	bool bTintFromQuantum = false;

	/** ColorToTint only, when not tinting from Quantum. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Light Lane")
	FLinearColor Tint = FLinearColor(1.0f, 0.6f, 0.9f, 1.0f);

	/** Runtime smoothed value (not saved). */
	float Smoothed = 0.0f;
};

/**
 * Light reactor -- routes the shared audio / Quantum / cymatic lanes into engine light parameters.
 *
 * Presentation only. It READS MPC_Melodia_Palette (which TouchDesigner OSC, the rhythm reactivity subsystem
 * and the Quantum draw subsystem already write) and UWorldFieldBus; it writes only the light components it
 * targets and restores their authored values at EndPlay. It owns no OSC socket and no MPC lane, so the
 * single-writer rules in Docs/Architecture/AUDIO_REACTIVE_CANON.md hold. OSC-driven lighting is therefore
 * "send OSC to the palette lanes, the lights follow"; a Quantum draw lights the level through QuantumPulse /
 * QuantumChoice / QuantumReactionColor.
 *
 * Targets: every ULightComponent on the owner, plus (optionally) lights in the world carrying LightTag within
 * Radius. Works with MegaLights: intensity/colour/attenuation are ordinary light parameters, and
 * bForceAllowMegaLights opts the targeted lights in (restored at EndPlay) so many reactive lights stay cheap.
 */
UCLASS(ClassGroup = (Melodia), meta = (BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaLightReactorComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaLightReactorComponent();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** Mappings, applied in order; several lanes may share a target (their factors multiply / blends chain). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Lights")
	TArray<FMelodiaLightLane> Lanes;

	/** Also drive lights elsewhere in the world that carry this actor/component tag. None = owner lights only. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Lights")
	FName LightTag = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Lights", meta = (ClampMin = "100"))
	float Radius = 20000.0f;

	/** Per-light cap so a big level cannot blow the frame budget. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Lights", meta = (ClampMin = "1"))
	int32 MaxLights = 256;

	/** Opt the targeted lights into MegaLights (restored at EndPlay). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Lights")
	bool bForceAllowMegaLights = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Lights", meta = (ClampMin = "1", ClampMax = "120"))
	float UpdateHz = 60.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Lights", meta = (ClampMin = "0.5"))
	float RescanIntervalSec = 3.0f;

	/** Seeds a default beat/bass/quantum mapping set. Called from the constructor and from the editor "reset" use. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Lights")
	void ResetToDefaultLanes();

private:
	struct FTrackedLight
	{
		TWeakObjectPtr<ULightComponent> Light;
		float BaseIntensity = 0.0f;
		float BaseAttenuation = 0.0f;
		float BaseSourceRadius = 0.0f;
		float BaseVolumetric = 0.0f;
		float BaseTemperature = 0.0f;
		FLinearColor BaseColor = FLinearColor::White;
		bool bBaseUseTemperature = false;
		bool bBaseMegaLights = false;
	};

	float ReadSource(EMelodiaLightSource Source, class UMaterialParameterCollectionInstance* Palette) const;
	void Track(ULightComponent* Light);
	void Rescan();
	void RestoreAll();
	void Apply(float DeltaSeconds);

	UPROPERTY(Transient)
	TObjectPtr<class UMaterialParameterCollection> PaletteMPC;

	TArray<FTrackedLight> Tracked;
	float RescanTimer = 0.0f;
	float UpdateTimer = 0.0f;
};
