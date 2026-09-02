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

    // Optionally modulate Tension by world position (distance from valley center)
    // For Faraway Mother: tension is strongest where VDM fold depth is highest
    // This is the minimum contract — no generalized framework, just Resonance/Tension
    float DistFromCenter = FVector2D(WorldPos).Size();
    float Falloff = FMath::Clamp(1.f - DistFromCenter / 5000.f, 0.f, 1.f);
    Sample.Tension *= Falloff;

    return Sample;
}

void UWorldFieldBus::PublishResonance(int32 N, int32 M, float Tension, float BeatPulse)
{
    LastPublished.ResonanceN = N;
    LastPublished.ResonanceM = M;
    LastPublished.Tension = Tension;
    LastPublished.BeatPulse = BeatPulse;
}
