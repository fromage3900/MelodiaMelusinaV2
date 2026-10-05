#include "MelodiaWorldFieldBus.h"
#include "MelodiaCymaticsSubsystem.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

FWorldFieldSample UWorldFieldBus::LastPublished;
TArray<FWorldFieldSource> UWorldFieldBus::Sources;
int32 UWorldFieldBus::NextSourceId = 1;

FWorldFieldSample UWorldFieldBus::SampleResonanceTension(FVector WorldPos)
{
    // LEGACY global path, unchanged: last published cymatic field + radial falloff.
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

FWorldFieldSample UWorldFieldBus::SampleAt(FVector WorldPos)
{
    FWorldFieldSample Out = LastPublished;
    Out.WorldPosition = WorldPos;
    if (Sources.Num() == 0)
    {
        return Out;
    }

    // Nearest-weighted blend of the sources that cover this point. Cosine falloff keeps
    // the blend continuous at the source boundary (zero slope at the radius edge).
    float SumTension = 0.f;
    float SumBeatPulse = 0.f;
    float SumConsonance = 0.f;
    float SumWeight = 0.f;
    FWorldFieldSample Dominant = LastPublished;
    float DominantWeight = -1.f;

    for (const FWorldFieldSource& Src : Sources)
    {
        if (Src.RadiusCm <= 0.f)
        {
            continue;
        }
        const float Dist = FVector::Dist(WorldPos, Src.Sample.WorldPosition);
        if (Dist >= Src.RadiusCm)
        {
            continue;
        }
        const float Norm = Dist / Src.RadiusCm;
        const float Falloff = 0.5f * (1.f + FMath::Cos(UE_PI * Norm));
        const float C = Falloff * Src.Weight;
        if (C <= 1e-4f)
        {
            continue;
        }
        SumTension += Src.Sample.Tension * C;
        SumBeatPulse += Src.Sample.BeatPulse * C;
        SumConsonance += Src.Sample.Consonance * C;
        SumWeight += C;
        if (C > DominantWeight)
        {
            DominantWeight = C;
            Dominant = Src.Sample;
        }
    }

    if (SumWeight > 1e-4f)
    {
        Out.Tension = FMath::Clamp(SumTension / SumWeight, 0.f, 1.f);
        Out.BeatPulse = FMath::Clamp(SumBeatPulse / SumWeight, 0.f, 1.f);
        Out.Consonance = FMath::Clamp(SumConsonance / SumWeight, 0.f, 1.f);
        // The discrete signature (N, M, Mode) belongs to the dominant local field, not a blend.
        Out.ResonanceN = Dominant.ResonanceN;
        Out.ResonanceM = Dominant.ResonanceM;
        Out.Mode = Dominant.Mode;
    }
    return Out;
}

void UWorldFieldBus::PublishResonance(int32 N, int32 M, float Tension, float BeatPulse)
{
    LastPublished.ResonanceN = N;
    LastPublished.ResonanceM = M;
    LastPublished.Tension = Tension;
    LastPublished.BeatPulse = BeatPulse;
}

int32 UWorldFieldBus::PublishFieldSource(FVector WorldPos, float RadiusCm,
    int32 N, int32 M, float Tension, float BeatPulse, uint8 Mode, float Consonance, float Weight)
{
    FWorldFieldSource Src;
    Src.Id = NextSourceId++;
    Src.Sample.ResonanceN = N;
    Src.Sample.ResonanceM = M;
    Src.Sample.Tension = Tension;
    Src.Sample.BeatPulse = BeatPulse;
    Src.Sample.Mode = Mode;
    Src.Sample.Consonance = Consonance;
    Src.Sample.WorldPosition = WorldPos;
    Src.RadiusCm = RadiusCm;
    Src.Weight = Weight;
    Sources.Add(Src);
    return Src.Id;
}

void UWorldFieldBus::RemoveFieldSource(int32 SourceId)
{
    for (int32 i = Sources.Num() - 1; i >= 0; --i)
    {
        if (Sources[i].Id == SourceId)
        {
            Sources.RemoveAt(i);
            return;
        }
    }
}
