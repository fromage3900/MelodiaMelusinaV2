#include "MelodiaWaterUnderwaterPostProcessComponent.h"

#include "Camera/PlayerCameraManager.h"
#include "Engine/Scene.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "MelodiaWaterInteractionSubsystem.h"
#include "MelodiaWaterProfile.h"
#include "UObject/ConstructorHelpers.h"
#include "WaterBodyComponent.h"

UMelodiaWaterUnderwaterPostProcessComponent::UMelodiaWaterUnderwaterPostProcessComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	// Feed the camera manager before its frame blend pass clears/consumes the
	// cached post-process list.
	PrimaryComponentTick.TickGroup = TG_PrePhysics;

	static ConstructorHelpers::FObjectFinder<UMaterialInterface> UnderwaterFinder(
		TEXT("/Game/EnvSandbox/Materials/Instances/Water/v9/MI_Water_Underwater_Post_Default.MI_Water_Underwater_Post_Default"));
	if (UnderwaterFinder.Succeeded())
	{
		UnderwaterMaterial = UnderwaterFinder.Object;
	}

	static ConstructorHelpers::FObjectFinder<UMelodiaWaterProfile> ProfileFinder(
		TEXT("/Game/MelodiaIntegration/Water/Profiles/DA_WaterV10_Default.DA_WaterV10_Default"));
	if (ProfileFinder.Succeeded())
	{
		Profile = ProfileFinder.Object;
	}
}

void UMelodiaWaterUnderwaterPostProcessComponent::BeginPlay()
{
	Super::BeginPlay();

	if (UWorld* World = GetWorld())
	{
		WaterSubsystem = World->GetSubsystem<UMelodiaWaterInteractionSubsystem>();
	}

	if (UnderwaterMaterial)
	{
		UnderwaterMID = UMaterialInstanceDynamic::Create(UnderwaterMaterial, this);
	}

	if (Profile && !Profile->UnderwaterMaterial.IsNull())
	{
		// The profile is the v10/native ownership seam. Do not replace the
		// rollback fallback MID above; custom surfaces still use that lane.
		if (UMaterialInterface* ProfileMaterial = Profile->UnderwaterMaterial.LoadSynchronous())
		{
			UnderwaterMaterial = ProfileMaterial;
		}
	}
}

void UMelodiaWaterUnderwaterPostProcessComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	UnderwaterMID = nullptr;
	NativeUnderwaterMID = nullptr;
	ActiveNativeWaterBody = nullptr;
	WaterSubsystem = nullptr;
	Super::EndPlay(EndPlayReason);
}

void UMelodiaWaterUnderwaterPostProcessComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (!WaterSubsystem || !GetWorld())
	{
		return;
	}

	FMelodiaWaterSample Sample;
	const bool bHasSample = WaterSubsystem->GetLatestSample(GetOwner(), Sample);
	const float TargetBlend = bHasSample && Sample.bUnderwater
		? FMath::Clamp(FMath::Max(Sample.Immersion, 0.35f), 0.0f, 1.0f)
		: 0.0f;

	UWaterBodyComponent* NativeWaterBody = nullptr;
	const bool bUseNativePostProcess = bUseNativeWaterPostProcess
		&& bHasSample
		&& Sample.bUnderwater
		&& !Sample.WaterBodyId.IsNone()
		&& WaterSubsystem->TryGetWaterBodyComponent(Sample.WaterBodyId, NativeWaterBody)
		&& IsValid(NativeWaterBody);
	if (bUseNativePostProcess)
	{
		if (ActiveNativeWaterBody.Get() != NativeWaterBody)
		{
			UMaterialInterface* NativeMaterial = nullptr;
			if (Profile && !Profile->UnderwaterMaterial.IsNull())
			{
				NativeMaterial = Profile->UnderwaterMaterial.LoadSynchronous();
			}
			if (NativeMaterial)
			{
				NativeWaterBody->SetUnderwaterPostProcessMaterial(NativeMaterial);
			}
			ActiveNativeWaterBody = NativeWaterBody;
		}

		NativeUnderwaterMID = NativeWaterBody->GetUnderwaterPostProcessMaterialInstance();
		if (NativeUnderwaterMID)
		{
			NativeUnderwaterMID->SetScalarParameterValue(BlendParameter, TargetBlend);
			NativeUnderwaterMID->SetScalarParameterValue(DepthParameter, Sample.ImmersionDepth);
		}

		CurrentBlend = TargetBlend;
		return;
	}

	ActiveNativeWaterBody = nullptr;
	NativeUnderwaterMID = nullptr;
	if (!UnderwaterMID)
	{
		return;
	}

	const float BlendSpeed = TargetBlend > CurrentBlend ? BlendInSpeed : BlendOutSpeed;
	CurrentBlend = FMath::FInterpTo(CurrentBlend, TargetBlend, DeltaTime, BlendSpeed);

	UnderwaterMID->SetScalarParameterValue(BlendParameter, CurrentBlend);
	UnderwaterMID->SetScalarParameterValue(DepthParameter, bHasSample ? Sample.ImmersionDepth : 0.0f);

	APlayerCameraManager* CameraManager = UGameplayStatics::GetPlayerCameraManager(this, 0);
	if (!CameraManager || CurrentBlend <= KINDA_SMALL_NUMBER)
	{
		return;
	}

	FPostProcessSettings PostProcessSettings;
	PostProcessSettings.WeightedBlendables.Array.Add(FWeightedBlendable(1.0f, UnderwaterMID));
	CameraManager->AddCachedPPBlend(PostProcessSettings, CurrentBlend);
}
