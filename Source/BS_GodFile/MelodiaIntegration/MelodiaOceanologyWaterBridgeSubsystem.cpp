#include "MelodiaOceanologyWaterBridgeSubsystem.h"
#include "MelodiaWorldFieldBus.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "Containers/Ticker.h"
#include "ProfilingDebugging/CpuProfilerTrace.h"
#include "UObject/StructOnScope.h"
#include "UObject/UnrealType.h"

static constexpr TCHAR OceanActorToken[] = TEXT("Oceanology");
static constexpr TCHAR MPCPalettePath[]  = TEXT("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.MPC_Melodia_Palette");

// Tunables — cymatic Tension -> water ripple scale
static constexpr float CymaticRippleGain = 1.1f;
static constexpr float BasinPoolTensionBoost = 0.35f;

namespace MelodiaOceanologyBridge
{
    UObject* GetWaterMID(AActor* Actor)
    {
        UFunction* Function = Actor->FindFunction(TEXT("GetWaterMID"));
        FObjectPropertyBase* ReturnProperty = Function
            ? FindFProperty<FObjectPropertyBase>(Function, TEXT("ReturnValue")) : nullptr;
        if (!ReturnProperty || !ReturnProperty->HasAnyPropertyFlags(CPF_ReturnParm) || Function->NumParms != 1)
        {
            return nullptr;
        }

        FStructOnScope Params(Function);
        Actor->ProcessEvent(Function, Params.GetStructMemory());
        return ReturnProperty->GetObjectPropertyValue_InContainer(Params.GetStructMemory());
    }

    void SetScalar(AActor* Actor, UObject* WaterMID, FName Name, float Value)
    {
        UFunction* Function = Actor->FindFunction(TEXT("SetScalarParameterValue"));
        FNameProperty* NameProperty = Function
            ? FindFProperty<FNameProperty>(Function, TEXT("ParameterName")) : nullptr;
        FFloatProperty* ValueProperty = Function
            ? FindFProperty<FFloatProperty>(Function, TEXT("Value")) : nullptr;
        if (NameProperty && ValueProperty && Function->NumParms == 2
            && NameProperty->HasAnyPropertyFlags(CPF_Parm) && ValueProperty->HasAnyPropertyFlags(CPF_Parm)
            && !NameProperty->HasAnyPropertyFlags(CPF_OutParm | CPF_ReturnParm)
            && !ValueProperty->HasAnyPropertyFlags(CPF_OutParm | CPF_ReturnParm))
        {
            FStructOnScope Params(Function);
            NameProperty->SetPropertyValue_InContainer(Params.GetStructMemory(), Name);
            ValueProperty->SetPropertyValue_InContainer(Params.GetStructMemory(), Value);
            Actor->ProcessEvent(Function, Params.GetStructMemory());
        }
        else if (UMaterialInstanceDynamic* MID = Cast<UMaterialInstanceDynamic>(WaterMID))
        {
            MID->SetScalarParameterValue(Name, Value);
        }
    }
}

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

    // Consume the published field; cymatics owns how resonance and tension are produced.
    const FWorldFieldSample Field = UWorldFieldBus::SampleResonanceTension(FVector::ZeroVector);
    DriveCymaticRipples(Field.BeatPulse, Field.Tension, Field.ResonanceN, Field.ResonanceM);
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
        UObject* Mid = MelodiaOceanologyBridge::GetWaterMID(Actor);

        FOceanBridgeEntry Entry;
        Entry.OceanActor = Actor;
        Entry.WaterMID = Mid;
        OceanEntries.Add(Entry);

        UE_LOG(LogTemp, Log, TEXT("[OceanBridge] Registered %s (MID %s) — valley thresholds %0.0f/%0.0f/%0.0f"),
            *Actor->GetName(), Mid ? *Mid->GetName() : TEXT("None"),
            HorizonConfig.ValleyWaterThreshold,
            HorizonConfig.ValleyFogThreshold, HorizonConfig.BasinDepressionZ);
    }
}

void UMelodiaOceanologyWaterBridgeSubsystem::ApplyHorizonEaterConfig()
{
    // Quadtree extent and actor Z are authored on the Oceanology actor in the editor.
    // Material scalars cannot configure that geometry; only refresh the fallback MID here.
    for (auto& Entry : OceanEntries)
    {
        AActor* Actor = Entry.OceanActor.Get();
        if (!Actor) continue;

        // Refresh MID handle if it was null at discovery time
        if (!Entry.WaterMID.IsValid())
        {
            Entry.WaterMID = MelodiaOceanologyBridge::GetWaterMID(Actor);
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

        // Oceanology's actor API writes near and far MIDs; direct MID is a fallback only.
        auto Push = [&](const TCHAR* Name, float Value)
        {
            MelodiaOceanologyBridge::SetScalar(Actor, Entry.WaterMID.Get(), FName(Name), Value);
        };
        // Dedicated cymatic shading only; audio-reactive presentation owns bioluminescence and tint.
        Push(TEXT("Cymatic_RippleWeight"), RippleWeight);
        Push(TEXT("Cymatic_BasinRipple"), BasinRipple);
        Push(TEXT("Cymatic_Tension"), TensionWeight);
        Push(TEXT("Cymatic_ResonanceN"), static_cast<float>(ResonanceN));
        Push(TEXT("Cymatic_ResonanceM"), static_cast<float>(ResonanceM));
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
    // manual dissolve scalar). Read the optional global MPC scalar only when present.

    UWorld* World = GetWorld();
    if (!World) return;

    float DissolveT = 0.f; // 0 intact, 1 fully dissolved
    bool bHasDissolveParameter = false;
    if (UMaterialParameterCollection* Palette = LoadObject<UMaterialParameterCollection>(nullptr, MPCPalettePath))
    {
        if (UMaterialParameterCollectionInstance* Inst = World->GetParameterCollectionInstance(Palette))
        {
            bHasDissolveParameter = Inst->GetScalarParameterValue(FName(TEXT("FarawayDissolveT")), DissolveT);
        }
    }
    if (!bHasDissolveParameter)
    {
        return; // This world has no dissolve driver; leave its authored water values alone.
    }

    // An existing driver returning to zero must restore all dedicated dissolve values.
    DissolveT = FMath::Clamp(DissolveT, 0.f, 1.f);
    const float ShorelineReveal = DissolveT;
    const float FoamReveal = FMath::Clamp(DissolveT * 0.9f + 0.1f, 0.f, 1.f);
    const float WaterOpacity = FMath::Clamp(0.65f + DissolveT * 0.35f, 0.f, 1.f);

    for (auto& Entry : OceanEntries)
    {
        AActor* Actor = Entry.OceanActor.Get();
        if (!Actor) continue;
        auto Push = [&](const TCHAR* Name, float Value)
        {
            MelodiaOceanologyBridge::SetScalar(Actor, Entry.WaterMID.Get(), FName(Name), Value);
        };
        Push(TEXT("ShorelineBlend"), ShorelineReveal);
        Push(TEXT("FoamReveal"), FoamReveal);
        Push(TEXT("WaterRevealOpacity"), WaterOpacity);
        // Tie dissolve into cymatic pool so dissolving ridges shimmer.
        Push(TEXT("Cymatic_DissolveT"), DissolveT);
    }
}
