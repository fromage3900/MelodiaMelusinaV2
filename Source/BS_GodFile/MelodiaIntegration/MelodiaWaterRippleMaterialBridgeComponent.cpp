#include "MelodiaWaterRippleMaterialBridgeComponent.h"

#include "Components/MeshComponent.h"
#include "Engine/World.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "MelodiaWaterInteractionSubsystem.h"
#include "MelodiaWaterProfile.h"
#include "WaterBodyComponent.h"

UMelodiaWaterRippleMaterialBridgeComponent::UMelodiaWaterRippleMaterialBridgeComponent()
{
	PrimaryComponentTick.bCanEverTick = true;

	static ConstructorHelpers::FObjectFinder<UMelodiaWaterProfile> ProfileFinder(
		TEXT("/Game/MelodiaIntegration/Water/Profiles/DA_WaterV10_Default.DA_WaterV10_Default"));
	if (ProfileFinder.Succeeded())
	{
		Profile = ProfileFinder.Object;
	}
}

void UMelodiaWaterRippleMaterialBridgeComponent::BeginPlay()
{
	Super::BeginPlay();

	if (WaterBodyId.IsNone() && GetOwner())
	{
		WaterBodyId = GetOwner()->GetFName();
	}
	if (Profile && !Profile->WaterBodyId.IsNone())
	{
		WaterBodyId = Profile->WaterBodyId;
	}

	DiscoverMaterials();
	if (UWorld* World = GetWorld())
	{
		WaterSubsystem = World->GetSubsystem<UMelodiaWaterInteractionSubsystem>();
		if (WaterSubsystem)
		{
			WaterSubsystem->OnContactEvent.AddUniqueDynamic(this, &ThisClass::HandleWaterContact);
		}
	}
	WriteParameters();
}

void UMelodiaWaterRippleMaterialBridgeComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (WaterSubsystem)
	{
		WaterSubsystem->OnContactEvent.RemoveDynamic(this, &ThisClass::HandleWaterContact);
	}
	WaterSubsystem = nullptr;
	WaterMaterials.Reset();
	Super::EndPlay(EndPlayReason);
}

void UMelodiaWaterRippleMaterialBridgeComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (bWriteNativeWaterParameters && WaterSubsystem && GetOwner())
	{
		FMelodiaWaterSample Sample;
		if (WaterSubsystem->GetLatestSample(GetOwner(), Sample))
		{
			UpdateNativeSample(Sample);
		}
	}

	for (float& Impulse : RippleImpulses)
	{
		Impulse = FMath::Max(0.0f, Impulse - RippleDecayPerSecond * DeltaTime);
	}
	WriteParameters();
}

void UMelodiaWaterRippleMaterialBridgeComponent::HandleWaterContact(FMelodiaWaterContactEvent Event)
{
	if (AcceptsEvent(Event))
	{
		UpdateNativeSample(Event.Sample);
		PushRipple(Event);
	}
}

void UMelodiaWaterRippleMaterialBridgeComponent::UpdateNativeSample(const FMelodiaWaterSample& Sample)
{
	if (bWriteNativeWaterParameters && Sample.bValid)
	{
		LastNativeSample = Sample;
		bHasNativeSample = true;
	}
}

void UMelodiaWaterRippleMaterialBridgeComponent::DiscoverMaterials()
{
	WaterMaterials.Reset();
	if (!GetOwner())
	{
		return;
	}

	TArray<UMeshComponent*> MeshComponents;
	GetOwner()->GetComponents<UMeshComponent>(MeshComponents);
	for (UMeshComponent* MeshComponent : MeshComponents)
	{
		if (!IsValid(MeshComponent))
		{
			continue;
		}

		for (int32 MaterialIndex = 0; MaterialIndex < MeshComponent->GetNumMaterials(); ++MaterialIndex)
		{
			if (UMaterialInstanceDynamic* Material = MeshComponent->CreateAndSetMaterialInstanceDynamic(MaterialIndex))
			{
				WaterMaterials.Add(Material);
			}
		}
	}

	// UE's quadtree water renderer owns the visible surface material on the
	// Water Body component rather than on an actor mesh. Prefer its managed
	// MIDs so this bridge also works for native Water Bodies with no mesh
	// component on the actor.
	if (UWaterBodyComponent* WaterBodyComponent = GetOwner()->FindComponentByClass<UWaterBodyComponent>())
	{
		if (UMaterialInstanceDynamic* WaterMaterial = WaterBodyComponent->GetWaterMaterialInstance())
		{
			WaterMaterials.AddUnique(WaterMaterial);
		}
		if (UMaterialInstanceDynamic* StaticMeshMaterial = WaterBodyComponent->GetWaterStaticMeshMaterialInstance())
		{
			WaterMaterials.AddUnique(StaticMeshMaterial);
		}
	}
}

void UMelodiaWaterRippleMaterialBridgeComponent::PushRipple(const FMelodiaWaterContactEvent& Event)
{
	RippleCenters[2] = RippleCenters[1];
	RippleCenters[1] = RippleCenters[0];
	RippleCenters[0] = Event.ContactLocation;
	RippleImpulses[2] = RippleImpulses[1];
	RippleImpulses[1] = RippleImpulses[0];
	RippleImpulses[0] = FMath::Clamp(Event.Intensity, 0.0f, 1.0f);
	WriteParameters();
}

void UMelodiaWaterRippleMaterialBridgeComponent::WriteParameters()
{
	const FName ImpulseNames[3] = { RippleImpulseAParameter, RippleImpulseBParameter, RippleImpulseCParameter };
	const FName CenterNames[3] = { RippleCenterAParameter, RippleCenterBParameter, RippleCenterCParameter };
	float TotalImpulse = 0.0f;

	for (int32 Slot = 0; Slot < 3; ++Slot)
	{
		TotalImpulse = FMath::Max(TotalImpulse, RippleImpulses[Slot]);
		const FLinearColor CenterColor(RippleCenters[Slot].X, RippleCenters[Slot].Y, RippleCenters[Slot].Z, 1.0f);
		for (UMaterialInstanceDynamic* Material : WaterMaterials)
		{
			if (IsValid(Material))
			{
				Material->SetVectorParameterValue(CenterNames[Slot], CenterColor);
				Material->SetScalarParameterValue(ImpulseNames[Slot], RippleImpulses[Slot]);
			}
		}
	}

	for (UMaterialInstanceDynamic* Material : WaterMaterials)
	{
		if (IsValid(Material))
		{
			Material->SetScalarParameterValue(BioluminescenceImpulseParameter, TotalImpulse);

			if (bWriteNativeWaterParameters && bHasNativeSample)
			{
				const float NativeAvailability = LastNativeSample.QueryProvider == EMelodiaWaterQueryProvider::Fallback
					? 0.0f
					: 1.0f;
				Material->SetScalarParameterValue(NativeWaterAvailabilityParameter, NativeAvailability);
				Material->SetScalarParameterValue(WaterBodyIndexParameter, static_cast<float>(LastNativeSample.WaterBodyIndex));
				Material->SetScalarParameterValue(WaterZoneIndexParameter, static_cast<float>(LastNativeSample.WaterZoneIndex));
				Material->SetScalarParameterValue(NativeShallowWaterHeightParameter, LastNativeSample.NativeShallowWaterHeight);
				Material->SetVectorParameterValue(
					NativeShallowWaterVelocityParameter,
					FLinearColor(
						LastNativeSample.NativeShallowWaterVelocity.X,
						LastNativeSample.NativeShallowWaterVelocity.Y,
						LastNativeSample.NativeShallowWaterVelocity.Z,
						1.0f));
				Material->SetVectorParameterValue(
					NativeShallowWaterNormalParameter,
					FLinearColor(
						LastNativeSample.NativeShallowWaterNormal.X,
						LastNativeSample.NativeShallowWaterNormal.Y,
						LastNativeSample.NativeShallowWaterNormal.Z,
						1.0f));
			}

			if (Profile && Profile->bUseSubstrateToonLayer)
			{
				Material->SetScalarParameterValue(ToonLightBandsParameter, Profile->ToonLightBands);
				Material->SetScalarParameterValue(ToonShadowSoftnessParameter, Profile->ToonShadowSoftness);
				Material->SetScalarParameterValue(ToonRimStrengthParameter, Profile->ToonRimStrength);
				Material->SetScalarParameterValue(ToonSpecularBandParameter, Profile->ToonSpecularBand);
				Material->SetVectorParameterValue(ToonShadowTintParameter, Profile->ToonShadowTint);
				Material->SetVectorParameterValue(ToonHighlightTintParameter, Profile->ToonHighlightTint);
				Material->SetScalarParameterValue(SurfaceRoughnessParameter, Profile->SurfaceRoughness);
				Material->SetScalarParameterValue(SurfaceMetallicParameter, Profile->SurfaceMetallic);
				Material->SetScalarParameterValue(SurfaceSubsurfaceWeightParameter, Profile->SurfaceSubsurfaceWeight);
				Material->SetScalarParameterValue(WaterBioluminescenceWeightParameter, Profile->WaterBioluminescenceWeight);
			}
		}
	}
}

bool UMelodiaWaterRippleMaterialBridgeComponent::AcceptsEvent(const FMelodiaWaterContactEvent& Event) const
{
	switch (Event.EventType)
	{
	case EMelodiaWaterContactType::SurfaceEntry:
	case EMelodiaWaterContactType::SurfaceExit:
	case EMelodiaWaterContactType::Ripple:
	case EMelodiaWaterContactType::Splash:
	case EMelodiaWaterContactType::Footstep:
	case EMelodiaWaterContactType::WaterImpact:
		break;
	default:
		return false;
	}

	return bAcceptUnidentifiedEvents
		? true
		: (!Event.Sample.WaterBodyId.IsNone() && Event.Sample.WaterBodyId == WaterBodyId);
}
