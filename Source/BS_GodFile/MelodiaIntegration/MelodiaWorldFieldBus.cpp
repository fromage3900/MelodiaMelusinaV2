#include "MelodiaWorldFieldBus.h"
#include "MelodiaCymaticsSubsystem.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

FWorldFieldSample UWorldFieldBus::LastPublished;

FWorldFieldSample UWorldFieldBus::SampleResonanceTension(FVector WorldPos)
{
    // In PIE, read from cymatics subsystem; offline, return last published
    FWorldFieldSample Sample = LastPublished;
    Sample.WorldPosition = WorldPos;

    // Tension falloff: strongest at plate center, zero at 5km radius.
    // Faraway Mother VDM fold depth and valley pooling both key off this.
    float DistFromCenter = FVector2D(WorldPos).Size();
    float Falloff = FMath::Clamp(1.f - DistFromCenter / 5000.f, 0.f, 1.f);
    Sample.Tension *= Falloff;

    return Sample;
}

float UWorldFieldBus::SampleCymaticRipple(FVector WorldPos)
{
    // Map world XY to normalized plate UV (0..1) over 10km span, then Chladni.
    const float U = FMath::Clamp((WorldPos.X + 5000.f) / 10000.f, 0.f, 1.f);
    const float V = FMath::Clamp((WorldPos.Y + 5000.f) / 10000.f, 0.f, 1.f);
    const int32 N = LastPublished.ResonanceN;
    const int32 M = LastPublished.ResonanceM;
    const float PiU = UE_PI * U;
    const float PiV = UE_PI * V;
    const float A = FMath::Cos(N * PiU) * FMath::Cos(M * PiV);
    const float B = FMath::Cos(M * PiU) * FMath::Cos(N * PiV);
    const float Amp = FMath::Abs((A - B) * FMath::Max(LastPublished.BeatPulse, 0.15f));
    // Basin pooling bias: Tension lifts ripple in depressions
    return FMath::Clamp(Amp * 0.7f + LastPublished.Tension * 0.3f, 0.f, 1.f);
}

EWorldFieldWaterDecision UWorldFieldBus::GetWaterDecision(FVector WorldPos)
{
    const float Z = WorldPos.Z;
    // Thresholds mirror UMelodiaOceanologyWaterBridgeSubsystem::HorizonConfig
    // and build_faraway_mother_height_aware_pcg.py height bands.
    // SeaAbove: Z~0 is water, false ocean at -5000 is presentation-only.
    // Faraway: valley_floor -800, basin_depression -1200, fog_threshold -400.
    static constexpr float ValleyWaterThreshold = -800.f;
    static constexpr float ValleyFogThreshold = -400.f;
    static constexpr float BasinDepressionZ = -1200.f;

    if (Z > ValleyFogThreshold) return EWorldFieldWaterDecision::Dry;
    if (Z > ValleyWaterThreshold) return EWorldFieldWaterDecision::Fog;
    if (Z <= BasinDepressionZ) return EWorldFieldWaterDecision::BasinPool;
    return EWorldFieldWaterDecision::Water;
}

bool UWorldFieldBus::IsWaterHeight(FVector WorldPos)
{
    const EWorldFieldWaterDecision D = GetWaterDecision(WorldPos);
    return D == EWorldFieldWaterDecision::Water || D == EWorldFieldWaterDecision::BasinPool;
}

float UWorldFieldBus::GetLODDissolveWaterReveal(int32 CurrentLOD, int32 MaxLOD)
{
    if (MaxLOD <= 0) return 0.f;
    const float T = FMath::Clamp(static_cast<float>(CurrentLOD) / static_cast<float>(MaxLOD), 0.f, 1.f);
    return T * T * (3.f - 2.f * T); // smoothstep
}

void UWorldFieldBus::PublishResonance(int32 N, int32 M, float Tension, float BeatPulse)
{
    LastPublished.ResonanceN = N;
    LastPublished.ResonanceM = M;
    LastPublished.Tension = Tension;
    LastPublished.BeatPulse = BeatPulse;
}
