#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaFoleyComponent.generated.h"

class USoundCue;

/**
 * Footstep foley surface: which authored sample layer plays for a given impact.
 *
 * Resolved at DESIGN TIME from authored world zones -- not from physics-material
 * probing. The spec (Docs/Production/FOLEY_BANK_SPEC_2026-10-05.md) rules out
 * surface-material probing because the maps are hand-authored: Morning's route
 * is known, so the designer places zones where the route crosses each surface.
 * No zone covers the position -> DefaultSurface.
 */
UENUM(BlueprintType)
enum class EMelodiaFoleySurface : uint8
{
	Grass  UMETA(DisplayName = "Grass / Meadow"),
	Dirt   UMETA(DisplayName = "Dirt / Trail"),
	Stone  UMETA(DisplayName = "Stone / Paving"),
	Wood   UMETA(DisplayName = "Wood / Deck"),
	Splash UMETA(DisplayName = "Water (shallow)")
};

/** One authored surface zone: "inside this world-space ball, footsteps use Surface". */
USTRUCT(BlueprintType)
struct FMelodiaFoleySurfaceZone
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Foley")
	EMelodiaFoleySurface Surface = EMelodiaFoleySurface::Grass;

	/** World-space center (cm). Authored per map; Morning is hand-authored. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Foley")
	FVector Center = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Foley", meta = (ClampMin = "1.0"))
	float RadiusCm = 500.0f;
};

/**
 * Melusina's footstep foley trigger + playback. Presentation-only.
 *
 * WHY THIS EXISTS: UE 5.8 has no built-in footstep event, and the locomotion
 * clips carry no per-impact notifies (verified 2026-10-05: the locomotion
 * blendspaces have none, so the spec's "one notify per foot impact" has no
 * hook to attach to). This component is the self-contained gait detector the
 * investigation settled on: a speed-scaled cadence timer while grounded, plus
 * a landing-impact trigger on air->ground with real fall speed, plus a hard
 * 0.26 s cooldown. It is deliberately REPLACEABLE by animation notifies: if
 * foot-impact notifies are later authored into the locomotion clips, the
 * cadence timer can be deleted and each notify call lands on PlayFootstep()
 * without touching anything else in this component.
 *
 * SURFACES: no physics probing (spec). Shallow water is the one runtime
 * exception and uses the movement component's own 5.8 state: MOVE_Walking is
 * the grounded check (there is no IsGrounded() in 5.8) and IsInWater() while
 * still Walking means wading, so Splash. Deep water forces Swimming mode,
 * which suppresses footstep entirely -- arms move, feet do not. Everything
 * else comes from authored FMelodiaFoleySurfaceZone balls, innermost wins,
 * DefaultSurface otherwise.
 *
 * ROUTING: cues are authored on SCL_Foley_Footstep (parent SCL_SFX), so
 * UMelodiaAudioBusSubsystem's sole SCL_SFX class override ducks the whole
 * footstep layer through /audio/bus/sfx/level. Nothing here writes bus gains.
 *
 * HUMANISE TIMBRE, NOT TIMING: pitch 0.92-1.08 per impact per the spec. The
 * step lands on the frame the detector fires -- there is no added delay, and
 * there must not be (a rhythm game reading footsteps late feels broken).
 *
 * CLOTH RUSTLE UNDERLAY: not in v1. The bank spec lists three re-voiced
 * rustle samples and the generated bank (65 waves, foley_bank_manifest.json)
 * does not contain them yet; the underlay lands with that re-voice.
 */
UCLASS(ClassGroup = (Melodia), meta = (BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaFoleyComponent final : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaFoleyComponent();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** True if any of the five surface cues loaded at BeginPlay. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Foley")
	bool IsFoleyReady() const { return bFoleyReady; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Foley")
	int32 GetFootstepsPlayed() const { return FootstepsPlayed; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Foley")
	int32 GetFootstepsDropped() const { return FootstepsDropped; }

	/** The surface the last resolved step used (diagnostics for zone authoring). */
	UFUNCTION(BlueprintPure, Category = "Melodia|Foley")
	EMelodiaFoleySurface GetLastSurface() const { return LastSurface; }

	/** Manual fire, for authoring a preview without walking. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Foley")
	void PlayFootstep(EMelodiaFoleySurface Surface, bool bIsLanding = false);

	/** Asset slots. Defaults point at the authored cues; nulls are no-ops. */
	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Foley|Assets")
	TSoftObjectPtr<USoundCue> GrassCue;

	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Foley|Assets")
	TSoftObjectPtr<USoundCue> DirtCue;

	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Foley|Assets")
	TSoftObjectPtr<USoundCue> StoneCue;

	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Foley|Assets")
	TSoftObjectPtr<USoundCue> WoodCue;

	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Foley|Assets")
	TSoftObjectPtr<USoundCue> SplashCue;

protected:
	void DetectFootstep(float DeltaTime);
	EMelodiaFoleySurface ResolveSurface(bool bSuppressWater) const;

	/**
	 * Cadence: one step every StepInterval at ReferenceSpeed; faster walking
	 * shortens the interval proportionally (clamped). The accumulator is
	 * decimated when stopped so the first step after standing still does not
	 * fire a buried backlog.
	 */
	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Foley|Gait", meta = (ClampMin = "0.2", ClampMax = "1.5"))
	float StepInterval = 0.55f;

	/** Walk speed (cm/s) the cadence is tuned for. */
	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Foley|Gait", meta = (ClampMin = "100.0"))
	float ReferenceSpeed = 400.0f;

	/** Below this horizontal speed there is no step (standing in place). */
	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Foley|Gait", meta = (ClampMin = "0.0"))
	float MinWalkSpeed = 60.0f;

	/** Hard minimum between any two footstep voices (spec: ~0.26 s). */
	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Foley|Gait", meta = (ClampMin = "0.05", ClampMax = "1.0"))
	float FootstepCooldown = 0.26f;

	/** Air->ground with fall speed above this (cm/s) fires a landing impact. */
	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Foley|Gait", meta = (ClampMin = "0.0"))
	float MinLandingImpactSpeed = 300.0f;

	/** Pitch range per the spec: 0.92-1.08. */
	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Foley|Timbre", meta = (ClampMin = "0.5", ClampMax = "2.0"))
	float PitchMin = 0.92f;

	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Foley|Timbre", meta = (ClampMin = "0.5", ClampMax = "2.0"))
	float PitchMax = 1.08f;

	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Foley|Timbre", meta = (ClampMin = "0.0", ClampMax = "2.0"))
	float WalkVolume = 0.5f;

	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Foley|Timbre", meta = (ClampMin = "0.0", ClampMax = "2.0"))
	float LandingVolume = 0.6f;

	/** No zone covers the position -> this surface. Morning: grass. */
	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Foley|Surfaces")
	EMelodiaFoleySurface DefaultSurface = EMelodiaFoleySurface::Grass;

	/** Authored surface balls (see FMelodiaFoleySurfaceZone). Innermost wins. */
	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Foley|Surfaces")
	TArray<FMelodiaFoleySurfaceZone> SurfaceZones;

	/** Slip under the actor so the voice sits at the feet, not the mesh origin. */
	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Foley")
	FVector FootOffset = FVector(0.0f, 0.0f, -60.0f);

	/** Voice budget over a sliding 1 s window (a landing burst cannot stack 6+). */
	UPROPERTY(EditDefaultsOnly, Category = "Melodia|Foley|Voice", meta = (ClampMin = "1", ClampMax = "16"))
	int32 MaxFootstepsPerSecond = 6;

	/** Index-ordered to EMelodiaFoleySurface: Grass, Dirt, Stone, Wood, Splash. */
	UPROPERTY(Transient)
	TObjectPtr<USoundCue> LoadedCues[5] = { nullptr, nullptr, nullptr, nullptr, nullptr };

	/** Wave-bank fallback (2026-10-17): the SC_FS_* cue files exist on disk but
	 *  are invisible to the asset registry, while the SW_FS_* waves register
	 *  fine. When a cue slot is null we pick a random wave from this bank --
	 *  same random+ pitch behaviour the cue's Random node would have given. */
	/** Flat bank: index = surface * 6 + (sample - 1). */
	UPROPERTY(Transient)
	TArray<TObjectPtr<class USoundWave>> LoadedWaves;

	float GaitAccumulator = 0.0f;
	float PrevVelocityZ = 0.0f;
	bool bWasGrounded = true;
	float FootstepCooldownRemaining = 0.0f;
	float EventWindowStart = 0.0f;
	int32 EventsInWindow = 0;

	int32 FootstepsPlayed = 0;
	int32 FootstepsDropped = 0;
	EMelodiaFoleySurface LastSurface = EMelodiaFoleySurface::Grass;
	bool bFoleyReady = false;
};
