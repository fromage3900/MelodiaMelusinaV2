#pragma once

#include "CoreMinimal.h"
#include "MelodiaWaterInteractionTypes.generated.h"

class AActor;

/** Simulation escalation ladder used by water profiles and performance tests. */
UENUM(BlueprintType)
enum class EMelodiaWaterSimulationTier : uint8
{
	AnalyticSurface UMETA(DisplayName = "Analytic Surface"),
	NiagaraParticles UMETA(DisplayName = "Niagara Particles"),
	ShallowWater2D UMETA(DisplayName = "Shallow Water 2D"),
	FLIP2D UMETA(DisplayName = "FLIP 2D"),
	FLIP3DHero UMETA(DisplayName = "FLIP 3D Hero")
};

/** Identifies which provider made a water sample authoritative. */
UENUM(BlueprintType)
enum class EMelodiaWaterQueryProvider : uint8
{
	Fallback UMETA(DisplayName = "Gameplay Fallback"),
	NativeWaterBody UMETA(DisplayName = "Native Water Body"),
	BakedShallowWater UMETA(DisplayName = "Baked Shallow Water"),
	Oceanology UMETA(DisplayName = "Oceanology")
};

/** Force semantics used when routing an event into native Water or Niagara. */
UENUM(BlueprintType)
enum class EMelodiaWaterForceMode : uint8
{
	Contact UMETA(DisplayName = "Contact"),
	Impulse UMETA(DisplayName = "Impulse"),
	Dynamic UMETA(DisplayName = "Dynamic")
};

/**
 * Stable vocabulary for water-driven presentation and simulation events.
 * Gameplay owns the fact that an interaction occurred; Niagara, materials,
 * audio, and fluid adapters consume this vocabulary without coupling to one
 * another.
 */
UENUM(BlueprintType)
enum class EMelodiaWaterContactType : uint8
{
	ProximityEntered UMETA(DisplayName = "Proximity Entered"),
	ProximityExited UMETA(DisplayName = "Proximity Exited"),
	SurfaceEntry UMETA(DisplayName = "Surface Entry"),
	SurfaceExit UMETA(DisplayName = "Surface Exit"),
	SwimStarted UMETA(DisplayName = "Swim Started"),
	SwimStopped UMETA(DisplayName = "Swim Stopped"),
	DiveStarted UMETA(DisplayName = "Dive Started"),
	DiveStopped UMETA(DisplayName = "Dive Stopped"),
	Ripple UMETA(DisplayName = "Ripple"),
	Splash UMETA(DisplayName = "Splash"),
	Footstep UMETA(DisplayName = "Footstep"),
	WaterImpact UMETA(DisplayName = "Water Impact")
};

/**
 * A water-body query result. bValid means the provider answered; the surface
 * flags make it safe to distinguish a real Water Body result from a gameplay
 * fallback while the query adapter is being brought online.
 */
USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaWaterSample
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	bool bValid = false;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	bool bSurfaceValid = false;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	bool bUnderwater = false;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	FName WaterBodyId = NAME_None;

	/** UE Water Body GPU-data index, when the provider supplied one. */
	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	int32 WaterBodyIndex = INDEX_NONE;

	/** UE Water Zone GPU/render-target index, when the body is assigned to one. */
	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	int32 WaterZoneIndex = INDEX_NONE;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	EMelodiaWaterQueryProvider QueryProvider = EMelodiaWaterQueryProvider::Fallback;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	bool bUsesBakedShallowWater = false;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	FVector SurfaceLocation = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	FVector SurfaceNormal = FVector::UpVector;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	FVector SurfaceVelocity = FVector::ZeroVector;

	/** Native/baked shallow-water height offset relative to the base surface. */
	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	float NativeShallowWaterHeight = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	FVector NativeShallowWaterVelocity = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	FVector NativeShallowWaterNormal = FVector::UpVector;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	float DistanceToSurface = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float Immersion = 0.0f;

	/** Raw UE Water Body immersion depth in centimeters. */
	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water", meta = (ClampMin = "0.0"))
	float ImmersionDepth = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water", meta = (ClampMin = "0.0"))
	float WaterDepth = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	float SampleTime = 0.0f;
};

/**
 * One normalized interaction packet. This is deliberately rich enough for a
 * Niagara event, an MPC/custom-data write, a MetaSound parameter set, or a
 * shallow-water impulse without requiring each consumer to re-query gameplay.
 */
USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaWaterContactEvent
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	EMelodiaWaterContactType EventType = EMelodiaWaterContactType::Ripple;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	TObjectPtr<AActor> SourceActor = nullptr;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	FMelodiaWaterSample Sample;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	FVector ContactLocation = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	FVector ImpactVelocity = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	FVector ImpulseVector = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water", meta = (ClampMin = "0.0"))
	float Radius = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float Intensity = 1.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water", meta = (ClampMin = "0.0"))
	float Duration = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	int32 RandomSeed = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	FName EffectProfileId = TEXT("Default");

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water")
	FName AudioProfileId = TEXT("Default");
};

/** Bounded impulse packet for Shallow Water/FLIP adapters and deterministic replay. */
USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaWaterFluidImpulse
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|Fluid")
	EMelodiaWaterSimulationTier RequestedTier = EMelodiaWaterSimulationTier::ShallowWater2D;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|Fluid")
	EMelodiaWaterForceMode ForceMode = EMelodiaWaterForceMode::Contact;

	/** True when the profile permits forwarding this packet to native Water. */
	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|Fluid")
	bool bRouteToNativeWater = true;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|Fluid")
	FName WaterBodyId = NAME_None;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|Fluid")
	FVector Location = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|Fluid")
	FVector Normal = FVector::UpVector;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|Fluid")
	FVector Impulse = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|Fluid", meta = (ClampMin = "0.0"))
	float Radius = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|Fluid", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float Strength = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|Fluid")
	float Timestamp = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|Fluid", meta = (ClampMin = "0.0"))
	float Duration = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|Fluid")
	FName EffectProfileId = TEXT("Default");

	/** Stable source-component identity for replay and diagnostics. */
	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|Fluid")
	FName SourceComponentId = NAME_None;
};

/** Runtime limits exposed by the installed UE Water subsystem. */
USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaWaterNativeLimits
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|Native")
	bool bWaterAvailable = false;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|Native")
	bool bShallowWaterSimulationEnabled = false;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|Native")
	bool bUnderwaterPostProcessEnabled = false;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|Native")
	int32 MaxDynamicForces = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|Native")
	int32 MaxImpulseForces = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Water|Native")
	int32 ShallowWaterRenderTargetSize = 0;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaWaterSampleUpdated, FMelodiaWaterSample, Sample);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaWaterContactEventSignature, FMelodiaWaterContactEvent, Event);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaWaterFluidImpulseSignature, FMelodiaWaterFluidImpulse, Impulse);
