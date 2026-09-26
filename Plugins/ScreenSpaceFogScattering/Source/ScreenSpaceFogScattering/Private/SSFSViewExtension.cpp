// Copyright 2025 Dmitry Karpukhin. All Rights Reserved.

#include "SSFSViewExtension.h"
#include "SSFSHeightFog.h"
#include "PostProcess/PostProcessing.h"
#include "PostProcess/PostProcessMaterial.h"
#include "PostProcess/PostProcessInputs.h"
#include "SceneCore.h"

namespace
{
	TAutoConsoleVariable<int32> CVarSSFS(
	TEXT("r.SSFS"),
	1,
	TEXT("Enable or disable the Screen Space Fog Scattering post process effect."),
	ECVF_RenderThreadSafe | ECVF_Scalability);

	TAutoConsoleVariable<int32> CVarSSFSQualityPreset(
	TEXT("r.SSFS.QualityPreset"),
	2,
	TEXT("Quality Preset for the scattering effect.\n")
	TEXT("0 = Low (4-tap Downsampling, 5-tap Upsampling)\n")
	TEXT("1 = Medium (8-tap Downsampling, 5-tap Upsampling)\n")
	TEXT("2 = High (8-tap Downsampling, 9-tap Upsampling)\n")
	TEXT("3 = Epic (13-tap Downsampling, 9-tap Upsampling)"),
	ECVF_RenderThreadSafe | ECVF_Scalability);

	TAutoConsoleVariable<int32> CVarSSFSFormat(
	TEXT("r.SSFS.Format"),
	1,
	TEXT("Texture format of the scattering effect.\n")
	TEXT("0 = PF_FloatR11G11B10 (faster, but not recommended for HDR content, considerable for VR)\n")
	TEXT("1 = PF_FloatRGBA (default, HDR)"),
	ECVF_RenderThreadSafe | ECVF_Scalability);

	TAutoConsoleVariable<int32> CVarSSFSLuminanceWeighting(
	TEXT("r.SSFS.LuminanceWeighting"),
	1,
	TEXT("Use additional filtering to reduce overly bright subpixels (fireflies).\n")
	TEXT("Recommended to be always on."),
	ECVF_RenderThreadSafe);

	TAutoConsoleVariable<int32> CVarSSFSPassAmount(
	TEXT("r.SSFS.PassAmount"),
	8,
	TEXT("Number of passes to render the Scattering effect.\n")
	TEXT("Recommended values: 8 for Full HD, 9 for QHD, 10 for 4K resolutions.\n")
	TEXT("Max number of passes is clamped to 12."),
	ECVF_RenderThreadSafe | ECVF_Scalability);

	TAutoConsoleVariable<float> CVarSSFSRadius(
	TEXT("r.SSFS.Radius"),
	0.9f,
	TEXT("The progressive radius of the scattering effect.\n")
	TEXT("Can be used to visibly increase (or decrease) the effect while staying with certain fog density.\n")
	TEXT("Recommended values are between 0.8-0.99.\n"),
	ECVF_RenderThreadSafe);

	TAutoConsoleVariable<float> CVarSSFSIntensity(
	TEXT("r.SSFS.Intensity"),
	1.0f,
	TEXT("Intensity of the effect scaled by the Exponential Height Fog density values."),
	ECVF_RenderThreadSafe);

	TAutoConsoleVariable<int32> CVarSSFSSkyAtmosphere(
	TEXT("r.SSFS.SkyAtmosphere"),
	0,
	TEXT("Whether to support Sky Atmosphere by the shader."),
	ECVF_RenderThreadSafe | ECVF_Scalability);

	TAutoConsoleVariable<float> CVarSSFSSkyAtmosphereIntensity(
	TEXT("r.SSFS.SkyAtmosphereIntensity"),
	1.0f,
	TEXT("Intensity of the effect scaled by the Sky Atmosphere."),
	ECVF_RenderThreadSafe);

	TAutoConsoleVariable<int32> CVarSSFSVolumetricCloud(
	TEXT("r.SSFS.VolumetricCloud"),
	0,
	TEXT("Whether to support Volumetric Clouds by the shader.\n")
	TEXT("Highly experimental! Works only with 'r.VolumetricRenderTarget.Mode 0'."),
	ECVF_RenderThreadSafe | ECVF_Scalability);

	TAutoConsoleVariable<float> CVarSSFSVolumetricCloudIntensity(
	TEXT("r.SSFS.VolumetricCloudIntensity"),
	1.0f,
	TEXT("Intensity of the effect scaled by the Volumetric Cloud density."),
	ECVF_RenderThreadSafe);

	TAutoConsoleVariable<float> CVarSSFSVolumetricFogILSIntensity(
	TEXT("r.SSFS.VolumetricFogILSIntensity"),
	1.0f,
	TEXT("Intensity of the Volumetric Fog Integrated Light Scattering on the effect."),
	ECVF_RenderThreadSafe);

	TAutoConsoleVariable<int32> CVarSSFSHeterogeneousVolumes(
	TEXT("r.SSFS.HeterogeneousVolumes"),
	1,
	TEXT("Whether to support Heterogeneous Volumes by the shader."),
	ECVF_RenderThreadSafe | ECVF_Scalability);
}

// Implement shaders
IMPLEMENT_UNIFORM_BUFFER_STRUCT(FFogUniformParametersSSFS, "FogStructSSFS");
IMPLEMENT_GLOBAL_SHADER(FSetupSSFSCS, "/Plugin/ScreenSpaceFogScattering/SSFSSetup.usf", "SetupCS", SF_Compute);
IMPLEMENT_GLOBAL_SHADER(FDownsampleSSFSCS, "/Plugin/ScreenSpaceFogScattering/SSFSDownsample.usf", "DownsampleCS", SF_Compute);
IMPLEMENT_GLOBAL_SHADER(FUpsampleCombineSSFSCS, "/Plugin/ScreenSpaceFogScattering/SSFSUpsampleCombine.usf", "UpsampleCombineCS", SF_Compute);
IMPLEMENT_GLOBAL_SHADER(FRecombineSSFSCS, "/Plugin/ScreenSpaceFogScattering/SSFSRecombine.usf", "RecombineCS", SF_Compute);

DECLARE_GPU_STAT_NAMED(SSFS, TEXT("Screen Space Fog Scattering"));

FScreenSpaceFogScatteringViewExtension::FScreenSpaceFogScatteringViewExtension(const FAutoRegister& AutoRegister) : FSceneViewExtensionBase(AutoRegister)
{
	UE_LOG(LogTemp, Log, TEXT("SceneViewExtension: Screen Space Fog Scattering is registered"));
}

// Render the SSFS at the start of the post processing pipeline (before DOF) ensuring that it's compatible with any other default post process effects
void FScreenSpaceFogScatteringViewExtension::PrePostProcessPass_RenderThread(FRDGBuilder& GraphBuilder, const FSceneView& View, const FPostProcessingInputs& Inputs)
{
	FSceneViewExtensionBase::PrePostProcessPass_RenderThread(GraphBuilder, View, Inputs);
	
	const FViewInfo& ViewInfo = static_cast<const FViewInfo&>(View);
	const FScreenPassTexture SceneColor((*Inputs.SceneTextures)->SceneColorTexture, ViewInfo.ViewRect);
	
	PassAmount = FMath::Clamp(CVarSSFSPassAmount.GetValueOnRenderThread(), 0, 12);

	if (SceneColor.IsValid() && PassAmount > 1 && View.Family->Scene->HasAnyExponentialHeightFog() && View.Family->ViewMode != VMI_PathTracing)
	{
		RDG_EVENT_SCOPE_STAT(GraphBuilder, SSFS, "ScreenSpaceFogScattering");
		RDG_EVENT_SCOPE(GraphBuilder, "ScreenSpaceFogScattering %dx%d (PassAmount=%d)", ViewInfo.ViewRect.Width(), ViewInfo.ViewRect.Height(), PassAmount);
		
		FScreenPassTexture SSFSOutput = RenderSSFS(GraphBuilder, ViewInfo, Inputs);

		// In the PrePostProcessPass_RenderThread we must specify copy positions manually to support stereoscopic rendering (unlike SubscribeToPostProcessingPass)
		AddCopyTexturePass(GraphBuilder, SSFSOutput.Texture, SceneColor.Texture, ViewInfo.ViewRect.Min, ViewInfo.ViewRect.Min, ViewInfo.ViewRect.Size());
	}
}

bool FScreenSpaceFogScatteringViewExtension::IsActiveThisFrame_Internal(const FSceneViewExtensionContext& Context) const
{
	const bool bIsValid = CVarSSFS.GetValueOnAnyThread() == 1 && CVarSSFSIntensity.GetValueOnAnyThread() > 0 && CVarSSFSRadius.GetValueOnAnyThread() > 0;
	return bIsValid;
}

FScreenPassTexture FScreenSpaceFogScatteringViewExtension::RenderSSFS(FRDGBuilder& GraphBuilder, const FViewInfo& View, const FPostProcessingInputs& Inputs)
{
	FScreenPassTexture SceneColor((*Inputs.SceneTextures)->SceneColorTexture, View.ViewRect);
	FScreenPassTexture SceneDepth((*Inputs.SceneTextures)->SceneDepthTexture, View.ViewRect);
	
	const FScreenPassTextureViewport SceneColorViewport(SceneColor);
	
	// Setup pass: SceneColor * HeightFog in RGB, HeightFog in A
	FRDGTextureRef SetupTexture = Setup(GraphBuilder, View, SceneColor, SceneDepth);

	// Both Downsample and Upsample methods for rendering Bloom are described here: http://www.iryoku.com/next-generation-post-processing-in-call-of-duty-advanced-warfare
	// You can learn about the Unreal implementation of this in detail here: https://www.froyok.fr/blog/2021-12-ue4-custom-bloom/
	// It's also a perfect fit for the Fog Scattering shader
	{
		RDG_EVENT_SCOPE(GraphBuilder, "SSFS Downsample");
		
		int32 Width = View.ViewRect.Width();
		int32 Height = View.ViewRect.Height();
		int32 Divider = 1;
		FScreenPassTexture PreviousPass(SetupTexture);

		for(int32 i = 0; i < PassAmount; i++)
		{
			FIntRect Size{0,0,FMath::Max(Width / Divider, 2),FMath::Max(Height / Divider, 2)};
			
			const FString PassName = "Downsample 1/" + FString::FromInt(Divider) + " ("
			+ FString::FromInt(i) + "/"
			+ FString::FromInt(PassAmount - 1) + ") "
			+ FString::FromInt(Size.Width()) + "x"
			+ FString::FromInt(Size.Height());

			const FString* TextureName = GraphBuilder.AllocObject<FString>("SSFS.Downsample(1/" 
			+ FString::FromInt(Divider)
			+ ")");

			PreviousPass.ViewRect = Size;
			FRDGTextureRef DownsampleTexture = nullptr;
		
			if (i == 0)
			{
				// First pass should be a full res Setup texture
				DownsampleTexture = PreviousPass.Texture;
			}
			else
			{
				// Fog Scattering downsample pass
				DownsampleTexture = Downsample(GraphBuilder, View, SceneColorViewport, PreviousPass, PassName, TextureName);
			}

			DownsampleMipMaps.Add({DownsampleTexture, Size});
			PreviousPass.Texture = DownsampleTexture;
			Divider *= 2;
		}
	}

	{
		RDG_EVENT_SCOPE(GraphBuilder, "SSFS Upsample");
		
		UpsampleMipMaps.Append(DownsampleMipMaps);
		
		for(int32 i = PassAmount - 2; i >= 0; i--)
		{
			FIntRect CurrentSize = UpsampleMipMaps[i].ViewRect;

			const FString PassName  = "Upsample & Combine ("
			+ FString::FromInt(i + 1) + "/"
			+ FString::FromInt(PassAmount - 1) + ") "
			+ FString::FromInt(CurrentSize.Width()) + "x"
			+ FString::FromInt(CurrentSize.Height());

			const FString* TextureName = GraphBuilder.AllocObject<FString>("SSFS.Upsample(" 
			+ FString::FromInt(i + 1) + "/"
			+ FString::FromInt(PassAmount - 1) + ")");

			// Fog Scattering upsample & combine pass
			FRDGTextureRef UpsampleTexture = UpsampleCombine(GraphBuilder, View, SceneColorViewport, UpsampleMipMaps[i], UpsampleMipMaps[i + 1], PassName, TextureName);

			FScreenPassTexture Upsample(UpsampleTexture, CurrentSize);
			UpsampleMipMaps[i] = Upsample;
		}
	}

	// Final recombine pass
	FRDGTextureRef RecombineTexture = Recombine(GraphBuilder, View, SceneColor, UpsampleMipMaps[0].Texture, SetupTexture);
	
	DownsampleMipMaps.Empty();
	UpsampleMipMaps.Empty();
	
	return FScreenPassTexture(RecombineTexture, SceneColor.ViewRect);
}

static bool IsVolumetricCloudRenderTargetValid()
{
	static const auto VolumetricCloudRenderTarget = IConsoleManager::Get().FindTConsoleVariableDataInt(TEXT("r.VolumetricRenderTarget"));
	static const auto VolumetricCloudRenderTargetMode = IConsoleManager::Get().FindTConsoleVariableDataInt(TEXT("r.VolumetricRenderTarget.Mode"));
	
	if (!VolumetricCloudRenderTarget || !VolumetricCloudRenderTargetMode)
	{
		return false;
	}
	
	return VolumetricCloudRenderTarget->GetValueOnRenderThread() == 1 && VolumetricCloudRenderTargetMode->GetValueOnRenderThread() == 0;
}

FRDGTextureRef FScreenSpaceFogScatteringViewExtension::Setup(FRDGBuilder& GraphBuilder, const FViewInfo& View, const FScreenPassTexture& SceneColor, const FScreenPassTexture& SceneDepth) const
{
	FRDGTextureDesc Desc = SceneColor.Texture->Desc;
	Desc.Reset();
	Desc.Flags |= TexCreate_UAV;
	Desc.Flags &= ~(TexCreate_RenderTargetable | TexCreate_FastVRAM);
	Desc.Extent = SceneColor.ViewRect.Size();
	Desc.Format = PF_FloatRGBA;
	Desc.ClearValue = FClearValueBinding(FLinearColor::Black);
	const FRDGTextureRef OutputTexture = GraphBuilder.CreateTexture(Desc, TEXT("SSFS.Setup"));
	
	const float Intensity = CVarSSFSIntensity.GetValueOnRenderThread();
	const float SkyAtmosphereIntensity = CVarSSFSSkyAtmosphereIntensity.GetValueOnRenderThread();
	const float VolumetricFogILSIntensity = CVarSSFSVolumetricFogILSIntensity.GetValueOnRenderThread();
	const float VolumetricCloudIntensity = CVarSSFSVolumetricCloudIntensity.GetValueOnRenderThread();
	const bool bUseSkyAtmosphere = CVarSSFSSkyAtmosphere.GetValueOnRenderThread() > 0;
	const bool bUseHeterogeneousVolumes = CVarSSFSHeterogeneousVolumes.GetValueOnRenderThread() > 0;
	const bool bUseVolumetricCloud = CVarSSFSVolumetricCloud.GetValueOnRenderThread() > 0;

	FScene* Scene = View.Family->Scene->GetRenderScene();
	const FEngineShowFlags EngineShowFlags = View.Family->EngineShowFlags;
	
	const bool bSupportHeightFog = Scene->ExponentialFogs.Num() > 0 && EngineShowFlags.Fog;
	const bool bSupportFogStartDistance = View.ExponentialFogParameters.W > 0;
	const bool bSupportFogInscatteringColorCubemap = View.FogInscatteringColorCubemap != nullptr;
	const bool bSupportFogSecondTerm = View.ExponentialFogParameters2.X > 0;
	const bool bSupportFogDirectionalInscattering = !bSupportFogInscatteringColorCubemap && (View.DirectionalInscatteringColor.GetLuminance() > 0 || View.bUseDirectionalInscattering);
	const bool bSupportVolumetricFog = Scene->ExponentialFogs[0].bEnableVolumetricFog && EngineShowFlags.VolumetricFog;
	const bool bSupportAerialPerspective = bUseSkyAtmosphere && Scene->HasSkyAtmosphere() && SkyAtmosphereIntensity > 0 && EngineShowFlags.Atmosphere;
	const bool bSupportHeterogeneousVolumes = bUseHeterogeneousVolumes && View.HeterogeneousVolumeRadiance && EngineShowFlags.HeterogeneousVolumes;
	const bool bSupportVolumetricCloud = bUseVolumetricCloud && IsVolumetricCloudRenderTargetValid() && Scene->HasVolumetricCloud() && VolumetricCloudIntensity > 0 && EngineShowFlags.Cloud;
	
	FSetupSSFSCS::FPermutationDomain PermutationVector;
	PermutationVector.Set<FSetupSSFSCS::FSupportHeightFog>(bSupportHeightFog);
	PermutationVector.Set<FSetupSSFSCS::FSupportFogStartDistance>(bSupportFogStartDistance);
	PermutationVector.Set<FSetupSSFSCS::FSupportFogInScatteringTexture>(bSupportFogInscatteringColorCubemap);
	PermutationVector.Set<FSetupSSFSCS::FSupportFogSecondTerm>(bSupportFogSecondTerm);
	PermutationVector.Set<FSetupSSFSCS::FSupportFogDirectionalLightInScattering>(bSupportFogDirectionalInscattering);
	PermutationVector.Set<FSetupSSFSCS::FSupportVolumetricFog>(bSupportVolumetricFog);
	PermutationVector.Set<FSetupSSFSCS::FSupportAerialPerspective>(bSupportAerialPerspective);
	PermutationVector.Set<FSetupSSFSCS::FSupportHeterogeneousVolume>(bSupportHeterogeneousVolumes);
	PermutationVector.Set<FSetupSSFSCS::FSupportVolumetricCloud>(bSupportVolumetricCloud);

	const FGlobalShaderMap* GlobalShaderMap = GetGlobalShaderMap(View.FeatureLevel);
	const TShaderMapRef<FSetupSSFSCS> ComputeShader(GlobalShaderMap, PermutationVector);
	FSetupSSFSCS::FParameters* PassParameters = GraphBuilder.AllocParameters<FSetupSSFSCS::FParameters>();
	
	const FScreenPassTextureViewport SceneColorViewport(SceneColor);
	TRDGUniformBufferRef<FFogUniformParametersSSFS> FogUniformBuffer = CreateFogUniformBufferSSFS(GraphBuilder, View);
	const FRDGSystemTextures& SystemTextures = FRDGSystemTextures::Get(GraphBuilder);
	
	PassParameters->CommonParameters.ViewUniformBuffer = View.ViewUniformBuffer;
	PassParameters->CommonParameters.InputViewport = GetScreenPassTextureViewportParameters(SceneColorViewport);
	PassParameters->CommonParameters.InputTexture = SceneColor.Texture;
	PassParameters->CommonParameters.InputSampler = TStaticSamplerState<SF_Bilinear>::GetRHI();
	PassParameters->FogStruct = FogUniformBuffer;
	PassParameters->DepthTex = SceneDepth.Texture;
	PassParameters->HeterogeneousVolumeTex = View.HeterogeneousVolumeRadiance ? View.HeterogeneousVolumeRadiance : SystemTextures.Black;
	PassParameters->VolumetricCloudTex = IsVolumetricCloudRenderTargetValid() && bSupportVolumetricCloud ? View.State->GetVolumetricCloudTexture(GraphBuilder) : SystemTextures.Black;
	PassParameters->Intensity = Intensity;
	PassParameters->SkyAtmosphereIntensity = SkyAtmosphereIntensity;
	PassParameters->VolumetricFogILSIntensity = VolumetricFogILSIntensity;
	PassParameters->VolumetricCloudIntensity = VolumetricCloudIntensity;
	PassParameters->Output = GraphBuilder.CreateUAV(FRDGTextureUAVDesc(OutputTexture));
	
	const FIntVector GroupCount = FComputeShaderUtils::GetGroupCount(View.ViewRect.Size(), GroupSize);

	FComputeShaderUtils::AddPass(
		GraphBuilder,
		RDG_EVENT_NAME("SSFS Setup %dx%d", View.ViewRect.Width(), View.ViewRect.Height()),
		ComputeShader,
		PassParameters,
		GroupCount);

	return OutputTexture;
}

FRDGTextureRef FScreenSpaceFogScatteringViewExtension::Downsample(FRDGBuilder& GraphBuilder, const FViewInfo& View, const FScreenPassTextureViewport& InputViewport, const FScreenPassTexture& InputTexture, const FString& PassName, const FString* TextureName) const
{
	FRDGTextureDesc Desc = InputTexture.Texture->Desc;
	Desc.Reset();
	Desc.Flags |= TexCreate_UAV;
	Desc.Flags &= ~(TexCreate_RenderTargetable | TexCreate_FastVRAM);
	Desc.Extent = InputTexture.ViewRect.Size();
	Desc.Format = CVarSSFSFormat.GetValueOnRenderThread() ? PF_FloatRGBA : PF_FloatR11G11B10;
	Desc.ClearValue = FClearValueBinding(FLinearColor::Black);
	const FRDGTextureRef OutputTexture = GraphBuilder.CreateTexture(Desc, **TextureName);
	
	const int QualityPreset = FMath::Clamp(CVarSSFSQualityPreset.GetValueOnRenderThread(), 0, 3);
	const bool bLuminanceWeighting = CVarSSFSLuminanceWeighting.GetValueOnRenderThread() > 0;

	FDownsampleSSFSCS::FPermutationDomain PermutationVector;
	PermutationVector.Set<FDownsampleSSFSCS::FQualityPreset>(QualityPreset);
	PermutationVector.Set<FDownsampleSSFSCS::FLuminanceWeighting>(bLuminanceWeighting);

	const FGlobalShaderMap* GlobalShaderMap = GetGlobalShaderMap(View.FeatureLevel);
	const TShaderMapRef<FDownsampleSSFSCS> ComputeShader(GlobalShaderMap, PermutationVector);
	FDownsampleSSFSCS::FParameters* PassParameters = GraphBuilder.AllocParameters<FDownsampleSSFSCS::FParameters>();
	
	PassParameters->CommonParameters.ViewUniformBuffer = View.ViewUniformBuffer;
	PassParameters->CommonParameters.InputViewport = GetScreenPassTextureViewportParameters(InputViewport);
	PassParameters->CommonParameters.InputTexture = InputTexture.Texture;
	PassParameters->CommonParameters.InputSampler = TStaticSamplerState<SF_Bilinear>::GetRHI();
	PassParameters->InputSize = FVector2f(InputTexture.ViewRect.Width(), InputTexture.ViewRect.Height());
	PassParameters->Output = GraphBuilder.CreateUAV(FRDGTextureUAVDesc(OutputTexture));
	
	const FIntVector GroupCount = FComputeShaderUtils::GetGroupCount(InputTexture.ViewRect.Size(), GroupSize);

	FComputeShaderUtils::AddPass(
		GraphBuilder,
		RDG_EVENT_NAME("%s", *PassName),
		ComputeShader,
		PassParameters,
		GroupCount);

	return OutputTexture;
}

FRDGTextureRef FScreenSpaceFogScatteringViewExtension::UpsampleCombine(FRDGBuilder& GraphBuilder, const FViewInfo& View, const FScreenPassTextureViewport& InputViewport, const FScreenPassTexture& InputTexture, const FScreenPassTexture& PreviousTexture, const FString& PassName, const FString* TextureName) const
{
	FRDGTextureDesc Desc = InputTexture.Texture->Desc;
	Desc.Reset();
	Desc.Flags |= TexCreate_UAV;
	Desc.Flags &= ~(TexCreate_RenderTargetable | TexCreate_FastVRAM);
	Desc.Extent = InputTexture.ViewRect.Size();
	Desc.Format = CVarSSFSFormat.GetValueOnRenderThread() ? PF_FloatRGBA : PF_FloatR11G11B10;
	Desc.ClearValue = FClearValueBinding(FLinearColor::Black);
	const FRDGTextureRef OutputTexture = GraphBuilder.CreateTexture(Desc, **TextureName);

	const int QualityPreset = FMath::Clamp(CVarSSFSQualityPreset.GetValueOnRenderThread(), 0, 3);

	FUpsampleCombineSSFSCS::FPermutationDomain PermutationVector;
	PermutationVector.Set<FUpsampleCombineSSFSCS::FQualityPreset>(QualityPreset);

	const FGlobalShaderMap* GlobalShaderMap = GetGlobalShaderMap(View.FeatureLevel);
	const TShaderMapRef<FUpsampleCombineSSFSCS> ComputeShader(GlobalShaderMap, PermutationVector);
	FUpsampleCombineSSFSCS::FParameters* PassParameters = GraphBuilder.AllocParameters<FUpsampleCombineSSFSCS::FParameters>();

	const float Radius = FMath::Clamp(CVarSSFSRadius.GetValueOnRenderThread(), 0, 1);
	
	PassParameters->CommonParameters.ViewUniformBuffer = View.ViewUniformBuffer;
	PassParameters->CommonParameters.InputViewport = GetScreenPassTextureViewportParameters(InputViewport);
	PassParameters->CommonParameters.InputTexture = InputTexture.Texture;
	PassParameters->CommonParameters.InputSampler = TStaticSamplerState<SF_Bilinear>::GetRHI();
	PassParameters->PreviousTexture = PreviousTexture.Texture;
	PassParameters->InputSize = FVector2f(InputTexture.ViewRect.Width(), InputTexture.ViewRect.Height());
	PassParameters->Radius = Radius;
	PassParameters->Output = GraphBuilder.CreateUAV(FRDGTextureUAVDesc(OutputTexture));
	
	const FIntVector GroupCount = FComputeShaderUtils::GetGroupCount(InputTexture.ViewRect.Size(), GroupSize);
	
	FComputeShaderUtils::AddPass(
		GraphBuilder,
		RDG_EVENT_NAME("%s", *PassName),
		ComputeShader,
		PassParameters,
		GroupCount);
	
	return OutputTexture;
}

FRDGTextureRef FScreenSpaceFogScatteringViewExtension::Recombine(FRDGBuilder& GraphBuilder, const FViewInfo& View, const FScreenPassTexture& SceneColor, const FRDGTextureRef& ScatteringTexture, const FRDGTextureRef& SetupTexture) const
{
	FRDGTextureDesc Desc = SceneColor.Texture->Desc;
	Desc.Reset();
	Desc.Flags |= TexCreate_UAV;
	Desc.Flags &= ~(TexCreate_RenderTargetable | TexCreate_FastVRAM);
	Desc.Extent = SceneColor.Texture->Desc.Extent;
	Desc.ClearValue = FClearValueBinding(FLinearColor::Black);
	const FRDGTextureRef OutputTexture = GraphBuilder.CreateTexture(Desc, TEXT("SSFS.Recombine"));

	const FGlobalShaderMap* GlobalShaderMap = GetGlobalShaderMap(View.FeatureLevel);
	const TShaderMapRef<FRecombineSSFSCS> ComputeShader(GlobalShaderMap);
	FRecombineSSFSCS::FParameters* PassParameters = GraphBuilder.AllocParameters<FRecombineSSFSCS::FParameters>();

	const FScreenPassTextureViewport SceneColorViewport(SceneColor);
	
	PassParameters->CommonParameters.ViewUniformBuffer = View.ViewUniformBuffer;
	PassParameters->CommonParameters.InputViewport = GetScreenPassTextureViewportParameters(SceneColorViewport);
	PassParameters->CommonParameters.InputTexture = SceneColor.Texture;
	PassParameters->CommonParameters.InputSampler = TStaticSamplerState<SF_Bilinear>::GetRHI();
	PassParameters->ScatteringTexture = ScatteringTexture;
	PassParameters->SetupTexture = SetupTexture;
	PassParameters->Output = GraphBuilder.CreateUAV(FRDGTextureUAVDesc(OutputTexture));
	
	const FIntVector GroupCount = FComputeShaderUtils::GetGroupCount(SceneColor.ViewRect.Size(), GroupSize);

	FComputeShaderUtils::AddPass(
		GraphBuilder,
		RDG_EVENT_NAME("SSFS Recombine %dx%d", SceneColor.ViewRect.Width(), SceneColor.ViewRect.Height()),
		ComputeShader,
		PassParameters,
		GroupCount);
	
	return OutputTexture;
}
