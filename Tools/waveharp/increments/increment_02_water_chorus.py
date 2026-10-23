"""Increment 2 - the water chorus: the world's water sings with the beat.

Adds:
  * FMelodiaWaterChorus (a plain C++ class, no reflected surface, no UHT pass): it binds
    the world's FluidNinja surfaces by ROLE, disperses rain over the horizon on every
    downbeat, dots the skyline with bubbles, beads Melusina's hair with globules, and
    lets the bass band drive the bound fluid surfaces so the puddles sing.
  * the waveharp component owns it: Start in BeginPlay, Tick in the tick, Stop in
    EndPlay, and a Burst on the form change - the magical-girl water transform.

Every system it dispatches already exists in the project. It authors no graphs, and it
READS the cymatics MPC - the cymatics writer stays the sole writer.
"""
from pathlib import Path

REPO = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
H = REPO / "Source/BS_GodFile/MelodiaIntegration/MelodiaWaveHarpCombatComponent.h"
C = REPO / "Source/BS_GodFile/MelodiaIntegration/MelodiaWaveHarpCombatComponent.cpp"
WH = REPO / "Source/BS_GodFile/MelodiaIntegration/MelodiaWaterChorus.h"
WC = REPO / "Source/BS_GodFile/MelodiaIntegration/MelodiaWaterChorus.cpp"

header = H.read_text(encoding="utf-8")
source = C.read_text(encoding="utf-8")
wheader = WH.read_text(encoding="utf-8")
wsource = WC.read_text(encoding="utf-8")


def swap(text, old, new, label):
    if old not in text:
        raise SystemExit("ANCHOR MISSING: " + label)
    if text.count(old) != 1:
        raise SystemExit("ANCHOR NOT UNIQUE (%d): %s" % (text.count(old), label))
    return text.replace(old, new)


# ------------------------------------------------------------------ the chorus: a burst
wheader = swap(
    wheader,
    """ int32 GetBeatCount() const { return Beats; }
 int32 GetDispatchCount() const { return Dispatches; }""",
    """ int32 GetBeatCount() const { return Beats; }
 int32 GetDispatchCount() const { return Dispatches; }

 /** The water transform: a full burst around the character. Used on the form change. */
 void Burst(AActor* Owner, float Scale = 2.2f);""",
    "chorus header burst")

wsource = swap(
    wsource,
    """void FMelodiaWaterChorus::Tick(float Delta, AActor* Owner)""",
    """void FMelodiaWaterChorus::Burst(AActor* Owner, const float Scale)
{
 if (!Owner) return;
 ++Dispatches;
 const FVector Base = Owner->GetActorLocation();
 if (UNiagaraSystem* Globules = LoadObject<UNiagaraSystem>(nullptr, MelodiaWaterChorusPaths::HairGlobules))
 {
  const FVector Where = Base + FVector(0.f, 0.f, 140.f);
  UNiagaraFunctionLibrary::SpawnSystemAtLocation(nullptr, Globules, Where, FRotator::ZeroRotator,
   FVector(Scale * .8f));
 }
 if (UNiagaraSystem* Splash = LoadObject<UNiagaraSystem>(nullptr, MelodiaWaterChorusPaths::FootSplash))
 {
  const FVector Where = Base + FVector(0.f, 0.f, 8.f);
  UNiagaraFunctionLibrary::SpawnSystemAtLocation(nullptr, Splash, Where, FRotator::ZeroRotator,
   FVector(Scale));
 }
 if (UNiagaraSystem* Mist = LoadObject<UNiagaraSystem>(nullptr, MelodiaWaterChorusPaths::SkylineMist))
 {
  const FVector Where = Base + FVector(0.f, 0.f, 60.f);
  UNiagaraFunctionLibrary::SpawnSystemAtLocation(nullptr, Mist, Where, FRotator::ZeroRotator,
   FVector(Scale * 1.4f));
 }
 UE_LOG(LogTemp, Log, TEXT("MELODIA_WATER_CHORUS burst scale=%.2f"), Scale);
}

void FMelodiaWaterChorus::Tick(float Delta, AActor* Owner)""",
    "chorus burst body")

# ------------------------------------------------------------------ the component: own it
header = swap(
    header,
    """#include "ProceduralMeshComponent.h"
#include "MelodiaWaveHarpCombatComponent.generated.h\"""",
    """#include "ProceduralMeshComponent.h"
#include "MelodiaWaterChorus.h"
#include "MelodiaWaveHarpCombatComponent.generated.h\"""",
    "component include")

header = swap(
    header,
    """ /** The aftermath length, seconds. The weight lands here, not in the swap. */""",
    """ /** The water chorus: the world's water sings with the beat, and Melusina's hair
 *  globulates on it. OFF by default; the owner turns it on once the surfaces are
 *  placed in the level. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Chorus")
 bool bEnableWaterChorus = false;

 /** The aftermath length, seconds. The weight lands here, not in the swap. */""",
    "component chorus flag")

header = swap(
    header,
    """ /** The stage the transition entered, used to fire each stage's beats exactly once. */
 EMelodiaWaveHarpFormStage LastFiredStage = EMelodiaWaveHarpFormStage::Idle;""",
    """ /** The stage the transition entered, used to fire each stage's beats exactly once. */
 EMelodiaWaveHarpFormStage LastFiredStage = EMelodiaWaveHarpFormStage::Idle;
 /** The world's water chorus. A plain C++ class: no reflected surface, no new owner
  *  on an existing surface - it READS the cymatics MPC and writes nothing. */
 FMelodiaWaterChorus WaterChorus;""",
    "component chorus member")

source = swap(
    source,
    """ UpdateInstruments(0.f);
}""",
    """ UpdateInstruments(0.f);
 if (bEnableWaterChorus && GetWorld())
 {
  WaterChorus.Start(*GetWorld());
  UE_LOG(LogTemp, Log, TEXT("MELODIA_WAVEHARP_CHORUS enabled"));
 }
}""",
    "component chorus start")

source = swap(
    source,
    """ if (ScytheRibbon) ScytheRibbon->DestroyComponent();
 if (Wand) Wand->DestroyComponent();""",
    """ if (ScytheRibbon) ScytheRibbon->DestroyComponent();
 if (Wand) Wand->DestroyComponent();
 WaterChorus.Stop();""",
    "component chorus stop")

source = swap(
    source,
    """ UpdateAimCamera(Delta);
 UpdateFormTransition(Delta);
 UpdateInstruments(Delta);""",
    """ UpdateAimCamera(Delta);
 UpdateFormTransition(Delta);
 UpdateInstruments(Delta);
 if (bEnableWaterChorus) WaterChorus.Tick(Delta, Character.Get());""",
    "component chorus tick")

source = swap(
    source,
    """ UpdateWandPresentation();
}""",
    """ UpdateWandPresentation();
 // The water transform: the form change breaks the surface of the world.
 if (bEnableWaterChorus) WaterChorus.Burst(Character.Get());
}""",
    "component chorus burst")

WH.write_text(wheader, encoding="utf-8")
WC.write_text(wsource, encoding="utf-8")
H.write_text(header, encoding="utf-8")
C.write_text(source, encoding="utf-8")
print("increment 2 applied: the water chorus")
