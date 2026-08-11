// Copyright 2024 Tore Lervik. All Rights Reserved.

#pragma once

#include "BlueNoise.h"
#include "GlobalShader.h"
#include "SceneTexturesConfig.h"
#include "ScreenPass.h"
#include "Misc/EngineVersionComparison.h"

#if UE_VERSION_OLDER_THAN(5, 4, 0)
#else
#include "Substrate/Substrate.h"
#endif

BEGIN_SHADER_PARAMETER_STRUCT(FMeshBlendGlobalData,)
	SHADER_PARAMETER(FVector4f, Size)
	SHADER_PARAMETER(FVector4f, MinSize)
	SHADER_PARAMETER(float, SlopeFactor)
	SHADER_PARAMETER(float, NoiseFade)
	SHADER_PARAMETER(float, NoiseOffset)
	SHADER_PARAMETER(float, NoiseFactor)
	SHADER_PARAMETER(float, NoiseTileSize)
END_SHADER_PARAMETER_STRUCT()

BEGIN_SHADER_PARAMETER_STRUCT(FMeshBlendShaderParameters,)
	SHADER_PARAMETER_RDG_TEXTURE(Texture2D, NoiseTexture)
	SHADER_PARAMETER_SAMPLER(SamplerState, NoiseTextureSampler)
	SHADER_PARAMETER_STRUCT(FMeshBlendGlobalData, MeshBlend)
	SHADER_PARAMETER_STRUCT_REF(FBlueNoise, BlueNoise)
	SHADER_PARAMETER_STRUCT_REF(FViewUniformShaderParameters, View)
	SHADER_PARAMETER_RDG_UNIFORM_BUFFER(FSceneTextureUniformParameters, SceneTexturesStruct)
#if UE_VERSION_OLDER_THAN(5, 4, 0)
#else
	SHADER_PARAMETER_RDG_UNIFORM_BUFFER(FSubstrateGlobalUniformParameters, SubstratePublic)
#endif
	SHADER_PARAMETER_STRUCT(FScreenPassTextureViewportParameters, PostProcessOutput)
	SHADER_PARAMETER_STRUCT_ARRAY(FScreenPassTextureInput, PostProcessInput, [1])
	RENDER_TARGET_BINDING_SLOTS()
END_SHADER_PARAMETER_STRUCT()

class FMeshBlendShaderPS : public FGlobalShader
{
public:
	DECLARE_EXPORTED_SHADER_TYPE(FMeshBlendShaderPS, Global,);
	using FParameters = FMeshBlendShaderParameters;
	SHADER_USE_PARAMETER_STRUCT(FMeshBlendShaderPS, FGlobalShader);

	class FMeshBlendQuality : SHADER_PERMUTATION_INT("MESH_BLEND_QUALITY", 4);

	class FMeshBlendVisualize : SHADER_PERMUTATION_INT("MESH_BLEND_VISUALIZE", 3);

	class FMeshBlendFrameDither : SHADER_PERMUTATION_INT("MESH_BLEND_FRAME_DITHER", 2);

	class FMeshBlendSubstrateVersion : SHADER_PERMUTATION_INT("MESH_BLEND_SUBSTRATE_VERSION", 2);

	using FPermutationDomain = TShaderPermutationDomain<FMeshBlendQuality, FMeshBlendVisualize, FMeshBlendFrameDither, FMeshBlendSubstrateVersion>;
};
