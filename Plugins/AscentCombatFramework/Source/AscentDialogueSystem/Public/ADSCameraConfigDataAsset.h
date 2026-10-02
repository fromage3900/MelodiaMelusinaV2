// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include <CineCameraActor.h>
#include <CineCameraSettings.h>
#include <Camera/PlayerCameraManager.h>

#include "ADSCameraConfigDataAsset.generated.h"

/**
 *
 */
UCLASS()
class ASCENTDIALOGUESYSTEM_API UADSCameraConfigDataAsset : public UPrimaryDataAsset {
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera|Position")
    FVector CameraOffset = FVector(350.0f, 50.0f, 0.0f);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
    float Aperture = 1.2f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
    float FocalLength = 85.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
    float FOV = 90.0f;

    // Complete camera settings
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera|Focus")
    FCameraFocusSettings FocusSettings;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera|LookAt")
    FCameraLookatTrackingSettings LookatTrackingSettings;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera|Transition")
    float BlendTime = .2f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera|Transition")
    TEnumAsByte<EViewTargetBlendFunction> BlendFunction = VTBlend_Cubic;
};
