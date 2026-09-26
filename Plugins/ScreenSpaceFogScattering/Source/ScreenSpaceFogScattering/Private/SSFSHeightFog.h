// Copyright 2025 Dmitry Karpukhin. All Rights Reserved.

#pragma once

#include "SSFSViewExtension.h"
#include "ScenePrivate.h"
#include "SystemTextures.h"
#include "Runtime/Engine/Classes/Engine/Texture.h"
#include "TextureResource.h"

inline void SetupFogUniformParametersSSFS(FRDGBuilder& GraphBuilder, const FViewInfo& View, FFogUniformParametersSSFS& OutParameters)
{
	// Exponential Height Fog
	{
		const FTexture* Cubemap = GWhiteTextureCube;

		if (View.FogInscatteringColorCubemap)
		{
			Cubemap = View.FogInscatteringColorCubemap->GetResource();
		}

		OutParameters.ExponentialFogParameters = View.ExponentialFogParameters;
		OutParameters.ExponentialFogColorParameter = FVector4f(View.ExponentialFogColor, 1.0f - View.FogMaxOpacity);
		OutParameters.ExponentialFogParameters2 = View.ExponentialFogParameters2;
		OutParameters.ExponentialFogParameters3 = View.ExponentialFogParameters3;
		OutParameters.SkyAtmosphereAmbientContributionColorScale = View.SkyAtmosphereAmbientContributionColorScale;
		OutParameters.SinCosInscatteringColorCubemapRotation = View.SinCosInscatteringColorCubemapRotation;
		OutParameters.FogInscatteringTextureParameters = (FVector3f)View.FogInscatteringTextureParameters;
		OutParameters.InscatteringLightDirection = (FVector3f)View.InscatteringLightDirection;
		OutParameters.InscatteringLightDirection.W = View.bUseDirectionalInscattering ? FMath::Max(0.f, View.DirectionalInscatteringStartDistance) : -1.f;
		OutParameters.DirectionalInscatteringColor = FVector4f(FVector3f(View.DirectionalInscatteringColor), FMath::Clamp(View.DirectionalInscatteringExponent, 0.000001f, 1000.0f));
		OutParameters.FogInscatteringColorCubemap = Cubemap->TextureRHI;
		OutParameters.FogInscatteringColorSampler = TStaticSamplerState<SF_Trilinear, AM_Clamp, AM_Clamp, AM_Clamp>::GetRHI();
#if UE_VERSION_NEWER_THAN_OR_EQUAL(5,5,0)
		OutParameters.EndDistance = View.FogEndDistance;
#endif

		OutParameters.SkyLightCaptureAffectsHeightFogStrength = 0.0f;
		OutParameters.SkyLightCaptureAffectsHeightFogRoughness = 0.0f;
		OutParameters.SkyLightCaptureAffectsHeightFogMipCount = 0.0f;
	}

	// Volumetric Fog
	{
		if (View.VolumetricFogResources.IntegratedLightScatteringTexture)
		{
			OutParameters.IntegratedLightScattering = View.VolumetricFogResources.IntegratedLightScatteringTexture;
			OutParameters.ApplyVolumetricFog = 1.0f;
		}
		else
		{
			const FRDGSystemTextures& SystemTextures = FRDGSystemTextures::Get(GraphBuilder);
			OutParameters.IntegratedLightScattering = SystemTextures.VolumetricBlackAlphaOne;
			OutParameters.ApplyVolumetricFog = 0.0f;
		}
		OutParameters.IntegratedLightScatteringSampler = TStaticSamplerState<SF_Bilinear, AM_Clamp, AM_Clamp, AM_Clamp>::GetRHI();
		OutParameters.VolumetricFogStartDistance = View.VolumetricFogStartDistance;
		OutParameters.VolumetricFogNearFadeInDistanceInv = View.VolumetricFogNearFadeInDistanceInv;
#if UE_VERSION_NEWER_THAN_OR_EQUAL(5,5,0)
		OutParameters.VolumetricFogPhaseG = View.VolumetricFogPhaseG;
		OutParameters.VolumetricFogAlbedo = View.VolumetricFogAlbedo;
#endif
	}
}

inline TRDGUniformBufferRef<FFogUniformParametersSSFS> CreateFogUniformBufferSSFS(FRDGBuilder& GraphBuilder, const FViewInfo& View)
{
	auto* FogStruct = GraphBuilder.AllocParameters<FFogUniformParametersSSFS>();
	SetupFogUniformParametersSSFS(GraphBuilder, View, *FogStruct);
	return GraphBuilder.CreateUniformBuffer(FogStruct);
}