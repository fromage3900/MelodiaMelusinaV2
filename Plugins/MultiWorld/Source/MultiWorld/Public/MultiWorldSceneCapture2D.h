// Copyright 2019-2020 UNAmedia. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

#include "Engine/SceneCapture2D.h"
#include "HAL/ThreadSafeBool.h"

#include "Components/SceneCaptureComponent2D.h"

#include "MultiWorldSceneCapture2D.generated.h"

/**
 * Specialization of USceneCaptureComponent2D component compatible with the MultiWorld plugin.
 *
 * The standard [USceneCaptureComponent2D](https://docs.unrealengine.com/en-US/API/Runtime/Engine/Components/USceneCaptureComponent2D/)
 * component class fails to capture the scene when in a Background World.
 *
 * @internal
 * The standard component defers the rendering and, when the capture is executed,
 * the wrong UWorld handler is used causing a wrong result.
 */
UCLASS(BlueprintType, meta=(BlueprintSpawnableComponent))
class MULTIWORLD_API UMultiWorldSceneCaptureComponent2D : public USceneCaptureComponent2D
{
    GENERATED_BODY()

public:

    UMultiWorldSceneCaptureComponent2D();

protected:

    /** Overrides of UActorComponent::TickComponent */
    virtual void TickComponent(float DeltaTime, enum ELevelTick TickType, FActorComponentTickFunction *ThisTickFunction) override;
	
    /** Overrides of UActorComponent::SendRenderTransform_Concurrent */
    virtual void SendRenderTransform_Concurrent() override;
	
private:

    FThreadSafeBool bForceCapture = false;
};

/**
 * Specialization of ASceneCapture2D compatible with the MultiWorld plugin.
 *
 * The standard [ASceneCapture2D](https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/ASceneCapture2D/) actor class
 * fails to capture the scene when in a Background World.
 */
UCLASS(BlueprintType)
class MULTIWORLD_API AMultiWorldSceneCapture2D : public ASceneCapture2D
{
    GENERATED_UCLASS_BODY()
};
