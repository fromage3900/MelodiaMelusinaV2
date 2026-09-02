#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "MelodiaOceanologyWaterBridgeSubsystem.generated.h"

/**
 * Oceanology SLW horizon-eater + cymatic ripple + height-aware + LOD-reflection bridge.
 *
 * SCAFFOLD — no Oceanology headers included. All plugin contact is via
 * FindFunction(TEXT("GetWaveInfoAtLocation"/"SetScalarParameterValue"/"GetWaterMID"))
 * so the module stays buildable with the plugin disabled or absent.
 *
 * Responsibilities (one authority, no second writer):
 *  - Sea Above horizon eater: configure OceanologyInfiniteOcean to 6km grid so the
 *    waterline eats the horizon, not a 500m false-ocean plane (SEA_ABOVE doc §4.2).
 *    Real ocean is at Z=0 SLW (Single Layer Water); false ocean plane at -50m is
 *    presentation-only and never becomes a Water Body.
 *  - Cymatic ripple displacement: sample WorldField.Resonance/Tension (Chladni
 *    N,M + Tension) and drive reflected Oceanology scalar params:
 *      Biolum_Intensity, Cymatic_RippleWeight, Cymatic_Tension, Toon_Weight
 *    plus native SLW params (PhaseGLow / ScatterBoost) via SetScalarParameterValue.
 *    WPO/displacement is NEVER touched — shading only (project invariant).
 *  - Height-aware placement: SeaAbove water at Z=0; Faraway Mother valley uses
 *    Z-thresholds — water only where terrain is below ValleyWaterThreshold (-800),
 *    valley fog where above, basin pooling where Tension is high in depressions.
 *  - LOD destruction reflection: when Faraway HLOD dissolves (fabric mountain
 *    crumbling), water shoreline SDF / foam / reveal opacity lerps so the mountain
 *    appears to dissolve *into* water rather than popping.
 *
 * Mirrors UMelodiaAudioReactivePresentationSubsystem's ocean beat drive but
 * for the cymatic/WorldField path. Both drives write grafted params only
 * (Biolum_*, Toon_*, Cymatic_*) — plugin-namespace params are untouched.
 */
USTRUCT(BlueprintType)
struct FOceanologyHorizonConfig
{
    GENERATED_BODY()
    /** Horizon-eater grid half-extent in cm. 600000 = 6km — edge past SLW extinction. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Oceanology|Horizon") float GridExtentCm = 600000.f;
    /** Real ocean surface Z (Sea Above). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Oceanology|Horizon") float WaterLevelZ = 0.f;
    /** Valley water threshold for Faraway Mother (only below this Z is water). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Oceanology|HeightAware") float ValleyWaterThreshold = -800.f;
    /** Valley fog vs water — above threshold is fog only. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Oceanology|HeightAware") float ValleyFogThreshold = -400.f;
    /** Basin depression threshold where standing-wave pooling is strongest. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Oceanology|HeightAware") float BasinDepressionZ = -1200.f;
    /** Force re-apply horizon config every N seconds (editor drift). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Oceanology|Horizon") float RescanIntervalSec = 2.f;
};

UENUM(BlueprintType)
enum class EWaterPlacementDecision : uint8
{
    Water       UMETA(DisplayName="Water"),
    Fog         UMETA(DisplayName="Valley Fog (no water)"),
    BasinPool   UMETA(DisplayName="Basin Pool (cymatic pooling)"),
    AboveWater  UMETA(DisplayName="Above Water (dry ridge)")
};

UCLASS()
class BS_GODFILE_API UMelodiaOceanologyWaterBridgeSubsystem final : public UWorldSubsystem
{
    GENERATED_BODY()
public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    /** Height-aware water vs fog decision for any world position. */
    UFUNCTION(BlueprintPure, Category="Melodia|Oceanology|Placement")
    EWaterPlacementDecision GetWaterPlacementDecision(FVector WorldPos) const;

    /** True if world position should show water (vs fog/dry). */
    UFUNCTION(BlueprintPure, Category="Melodia|Oceanology|Placement")
    bool IsWaterHeight(FVector WorldPos) const { return GetWaterPlacementDecision(WorldPos) != EWaterPlacementDecision::Fog && GetWaterPlacementDecision(WorldPos) != EWaterPlacementDecision::AboveWater; }

    /** LOD dissolve factor for water reveal: 0 = mountain intact, 1 = fully dissolved into water. */
    UFUNCTION(BlueprintPure, Category="Melodia|Oceanology|LOD")
    float GetLODDissolveWaterReveal(int32 CurrentLOD, int32 MaxLOD) const;

    /** Faraway shoreline blend: how much water should bleed into dissolving fabric (0..1). */
    UFUNCTION(BlueprintPure, Category="Melodia|Oceanology|LOD")
    float GetShorelineRevealForLOD(int32 CurrentLOD) const;

    /** Config — edited per level (SeaAbove vs FarawayMother data layer). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Oceanology|Config")
    FOceanologyHorizonConfig HorizonConfig;

private:
    bool TickBridge(float DeltaTime);
    void DiscoverOceanActors();
    void ApplyHorizonEaterConfig();
    void DriveCymaticRipples(float BeatPulse, float Tension, int32 ResonanceN, int32 ResonanceM);
    void DriveLODDissolveReflection();

    struct FOceanBridgeEntry
    {
        TWeakObjectPtr<AActor> OceanActor;
        TWeakObjectPtr<UObject> WaterMID; // UMaterialInstanceDynamic via UObject to avoid header
    };
    TArray<FOceanBridgeEntry> OceanEntries;
    double LastRescanTime = 0.0;
    double LastHorizonApplyTime = 0.0;
    FTSTicker::FDelegateHandle TickerHandle;

    // Height-aware: last known terrain Z per level (for offline probe fallback)
    float CachedSeaAboveWaterZ = 0.f;
};
