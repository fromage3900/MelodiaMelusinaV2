#include "MelodiaFoleyComponent.h"

#include "GameFramework/CharacterMovementComponent.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundCue.h"
#include "Sound/SoundWave.h"

UMelodiaFoleyComponent::UMelodiaFoleyComponent()
{
	PrimaryComponentTick.bCanEverTick = true;

	// Cue slots default to the authored footsteps bank. A null slot is a
	// silent no-op at play time (counted as dropped), so the component
	// compiles and runs before the cues exist on disk.
	// Defaults repointed 2026-10-17 (Phase 0 audit): the bank on disk is
	// Footsteps/<Surface>/SC_FS_<Surface>; the SC_Foley_Footstep_* paths never existed.
	GrassCue = FSoftObjectPath(TEXT("/Game/Melodia/Audio/Foley/Footsteps/Grass/SC_FS_Grass.SC_FS_Grass"));
	DirtCue = FSoftObjectPath(TEXT("/Game/Melodia/Audio/Foley/Footsteps/Dirt/SC_FS_Dirt.SC_FS_Dirt"));
	StoneCue = FSoftObjectPath(TEXT("/Game/Melodia/Audio/Foley/Footsteps/Stone/SC_FS_Stone.SC_FS_Stone"));
	WoodCue = FSoftObjectPath(TEXT("/Game/Melodia/Audio/Foley/Footsteps/Wood/SC_FS_Wood.SC_FS_Wood"));
	SplashCue = FSoftObjectPath(TEXT("/Game/Melodia/Audio/Foley/Footsteps/Splash/SC_FS_Splash.SC_FS_Splash"));
}

void UMelodiaFoleyComponent::BeginPlay()
{
	Super::BeginPlay();

	const TSoftObjectPtr<USoundCue> Slots[5] = { GrassCue, DirtCue, StoneCue, WoodCue, SplashCue };
	for (int32 i = 0; i < 5; ++i)
	{
		LoadedCues[i] = Slots[i].LoadSynchronous();
		if (LoadedCues[i] == nullptr)
		{
			UE_LOG(LogTemp, Warning,
				TEXT("MelodiaFoley: cue slot %d (%s) is null; that surface will be silent."),
				i, *Slots[i].ToString());
		}
	}

	// Wave-bank fallback: Footsteps/<Surface>/SW_FS_<Surface>_<1..6>
	static const TCHAR* SurfaceNames[5] = { TEXT("Grass"), TEXT("Dirt"), TEXT("Stone"), TEXT("Wood"), TEXT("Splash") };
	LoadedWaves.SetNum(30);
	for (int32 s = 0; s < 5; ++s)
	{
		for (int32 n = 0; n < 6; ++n)
		{
			const FString Path = FString::Printf(
				TEXT("/Game/Melodia/Audio/Foley/Footsteps/%s/SW_FS_%s_%d.SW_FS_%s_%d"),
				SurfaceNames[s], SurfaceNames[s], n + 1, SurfaceNames[s], n + 1);
			LoadedWaves[s * 6 + n] = LoadObject<USoundWave>(nullptr, *Path);
		}
	}

	bFoleyReady = LoadedCues[0] != nullptr || LoadedCues[1] != nullptr ||
		LoadedCues[2] != nullptr || LoadedCues[3] != nullptr || LoadedCues[4] != nullptr ||
		LoadedWaves[0] != nullptr;
	if (bFoleyReady && LoadedCues[0] == nullptr)
	{
		UE_LOG(LogTemp, Log, TEXT("MelodiaFoley: cues unavailable, using SW_FS wave-bank fallback"));
	}
}

void UMelodiaFoleyComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	// No resident voices: footsteps are location-anchored one-shots fired
	// through GameplayStatics, so there is nothing to stop or reclaim.
	Super::EndPlay(EndPlayReason);
}

void UMelodiaFoleyComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	DetectFootstep(DeltaTime);
}

void UMelodiaFoleyComponent::DetectFootstep(float DeltaTime)
{
	ACharacter* OwnerCharacter = Cast<ACharacter>(GetOwner());
	if (!OwnerCharacter)
	{
		return;
	}
	UCharacterMovementComponent* Movement = OwnerCharacter->GetCharacterMovement();
	if (!Movement)
	{
		return;
	}
	const UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	// Sliding 1 s window for the voice budget.
	const float Now = World->GetTimeSeconds();
	if (Now - EventWindowStart >= 1.0f)
	{
		EventWindowStart = Now;
		EventsInWindow = 0;
	}
	FootstepCooldownRemaining = FMath::Max(0.0f, FootstepCooldownRemaining - DeltaTime);

	// 5.8 API: no IsGrounded() -- Walking mode IS the grounded state (Falling
	// means airborne even with feet touching; Swimming/Flying mean the feet
	// are not the thing moving, so no footstep).
	const bool bGrounded = Movement->MovementMode == MOVE_Walking;

	if (!bGrounded || FootstepCooldownRemaining > 0.0f)
	{
		// No step debt while airborne / stopped / on cooldown: the first step
		// after standing still must not fire a buried backlog.
		GaitAccumulator = 0.0f;
	}
	else
	{
		// Cadence scales with speed (clamped), tuned at ReferenceSpeed.
		const float Speed2D = Movement->Velocity.Size2D();
		if (Speed2D >= MinWalkSpeed)
		{
			const float SpeedScale = FMath::Clamp(Speed2D / ReferenceSpeed, 0.7f, 1.2f);
			GaitAccumulator += DeltaTime * SpeedScale;
			if (GaitAccumulator >= StepInterval)
			{
				GaitAccumulator = 0.0f;
				PlayFootstep(ResolveSurface(/*bSuppressWater*/ false), /*bIsLanding*/ false);
			}
		}
	}

	// Landing impact: air -> ground with a real fall speed. The cadence
	// accumulator is zero on this frame (it was reset while airborne), so a
	// landing never doubles up with a walking step.
	if (bGrounded && !bWasGrounded && PrevVelocityZ < -MinLandingImpactSpeed)
	{
		PlayFootstep(ResolveSurface(/*bSuppressWater*/ false), /*bIsLanding*/ true);
	}

	bWasGrounded = bGrounded;
	PrevVelocityZ = Movement->Velocity.Z;
}

EMelodiaFoleySurface UMelodiaFoleyComponent::ResolveSurface(bool bSuppressWater) const
{
	ACharacter* OwnerCharacter = Cast<ACharacter>(GetOwner());
	if (!OwnerCharacter)
	{
		return DefaultSurface;
	}

	if (const UCharacterMovementComponent* Movement = OwnerCharacter->GetCharacterMovement())
	{
		// Shallow water is the one runtime surface: a character that is still
		// Walking while in water is wading its surface (deep water forces
		// Swimming mode, which the caller already excluded). The authored
		// balls below never claim water, so this check runs first.
		if (!bSuppressWater && Movement->IsInWater())
		{
			return EMelodiaFoleySurface::Splash;
		}
	}

	const FVector Position = OwnerCharacter->GetActorLocation() + FootOffset;
	EMelodiaFoleySurface Best = DefaultSurface;
	float BestDistance = MAX_flt;
	bool bFoundZone = false;
	for (const FMelodiaFoleySurfaceZone& Zone : SurfaceZones)
	{
		const float Distance = FVector::Dist(Position, Zone.Center);
		if (Distance < Zone.RadiusCm && Distance < BestDistance)
		{
			Best = Zone.Surface;
			BestDistance = Distance;
			bFoundZone = true;
		}
	}
	return bFoundZone ? Best : DefaultSurface;
}

void UMelodiaFoleyComponent::PlayFootstep(EMelodiaFoleySurface Surface, bool bIsLanding)
{
	const int32 Slot = static_cast<int32>(Surface);
	USoundBase* Sound = (Slot >= 0 && Slot < 5) ? LoadedCues[Slot].Get() : nullptr;
	if (Sound == nullptr && Slot >= 0 && Slot < 5)
	{
		// Cue unavailable (see header): random wave from the surface bank.
		TArray<USoundWave*> Bank;
		for (int32 n = 0; n < 6; ++n)
		{
			if (LoadedWaves.IsValidIndex(Slot * 6 + n) && LoadedWaves[Slot * 6 + n]) Bank.Add(LoadedWaves[Slot * 6 + n].Get());
		}
		if (Bank.Num() > 0) Sound = Bank[FMath::RandRange(0, Bank.Num() - 1)];
	}
	if (Sound == nullptr)
	{
		// A missing bank is a content gap, not a runtime fault: count it so
		// PIE evidence can tell "trigger fired, no asset" from "no trigger".
		++FootstepsDropped;
		return;
	}
	if (EventsInWindow >= MaxFootstepsPerSecond)
	{
		++FootstepsDropped;
		return;
	}
	++EventsInWindow;

	AActor* Owner = GetOwner();
	const FVector Location = Owner ? Owner->GetActorLocation() + FootOffset : FVector::ZeroVector;

	const float Pitch = FMath::FRandRange(PitchMin, PitchMax);
	const float BaseVolume = bIsLanding ? LandingVolume : WalkVolume;
	const float Volume = FMath::Clamp(BaseVolume * FMath::FRandRange(0.9f, 1.0f), 0.0f, 2.0f);

	UGameplayStatics::PlaySoundAtLocation(this, Sound, Location, /*VolumeMultiplier*/ Volume, /*PitchMultiplier*/ Pitch, /*StartTime*/ 0.0f);

	FootstepCooldownRemaining = FootstepCooldown;
	LastSurface = Surface;
	++FootstepsPlayed;
}
