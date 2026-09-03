#include "MelodiaOceanologyWaterBridgeSubsystem.h"
#include "MelodiaWorldFieldBus.h"
#include "MelodiaCymaticsSubsystem.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "Containers/Ticker.h"
#include "ProfilingDebugging/CpuProfilerTrace.h"

static constexpr TCHAR OceanActorToken[] = TEXT("Oceanology");
static constexpr TCHAR MPCPalettePath[]  = TEXT("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.MPC_Melodia_Palette");
static constexpr TCHAR MPCCymaticsPath[] = TEXT("/Game/Melodia/Cymatics/MPC_Cymatics_Driver.MPC_Cymatics_Driver");

// Tunables — cymatic Tension -> water ripple scale
static constexpr float CymaticRippleGain = 1.1f;
static constexpr float BasinPoolTensionBoost = 0.35f;

void UMelodiaOceanologyWaterBridgeSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    TickerHandle = FTSTicker::GetCoreTicker().AddTicker(
        FTickerDelegate::CreateUObject(this, &UMelodiaOceanologyWaterBridgeSubsystem::TickBridge));
}

void UMelodiaOceanologyWaterBridgeSubsystem::Deinitialize()
{
    if (TickerHandle.IsValid())
    {
        FTSTicker::GetCoreTicker().RemoveTicker(TickerHandle);
        TickerHandle.Reset();
    }
    OceanEntries.Reset();
    Super::Deinitialize();
}

EWaterPlacementDecision UMelodiaOceanologyWaterBridgeSubsystem::GetWaterPlacementDecision(FVector WorldPos) const
{
    const float Z = WorldPos.Z;
    // Sea Above: water is at HorizonConfig.WaterLevelZ (0). Anything above is dry.
    // Faraway Mother: three bands — mirror build_faraway_mother_height_aware_pcg.py choices
    //   ridge_high/mid/low: 2800-3800 -> AboveWater
    //   shoulder_fold: 1500 -> AboveWater (fabric, not water)
    //   valley_floor: -800 -> Water or Fog
    //   valley_depression: -1200 -> BasinPool
    if (Z > HorizonConfig.ValleyFogThreshold)
    {
        return EWaterPlacementDecision::AboveWater;
    }
    if (Z > HorizonConfig.ValleyWaterThreshold)
    {
        return EWaterPlacementDecision::Fog; // valley fog volume, no water surface
    }
    if (Z <= HorizonConfig.BasinDepressionZ)
    {
        return EWaterPlacementDecision::BasinPool; // cymatic pooling depression
    }
    return EWaterPlacementDecision::Water;
}

float UMelodiaOceanologyWaterBridgeSubsystem::GetLODDissolveWaterReveal(int32 CurrentLOD, int32 MaxLOD) const
{
    if (MaxLOD <= 0) return 0.f;
    // LOD0 intact -> 0, LOD Max -> 1 (fully dissolved into water). Ease.
    const float T = FMath::Clamp(static_cast<float>(CurrentLOD) / static_cast<float>(MaxLOD), 0.f, 1.f);
    // smoothstep so reveal accelerates at LOD2+
    return T * T * (3.f - 2.f * T);
}

float UMelodiaOceanologyWaterBridgeSubsystem::GetShorelineRevealForLOD(int32 CurrentLOD) const
{
    // Faraway shoreline SDF blend — shoreline bleeds into water as LOD climbs
    // LOD0 0, LOD1 0.15, LOD2 0.55, LOD3 1.0
    static const float Table[4] = {0.f, 0.15f, 0.55f, 1.0f};
    const int32 Clamped = FMath::Clamp(CurrentLOD, 0, 3);
    return Table[Clamped];
}

bool UMelodiaOceanologyWaterBridgeSubsystem::TickBridge(float DeltaTime)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MelodiaOceanologyWaterBridge_Tick);
    UWorld* World = GetWorld();
    if (!World || !World->IsGameWorld())
    {
        return true;
    }

    const double Now = FPlatformTime::Seconds();
    const bool bRescan = (Now - LastRescanTime) > HorizonConfig.RescanIntervalSec;
    if (bRescan)
    {
        LastRescanTime = Now;
        DiscoverOceanActors();
    }
    if ((Now - LastHorizonApplyTime) > HorizonConfig.RescanIntervalSec)
    {
        LastHorizonApplyTime = Now;
        ApplyHorizonEaterConfig();
    }

    // Read WorldField.Resonance/Tension — the cymatic source bus.
    // Preference: live cymatics subsystem; fallback: UWorldFieldBus::LastPublished.
    float BeatPulse = 0.f;
    float Tension = 0.f;
    int32 ResonanceN = 2, ResonanceM = 3;

    if (UGameInstance* GI = World->GetGameInstance())
    {
        if (UMelodiaCymaticsSubsystem* Cym = GI->GetSubsystem<UMelodiaCymaticsSubsystem>())
        {
            BeatPulse = Cym->GetBeatPulse();
            Tension = FMath::Abs(Cym->SampleCymaticAmplitude(0.5f, 0.5f));
            Cym->GetCymaticMode(ResonanceN, ResonanceM);
        }
        else
        {
            const FWorldFieldSample S = UWorldFieldBus::SampleResonanceTension(FVector::ZeroVector);
            ResonanceN = S.ResonanceN; ResonanceM = S.ResonanceM;
            Tension = S.Tension; BeatPulse = S.BeatPulse;
        }
    }

    // Also read MPC_Cymatics_Driver Tension override (Writer lane may hold fresher Bass)
    if (UMaterialParameterCollection* CymMPC = LoadObject<UMaterialParameterCollection>(nullptr, MPCCymaticsPath))
    {
        if (UMaterialParameterCollectionInstance* Inst = World->GetParameterCollectionInstance(CymMPC))
        {
            float Bass = 0.f;
            if (Inst->GetScalarParameterValue(FName(TEXT("Cymatic_BassIntensity")), Bass))
            {
                Tension = FMath::Max(Tension, Bass * 0.85f);
            }
        }
    }

    DriveCymaticRipples(BeatPulse, Tension, ResonanceN, ResonanceM);
    DriveLODDissolveReflection();
    return true;
}

void UMelodiaOceanologyWaterBridgeSubsystem::DiscoverOceanActors()
{
    UWorld* World = GetWorld();
    if (!World) return;

    OceanEntries.RemoveAll([](const FOceanBridgeEntry& E){ return !E.OceanActor.IsValid(); });

    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (!Actor || !Actor->GetClass()->GetName().Contains(OceanActorToken))
        {
            continue;
        }
        bool bKnown = false;
        for (const auto& E : OceanEntries)
        {
            if (E.OceanActor.Get() == Actor) { bKnown = true; break; }
        }
        if (bKnown) continue;

        // Prefer GetWaterMID (plugin API) — reflected, no header.
        UObject* Mid = nullptr;
        if (UFunction* GetMidFunc = Actor->FindFunction(FName(TEXT("GetWaterMID"))))
        {
            struct FGetMidParams { UObject* ReturnValue = nullptr; };
            FGetMidParams P;
            Actor->ProcessEvent(GetMidFunc, &P);
            Mid = P.ReturnValue;
        }
        // Fallback: mesh material 0 if MID not yet created (editor PIE race)
        if (!Mid)
        {
            if (UFunction* GetMeshMid = Actor->FindFunction(FName(TEXT("GetWaterMaterial"))))
            {
                // Some builds expose GetWaterMaterial instead
                (void)GetMeshMid;
            }
        }

        FOceanBridgeEntry Entry;
        Entry.OceanActor = Actor;
        Entry.WaterMID = Mid;
        OceanEntries.Add(Entry);

        UE_LOG(LogTemp, Log, TEXT("[OceanBridge] Registered %s (MID %s) — horizon %0.0f cm, valley thresholds %0.0f/%0.0f/%0.0f"),
            *Actor->GetName(), Mid ? *Mid->GetName() : TEXT("None"),
            HorizonConfig.GridExtentCm, HorizonConfig.ValleyWaterThreshold,
            HorizonConfig.ValleyFogThreshold, HorizonConfig.BasinDepressionZ);
    }
}

void UMelodiaOceanologyWaterBridgeSubsystem::ApplyHorizonEaterConfig()
{
    // The OceanologyInfiniteOcean quad-tree tiles infinitely, but its
    // effective horizon is bounded by SLW extinction + scattering + draw distance.
    // Push horizon-eater params via reflected SetScalarParameterValue so the
    // 6km water grid genuinely eats the horizon past SLW extinction (~1.2km)
    // instead of a 500m plane with a visible edge (SeaAbove doc §4.2).
    for (auto& Entry : OceanEntries)
    {
        AActor* Actor = Entry.OceanActor.Get();
        if (!Actor) continue;

        // Refresh MID handle if it was null at discovery time
        if (!Entry.WaterMID.IsValid())
        {
            if (UFunction* GetMidFunc = Actor->FindFunction(FName(TEXT("GetWaterMID"))))
            {
                struct FGetMidParams { UObject* ReturnValue = nullptr; };
                FGetMidParams P;
                Actor->ProcessEvent(GetMidFunc, &P);
                Entry.WaterMID = P.ReturnValue;
            }
        }

        UFunction* SetScalar = Actor->FindFunction(FName(TEXT("SetScalarParameterValue")));
        UFunction* SetVector = Actor->FindFunction(FName(TEXT("SetVectorParameterValue")));
        if (!SetScalar) continue;

        auto PushScalar = [&](FName Name, float Value)
        {
            struct FSetScalarParams { FName ParameterName; float Value; };
            FSetScalarParams P{ Name, Value };
            Actor->ProcessEvent(SetScalar, &P);
        };

        // Horizon eater — ensure water grid is not clamped to 500m prototype.
        // These are grafted/custom scalars on M_Water_Oceanology_Melodia:
        PushScalar(FName(TEXT("HorizonGridExtent")), HorizonConfig.GridExtentCm);
        PushScalar(FName(TEXT("WaterLevelZ")), HorizonConfig.WaterLevelZ);
        PushScalar(FName(TEXT("ValleyWaterThreshold")), HorizonConfig.ValleyWaterThreshold);

        // SLW absorption tuning — the "non-physical haze budget of kilometres over metres"
        // that makes the second ocean read as kilometres deep (SeaAbove doc §3).
        // Kept conservative here; lookdev tunes via MI, not code.
        PushScalar(FName(TEXT("AbsorptionExtinctionTune")), 1.f);

        // Also drive shoreline RVT hint so valley water meets fabric without popping
        PushScalar(FName(TEXT("ShorelineBlend")), 0.f); // overridden per LOD in DriveLODDissolveReflection

        if (SetVector)
        {
            (void)SetVector; // reserved for DeepScatteringColor cymatic tint below
        }
    }
}

void UMelodiaOceanologyWaterBridgeSubsystem::DriveCymaticRipples(float BeatPulse, float Tension, int32 ResonanceN, int32 ResonanceM)
{
    // Tension is 0..1 Chladni amplitude; BeatPulse is 0..1 cos^2 beat.
    // Map to water ripple displacement *as shading* — WaveAmplitude / ripple weight,
    // never WPO. This keeps Oceanology CPU/GPU wave solvers in sync.
    const float RippleWeight = FMath::Clamp(BeatPulse * CymaticRippleGain + Tension * 0.6f, 0.f, 1.f);
    const float TensionWeight = FMath::Clamp(Tension, 0.f, 1.f);
    // Basin pooling bias: depressions pool more when Tension is high
    const float BasinRipple = FMath::Clamp(RippleWeight + Tension * BasinPoolTensionBoost, 0.f, 1.f);

    for (auto& Entry : OceanEntries)
    {
        AActor* Actor = Entry.OceanActor.Get();
        if (!Actor) continue;

        // 1) Reflected Oceanology actor API — writes WaterMID + far MID together
        if (UFunction* SetScalar = Actor->FindFunction(FName(TEXT("SetScalarParameterValue"))))
        {
            auto Push = [&](const TCHAR* Name, float V)
            {
                struct FSetScalarParams { FName ParameterName; float Value; };
                FSetScalarParams P{ FName(Name), V };
                Actor->ProcessEvent(SetScalar, &P);
            };
            // Grafted params on M_Water_Oceanology_Melodia (never overwritten by plugin helpers)
            Push(TEXT("Cymatic_RippleWeight"), RippleWeight);
            Push(TEXT("Cymatic_BasinRipple"), BasinRipple);
            Push(TEXT("Cymatic_Tension"), TensionWeight);
            Push(TEXT("Cymatic_ResonanceN"), static_cast<float>(ResonanceN));
            Push(TEXT("Cymatic_ResonanceM"), static_cast<float>(ResonanceM));
            // Also ride the existing Biolum_*/Toon_* grafts so cymatic pulses are visible even before
            // the Cymatic_* params are wired in the master.
            Push(TEXT("Biolum_Intensity"), 1.0f + BeatPulse * 1.2f + Tension * 0.5f);
            // Keep Toon_Weight ride subtle — SLW banding must stay hand-matched to reef
            Push(TEXT("Toon_Weight"), 0.60f + Tension * 0.12f);
        }

        // 2) Direct MID fallback (if GetWaterMID resolved)
        if (UMaterialInstanceDynamic* Mid = Cast<UMaterialInstanceDynamic>(Entry.WaterMID.Get()))
        {
            Mid->SetScalarParameterValue(FName(TEXT("Cymatic_RippleWeight")), RippleWeight);
            Mid->SetScalarParameterValue(FName(TEXT("Cymatic_Tension")), TensionWeight);
            Mid->SetScalarParameterValue(FName(TEXT("Biolum_Intensity")), 1.0f + BeatPulse * 1.2f + Tension * 0.5f);
        }

        // 3) Reflected vector tint — cymatic Tension pulls DeepScattering toward violet on peaks
        if (UFunction* SetVector = Actor->FindFunction(FName(TEXT("SetVectorParameterValue"))))
        {
            struct FSetVectorParams { FName ParameterName; FLinearColor Value; };
            const float VioletPull = Tension * 0.10f;
            FSetVectorParams P{ FName(TEXT("DeepScatteringColor")),
                FLinearColor(0.05f + VioletPull * 0.6f, 0.25f - VioletPull * 0.2f, 0.30f + VioletPull, 0.15f) };
            Actor->ProcessEvent(SetVector, &P);
        }
    }
}

void UMelodiaOceanologyWaterBridgeSubsystem::DriveLODDissolveReflection()
{
    // LOD reflection: as Faraway fabric HLOD dissolves (LOD climbs), water's
    // shoreline/foam/reveal lerps so mountains appear to dissolve *into* water
    // rather than popping. Driven per tick so owner can push LOD via console
    // or HLOD system and water follows within one frame.
    //
    // Source of truth for current LOD is external (HLOD / Nanite fallback /
    // manual dissolve scalar). For scaffold we read a global MPC dissolve scalar
    // if present, else assume LOD0 (no dissolve) so Sea Above is unaffected.

    UWorld* World = GetWorld();
    if (!World) return;

    float DissolveT = 0.f; // 0 intact, 1 fully dissolved
    if (UMaterialParameterCollection* Palette = LoadObject<UMaterialParameterCollection>(nullptr, MPCPalettePath))
    {
        if (UMaterialParameterCollectionInstance* Inst = World->GetParameterCollectionInstance(Palette))
        {
            // Optional scalar published by HLOD / dress pass — absent = 0 (safe)
            Inst->GetScalarParameterValue(FName(TEXT("FarawayDissolveT")), DissolveT);
        }
    }
    if (DissolveT <= KINDA_SMALL_NUMBER)
    {
        return; // off-path — no per-frame work, no log spam
    }

    const float ShorelineReveal = FMath::Clamp(DissolveT, 0.f, 1.f);
    const float FoamReveal = FMath::Clamp(DissolveT * 0.9f + 0.1f, 0.f, 1.f);
    const float WaterOpacity = FMath::Clamp(0.65f + DissolveT * 0.35f, 0.f, 1.f);

    for (auto& Entry : OceanEntries)
    {
        AActor* Actor = Entry.OceanActor.Get();
        if (!Actor) continue;
        if (UFunction* SetScalar = Actor->FindFunction(FName(TEXT("SetScalarParameterValue"))))
        {
            auto Push = [&](const TCHAR* Name, float V)
            {
                struct FSetScalarParams { FName ParameterName; float Value; };
                FSetScalarParams P{ FName(Name), V };
                Actor->ProcessEvent(SetScalar, &P);
            };
            Push(TEXT("ShorelineBlend"), ShorelineReveal);
            Push(TEXT("FoamReveal"), FoamReveal);
            Push(TEXT("WaterRevealOpacity"), WaterOpacity);
            // Tie dissolve into cymatic pool so dissolving ridges shimmer
            Push(TEXT("Cymatic_DissolveT"), DissolveT);
        }
        if (UMaterialInstanceDynamic* Mid = Cast<UMaterialInstanceDynamic>(Entry.WaterMID.Get()))
        {
            Mid->SetScalarParameterValue(FName(TEXT("ShorelineBlend")), ShorelineReveal);
            Mid->SetScalarParameterValue(FName(TEXT("WaterRevealOpacity")), WaterOpacity);
        }
    }
}
