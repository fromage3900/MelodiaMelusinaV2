#pragma once
#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "MelodiaWorldFieldBus.generated.h"

/**
 * Melodia World Field Bus — minimum shared spatial-field contract (§5b)
 *
 * Discovered via R&D per EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31 §5b.
 * Do not build a generalized framework — this is the minimum contract so
 * plugins stop inventing their own world truth.
 *
 * Representations by scale:
 * - MPC scalars (Resonance/Tension) for materials
 * - RVTs for landscape
 * - Niagara grids for particles
 * - Houdini fields (COPs/SOPs) for bake
 * - PCG metadata for scatter
 *
 * Cymatic publisher (§5b-i): UMelodiaCymaticsSubsystem publishes
 * ModeN/ModeM → WorldField.Resonance, Amplitude → WorldField.Tension
 * Consumers (VegetationGrowth, water ripple, PCG scatter) read these,
 * never call cymatics directly.
 *
 * PCG AWARENESS (2026-10-05): the bus now also carries the full harmonic
 * register (Mode + Consonance, alongside Resonance/Tension) and supports
 * MULTIPLE spatial field sources, so cymatic volumes, the piano walkway and
 * PCG densities each publish a local field and consumers sample the blended
 * result at their own position. The legacy global single-sample path
 * (PublishResonance / SampleResonanceTension) is unchanged so existing
 * consumers keep compiling.
 *
 * SCAFFOLD — requires closed-editor Build.bat to activate.
 * Offline probe: Tools/test_world_field_bus.py
 */
USTRUCT(BlueprintType)
struct BS_GODFILE_API FWorldFieldSample
{
    GENERATED_BODY()
    /** Standing-wave harmonic signature at point (ModeN,ModeM) → Resonance */
    UPROPERTY(BlueprintReadOnly) int32 ResonanceN = 2;
    UPROPERTY(BlueprintReadOnly) int32 ResonanceM = 3;
    /** How strongly the pattern pulls at location (0..1) → Tension */
    UPROPERTY(BlueprintReadOnly) float Tension = 0.f;
    /** Beat pulse 0..1 (mirrors MPC BeatPulse) */
    UPROPERTY(BlueprintReadOnly) float BeatPulse = 0.f;
    /** Harmonic mode 0..4 (0=rest,1=major,2=minor,3=dominant,4=chromatic). PCG-aware register. */
    UPROPERTY(BlueprintReadOnly) uint8 Mode = 0;
    /** Consonance 0..1 — stability of the current harmony (PCG-aware register). */
    UPROPERTY(BlueprintReadOnly) float Consonance = 0.5f;
    /** World position of sample */
    UPROPERTY(BlueprintReadOnly) FVector WorldPosition = FVector::ZeroVector;
};

/** One published spatial field source (a cymatic volume, PCG cluster, or walkway). */
struct FWorldFieldSource
{
    int32 Id = 0;
    FWorldFieldSample Sample;
    /** Sources only affect samples within this radius (cm) of their position. */
    float RadiusCm = 0.f;
    float Weight = 1.f;
};

UCLASS(BlueprintType)
class BS_GODFILE_API UWorldFieldBus : public UObject
{
    GENERATED_BODY()
public:
    /** Sample Resonance/Tension at world position (reads cymatic field). LEGACY global path. */
    UFUNCTION(BlueprintCallable, Category="Melodia|WorldField")
    static FWorldFieldSample SampleResonanceTension(FVector WorldPos);

    /**
     * PCG-aware spatial sample: blends every active field source within its radius of
     * WorldPos (nearest-weighted), falling back to the global last-published field when
     * no source covers the point. This is what makes PCG / materials / water read a LOCAL
     * harmonic + cymatic register instead of one global number.
     */
    UFUNCTION(BlueprintCallable, Category="Melodia|WorldField")
    static FWorldFieldSample SampleAt(FVector WorldPos);

    /** Publish from cymatics — called by UMelodiaCymaticsSubsystem Tick. LEGACY + global source. */
    static void PublishResonance(int32 N, int32 M, float Tension, float BeatPulse);

    /**
     * Publish a spatial field source at a world position with a radius and the full harmonic
     * register. Returns a stable id for RemoveFieldSource. Additive, no overwrite of the
     * global sample. Call once at BeginPlay, RemoveFieldSource at EndPlay.
     */
    static int32 PublishFieldSource(FVector WorldPos, float RadiusCm,
        int32 N, int32 M, float Tension, float BeatPulse, uint8 Mode, float Consonance, float Weight = 1.0f);

    static void RemoveFieldSource(int32 SourceId);

private:
    static FWorldFieldSample LastPublished;
    static TArray<FWorldFieldSource> Sources;
    static int32 NextSourceId;
};
