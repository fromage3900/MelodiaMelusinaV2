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
 };

 /** Classify an exposed parameter name into a role. Empty means "not a role". */
 static FName RoleForParameter(const FString& ParameterName);

 void BindSurface(UNiagaraComponent* Niagara);
 void DispatchBeat(AActor* Owner);
 FVector HorizonPoint(const AActor* Owner, float Distance, float Height) const;

 TArray<FSurface> Surfaces;
 TWeakObjectPtr<AActor> CharacterLive;
 TWeakObjectPtr<AActor> PuddleLive;
 int32 BoundParameterCount = 0;
 int32 Beats = 0;
 int32 Dispatches = 0;
 float PreviousPhase = -1.f;
 bool bStarted = false;
};
