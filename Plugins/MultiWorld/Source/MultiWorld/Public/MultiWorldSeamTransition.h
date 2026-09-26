// Copyright 2019 UNAmedia. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Tickable.h"

#include "MultiWorldHandle.h"

#include "MultiWorldSeamTransition.generated.h"

class APostProcessVolume;
class UMaterial;
class UMaterialInstanceDynamic;
class UTextureRenderTarget2D;
class ASceneCapture2D;
class USceneCaptureComponent2D;

DECLARE_DYNAMIC_DELEGATE(FOnTransitionEnd);

/**
 * Helper class to make a seam transition between two worlds, driving a customizable graphics effect.
 */
UCLASS()
class MULTIWORLD_API UMultiWorldSeamTransition
    : public UGameInstanceSubsystem
    , public FTickableGameObject
{
	GENERATED_BODY()

public:

	/**
	Start a seam visual transition that brings the player to a new world.

	@param[in] WorldContextObject World context object.
	@param[in] InDestinationWorldHandle Destination world handle.
	@param[in] TransitionMaterial The material used by the visual transition. Read the notes below for details.
	@param[in] OnTransitionEnd Callback called when the transition ends.
	@param[in] DurationInSeconds Transition duration in seconds. Must be not negative.
	@param[in] WorldSwitchNormalizedTime Normalized time in [0, 1] used to control when the world switching is performed
		(i.e. when UMultiWorldStatics::SwitchWorld() is called).
		For example, with @a WorldSwitchNormalizedTime = 0.5f the switch is performed at the middle of the transition;
		with @a WorldSwitchNormalizedTime = 1.0f the switch is performed at the end of the transition.
    @param[in] bForceWorldsTickingDuringTransition if true, the ticking is forced for both worlds involved for the transition duration.
	@param[in] bAutoHandleAudioFade if true, then the audio fade-in/out between the two worlds is handled automatically.
		It requires that each of the involved worlds have a dedicated audio device.

	Only one active transition can run at a given time, otherwise the call will fail returning false.

	# Transition Material

	The effect uses a Material to drive the visual transition. This material must complies to some requirements:

	- the *Material Domain* property MUST be set to `User Interface`;
	- you can use the Material Function `MultiWorld_SeamTransition_MF` to access the information needed to mix the two rendered worlds
	(like the current animation factor, the sampled colors from the source and destination worlds, etc).
	
	![A simple cross-fading transition effect](SeamTransitionMaterial.png "A simple cross-fading transition effect")

	The plugin provides some ready-to-use materials (e.g. `MW_ST_CrossFading_PPM`, `MW_ST_WipeLeftToRight_PPM`, etc.),
	that you can use as-is or analyze to create your custom ones.

    # HUD and UMG widgets

    HUD and UMG widgets of the switching worlds are not visible during the transition.
    If you want them to gently disappear/appear on screen, you must manually
    take care of it (e.g. animating their opacity) before starting the transition and when the transition ends
    (see the @a OnTransitionEnd parameter).

	@return true if the transition is started.
	*/
    UFUNCTION(BlueprintCallable, Category = "MultiWorld", meta = (WorldContext = "WorldContextObject", AutoCreateRefTerm = "OnTransitionEnd"))
    bool StartTransition(UObject* WorldContextObject, 
        FMultiWorldHandle InDestinationWorldHandle,
        UMaterialInterface* TransitionMaterial,
        const FOnTransitionEnd& OnTransitionEnd,
        float DurationInSeconds = 1.0f,
        float WorldSwitchNormalizedTime = 0.5f,
        bool bForceWorldsTickingDuringTransition = true,
        bool bAutoHandleAudioFade = true);

    /// Checks if a transition is still running
    UFUNCTION(BlueprintPure, Category = "MultiWorld")
    bool IsInTransition() const;

	/**
	Set the ZOrder value used by the widget showing the transition VFX.
	
	@param ZOrder The new ZOrder value to use. The higher the number, the more on top the widget will be.

	The new value will be effective on the next call of StartTransition().
	*/
	UFUNCTION(BlueprintCallable, Category = "MultiWorld")
	void SetDefaultFXLayerZOrder(int32 ZOrder);

public:

    UMultiWorldSeamTransition();

	// Begin USubsystem
    virtual bool ShouldCreateSubsystem(UObject* Outer) const override; ///< Override
    virtual void Initialize(FSubsystemCollectionBase& Collection) override; ///< Override
	// End USubsystem

    // Begin FTickableGameObject Interface.
    virtual void Tick(float DeltaTime) override;    ///< Override
    virtual bool IsTickable() const override;       ///< Override
    virtual TStatId GetStatId() const override;     ///< Override
    // End FTickableGameObject Interface.

private:

    void InitSceneCapture(UWorld* InWorld, USceneCaptureComponent2D* InSceneCapture, UTextureRenderTarget2D* RT) const;

    UTextureRenderTarget2D* CreateRenderTarget(FVector2D ViewportSize);

private:

    AActor* GetViewTargetForWorld(UWorld* InWorld) const;
    USceneCaptureComponent2D* FindSceneCaptureForWorld(UWorld* InWorld) const;

    ASceneCapture2D* CreateSceneCaptureForWorld(UWorld* InWorld, UTextureRenderTarget2D* RT) const;

    void CreateFXLayer();

    void UpdateSceneCapture(ASceneCapture2D* SceneCapture, float DeltaTime);
    void CaptureWorlds();

    void AudioFading(float NormalizedTime);

private:

    void NativeOnTransitionStart();
    void NativeOnTransitionEnd();

    void DoWorldSwitch();

    UFUNCTION()
    void OnPreWorldEnded(FMultiWorldHandle InWorldToEnd);

private:

    UPROPERTY()
    TSubclassOf<class UUserWidget> UMGEffetLayerClass;

    UPROPERTY(Transient)
    class UMultiWorldSeamTransitionFXLayer* FXLayer;

    UPROPERTY(Transient)
    FOnTransitionEnd OnTransitionEnd;

    UPROPERTY(Transient)
    UTextureRenderTarget2D* SrcWorldRT;

    UPROPERTY(Transient)
    UTextureRenderTarget2D* DstWorldRT;

    UPROPERTY(Transient)
    UMaterialInstanceDynamic* MatInstance;

    UPROPERTY(Transient)
    ASceneCapture2D* SrcWorldSceneCapture;

    UPROPERTY(Transient)
    ASceneCapture2D* DstWorldSceneCapture;

    float TransitionDuration = 0;
    float CurrentTransitionTime = 0;
    float WorldSwitchNormalizedTime = 1.0f;
    bool bWorldSwitched = false;
    bool bAutoHandleAudioFade = true;
    bool bForceWorldsTickingDuringTransition = true;
    bool bRestoreSrcWorldTickingFlag = false;
    int32 fxLayerZOrder;

    UPROPERTY(Transient)
    FMultiWorldHandle DestinationWorldHandle;

    UPROPERTY(Transient)
    FMultiWorldHandle SourceWorldHandle;
};
