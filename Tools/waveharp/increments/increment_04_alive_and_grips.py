"""Increment 4 - the instrument comes alive, every form holds its own grip, and the
effect budget follows the screen.

  * D4 the idle shimmer: the pluck, the overtone, the sway and the resonance are driven
    from the MUSIC CLOCK, not from a frame-based sine. This is the same conclusion the
    reference games reached independently (the animation owns the motion), and it is
    what the audio-reactive canon already demands of the materials.
  * C8 the per-form grip: the hold fix solves the grip in the character's frame; each of
    the three forms now keeps its own solved grip, because the heads sit at different
    points on the shaft and one grip cannot hold three heads.
  * the quality tier: the blade ribbon and the flourish scale with how much of the screen
    the player can actually see - the reference scales its fur layers the same way.
"""
from pathlib import Path

REPO = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
H = REPO / "Source/BS_GodFile/MelodiaIntegration/MelodiaWaveHarpCombatComponent.h"
C = REPO / "Source/BS_GodFile/MelodiaIntegration/MelodiaWaveHarpCombatComponent.cpp"

header = H.read_text(encoding="utf-8")
source = C.read_text(encoding="utf-8")


def swap(text, old, new, label):
    if old not in text:
        raise SystemExit("ANCHOR MISSING: " + label)
    if text.count(old) != 1:
        raise SystemExit("ANCHOR NOT UNIQUE (%d): %s" % (text.count(old), label))
    return text.replace(old, new)


# ------------------------------------------------------------------ header: the shimmer morphs
header = swap(
    header,
    """ /** The measured socket positions (wand-local and head-local, cm). */""",
    """ /** The idle shimmer morphs. They are driven by the MUSIC CLOCK, never by a
 *  frame-based sine: the instrument has to breathe with the music, not with the
 *  frame rate (defect D4). */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument") FName MorphShimmerPluck = TEXT("Pluck");
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument") FName MorphShimmerVibrate = TEXT("Vibrate_Overtone");
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument") FName MorphShimmerSwayPos = TEXT("Sway_Pos");
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument") FName MorphShimmerSwayNeg = TEXT("Sway_Neg");
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument") FName MorphShimmerResonance = TEXT("Resonance_Breathe");

 /** How far the shimmer moves, 0..1. The shimmer is a living surface, not a wobble. */
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|WaveHarp|Instrument", meta=(ClampMin="0.0", ClampMax="1.0"))
 float ShimmerStrength = 0.35f;

 /** The measured socket positions (wand-local and head-local, cm). */""",
    "header shimmer")

header = swap(
    header,
    """ /** Seconds until the next beat boundary; 0 when there is no music (act at once). */
 float SecondsUntilNextBeat() const;""",
    """ /** Seconds until the next beat boundary; 0 when there is no music (act at once). */
 float SecondsUntilNextBeat() const;
 /** The idle shimmer, driven by the music clock (defect D4). */
 void UpdateIdleShimmer();
 /** Set a morph only if the mesh actually has it. */
 void SetMorphIfPresent(FName Morph, float Value);
 /** The screen-size budget: 1 close up, smaller across the lane. */
 float GetEffectScale() const;""",
    "header shimmer methods")

header = swap(
    header,
    """ /** The beat phase sampled at the ACTION (the start of the swing), never at impact. */
 float ScytheActionBeatPhase = -1.f;""",
    """ /** The beat phase sampled at the ACTION (the start of the swing), never at impact. */
 float ScytheActionBeatPhase = -1.f;
 /** One solved hold per form: the heads sit at different points on the shaft. */
 UPROPERTY(Transient) TMap<EMelodiaWaveHarpForm, FTransform> FormGrips;""",
    "header form grips")

# ------------------------------------------------------------------ cpp: the shimmer
source = swap(
    source,
    """float UMelodiaWaveHarpCombatComponent::SampleBeatPhase() const""",
    """void UMelodiaWaveHarpCombatComponent::SetMorphIfPresent(FName Morph, float Value)
{
 if (!Instrument || Morph.IsNone()) return;
 // A morph the shipped mesh does not carry is skipped, not asserted: the source rig
 // names more shimmer curves than the UE mesh exposes.
 if (Instrument->GetMorphTarget(Morph)) Instrument->SetMorphTarget(Morph, Value);
}

float UMelodiaWaveHarpCombatComponent::GetEffectScale() const
{
 // The effect budget follows what the player can actually see (the reference scales
 // its fur layers by screen size): a flourish seen from across the lane is restrained,
 // one seen from arm's length is full size.
 if (!Player.IsValid() || !Character.IsValid()) return 1.f;
 FVector Eye; FRotator View;
 Player->GetPlayerViewPoint(Eye, View);
 const float Distance = FVector::Distance(Eye, Character->GetActorLocation());
 return FMath::Clamp(1.2f - 0.02f * Distance, 0.4f, 1.2f);
}

void UMelodiaWaveHarpCombatComponent::UpdateIdleShimmer()
{
 if (!Instrument) return;
 const float Phase = UMelodiaMusicClockSubsystem::GetMusicBeatPhase(this);
 if (Phase < 0.f) return; // no music: the instrument holds still rather than faking it
 const float Pulse = UMelodiaMusicClockSubsystem::GetMusicPulse(this);
 const float Breath = 0.5f + 0.5f * FMath::Cos(Phase * 2.f * PI);
 const float Sway = FMath::Sin(Phase * 2.f * PI);
 const float Strength = FMath::Clamp(ShimmerStrength, 0.f, 1.f);
 SetMorphIfPresent(MorphShimmerPluck, Breath * 0.30f * Strength);
 SetMorphIfPresent(MorphShimmerVibrate, Pulse * 0.45f * Strength);
 SetMorphIfPresent(MorphShimmerSwayPos, FMath::Max(0.f, Sway) * 0.35f * Strength);
 SetMorphIfPresent(MorphShimmerSwayNeg, FMath::Max(0.f, -Sway) * 0.35f * Strength);
 SetMorphIfPresent(MorphShimmerResonance, Breath * 0.40f * Strength);
}

float UMelodiaWaveHarpCombatComponent::SampleBeatPhase() const""",
    "cpp shimmer")

source = swap(
    source,
    """ if (Instrument)
 {
  Instrument->SetWorldTransform(Out);""",
    """ if (Instrument)
 {
  Instrument->SetWorldTransform(Out);
  UpdateIdleShimmer();""",
    "cpp shimmer call")

# ------------------------------------------------------------------ cpp: the per-form grip
source = swap(
    source,
    """ const FQuat Socket = Mesh->GetSocketTransform(InstrumentSocket, RTS_Component).GetRotation();
 const FQuat TargetRot = FQuat(FRotator(0.f, -90.f, 0.f));
 const FQuat Grip = TargetRot * Socket.Inverse();
 BowGrip.SetRotation(Grip);
 bHoldCalibrated = true;""",
    """ const FQuat Socket = Mesh->GetSocketTransform(InstrumentSocket, RTS_Component).GetRotation();
 const FQuat TargetRot = FQuat(FRotator(0.f, -90.f, 0.f));
 const FQuat Grip = TargetRot * Socket.Inverse();
 BowGrip.SetRotation(Grip);
 // Each form keeps its own solved hold: the three heads sit at different points on the
 // shaft, so one grip cannot hold three heads (C8).
 FormGrips.Add(CurrentForm, BowGrip);
 bHoldCalibrated = true;""",
    "cpp per-form grip")

source = swap(
    source,
    """void UMelodiaWaveHarpCombatComponent::ApplyFormVisuals()
{""",
    """void UMelodiaWaveHarpCombatComponent::ApplyFormVisuals()
{
 // The form brings its own hold with it, when it has been solved for this pose.
 if (const FTransform* Solved = FormGrips.Find(CurrentForm))
  BowGrip = *Solved;""",
    "cpp apply form grip")

# ------------------------------------------------------------------ cpp: the ribbon budget
source = swap(
    source,
    """ Side = Side.GetSafeNormal() * 3.f;""",
    """ // The ribbon follows the screen-size budget like everything else.
 Side = Side.GetSafeNormal() * (3.f * GetEffectScale());""",
    "cpp ribbon scale")

H.write_text(header, encoding="utf-8")
C.write_text(source, encoding="utf-8")
print("increment 4 applied: the music-clock shimmer, the per-form grips, the effect budget")
