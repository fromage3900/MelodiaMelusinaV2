#include "MelodiaLightReactorComponent.h"

#include "MelodiaWorldFieldBus.h"
#include "Components/LightComponent.h"
#include "Components/LocalLightComponent.h"
#include "Components/PointLightComponent.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"

namespace
{
	const TCHAR* PalettePath = TEXT("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.MPC_Melodia_Palette");
}

UMelodiaLightReactorComponent::UMelodiaLightReactorComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
	ResetToDefaultLanes();
}

void UMelodiaLightReactorComponent::ResetToDefaultLanes()
{
	Lanes.Reset();
	{
		FMelodiaLightLane L;
		L.Source = EMelodiaLightSource::BeatPulse;
		L.Target = EMelodiaLightTarget::Intensity;
		L.Amount = 0.6f;
		Lanes.Add(L);
	}
	{
		FMelodiaLightLane L;
		L.Source = EMelodiaLightSource::Bass;
		L.Target = EMelodiaLightTarget::Intensity;
		L.Amount = 0.4f;
		L.ReleaseSec = 0.4f;
		Lanes.Add(L);
	}
	{
		FMelodiaLightLane L;
		L.Source = EMelodiaLightSource::Mid;
		L.Target = EMelodiaLightTarget::AttenuationRadius;
		L.Amount = 0.15f;
		L.AttackSec = 0.05f;
		L.ReleaseSec = 0.5f;
		Lanes.Add(L);
	}
	{
		FMelodiaLightLane L;
		L.Source = EMelodiaLightSource::QuantumPulse;
		L.Target = EMelodiaLightTarget::ColorToTint;
		L.Amount = 0.8f;
		L.bTintFromQuantum = true;
		L.AttackSec = 0.0f;
		L.ReleaseSec = 0.3f;
		Lanes.Add(L);
	}
}

void UMelodiaLightReactorComponent::BeginPlay()
{
	Super::BeginPlay();
	PaletteMPC = Cast<UMaterialParameterCollection>(StaticLoadObject(UMaterialParameterCollection::StaticClass(), nullptr, PalettePath));
	Rescan();
}

void UMelodiaLightReactorComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	RestoreAll();
	Super::EndPlay(EndPlayReason);
}

void UMelodiaLightReactorComponent::Track(ULightComponent* Light)
{
	if (!Light || Tracked.Num() >= MaxLights)
	{
		return;
	}
	for (const FTrackedLight& T : Tracked)
	{
		if (T.Light.Get() == Light)
		{
			return;
		}
	}
	FTrackedLight& T = Tracked.AddDefaulted_GetRef();
	T.Light = Light;
	T.BaseIntensity = Light->Intensity;
	T.BaseVolumetric = Light->VolumetricScatteringIntensity;
	T.BaseTemperature = Light->Temperature;
	T.bBaseUseTemperature = Light->bUseTemperature;
	T.BaseColor = FLinearColor(Light->LightColor);
	T.bBaseMegaLights = Light->bAllowMegaLights;
	if (const ULocalLightComponent* Local = Cast<ULocalLightComponent>(Light))
	{
		T.BaseAttenuation = Local->AttenuationRadius;
	}
	if (const UPointLightComponent* Point = Cast<UPointLightComponent>(Light))
	{
		T.BaseSourceRadius = Point->SourceRadius;
	}
	if (bForceAllowMegaLights && !Light->bAllowMegaLights)
	{
		Light->bAllowMegaLights = true;
		Light->MarkRenderStateDirty();
	}
}

void UMelodiaLightReactorComponent::Rescan()
{
	Tracked.RemoveAll([](const FTrackedLight& T) { return !T.Light.IsValid(); });

	const AActor* Owner = GetOwner();
	const UWorld* World = GetWorld();
	if (!Owner || !World)
	{
		return;
	}

	TInlineComponentArray<ULightComponent*> OwnerLights;
	Owner->GetComponents(OwnerLights);
	for (ULightComponent* L : OwnerLights)
	{
		Track(L);
	}

	if (LightTag.IsNone())
	{
		return;
	}
	const FVector Center = Owner->GetActorLocation();
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		AActor* Actor = *It;
		if (!Actor || Actor == Owner || FVector::DistSquared(Actor->GetActorLocation(), Center) > FMath::Square(Radius))
		{
			continue;
		}
		const bool bActorTagged = Actor->ActorHasTag(LightTag);
		TInlineComponentArray<ULightComponent*> Lights;
		Actor->GetComponents(Lights);
		for (ULightComponent* L : Lights)
		{
			if (bActorTagged || L->ComponentHasTag(LightTag))
			{
				Track(L);
			}
		}
	}
}

void UMelodiaLightReactorComponent::RestoreAll()
{
	for (FTrackedLight& T : Tracked)
	{
		ULightComponent* Light = T.Light.Get();
		if (!Light)
		{
			continue;
		}
		Light->SetIntensity(T.BaseIntensity);
		Light->SetVolumetricScatteringIntensity(T.BaseVolumetric);
		Light->SetLightColor(T.BaseColor, true);
		Light->SetTemperature(T.BaseTemperature);
		Light->bUseTemperature = T.bBaseUseTemperature;
		if (ULocalLightComponent* Local = Cast<ULocalLightComponent>(Light))
		{
			Local->SetAttenuationRadius(T.BaseAttenuation);
		}
		if (UPointLightComponent* Point = Cast<UPointLightComponent>(Light))
		{
			Point->SetSourceRadius(T.BaseSourceRadius);
		}
		if (Light->bAllowMegaLights != T.bBaseMegaLights)
		{
			Light->bAllowMegaLights = T.bBaseMegaLights;
			Light->MarkRenderStateDirty();
		}
	}
	Tracked.Reset();
}

float UMelodiaLightReactorComponent::ReadSource(const EMelodiaLightSource Source, UMaterialParameterCollectionInstance* Palette) const
{
	if (Source == EMelodiaLightSource::CymaticTension)
	{
		return FMath::Clamp(UWorldFieldBus::SampleResonanceTension(FVector::ZeroVector).Tension, 0.0f, 1.0f);
	}
	if (!Palette)
	{
		return 0.0f;
	}
	const TCHAR* Name = TEXT("BeatPulse");
	switch (Source)
	{
	case EMelodiaLightSource::Bass: Name = TEXT("Bass"); break;
	case EMelodiaLightSource::Mid: Name = TEXT("Mid"); break;
	case EMelodiaLightSource::Treble: Name = TEXT("Treble"); break;
	case EMelodiaLightSource::BeatPulse: Name = TEXT("BeatPulse"); break;
	case EMelodiaLightSource::RhythmPulse: Name = TEXT("RhythmPulse"); break;
	case EMelodiaLightSource::Sparkle: Name = TEXT("GlobalSparkleIntensity"); break;
	case EMelodiaLightSource::QuantumPulse: Name = TEXT("QuantumPulse"); break;
	case EMelodiaLightSource::QuantumChoice: Name = TEXT("QuantumChoice"); break;
	default: break;
	}
	float V = 0.0f;
	Palette->GetScalarParameterValue(FName(Name), V);
	return FMath::Clamp(V, 0.0f, 1.0f);
}

void UMelodiaLightReactorComponent::TickComponent(const float DeltaTime, const ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	const UWorld* World = GetWorld();
	if (!World || !World->IsGameWorld())
	{
		return; // never move authored light values in the editor viewport
	}
	if (!LightTag.IsNone())
	{
		RescanTimer += DeltaTime;
		if (RescanTimer >= RescanIntervalSec)
		{
			RescanTimer = 0.0f;
			Rescan();
		}
	}
	UpdateTimer += DeltaTime;
	if (UpdateTimer >= 1.0f / FMath::Max(UpdateHz, 1.0f))
	{
		Apply(UpdateTimer);
		UpdateTimer = 0.0f;
	}
}

void UMelodiaLightReactorComponent::Apply(const float DeltaSeconds)
{
	if (Tracked.Num() == 0 || Lanes.Num() == 0)
	{
		return;
	}
	UMaterialParameterCollectionInstance* Palette = (PaletteMPC && GetWorld()) ? GetWorld()->GetParameterCollectionInstance(PaletteMPC) : nullptr;

	FLinearColor QuantumColor = FLinearColor::White;
	if (Palette)
	{
		Palette->GetVectorParameterValue(FName(TEXT("QuantumReactionColor")), QuantumColor);
	}

	// Smooth each lane once per update, not per light.
	for (FMelodiaLightLane& Lane : Lanes)
	{
		const float Target = ReadSource(Lane.Source, Palette);
		const float Tau = Target > Lane.Smoothed ? Lane.AttackSec : Lane.ReleaseSec;
		const float Alpha = Tau <= KINDA_SMALL_NUMBER ? 1.0f : 1.0f - FMath::Exp(-DeltaSeconds / Tau);
		Lane.Smoothed += (Target - Lane.Smoothed) * Alpha;
	}

	for (FTrackedLight& T : Tracked)
	{
		ULightComponent* Light = T.Light.Get();
		if (!Light)
		{
			continue;
		}
		float IntensityAdd = 0.0f;
		float AttenAdd = 0.0f;
		float SourceAdd = 0.0f;
		float VolAdd = 0.0f;
		float TempAdd = 0.0f;
		FLinearColor Color = T.BaseColor;
		bool bColorMoved = false;
		for (const FMelodiaLightLane& Lane : Lanes)
		{
			const float V = Lane.Smoothed * Lane.Amount;
			switch (Lane.Target)
			{
			case EMelodiaLightTarget::Intensity: IntensityAdd += V; break;
			case EMelodiaLightTarget::AttenuationRadius: AttenAdd += V; break;
			case EMelodiaLightTarget::SourceRadius: SourceAdd += V; break;
			case EMelodiaLightTarget::VolumetricScattering: VolAdd += V; break;
			case EMelodiaLightTarget::Temperature: TempAdd += V * 1000.0f; break;
			case EMelodiaLightTarget::ColorToTint:
			{
				const FLinearColor Tint = Lane.bTintFromQuantum ? QuantumColor : Lane.Tint;
				Color = FLinearColor::LerpUsingHSV(Color, Tint, FMath::Clamp(V, 0.0f, 1.0f));
				bColorMoved = true;
				break;
			}
			}
		}
		Light->SetIntensity(FMath::Max(0.0f, T.BaseIntensity * (1.0f + IntensityAdd)));
		if (VolAdd != 0.0f)
		{
			Light->SetVolumetricScatteringIntensity(FMath::Max(0.0f, T.BaseVolumetric * (1.0f + VolAdd)));
		}
		if (bColorMoved)
		{
			Light->SetLightColor(Color, true);
		}
		if (TempAdd != 0.0f)
		{
			Light->bUseTemperature = true;
			Light->SetTemperature(FMath::Clamp(T.BaseTemperature + TempAdd, 1700.0f, 12000.0f));
		}
		if (AttenAdd != 0.0f)
		{
			if (ULocalLightComponent* Local = Cast<ULocalLightComponent>(Light))
			{
				Local->SetAttenuationRadius(FMath::Max(1.0f, T.BaseAttenuation * (1.0f + AttenAdd)));
			}
		}
		if (SourceAdd != 0.0f)
		{
			if (UPointLightComponent* Point = Cast<UPointLightComponent>(Light))
			{
				Point->SetSourceRadius(FMath::Max(0.0f, T.BaseSourceRadius * (1.0f + SourceAdd)));
			}
		}
	}
}
