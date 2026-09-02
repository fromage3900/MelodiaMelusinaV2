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

/** Height-aware water vs fog decision. */
UENUM(BlueprintType)
enum class EWorldFieldWaterDecision : uint8
{
    Water       UMETA(DisplayName="Water"),
    Fog         UMETA(DisplayName="Valley Fog"),
    BasinPool   UMETA(DisplayName="Basin Pool"),
    Dry         UMETA(DisplayName="Dry Ridge")
};

UCLASS(BlueprintType)
class BS_GODFILE_API UWorldFieldBus : public UObject
{
    GENERATED_BODY()
public:
    /** Sample Resonance/Tension at world position (reads cymatic field). */
    UFUNCTION(BlueprintCallable, Category="Melodia|WorldField")
    static FWorldFieldSample SampleResonanceTension(FVector WorldPos);

    /** Cymatic ripple displacement (0..1) at normalized plate coords — for water shading. */
    UFUNCTION(BlueprintPure, Category="Melodia|WorldField")
    static float SampleCymaticRipple(FVector WorldPos);

    /** Height-aware: water vs valley-fog vs dry ridge at world position. */
    UFUNCTION(BlueprintPure, Category="Melodia|WorldField")
    static EWorldFieldWaterDecision GetWaterDecision(FVector WorldPos);

    /** True if position should show a water surface (vs fog/dry). */
    UFUNCTION(BlueprintPure, Category="Melodia|WorldField")
    static bool IsWaterHeight(FVector WorldPos);

    /** LOD dissolve -> water reveal (0 intact, 1 fully dissolved into water). */
    UFUNCTION(BlueprintPure, Category="Melodia|WorldField")
    static float GetLODDissolveWaterReveal(int32 CurrentLOD, int32 MaxLOD);

    /** Publish from cymatics — called by UMelodiaCymaticsSubsystem/Writer Tick. */
    static void PublishResonance(int32 N, int32 M, float Tension, float BeatPulse);

    /** Last published sample (offline probe fallback). */
    static FWorldFieldSample GetLastPublished() { return LastPublished; }

private:
    static FWorldFieldSample LastPublished;
};
