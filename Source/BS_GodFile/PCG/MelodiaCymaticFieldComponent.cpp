#include "MelodiaCymaticFieldComponent.h"

#include "../MelodiaIntegration/MelodiaWorldFieldBus.h"
#include "MelodiaRhythmReactivitySubsystem.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"

namespace
{
	constexpr int32 MaxActiveRipples = 8;

	float Chladni01(const int32 N, const int32 M, const float U, const float V)
	{
		const float PiU = UE_PI * U;
		const float PiV = UE_PI * V;
		const float A = FMath::Cos(N * PiU) * FMath::Cos(M * PiV);
		const float B = FMath::Cos(M * PiU) * FMath::Cos(N * PiV);
		return FMath::Abs(A - B) * 0.5f; // raw range [-2,2] -> |.|/2 in [0,1]
	}

	float Wrap01(const float X)
	{
		return X - FMath::FloorToFloat(X);
	}
}

TArray<TWeakObjectPtr<UMelodiaCymaticFieldComponent>> UMelodiaCymaticFieldComponent::Active;

UMelodiaCymaticFieldComponent::UMelodiaCymaticFieldComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
}

void UMelodiaCymaticFieldComponent::BeginPlay()
{
	Super::BeginPlay();
	if (AActor* Owner = GetOwner())
	{
		Owner->OnActorBeginOverlap.AddDynamic(this, &UMelodiaCymaticFieldComponent::HandleOwnerOverlap);
	}
	Active.AddUnique(this);
	Rescan();
}

void UMelodiaCymaticFieldComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (AActor* Owner = GetOwner())
	{
		Owner->OnActorBeginOverlap.RemoveDynamic(this, &UMelodiaCymaticFieldComponent::HandleOwnerOverlap);
	}
	Active.Remove(this);
	RestoreAll();
	Super::EndPlay(EndPlayReason);
}

void UMelodiaCymaticFieldComponent::HandleOwnerOverlap(AActor* /*OverlappedActor*/, AActor* OtherActor)
{
	if (bHitOnPawnOverlap && Cast<APawn>(OtherActor))
	{
		TriggerHit(OtherActor->GetActorLocation(), 1.0f);
	}
}

void UMelodiaCymaticFieldComponent::BroadcastHit(const UWorld* World, const FVector WorldOrigin, const float Strength)
{
	Active.RemoveAll([](const TWeakObjectPtr<UMelodiaCymaticFieldComponent>& C) { return !C.IsValid(); });
	for (const TWeakObjectPtr<UMelodiaCymaticFieldComponent>& C : Active)
	{
		if (C.IsValid() && C->GetWorld() == World)
		{
			C->AddRipple(WorldOrigin, Strength);
		}
	}
}

void UMelodiaCymaticFieldComponent::AddRipple(const FVector WorldOrigin, const float Strength)
{
	if (Ripples.Num() >= MaxActiveRipples)
	{
		Ripples.RemoveAt(0);
	}
	FRipple& R = Ripples.AddDefaulted_GetRef();
	R.Origin = WorldOrigin;
	R.Strength = FMath::Clamp(Strength, 0.0f, 1.0f);
}

void UMelodiaCymaticFieldComponent::TriggerHit(const FVector WorldOrigin, const float Strength)
{
	AddRipple(WorldOrigin, Strength);

	if (bNotifyReactivity)
	{
		if (UMelodiaRhythmReactivitySubsystem* Reactivity = UMelodiaRhythmReactivitySubsystem::Get(this))
		{
			Reactivity->NotifyCommandResolved(EMelodiaRhythmGrade::Great, 0.0f, 0.0f, 0.0f, 0);
		}
	}
}

void UMelodiaCymaticFieldComponent::Rescan()
{
	const UWorld* World = GetWorld();
	const AActor* Owner = GetOwner();
	if (!World || !Owner)
	{
		return;
	}

	// Drop dead entries; keep live ones (their Rest is still the authoritative undisplaced pose).
	Tracked.RemoveAll([](const FTracked& T) { return !T.Comp.IsValid(); });

	const FVector Center = Owner->GetActorLocation();
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		AActor* Actor = *It;
		if (!Actor || Actor == Owner)
		{
			continue;
		}
		const bool bActorTagged = Actor->ActorHasTag(ReactiveTag);

		TInlineComponentArray<UInstancedStaticMeshComponent*> Comps;
		Actor->GetComponents(Comps);
		for (UInstancedStaticMeshComponent* Comp : Comps)
		{
			if (!Comp || Comp->GetInstanceCount() == 0)
			{
				continue;
			}
			if (!bReactToAllInstancedMeshes && !bActorTagged && !Comp->ComponentHasTag(ReactiveTag))
			{
				continue;
			}
			const FBoxSphereBounds B = Comp->Bounds;
			if (FVector::Dist(B.Origin, Center) > ReactRadius + B.SphereRadius)
			{
				continue;
			}

			FTracked* Existing = Tracked.FindByPredicate([Comp](const FTracked& T) { return T.Comp.Get() == Comp; });
			if (Existing && Existing->Rest.Num() == Comp->GetInstanceCount())
			{
				continue;
			}
			if (!Existing)
			{
				Existing = &Tracked.AddDefaulted_GetRef();
				Existing->Comp = Comp;
			}
			// A changed count means PCG regenerated the component, so its transforms are fresh and undisplaced.
			Existing->Rest.Reset();
			Existing->Rest.Reserve(Comp->GetInstanceCount());
			for (int32 i = 0; i < Comp->GetInstanceCount(); ++i)
			{
				FTransform T;
				Comp->GetInstanceTransform(i, T, /*bWorldSpace*/ false);
				Existing->Rest.Add(T);
			}
			Existing->Scratch = Existing->Rest;
		}
	}
}

void UMelodiaCymaticFieldComponent::RestoreAll()
{
	for (FTracked& T : Tracked)
	{
		if (UInstancedStaticMeshComponent* Comp = T.Comp.Get())
		{
			if (Comp->GetInstanceCount() == T.Rest.Num() && T.Rest.Num() > 0)
			{
				Comp->BatchUpdateInstancesTransforms(0, T.Rest, false, true, true);
			}
		}
	}
	Tracked.Reset();
	Ripples.Reset();
}

void UMelodiaCymaticFieldComponent::TickComponent(const float DeltaTime, const ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	const UWorld* World = GetWorld();
	if (!World || !World->IsGameWorld())
	{
		return; // never move instances in the editor viewport
	}

	for (int32 i = Ripples.Num() - 1; i >= 0; --i)
	{
		Ripples[i].Age += DeltaTime;
		if (Ripples[i].Age >= RippleLifeSec)
		{
			Ripples.RemoveAtSwap(i);
		}
	}

	if (bHitOnBeat)
	{
		const float Pulse = UWorldFieldBus::SampleResonanceTension(FVector::ZeroVector).BeatPulse;
		if (Pulse > 0.8f && LastBeatPulse < 0.5f)
		{
			TriggerHit(GetOwner()->GetActorLocation(), 0.8f);
		}
		LastBeatPulse = Pulse;
	}

	RescanTimer += DeltaTime;
	if (RescanTimer >= RescanIntervalSec)
	{
		RescanTimer = 0.0f;
		Rescan();
	}

	UpdateTimer += DeltaTime;
	const float Step = 1.0f / FMath::Max(UpdateHz, 1.0f);
	if (UpdateTimer >= Step)
	{
		Apply(UpdateTimer);
		UpdateTimer = 0.0f;
	}
}

void UMelodiaCymaticFieldComponent::Apply(float /*DeltaSeconds*/)
{
	const AActor* Owner = GetOwner();
	if (!Owner || Tracked.Num() == 0)
	{
		return;
	}

	// Sampled at the origin so the bus's Faraway-specific radial falloff is 1: the raw, non-spatial field.
	const FWorldFieldSample Field = UWorldFieldBus::SampleResonanceTension(FVector::ZeroVector);
	const float Drive = FMath::Clamp(Field.Tension, 0.0f, 1.0f);
	const FVector Center = Owner->GetActorLocation();
	const float Plate = FMath::Max(PlateSizeCm, 100.0f);
	int32 Budget = MaxInstances;

	for (FTracked& T : Tracked)
	{
		UInstancedStaticMeshComponent* Comp = T.Comp.Get();
		if (!Comp || Comp->GetInstanceCount() != T.Rest.Num() || T.Rest.Num() == 0)
		{
			continue;
		}
		const FTransform CompToWorld = Comp->GetComponentTransform();
		const FVector LocalUp = CompToWorld.InverseTransformVectorNoScale(FVector::UpVector);
		const int32 Count = FMath::Min(T.Rest.Num(), Budget);
		Budget -= Count;

		for (int32 i = 0; i < Count; ++i)
		{
			const FTransform& Rest = T.Rest[i];
			const FVector W = CompToWorld.TransformPosition(Rest.GetLocation());

			float Lift = 0.0f;
			float Scale = 0.0f;
			if (FVector::DistSquared2D(W, Center) <= FMath::Square(ReactRadius))
			{
				const float U = Wrap01((W.X - Center.X) / Plate + 0.5f);
				const float V = Wrap01((W.Y - Center.Y) / Plate + 0.5f);
				const float Wave = Chladni01(Field.ResonanceN, Field.ResonanceM, U, V) * Drive;
				Lift = MaxLiftCm * Wave;
				Scale = ScalePulse * Wave;

				for (const FRipple& R : Ripples)
				{
					const float D = FVector::Dist2D(W, R.Origin);
					const float Front = RippleSpeedCmPerSec * R.Age;
					const float X = (D - Front) / RippleWidthCm;
					const float Ring = FMath::Exp(-X * X) * R.Strength * (1.0f - R.Age / RippleLifeSec);
					Lift += RippleLiftCm * Ring;
					Scale += ScalePulse * Ring;
				}
			}

			FTransform Out = Rest;
			Out.AddToTranslation(LocalUp * Lift);
			Out.SetScale3D(Rest.GetScale3D() * (1.0f + Scale));
			T.Scratch[i] = Out;
		}
		for (int32 i = Count; i < T.Rest.Num(); ++i)
		{
			T.Scratch[i] = T.Rest[i];
		}
		Comp->BatchUpdateInstancesTransforms(0, T.Scratch, false, true, true);
	}
}
