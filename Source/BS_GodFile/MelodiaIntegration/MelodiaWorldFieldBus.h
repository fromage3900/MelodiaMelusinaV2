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
    /** World position of sample */
    UPROPERTY(BlueprintReadOnly) FVector WorldPosition = FVector::ZeroVector;
};

UCLASS(BlueprintType)
class BS_GODFILE_API UWorldFieldBus : public UObject
{
    GENERATED_BODY()
public:
    /** Sample Resonance/Tension at world position (reads cymatic field). */
    UFUNCTION(BlueprintCallable, Category="Melodia|WorldField")
    static FWorldFieldSample SampleResonanceTension(FVector WorldPos);

    /** Publish from cymatics — called by UMelodiaCymaticsSubsystem Tick. */
    static void PublishResonance(int32 N, int32 M, float Tension, float BeatPulse);

private:
    static FWorldFieldSample LastPublished;
};
