// Copyright 2019-2020 UNAmedia. All Rights Reserved.

#include "MultiWorldSceneCapture2D.h"

#include "Engine/World.h"

#include "Runtime/Renderer/Private/ScenePrivate.h"

#if WITH_EDITOR
void ResetAndShrinkModifiedBounds(TArray<FBox>& Bounds)
{
    constexpr uint32 MinPrimitiveModifiedBoundsAllocation = 16 * 1024;

    const int32 MaxAllocatedSize = FMath::RoundUpToPowerOfTwo(FMath::Max<uint32>(MinPrimitiveModifiedBoundsAllocation, Bounds.Num()));

    if (Bounds.Max() > MaxAllocatedSize)
    {
        Bounds.Empty(MaxAllocatedSize);
    }

    Bounds.Reset();
}

#else
extern void ResetAndShrinkModifiedBounds(TArray<FBox>& Bounds);
#endif // WITH_EDITOR

UMultiWorldSceneCaptureComponent2D::UMultiWorldSceneCaptureComponent2D()
{
    // Because we have to set bCaptureEveryFrame to false
    // this must be true to have a persistent rendering state (the default behaviour).
    bAlwaysPersistRenderingState = true;
}

void UMultiWorldSceneCaptureComponent2D::TickComponent(float DeltaTime, enum ELevelTick TickType, FActorComponentTickFunction *ThisTickFunction)
{
    USceneComponent::TickComponent(DeltaTime, TickType, ThisTickFunction);

    if (bCaptureEveryFrame || bForceCapture)
    {
        bool bCaptureEveryFrameToRestore = bCaptureEveryFrame;
        bCaptureEveryFrame = false;

        CaptureScene();

        FScene* Scene = (FScene*)GetWorld()->Scene;

        // Bug #1277: the array Scene->DistanceFieldSceneData.PrimitiveModifiedBounds is shrink in RenderViewFamilies_RenderThread 
        // but this function is not called if the world is not rendered (this happen when the world is not active).
        ENQUEUE_RENDER_COMMAND(ResetAndShrinkModifiedBoundsRenderCommand)(
            [Scene](FRHICommandListImmediate& RHICmdList)
            {
                for (int32 CacheType = 0; CacheType < UE_ARRAY_COUNT(Scene->DistanceFieldSceneData.PrimitiveModifiedBounds); CacheType++)
                {
                    ResetAndShrinkModifiedBounds(Scene->DistanceFieldSceneData.PrimitiveModifiedBounds[CacheType]);
                }
            });

        bCaptureEveryFrame = bCaptureEveryFrameToRestore;
        bForceCapture = false;
    }
}

void UMultiWorldSceneCaptureComponent2D::SendRenderTransform_Concurrent()
{
    USceneComponent::SendRenderTransform_Concurrent();
	
    if(bCaptureOnMovement && !bCaptureEveryFrame)
    {
	    bForceCapture = true;
    }
}

AMultiWorldSceneCapture2D::AMultiWorldSceneCapture2D(const FObjectInitializer& ObjectInitializer)
: Super(ObjectInitializer.SetDefaultSubobjectClass<UMultiWorldSceneCaptureComponent2D>(TEXT("NewSceneCaptureComponent2D")))
{
}
