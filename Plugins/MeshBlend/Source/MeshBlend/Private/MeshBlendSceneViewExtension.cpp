// Copyright 2024 Tore Lervik. All Rights Reserved.


#include "MeshBlendSceneViewExtension.h"

#include "DataDrivenShaderPlatformInfo.h"
#include "DynamicResolutionState.h"
#include "GlobalShader.h"
#include "MeshBlendShaders.h"
#include "PixelShaderUtils.h"
#include "SceneRendering.h"
#include "SceneRenderTargetParameters.h"
#include "ScreenPass.h"
#include "TextureResource.h"
#include "VectorUtil.h"
#include "Engine/Texture2D.h"
#include "Misc/EngineVersionComparison.h"
#include "PostProcess/PostProcessing.h"

#if UE_VERSION_OLDER_THAN(5, 4, 0)
#else
#include "Substrate/Substrate.h"
#endif

#if UE_VERSION_OLDER_THAN(5, 6, 0)
#else
#include "PostProcess/PostProcessMaterialInputs.h"
#endif

static TAutoConsoleVariable<int32> CVarMeshBlendQuality(TEXT("r.MeshBlend.Quality"), 2, TEXT("Low, Medium, High, Epic"), ECVF_Scalability);
static TAutoConsoleVariable<int32> CVarMeshBlendVisualize(TEXT("r.MeshBlend.Visualize"), 0, TEXT(".."));

static TAutoConsoleVariable<float> CVarMeshBlendSmallSize(TEXT("r.MeshBlend.Small.Size"), 6.0, TEXT(".."));
static TAutoConsoleVariable<float> CVarMeshBlendMediumSize(TEXT("r.MeshBlend.Medium.Size"), 10.0, TEXT(".."));
static TAutoConsoleVariable<float> CVarMeshBlendLargeSize(TEXT("r.MeshBlend.Large.Size"), 20.0, TEXT(".."));
static TAutoConsoleVariable<float> CVarMeshBlendExtraLargeSize(TEXT("r.MeshBlend.ExtraLarge.Size"), 30.0, TEXT(".."));

static TAutoConsoleVariable<float> CVarMeshBlendSmallMinSize(TEXT("r.MeshBlend.Small.MinSize"), 1.5, TEXT(".."));
static TAutoConsoleVariable<float> CVarMeshBlendMediumMinSize(TEXT("r.MeshBlend.Medium.MinSize"), 3.0, TEXT(".."));
static TAutoConsoleVariable<float> CVarMeshBlendLargeMinSize(TEXT("r.MeshBlend.Large.MinSize"), 3.0, TEXT(".."));
static TAutoConsoleVariable<float> CVarMeshBlendExtraLargeMinSize(TEXT("r.MeshBlend.ExtraLarge.MinSize"), 5.0, TEXT(".."));

static TAutoConsoleVariable<float> CVarMeshBlendSlopeFactor(TEXT("r.MeshBlend.SlopeFactor"), 2.0, TEXT(".."));
static TAutoConsoleVariable<int32> CVarMeshBlendFrameDither(TEXT("r.MeshBlend.FrameDither"), 1, TEXT(".."));

static TAutoConsoleVariable<float> CVarMeshBlendNoiseFactor(TEXT("r.MeshBlend.NoiseFactor"), 0.3, TEXT(".."));
static TAutoConsoleVariable<float> CVarMeshBlendNoiseTileSize(TEXT("r.MeshBlend.NoiseTileSize"), 10, TEXT(".."));
static TAutoConsoleVariable<float> CVarMeshBlendNoiseFade(TEXT("r.MeshBlend.NoiseFade"), 0.5, TEXT(".."));
static TAutoConsoleVariable<float> CVarMeshBlendNoiseOffset(TEXT("r.MeshBlend.NoiseOffset"), 0.0, TEXT(".."));

DECLARE_GPU_STAT_NAMED(MeshBlend_RenderPass, TEXT("MeshBlend"));

FMeshBlendSceneViewExtension::FMeshBlendSceneViewExtension(const FAutoRegister& AutoRegister) : FSceneViewExtensionBase(AutoRegister)
{
}

namespace
{
	FScreenPassTextureViewportParameters GetTextureViewportParameters(const FScreenPassTextureViewport& InViewport)
	{
		const FVector2f Extent(InViewport.Extent);
		const FVector2f ViewportMin(InViewport.Rect.Min.X, InViewport.Rect.Min.Y);
		const FVector2f ViewportMax(InViewport.Rect.Max.X, InViewport.Rect.Max.Y);
		const FVector2f ViewportSize = ViewportMax - ViewportMin;

		FScreenPassTextureViewportParameters Parameters;

		if (!InViewport.IsEmpty())
		{
			Parameters.Extent = FVector2f(Extent);
			Parameters.ExtentInverse = FVector2f(1.0f / Extent.X, 1.0f / Extent.Y);

			Parameters.ScreenPosToViewportScale = FVector2f(0.5f, -0.5f) * ViewportSize;
			Parameters.ScreenPosToViewportBias = (0.5f * ViewportSize) + ViewportMin;

			Parameters.ViewportMin = InViewport.Rect.Min;
			Parameters.ViewportMax = InViewport.Rect.Max;

			Parameters.ViewportSize = ViewportSize;
			Parameters.ViewportSizeInverse = FVector2f(1.0f / Parameters.ViewportSize.X, 1.0f / Parameters.ViewportSize.Y);

			Parameters.UVViewportMin = ViewportMin * Parameters.ExtentInverse;
			Parameters.UVViewportMax = ViewportMax * Parameters.ExtentInverse;

			Parameters.UVViewportSize = Parameters.UVViewportMax - Parameters.UVViewportMin;
			Parameters.UVViewportSizeInverse = FVector2f(1.0f / Parameters.UVViewportSize.X, 1.0f / Parameters.UVViewportSize.Y);

			Parameters.UVViewportBilinearMin = Parameters.UVViewportMin + 0.5f * Parameters.ExtentInverse;
			Parameters.UVViewportBilinearMax = Parameters.UVViewportMax - 0.5f * Parameters.ExtentInverse;
		}

		return Parameters;
	}

	FRDGTextureRef GetNoiseTexture(FRDGBuilder& GraphBuilder, UTexture2D* NoiseTexture)
	{
		FTextureRHIRef TextureRHI = GBlackTexture->TextureRHI;

		if (NoiseTexture != nullptr && NoiseTexture->GetResource() != nullptr && NoiseTexture->GetResource()->TextureRHI.IsValid())
		{
			TextureRHI = NoiseTexture->GetResource()->TextureRHI;
		}

		return GraphBuilder.RegisterExternalTexture(CreateRenderTarget(TextureRHI, TEXT("MeshBlend_NoiseTexture")));
	}
}


#if UE_VERSION_OLDER_THAN(5, 6, 0)

void FMeshBlendSceneViewExtension::PrePostProcessPass_RenderThread(FRDGBuilder& GraphBuilder, const FSceneView& View, const FPostProcessingInputs& Inputs)
{
	if (!IsEnabled(View))
	{
		return;
	}

	Inputs.Validate();

	checkSlow(View.bIsViewInfo); // can't do dynamic_cast because FViewInfo doesn't have any virtual functions.
	const FViewInfo& ViewInfo = static_cast<const FViewInfo&>(View);
	const FIntRect PrimaryViewRect = ViewInfo.ViewRect;

	FScreenPassTexture SceneColor((*Inputs.SceneTextures)->SceneColorTexture, PrimaryViewRect);

	if (!SceneColor.IsValid())
	{
		return;
	}

	{
		RDG_EVENT_SCOPE(GraphBuilder, "MeshBlend");

		check(View.bIsViewInfo);
		FSceneTextureShaderParameters SceneTextures = CreateSceneTextureShaderParameters(GraphBuilder, View, ESceneTextureSetupMode::All);

		FScreenPassRenderTarget RenderTarget = FScreenPassRenderTarget::CreateFromInput(GraphBuilder, SceneColor, View.GetOverwriteLoadAction(), TEXT("MeshBlendRenderTarget"));

		AddMeshBlendPass(GraphBuilder, View, SceneColor, RenderTarget, SceneTextures);

		FRDGTextureDesc SceneColorDesc = SceneColor.Texture->Desc;
		FRHICopyTextureInfo CopyTextureInfo;
		CopyTextureInfo.NumMips = 1;
		CopyTextureInfo.Size = FIntVector(SceneColorDesc.GetSize().X, SceneColorDesc.GetSize().Y, 0);

		AddCopyTexturePass(GraphBuilder, RenderTarget.Texture, SceneColor.Texture, CopyTextureInfo);
	}
}

#else

void FMeshBlendSceneViewExtension::SubscribeToPostProcessingPass(EPostProcessingPass PassId,
                                                                 const FSceneView& View,
                                                                 FAfterPassCallbackDelegateArray& InOutPassCallbacks,
                                                                 bool bIsPassEnabled)
{
	if (PassId == EPostProcessingPass::BeforeDOF)
	{
		if (!IsEnabled(View))
		{
			return;
		}

		InOutPassCallbacks.Add(FAfterPassCallbackDelegate::CreateRaw(this, &FMeshBlendSceneViewExtension::PostProcess_RenderThread));
	}
}

FScreenPassTexture FMeshBlendSceneViewExtension::PostProcess_RenderThread(FRDGBuilder& GraphBuilder, const FSceneView& View, const FPostProcessMaterialInputs& InOutInputs)
{
	RDG_EVENT_SCOPE(GraphBuilder, "MeshBlend");
	check(View.bIsViewInfo);
	
	const FScreenPassTexture& SceneColor = FScreenPassTexture::CopyFromSlice(GraphBuilder, InOutInputs.GetInput(EPostProcessMaterialInput::SceneColor));
	check(SceneColor.IsValid());

	FScreenPassRenderTarget Output = InOutInputs.OverrideOutput;

	// If the override output is provided, it means that this is not the first pass in the post processing chain.
	if (!Output.IsValid())
	{
		Output = FScreenPassRenderTarget::CreateFromInput(GraphBuilder, SceneColor, View.GetOverwriteLoadAction(), TEXT("MeshBlendRenderTarget"));
	}

	FSceneTextureShaderParameters SceneTextures = CreateSceneTextureShaderParameters(GraphBuilder, View, ESceneTextureSetupMode::All);

	AddMeshBlendPass(GraphBuilder, View, SceneColor, Output, SceneTextures);

	if (InOutInputs.OverrideOutput.IsValid())
	{
		AddDrawTexturePass(GraphBuilder, View, Output, InOutInputs.OverrideOutput);
		return InOutInputs.OverrideOutput;
	}
	
	return MoveTemp(Output);
}

#endif

void FMeshBlendSceneViewExtension::AddMeshBlendPass(FRDGBuilder& GraphBuilder,
                                                    const FSceneView& View,
                                                    const FScreenPassTexture& SceneColor,
                                                    const FScreenPassRenderTarget& Output,
                                                    FSceneTextureShaderParameters SceneTextures)
{
	checkSlow(View.bIsViewInfo);

	FScreenPassRenderTarget SceneColorRenderTarget(SceneColor, ERenderTargetLoadAction::ELoad);
	FScreenPassTexture SceneColorRenderTargetTexture = SceneColorRenderTarget;
	const FScreenPassTextureViewport SceneColorTextureViewport(SceneColorRenderTargetTexture);

	FMeshBlendGlobalData MeshBlendData;

	MeshBlendData.Size = FVector4f(
		CVarMeshBlendSmallSize.GetValueOnRenderThread(),
		CVarMeshBlendMediumSize.GetValueOnRenderThread(),
		CVarMeshBlendLargeSize.GetValueOnRenderThread(),
		CVarMeshBlendExtraLargeSize.GetValueOnRenderThread()
	);

	MeshBlendData.MinSize = FVector4f(
		CVarMeshBlendSmallMinSize.GetValueOnRenderThread(),
		CVarMeshBlendMediumMinSize.GetValueOnRenderThread(),
		CVarMeshBlendLargeMinSize.GetValueOnRenderThread(),
		CVarMeshBlendExtraLargeMinSize.GetValueOnRenderThread()
	);

	MeshBlendData.NoiseFactor = FMath::Clamp(CVarMeshBlendNoiseFactor.GetValueOnRenderThread(), 0.0f, 5.0f);
	MeshBlendData.NoiseFade = CVarMeshBlendNoiseFade.GetValueOnRenderThread();
	MeshBlendData.NoiseOffset = FMath::Clamp(CVarMeshBlendNoiseOffset.GetValueOnRenderThread(), -1.0f, 1.0f);
	MeshBlendData.NoiseTileSize = FMath::Max(0.1f, CVarMeshBlendNoiseTileSize.GetValueOnRenderThread());
	MeshBlendData.SlopeFactor = FMath::Clamp(CVarMeshBlendSlopeFactor.GetValueOnRenderThread(), 1.0f, 100.0f);

	int32 MeshBlendQuality = FMath::Clamp(CVarMeshBlendQuality.GetValueOnRenderThread(), 1, 4);
	int32 MeshBlendVisualize = FMath::Clamp(CVarMeshBlendVisualize.GetValueOnRenderThread(), 0, 2);
	int32 MeshBlendFrameDither = FMath::Clamp(CVarMeshBlendFrameDither.GetValueOnRenderThread(), 0, 1);
	
#if UE_VERSION_OLDER_THAN(5, 7, 0)
	int32 MeshBlendSubstrateVersion = 0;
#else
	int32 MeshBlendSubstrateVersion = 1;
#endif

	FGlobalShaderMap* GlobalShaderMap = GetGlobalShaderMap(GMaxRHIFeatureLevel);
	FMeshBlendShaderPS::FPermutationDomain PermutationVector;
	PermutationVector.Set<FMeshBlendShaderPS::FMeshBlendQuality>(MeshBlendQuality - 1);
	PermutationVector.Set<FMeshBlendShaderPS::FMeshBlendVisualize>(MeshBlendVisualize);
	PermutationVector.Set<FMeshBlendShaderPS::FMeshBlendFrameDither>(MeshBlendFrameDither);
	PermutationVector.Set<FMeshBlendShaderPS::FMeshBlendSubstrateVersion>(MeshBlendSubstrateVersion);

	TShaderMapRef<FMeshBlendShaderPS> MeshBlendPixelShader(GlobalShaderMap, PermutationVector);
	FMeshBlendShaderPS::FParameters* MeshBlendShaderParameters = GraphBuilder.AllocParameters<FMeshBlendShaderPS::FParameters>();
	MeshBlendShaderParameters->SceneTexturesStruct = SceneTextures.SceneTextures.GetUniformBuffer();

#if UE_VERSION_OLDER_THAN(5, 4, 0)
#else
	if (Substrate::IsSubstrateEnabled())
	{
		const FViewInfo& ViewInfo = static_cast<const FViewInfo&>(View);
		
		if (ViewInfo.SubstrateViewData.SubstrateGlobalUniformParameters != nullptr)
		{
			MeshBlendShaderParameters->SubstratePublic = ViewInfo.SubstrateViewData.SubstrateGlobalUniformParameters;
		}
	}
#endif

	MeshBlendShaderParameters->PostProcessOutput = GetTextureViewportParameters(SceneColorTextureViewport);
	MeshBlendShaderParameters->PostProcessInput[0] =
		GetScreenPassTextureInput(SceneColorRenderTargetTexture, TStaticSamplerState<SF_Point, AM_Clamp, AM_Clamp, AM_Clamp>::GetRHI());
	MeshBlendShaderParameters->NoiseTexture = GetNoiseTexture(GraphBuilder, NoiseTexture);
	MeshBlendShaderParameters->NoiseTextureSampler = TStaticSamplerState<SF_Bilinear, AM_Wrap, AM_Wrap, AM_Wrap>::GetRHI();
	
	FBlueNoise BlueNoise = GetBlueNoiseGlobalParameters();
	MeshBlendShaderParameters->BlueNoise = CreateUniformBufferImmediate(BlueNoise, EUniformBufferUsage::UniformBuffer_SingleDraw);
	
	MeshBlendShaderParameters->View = View.ViewUniformBuffer;
	MeshBlendShaderParameters->MeshBlend = MeshBlendData;
	MeshBlendShaderParameters->RenderTargets[0] = Output.GetRenderTargetBinding();

#if UE_VERSION_OLDER_THAN(5, 6, 0)
	RDG_GPU_STAT_SCOPE(GraphBuilder, MeshBlend_RenderPass);
#else
	RDG_EVENT_SCOPE_STAT(GraphBuilder, MeshBlend_RenderPass, "MeshBlend");
#endif

	FPixelShaderUtils::AddFullscreenPass(GraphBuilder, GlobalShaderMap, FRDGEventName(TEXT("MeshBlend")), MeshBlendPixelShader, MeshBlendShaderParameters, Output.ViewRect);
}

bool FMeshBlendSceneViewExtension::IsEnabled(const FSceneView& View)
{
	static const auto CVarMeshBlendEnabled = IConsoleManager::Get().FindConsoleVariable(TEXT("r.MeshBlend.Enable"));

	if (!CVarMeshBlendEnabled->GetBool())
	{
		return false;
	}

	const EShaderPlatform ShaderPlatform = View.Family->GetShaderPlatform();

	if (IsForwardShadingEnabled(ShaderPlatform) || IsMobilePlatform(ShaderPlatform))
	{
		return false;
	}

	return true;
}