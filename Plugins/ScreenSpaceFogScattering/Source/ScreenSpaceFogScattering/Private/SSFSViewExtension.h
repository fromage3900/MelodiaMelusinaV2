// Copyright 2025 Dmitry Karpukhin. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "SceneViewExtension.h"
#include "SceneView.h"
#include "RenderGraphUtils.h"
#include "Runtime/Renderer/Public/ScreenPass.h"
#include "DataDrivenShaderPlatformInfo.h"
#include "Misc/EngineVersionComparison.h"

#if UE_VERSION_OLDER_THAN(5,6,0)
// Useful macro from UE 5.6
#define UE_VERSION_NEWER_THAN_OR_EQUAL(MajorVersion, MinorVersion, PatchVersion)\
UE_GREATER_SORT(ENGINE_MAJOR_VERSION, MajorVersion, UE_GREATER_SORT(ENGINE_MINOR_VERSION, MinorVersion, UE_GREATER_SORT(ENGINE_PATCH_VERSION, PatchVersion, true)))
#endif

class FScreenSpaceFogScatteringViewExtension : public FSceneViewExtensionBase
{
public:
	FScreenSpaceFogScatteringViewExtension(const FAutoRegister& AutoRegister);
	
	virtual void SetupViewFamily(FSceneViewFamily& InViewFamily) override {};
	virtual void SetupView(FSceneViewFamily& InViewFamily, FSceneView& InView) override {};
	virtual void BeginRenderViewFamily(FSceneViewFamily& InViewFamily) override {};
	virtual void PrePostProcessPass_RenderThread(FRDGBuilder& GraphBuilder, const FSceneView& View, const FPostProcessingInputs& Inputs) override;
	virtual bool IsActiveThisFrame_Internal(const FSceneViewExtensionContext& Context) const override;
	
private:
	int32 PassAmount = 8;

	FScreenPassTexture RenderSSFS(FRDGBuilder& GraphBuilder, const FViewInfo& View, const FPostProcessingInputs& Inputs);

	TArray<FScreenPassTexture> DownsampleMipMaps;
	TArray<FScreenPassTexture> UpsampleMipMaps;
	
	const int32 GroupSize = 8;
	
	FRDGTextureRef Setup(FRDGBuilder& GraphBuilder, const FViewInfo& View, const FScreenPassTexture& SceneColor, const FScreenPassTexture& SceneDepth) const;
	FRDGTextureRef Downsample(FRDGBuilder& GraphBuilder, const FViewInfo& View, const FScreenPassTextureViewport& InputViewport, const FScreenPassTexture& InputTexture, const FString& PassName, const FString* TextureName) const;
	FRDGTextureRef UpsampleCombine(FRDGBuilder& GraphBuilder, const FViewInfo& View, const FScreenPassTextureViewport& InputViewport, const FScreenPassTexture& InputTexture, const FScreenPassTexture& PreviousTexture, const FString& PassName, const FString* TextureName) const;
	FRDGTextureRef Recombine(FRDGBuilder& GraphBuilder, const FViewInfo& View, const FScreenPassTexture& SceneColor, const FRDGTextureRef& ScatteringTexture, const FRDGTextureRef& SetupTexture) const;
};

// Shader declarations
BEGIN_SHADER_PARAMETER_STRUCT(FCommonParametersSSFS, )
	SHADER_PARAMETER_STRUCT_REF(FViewUniformShaderParameters, ViewUniformBuffer)
	SHADER_PARAMETER_STRUCT(FScreenPassTextureViewportParameters, InputViewport)
	SHADER_PARAMETER_RDG_TEXTURE(Texture2D, InputTexture)
	SHADER_PARAMETER_SAMPLER(SamplerState, InputSampler)
END_SHADER_PARAMETER_STRUCT()

// We can't include FFogUniformParameters from FogRendering.h directly, but we can make an impostor and feed him the same data...
BEGIN_GLOBAL_SHADER_PARAMETER_STRUCT(FFogUniformParametersSSFS,)
	SHADER_PARAMETER(FVector4f, ExponentialFogParameters)
	SHADER_PARAMETER(FVector4f, ExponentialFogParameters2)
	SHADER_PARAMETER(FVector4f, ExponentialFogColorParameter)
	SHADER_PARAMETER(FVector4f, ExponentialFogParameters3)
	SHADER_PARAMETER(FVector4f, SkyAtmosphereAmbientContributionColorScale)
	SHADER_PARAMETER(FVector4f, InscatteringLightDirection) // non negative DirectionalInscatteringStartDistance in .W
	SHADER_PARAMETER(FVector4f, DirectionalInscatteringColor)
	SHADER_PARAMETER(FVector2f, SinCosInscatteringColorCubemapRotation)
	SHADER_PARAMETER(FVector3f, FogInscatteringTextureParameters)

	SHADER_PARAMETER(float, SkyLightCaptureAffectsHeightFogStrength)
	SHADER_PARAMETER(float, SkyLightCaptureAffectsHeightFogRoughness)
	SHADER_PARAMETER(float, SkyLightCaptureAffectsHeightFogMipCount)

#if UE_VERSION_NEWER_THAN_OR_EQUAL(5,5,0)
	SHADER_PARAMETER(float, EndDistance)
#endif
	SHADER_PARAMETER(float, ApplyVolumetricFog)
	SHADER_PARAMETER(float, VolumetricFogStartDistance)
	SHADER_PARAMETER(float, VolumetricFogNearFadeInDistanceInv)
#if UE_VERSION_NEWER_THAN_OR_EQUAL(5,5,0)
	SHADER_PARAMETER(FVector3f, VolumetricFogAlbedo)
	SHADER_PARAMETER(float, VolumetricFogPhaseG)
#endif
	SHADER_PARAMETER_TEXTURE(TextureCube, FogInscatteringColorCubemap)
	SHADER_PARAMETER_SAMPLER(SamplerState, FogInscatteringColorSampler)
	SHADER_PARAMETER_RDG_TEXTURE(Texture3D, IntegratedLightScattering)
	SHADER_PARAMETER_SAMPLER(SamplerState, IntegratedLightScatteringSampler)
END_GLOBAL_SHADER_PARAMETER_STRUCT()

class FSetupSSFSCS : public FGlobalShader
{
public:
	DECLARE_GLOBAL_SHADER(FSetupSSFSCS);
	SHADER_USE_PARAMETER_STRUCT(FSetupSSFSCS, FGlobalShader);

	BEGIN_SHADER_PARAMETER_STRUCT(FParameters, )
		SHADER_PARAMETER_STRUCT_INCLUDE(FCommonParametersSSFS, CommonParameters)
		SHADER_PARAMETER_RDG_UNIFORM_BUFFER(FFogUniformParametersSSFS, FogStruct)
		SHADER_PARAMETER_RDG_TEXTURE(Texture2D, DepthTex)
		SHADER_PARAMETER_RDG_TEXTURE(Texture2D, HeterogeneousVolumeTex)
		SHADER_PARAMETER_RDG_TEXTURE(Texture2D, VolumetricCloudTex)
		SHADER_PARAMETER(float, Intensity)
		SHADER_PARAMETER(float, SkyAtmosphereIntensity)
		SHADER_PARAMETER(float, VolumetricCloudIntensity)
		SHADER_PARAMETER(float, VolumetricFogILSIntensity)
		SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture2D<float4>, Output)
	END_SHADER_PARAMETER_STRUCT()

	class FSupportHeightFog							: SHADER_PERMUTATION_BOOL("PERMUTATION_SUPPORT_HEIGHT_FOG");
	class FSupportFogStartDistance					: SHADER_PERMUTATION_BOOL("PERMUTATION_SUPPORT_FOG_START_DISTANCE");
	class FSupportFogInScatteringTexture			: SHADER_PERMUTATION_BOOL("PERMUTATION_SUPPORT_FOG_INSCATTERING_TEXTURE");
	class FSupportFogSecondTerm						: SHADER_PERMUTATION_BOOL("PERMUTATION_SUPPORT_FOG_SECOND_TERM");
	class FSupportFogDirectionalLightInScattering	: SHADER_PERMUTATION_BOOL("PERMUTATION_SUPPORT_FOG_DIRECTIONAL_LIGHT_INSCATTERING");
	class FSupportVolumetricFog						: SHADER_PERMUTATION_BOOL("PERMUTATION_SUPPORT_VOLUMETRIC_FOG");
	class FSupportAerialPerspective					: SHADER_PERMUTATION_BOOL("PERMUTATION_SUPPORT_AERIAL_PERSPECTIVE");
	class FSupportHeterogeneousVolume				: SHADER_PERMUTATION_BOOL("PERMUTATION_SUPPORT_HETEROGENEOUS_VOLUME");
	class FSupportVolumetricCloud					: SHADER_PERMUTATION_BOOL("PERMUTATION_SUPPORT_VOLUMETRIC_CLOUD");
	
	using FPermutationDomain = TShaderPermutationDomain< 
		FSupportHeightFog, 
		FSupportFogStartDistance,
		FSupportFogInScatteringTexture, 
		FSupportFogSecondTerm,
		FSupportFogDirectionalLightInScattering,
		FSupportVolumetricFog,
		FSupportAerialPerspective,
		FSupportHeterogeneousVolume,
		FSupportVolumetricCloud
	>;

	static FPermutationDomain RemapPermutation(FPermutationDomain PermutationVector)
	{
		if (PermutationVector.Get<FSupportHeightFog>() == false)
		{
			PermutationVector.Set<FSupportFogInScatteringTexture>(false);
			PermutationVector.Set<FSupportFogDirectionalLightInScattering>(false);
			PermutationVector.Set<FSupportFogStartDistance>(false);
			PermutationVector.Set<FSupportFogSecondTerm>(false);
		}
		return PermutationVector;
	}

	static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& Parameters)
	{
		return IsFeatureLevelSupported(Parameters.Platform, ERHIFeatureLevel::SM5);
	}

	static void ModifyCompilationEnvironment(const FGlobalShaderPermutationParameters& Parameters, FShaderCompilerEnvironment& OutEnvironment)
	{
		FGlobalShader::ModifyCompilationEnvironment(Parameters, OutEnvironment);

		// Pass engine versions to the shader, which is important for compatibility
		OutEnvironment.SetDefine(TEXT("ENGINE_MAJOR_VERSION"), ENGINE_MAJOR_VERSION);
		OutEnvironment.SetDefine(TEXT("ENGINE_MINOR_VERSION"), ENGINE_MINOR_VERSION);
	}
};

class FDownsampleSSFSCS : public FGlobalShader
{
public:
	DECLARE_GLOBAL_SHADER(FDownsampleSSFSCS);
	SHADER_USE_PARAMETER_STRUCT(FDownsampleSSFSCS, FGlobalShader);

	BEGIN_SHADER_PARAMETER_STRUCT(FParameters, )
		SHADER_PARAMETER_STRUCT_INCLUDE(FCommonParametersSSFS, CommonParameters)
		SHADER_PARAMETER(FVector2f, InputSize)
		SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture2D<float4>, Output)
	END_SHADER_PARAMETER_STRUCT()
	
	class FQualityPreset		: SHADER_PERMUTATION_INT("PERMUTATION_QUALITY_PRESET", 4);
	class FLuminanceWeighting	: SHADER_PERMUTATION_BOOL("PERMUTATION_LUMINANCE_WEIGHTING");

	using FPermutationDomain = TShaderPermutationDomain<FQualityPreset, FLuminanceWeighting>;

	static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& Parameters)
	{
		return IsFeatureLevelSupported(Parameters.Platform, ERHIFeatureLevel::SM5);
	}
};

class FUpsampleCombineSSFSCS : public FGlobalShader
{
public:
	DECLARE_GLOBAL_SHADER(FUpsampleCombineSSFSCS);
	SHADER_USE_PARAMETER_STRUCT(FUpsampleCombineSSFSCS, FGlobalShader);

	BEGIN_SHADER_PARAMETER_STRUCT(FParameters, )
		SHADER_PARAMETER_STRUCT_INCLUDE(FCommonParametersSSFS, CommonParameters)
		SHADER_PARAMETER(FVector2f, InputSize)
		SHADER_PARAMETER_RDG_TEXTURE(Texture2D, PreviousTexture)
		SHADER_PARAMETER(float, Radius)
		SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture2D<float4>, Output)
	END_SHADER_PARAMETER_STRUCT()

	class FQualityPreset : SHADER_PERMUTATION_INT("PERMUTATION_QUALITY_PRESET", 4);

	using FPermutationDomain = TShaderPermutationDomain<FQualityPreset>;

	static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& Parameters)
	{
		return IsFeatureLevelSupported(Parameters.Platform, ERHIFeatureLevel::SM5);
	}
};

class FRecombineSSFSCS : public FGlobalShader
{
public:
	DECLARE_GLOBAL_SHADER(FRecombineSSFSCS);
	SHADER_USE_PARAMETER_STRUCT(FRecombineSSFSCS, FGlobalShader);

	BEGIN_SHADER_PARAMETER_STRUCT(FParameters, )
		SHADER_PARAMETER_STRUCT_INCLUDE(FCommonParametersSSFS, CommonParameters)
		SHADER_PARAMETER_RDG_TEXTURE(Texture2D, ScatteringTexture)
		SHADER_PARAMETER_RDG_TEXTURE(Texture2D, SetupTexture)
		SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture2D<float4>, Output)
	END_SHADER_PARAMETER_STRUCT()

	static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& Parameters)
	{
		return IsFeatureLevelSupported(Parameters.Platform, ERHIFeatureLevel::SM5);
	}
};
