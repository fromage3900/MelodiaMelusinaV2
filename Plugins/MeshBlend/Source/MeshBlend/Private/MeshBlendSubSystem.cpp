// Copyright 2024 Tore Lervik. All Rights Reserved.


#include "MeshBlendSubSystem.h"
#include "SceneViewExtension.h"
#include "Engine/Texture2D.h"

static TAutoConsoleVariable<FString> CVarMeshBlendNoiseTexture(TEXT("r.MeshBlend.NoiseTexture"), "", TEXT(".."));

static FAutoConsoleCommandWithWorld SetMaterialInstancedUsage(TEXT("r.MeshBlend.RefreshNoiseTexture"),
                                                              TEXT("..."),
                                                              FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
                                                              {
	                                                              GEngine->GetEngineSubsystem<UMeshBlendSubSystem>()->ReloadNoiseTexture();
                                                              }));

void UMeshBlendSubSystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	MeshBlendSceneViewExtension = FSceneViewExtensions::NewExtension<FMeshBlendSceneViewExtension>();
	ReloadNoiseTexture();
}

void UMeshBlendSubSystem::Deinitialize()
{
	Super::Deinitialize();

	if (MeshBlendSceneViewExtension.IsValid())
	{
		MeshBlendSceneViewExtension.Reset();
	}
}

void UMeshBlendSubSystem::ReloadNoiseTexture()
{
	FString NoiseTexturePath = CVarMeshBlendNoiseTexture.GetValueOnAnyThread();

	if (NoiseTexturePath.IsEmpty())
	{
		NoiseTexturePath = TEXT("/MeshBlend/Materials/TilingNoise05.TilingNoise05");
	}

	if (UTexture2D* NoiseTextureObject = LoadObject<UTexture2D>(nullptr, *NoiseTexturePath))
	{
		NoiseTexture = NoiseTextureObject;

		if (MeshBlendSceneViewExtension.IsValid())
		{
			MeshBlendSceneViewExtension.Get()->NoiseTexture = NoiseTexture;
		}
	}
}
