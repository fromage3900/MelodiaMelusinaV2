// Copyright 2024 Tore Lervik. All Rights Reserved.

#pragma once

#include "SceneViewExtension.h"
#include "ScreenPass.h"
#include "Misc/EngineVersionComparison.h"


class FMeshBlendSceneViewExtension : public FSceneViewExtensionBase
{
public:
	FMeshBlendSceneViewExtension(const FAutoRegister& AutoRegister);

	virtual void SetupViewFamily(FSceneViewFamily& InViewFamily) override
	{
	};

	virtual void SetupView(FSceneViewFamily& InViewFamily, FSceneView& InView) override
	{
	};

	virtual void BeginRenderViewFamily(FSceneViewFamily& InViewFamily) override
	{
	};

	UTexture2D* NoiseTexture = nullptr;


#if UE_VERSION_OLDER_THAN(5, 6, 0)
	virtual void PrePostProcessPass_RenderThread(FRDGBuilder& GraphBuilder, const FSceneView& View, const FPostProcessingInputs& Inputs) override;
#else
	virtual void SubscribeToPostProcessingPass(EPostProcessingPass PassId,
	                                           const FSceneView& View,
	                                           FAfterPassCallbackDelegateArray& InOutPassCallbacks,
	                                           bool bIsPassEnabled) override;
	FScreenPassTexture PostProcess_RenderThread(FRDGBuilder& GraphBuilder, const FSceneView& View, const FPostProcessMaterialInputs& InOutInputs);
#endif

private:
	void AddMeshBlendPass(FRDGBuilder& GraphBuilder,
	                      const FSceneView& View,
	                      const FScreenPassTexture& SceneColor,
	                      const FScreenPassRenderTarget& Output,
	                      FSceneTextureShaderParameters SceneTextures);

	bool IsEnabled(const FSceneView& View);
};
