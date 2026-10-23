#pragma once

#include "CoreMinimal.h"

class AActor;
class UNiagaraComponent;
class UWorld;

/**
 * The world's water chorus: the surreal register Melusina lives in.
 *
 * WHY A PLAIN C++ CLASS: it adds no reflected surface, so it needs no UHT pass, and it
 * is owned by the waveharp component, which already ticks and already owns the
 * beat-driven presentation of the instrument. One writer per surface still holds: this
 * class READS the cymatics MPC, it never writes it.
 *
 * WHAT IT DOES:
 *  - binds the world's FluidNinja surfaces by ROLE (density, strength, beat, input,
 *    colour) instead of by hard-coded parameter names, and logs what it bound, so a
 *    renamed parameter is a log line, not a silent no-op;
 *  - on every downbeat it disperses rain over the horizon, dots the skyline with
 *    bubbles, and beads Melusina's hair with globules;
 *  - the puddles SING: the bass band from the cymatics MPC drives the strength of the
 *    bound fluid surfaces, so the water moves with the music instead of near it.
 *
 * All the systems it dispatches already exist in the project. It authors no graphs.
 */
class FMelodiaWaterChorus
{
public:
 /** Find the world's water surfaces and bind them by role. */
 void Start(UWorld& World);

 /** (Re)bind every water surface in the world, by role. */
 void BindAll();

 /** Spawn the FluidNinja setups that belong to a character: the live actor that tracks
 *  her bones (the hair globulates, the movement leaves a trail) and the small water body
 *  at her feet (the puddles sing). Returns how many were spawned. */
 int32 SpawnCharacterSetups(AActor* Owner);

 /** True for the class names FluidNinja's live setups use (the world actor and the unit's component). */
 static bool IsNinjaLiveClassName(const FString& ClassName);

 /** Forget everything. */
 void Stop();

 /** Advance the chorus. Owner is Melusina; it may be null. */
 void Tick(float Delta, AActor* Owner);

 int32 GetBoundSurfaceCount() const { return Surfaces.Num(); }
 int32 GetBoundParameterCount() const { return BoundParameterCount; }
 int32 GetBeatCount() const { return Beats; }
 int32 GetDispatchCount() const { return Dispatches; }

 /** The water transform: a full burst around the character. Used on the form change. */
 void Burst(AActor* Owner, float Scale = 2.2f);

 /** A note landed at Where (strength 0..1): the nearest live water takes a brush stamp there and a splash
  *  rises. Called next to UMelodiaCymaticFieldComponent::BroadcastHit, so the ripple and the water are one hit. */
 void Splash(const FVector& Where, float Strength);

 int32 GetActiveSurfaceCount() const;

 // --- Pure, world-free rules (unit-tested) ---

 /** The water tint for a harmonic mode (0 rest, 1 major, 2 minor, 3 dominant, 4 chromatic). Phase 0..1 only moves the chromatic hue. */
 static FLinearColor TintForMode(uint8 Mode, float Phase);

 /** Churn 0..1: a consonant harmony calms the water, a dissonant one stirs it. */
 static float TurbulenceForConsonance(float Consonance);

 /** Sim-speed multiplier: dissonance runs the sim faster. */
 static float SimSpeedScale(float Consonance);

 /** Which surfaces stay simulated. Owned surfaces (distance <= 0) always stay on; the rest must be inside
  *  Radius (Radius*Hysteresis if they were already on) and within the MaxActive nearest. */
 static TArray<bool> SelectActiveSurfaces(const TArray<float>& Distances, const TArray<bool>& WasActive,
  float Radius, float Hysteresis, int32 MaxActive);

private:
 struct FSurface
 {
  TWeakObjectPtr<UNiagaraComponent> Niagara;
  FName Density;
  FName Strength;
  FName Beat;
  FName Input;
  FName Colour;
  /** FluidNinja's own API, bound by exact name (learned from the live surface). */
  FName SimSpeed;
  FName BrushStrength;
  FName BrushSize;
  FName BrushVelocity;
  FName SimplePainter;
  FName VolumeRender;
  FName FogVolumeRender;
  /** The character and puddle actors this chorus spawned: always simulated. */
  bool bOwned = false;
  /** Distance budget: a paused surface costs nothing. */
  bool bActive = true;
  /** The decaying brush stamp left by Splash(). */
  FVector SplashAt = FVector::ZeroVector;
  float SplashStrength = 0.f;
 };

 /** Cm from the owner inside which a world surface keeps simulating. */
 static constexpr float BudgetRadiusCm = 6000.f;
 static constexpr int32 BudgetMaxActive = 6;

 /** Classify an exposed parameter name into a role. Empty means "not a role". */
 static FName RoleForParameter(const FString& ParameterName);

 void BindSurface(UNiagaraComponent* Niagara);
 void DispatchBeat(AActor* Owner);
 FVector HorizonPoint(const AActor* Owner, float Distance, float Height) const;

 TArray<FSurface> Surfaces;
 /** The runtime unit (Melusina). It already carries its own FluidNinja (WaterHairFluid), so no second character sim is spawned. */
 TWeakObjectPtr<AActor> ChorusOwner;
 bool bSetupsDone = false;
 bool bUnitHasOwnFluid = false;
 TWeakObjectPtr<AActor> CharacterLive;
 TWeakObjectPtr<AActor> PuddleLive;
 int32 BoundParameterCount = 0;
 int32 Beats = 0;
 int32 Dispatches = 0;
 float PreviousPhase = -1.f;
 bool bStarted = false;
};
