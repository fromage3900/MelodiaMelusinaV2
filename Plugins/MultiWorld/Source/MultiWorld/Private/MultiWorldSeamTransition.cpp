// Copyright 2019 UNAmedia. All rights reserved.

#include "MultiWorldSeamTransition.h"

#include "Kismet/KismetRenderingLibrary.h"

#include "Components/SceneCaptureComponent2D.h"
#include "Components/PostProcessComponent.h"

#include "Engine/PostProcessVolume.h"
#include "Engine/SceneCapture2D.h"
#include "Engine/GameInstance.h"
#include "Engine/GameViewportClient.h"
#include "Materials/MaterialInstanceDynamic.h"

#include "MultiWorldManager.h"
#include "Private/MultiWorldSeamTransitionFXLayer.h"

#include "UObject/ConstructorHelpers.h"

#include "Runtime/Launch/Resources/Version.h" // for ENGINE_MAJOR_VERSION
#include "Engine/Engine.h"

#include "AudioDevice.h"

UMultiWorldSeamTransition::UMultiWorldSeamTransition()
	: fxLayerZOrder(1000)
{
    static ConstructorHelpers::FClassFinder<UUserWidget> WBPClassFinder(TEXT("/MultiWorld/SeamTransition/UMG_Effect"));
    UMGEffetLayerClass = WBPClassFinder.Class;
}

void UMultiWorldSeamTransition::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);

    UMultiWorldManager& MultiWorldManager = UMultiWorldManager::GetInstance(this);
    MultiWorldManager.OnPreWorldEnded.AddDynamic(this, &UMultiWorldSeamTransition::OnPreWorldEnded);
}

UTextureRenderTarget2D* UMultiWorldSeamTransition::CreateRenderTarget(FVector2D ViewportSize)
{
    return UKismetRenderingLibrary::CreateRenderTarget2D(this, ViewportSize.X, ViewportSize.Y, RTF_RGBA16f);
}

void UMultiWorldSeamTransition::Tick(float DeltaTime)
{
    if (!IsInTransition())
        return;

    CurrentTransitionTime += DeltaTime;

    float NormalizedTime = FMath::Clamp(CurrentTransitionTime / TransitionDuration, 0.f, 1.f);

    // wait some frames before adding the FX layer to the viewport
    // this is needed cos some post processing effect (e.g. the eye-adaptation) needs some frames to
    // compute the final rendering otherwise the user will see a jump...
    //(0.0833f = 1/60 * 5 frames)
    if (FXLayer && !FXLayer->IsInViewport() && CurrentTransitionTime > 0.0833f)
    {
        FXLayer->AddToViewport(fxLayerZOrder);
    }

    MatInstance->SetScalarParameterValue("MW_TransitionAlpha", NormalizedTime);

    if (!bWorldSwitched 
        && NormalizedTime >= WorldSwitchNormalizedTime)
    {
        DoWorldSwitch();
        bWorldSwitched = true;
    }

    UpdateSceneCapture(SrcWorldSceneCapture, DeltaTime);
    UpdateSceneCapture(DstWorldSceneCapture, DeltaTime);

    CaptureWorlds();

    AudioFading(NormalizedTime);

    if (NormalizedTime >= 1.0f)
    {
        NativeOnTransitionEnd();
    }
}

void UMultiWorldSeamTransition::OnPreWorldEnded(FMultiWorldHandle InWorldToEnd)
{
    if (InWorldToEnd == DestinationWorldHandle
		|| InWorldToEnd == SourceWorldHandle)
    {
        NativeOnTransitionEnd();
    }
}

bool UMultiWorldSeamTransition::IsTickable() const
{
    return true;
}

TStatId UMultiWorldSeamTransition::GetStatId() const
{
    return UObject::GetStatID();
}

void UMultiWorldSeamTransition::InitSceneCapture(UWorld* InWorld, USceneCaptureComponent2D* InSceneCapture, UTextureRenderTarget2D* RT) const
{
    check(InSceneCapture);
    check(RT);

    AActor* ViewTarget = GetViewTargetForWorld(InWorld);

    FMinimalViewInfo ViewInfo;
    ViewTarget->CalcCamera(/*DeltaTime =*/0.f, ViewInfo);

    InSceneCapture->FOVAngle = ViewInfo.FOV;

    InSceneCapture->bCaptureEveryFrame = 0;
    InSceneCapture->bCaptureOnMovement = 0;
    InSceneCapture->bAlwaysPersistRenderingState = true;
    InSceneCapture->TextureTarget = RT;
    InSceneCapture->CaptureSource = ESceneCaptureSource::SCS_FinalToneCurveHDR;

#if (ENGINE_MAJOR_VERSION == 4)
    ERHIFeatureLevel::Type FeatureLevel = InWorld->Scene->GetFeatureLevel();
    if (FeatureLevel <= ERHIFeatureLevel::ES3_1)
    {
        // On UE4.x SCS_FinalToneCurveHDR is not supported by the mobile renderer (ES3.1).
        // To avoid an assert in UE4 with the mobile renderer SCS_FinalColorHDR is used instead. 
        // Of couse the result is not the desidered one...
        InSceneCapture->CaptureSource = ESceneCaptureSource::SCS_FinalColorHDR;
        UE_LOG(LogTemp, Warning, TEXT("Tone mapping is not supported by the capture scene using the mobile renderer."));
    }
#endif
}

AActor* UMultiWorldSeamTransition::GetViewTargetForWorld(UWorld* InWorld) const
{
    check(InWorld);

    if (APlayerController* PC = InWorld->GetFirstPlayerController())
    {
        return PC->GetViewTarget();
    }

    return nullptr;
}

USceneCaptureComponent2D* UMultiWorldSeamTransition::FindSceneCaptureForWorld(UWorld* InWorld) const
{
    //@TODO: Design an interface that actors can implement so we can find the scenecapture easly.
    AActor* ViewTarget = GetViewTargetForWorld(InWorld);
    if(ViewTarget)
        return (USceneCaptureComponent2D*)ViewTarget->GetComponentByClass(USceneCaptureComponent2D::StaticClass());

    return nullptr;
}

ASceneCapture2D* UMultiWorldSeamTransition::CreateSceneCaptureForWorld(UWorld* InWorld, UTextureRenderTarget2D* RT) const
{
    check(InWorld);

    FActorSpawnParameters SpawnParameters;
    FTransform T = FTransform::Identity;
    ASceneCapture2D* SceneCapture = (ASceneCapture2D*)InWorld->SpawnActor(ASceneCapture2D::StaticClass(), &T, SpawnParameters);

    if (SceneCapture)
    {
        InitSceneCapture(InWorld, SceneCapture->GetCaptureComponent2D(), RT);
    }

    return SceneCapture;
}

void UMultiWorldSeamTransition::CreateFXLayer()
{
    check(!FXLayer);
    check(UMGEffetLayerClass);

    FXLayer = CastChecked<UMultiWorldSeamTransitionFXLayer>(CreateWidget(GetWorld(), UMGEffetLayerClass));
    if (FXLayer)
    {
        FXLayer->SetEffect(MatInstance);
        
        // postponed: see the tick function...
        //FXLayer->AddToViewport();
    }
}

void UMultiWorldSeamTransition::UpdateSceneCapture(ASceneCapture2D* SceneCapture, float DeltaTime)
{
    if (SceneCapture)
    {
        UWorld* SceneCaptureWorld = SceneCapture->GetWorld();

        AActor* ViewTarget = GetViewTargetForWorld(SceneCaptureWorld);

        FMinimalViewInfo ViewInfo;
        ViewTarget->CalcCamera(DeltaTime, ViewInfo);

        SceneCapture->SetActorLocation(ViewInfo.Location);
        SceneCapture->SetActorRotation(ViewInfo.Rotation);
        SceneCapture->GetCaptureComponent2D()->FOVAngle = ViewInfo.FOV;
    }
}

void UMultiWorldSeamTransition::CaptureWorlds()
{
    if (SrcWorldSceneCapture)
    {
        SrcWorldSceneCapture->GetCaptureComponent2D()->CaptureScene();
    }
    if (DstWorldSceneCapture)
    {
        DstWorldSceneCapture->GetCaptureComponent2D()->CaptureScene();
    }
}

void UMultiWorldSeamTransition::AudioFading(float NormalizedTime)
{
    UWorld* SourceWorld = GEngine->GetWorldFromContextObject(SourceWorldHandle.GetWorldContextObject(), EGetWorldErrorMode::Assert);
    UWorld* TargetWorld = GEngine->GetWorldFromContextObject(DestinationWorldHandle.GetWorldContextObject(), EGetWorldErrorMode::Assert);

    FAudioDevice* SourceAudioDevice = SourceWorld->GetAudioDevice().GetAudioDevice();
    FAudioDevice* TargetAudioDevice = TargetWorld->GetAudioDevice().GetAudioDevice();

    if (TargetAudioDevice != SourceAudioDevice)
    {
        if(SourceAudioDevice)
            SourceAudioDevice->SetTransientPrimaryVolume(1.0f - NormalizedTime);

        if (TargetAudioDevice)
            TargetAudioDevice->SetTransientPrimaryVolume(NormalizedTime);
    }
    
}

bool UMultiWorldSeamTransition::StartTransition(
    UObject* WorldContextObject,
    FMultiWorldHandle InDestinationWorldHandle,
    UMaterialInterface* PostProcessMaterial,
    const FOnTransitionEnd& InOnTransitionEnd,
    float InDurationInSeconds,
    float InWorldSwitchNormalizedTime,
    bool bInForceWorldsTickingDuringTransition,
    bool bInAutoHandleAudioFade)
{
    UWorld* DestinationWorld = GEngine->GetWorldFromContextObject(InDestinationWorldHandle.GetWorldContextObject(), EGetWorldErrorMode::LogAndReturnNull);
    if (!DestinationWorld)
    {
        UE_LOG(LogTemp, Warning, TEXT("Invalid destination world!."));
        return false;
    }

    UWorld* SrcWorld = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::Assert);
    if (SrcWorld == DestinationWorld)
    {
        UE_LOG(LogTemp, Warning, TEXT("Source and destination worlds are equals!."));
        return false;
    }

    if (!PostProcessMaterial)
    {
        UE_LOG(LogTemp, Warning, TEXT("Invalid reference to the post process material!."));
        return false;
    }

    if (InDurationInSeconds <= 0.f)
    {
        UE_LOG(LogTemp, Warning, TEXT("DurationInSeconds must be a not negative value!."));
        return false;
    }

    if (InWorldSwitchNormalizedTime < 0.0f || InWorldSwitchNormalizedTime > 1.0f)
    {
        UE_LOG(LogTemp, Warning, TEXT("WorldSwitchNormalizedTime must be a normalized value [0,1]."));
        return false;
    }

    if (IsInTransition())
    {
        UE_LOG(LogTemp, Warning, TEXT("A previous transition is still running; Wait the end to be able to start a new transition."));
        return false;
    }

    OnTransitionEnd = InOnTransitionEnd;

    UGameViewportClient* GameViewport = SrcWorld->GetGameInstance()->GetGameViewportClient();
    FVector2D ViewportSize;
    GameViewport->GetViewportSize(ViewportSize);

    //@FIXME: lazy initialization, find a better solution
    if (!SrcWorldRT)
    {
        SrcWorldRT = CreateRenderTarget(ViewportSize);
    }
    else 
    {
        // be sure that the RT size match the viewport size
        // (ResizeTarget do nothing if sizes match)
        SrcWorldRT->ResizeTarget(ViewportSize.X, ViewportSize.Y);
    }

    if (!DstWorldRT)
    {
        DstWorldRT = CreateRenderTarget(ViewportSize);
    }
    else
    {
        // be sure that the RT size match the viewport size
        // (ResizeTarget do nothing if sizes match)
        DstWorldRT->ResizeTarget(ViewportSize.X, ViewportSize.Y);
    }

    MatInstance = UMaterialInstanceDynamic::Create(PostProcessMaterial, this);
    MatInstance->SetTextureParameterValue("MW_SrcWorldRT", SrcWorldRT);
    MatInstance->SetTextureParameterValue("MW_DstWorldRT", DstWorldRT);

    TransitionDuration = InDurationInSeconds;
    DestinationWorldHandle = InDestinationWorldHandle;
    WorldSwitchNormalizedTime = InWorldSwitchNormalizedTime;
    bAutoHandleAudioFade = bInAutoHandleAudioFade;
    bForceWorldsTickingDuringTransition = bInForceWorldsTickingDuringTransition;

    UMultiWorldManager& MultiWorldManager = UMultiWorldManager::GetInstance(this);
    SourceWorldHandle = MultiWorldManager.GetActiveWorldHandle();
   
    SrcWorldSceneCapture = CreateSceneCaptureForWorld(SrcWorld, SrcWorldRT);
    check(SrcWorldSceneCapture);

    DstWorldSceneCapture = CreateSceneCaptureForWorld(DestinationWorld, DstWorldRT);
    check(DstWorldSceneCapture);
	
    bRestoreSrcWorldTickingFlag = false;

    CreateFXLayer();

    NativeOnTransitionStart();
    return true;
}

bool UMultiWorldSeamTransition::IsInTransition() const
{
    return TransitionDuration > 0.f;
}

void UMultiWorldSeamTransition::SetDefaultFXLayerZOrder(int32 ZOrder)
{
	fxLayerZOrder = ZOrder;
}

void UMultiWorldSeamTransition::NativeOnTransitionStart()
{
    MatInstance->SetScalarParameterValue("MW_SourceWorldIsInBackground", 0.0f);

    UWorld* SourceWorld = GEngine->GetWorldFromContextObject(SourceWorldHandle.GetWorldContextObject(), EGetWorldErrorMode::Assert);
    UWorld* TargetWorld = GEngine->GetWorldFromContextObject(DestinationWorldHandle.GetWorldContextObject(), EGetWorldErrorMode::Assert);

    if (bAutoHandleAudioFade)
    {
        FAudioDevice* SourceAudioDevice = SourceWorld->GetAudioDevice().GetAudioDevice();
        FAudioDevice* TargetAudioDevice = TargetWorld->GetAudioDevice().GetAudioDevice();

        if (SourceAudioDevice != TargetAudioDevice)
        {
            if (TargetAudioDevice)
            {
                TargetAudioDevice->SetDeviceMuted(false);
                TargetAudioDevice->SetTransientPrimaryVolume(0.f);
            }
        }
        else
        {
            UE_LOG(LogTemp, Warning, TEXT("bAutoHandleAudioFade is true but worlds have a shared audio device!"));
        }
    }

    if (bForceWorldsTickingDuringTransition)
    {
        if (!TargetWorld->ShouldTick())
        {
            TargetWorld->SetShouldTick(true);
        }
    }
}

void UMultiWorldSeamTransition::DoWorldSwitch()
{
    UMultiWorldManager& MultiWorldManager = UMultiWorldManager::GetInstance(this);

    MultiWorldManager.SwitchWorld(DestinationWorldHandle);

    UWorld* SourceWorld = GEngine->GetWorldFromContextObject(SourceWorldHandle.GetWorldContextObject(), EGetWorldErrorMode::Assert);

    if (bAutoHandleAudioFade)
    {
        FAudioDevice* SourceAudioDevice = SourceWorld->GetAudioDevice().GetAudioDevice();
        if (SourceAudioDevice)
            SourceAudioDevice->SetDeviceMuted(false);
    }

    if (bForceWorldsTickingDuringTransition)
    {
        if (!SourceWorld->ShouldTick())
        {
            SourceWorld->SetShouldTick(true);
            bRestoreSrcWorldTickingFlag = true;
        }
    }

    MatInstance->SetScalarParameterValue("MW_SourceWorldIsInBackground", 1.0f);
}

void UMultiWorldSeamTransition::NativeOnTransitionEnd()
{
    UWorld* SourceWorld = GEngine->GetWorldFromContextObject(SourceWorldHandle.GetWorldContextObject(), EGetWorldErrorMode::Assert);
    UWorld* TargetWorld = GEngine->GetWorldFromContextObject(DestinationWorldHandle.GetWorldContextObject(), EGetWorldErrorMode::Assert);

    UMultiWorldManager& MultiWorldManager = UMultiWorldManager::GetInstance(this);
    // re-check if we have switched world or not...
    // This is needed because the bWorldSwitched flag can be a false-positive 
    // when the user end the destination world when the transation is not over but the switch was done.
    // In this scenario the main world is activated and so it's like we have not make the switch.
    bWorldSwitched = MultiWorldManager.GetActiveWorldHandle() == DestinationWorldHandle;

    if (bWorldSwitched && bForceWorldsTickingDuringTransition && bRestoreSrcWorldTickingFlag)
    {
        SourceWorld->SetShouldTick(false);
    }

    {
        FXLayer->RemoveFromParent();
        FXLayer = nullptr;
    }

    SrcWorldSceneCapture->Destroy();
    SrcWorldSceneCapture = nullptr;

    DstWorldSceneCapture->Destroy();
    DstWorldSceneCapture = nullptr;

    TransitionDuration = 0;
    CurrentTransitionTime = 0;
    bWorldSwitched = false;

    if (bAutoHandleAudioFade)
    {
        FAudioDevice* SourceAudioDevice = SourceWorld->GetAudioDevice().GetAudioDevice();
        FAudioDevice* TargetAudioDevice = TargetWorld->GetAudioDevice().GetAudioDevice();

        if (SourceAudioDevice != TargetAudioDevice)
        {
            if (SourceAudioDevice)
            {
                SourceAudioDevice->SetDeviceMuted(true);
                SourceAudioDevice->SetTransientPrimaryVolume(1.0f);
            }
        }
    }

    DestinationWorldHandle = FMultiWorldHandle();
    SourceWorldHandle = FMultiWorldHandle();

    if (OnTransitionEnd.IsBound())
    {
        OnTransitionEnd.Execute();
    }
}
