// Copyright 2024 Tore Lervik. All Rights Reserved.

#include "MeshBlendConfigUtils.h"

#if WITH_EDITOR

#include "UnrealEdMisc.h"
#include "HAL/IConsoleManager.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/Paths.h"

static FAutoConsoleCommandWithWorld MeshBlendLoadFromConfig(TEXT("r.MeshBlend.LoadFromConfig"),
                                                            TEXT("..."),
                                                            FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
                                                            {
	                                                            FMeshBlendConfigUtils::LoadFromConfig();
                                                            }));

static FAutoConsoleCommandWithWorld MeshBlendSaveToConfig(TEXT("r.MeshBlend.SaveToConfig"),
                                                          TEXT("..."),
                                                          FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
                                                          {
	                                                          FMeshBlendConfigUtils::SaveToConfig();
                                                          }));

void FMeshBlendConfigUtils::LoadFloatFromConfig(const FString& Name)
{
	const FString DefaultEngineIni = FPaths::Combine(FPaths::ProjectDir(), "Config", "DefaultEngine.ini");
	float Value;

	if (GConfig->GetFloat(TEXT("/Script/Engine.RendererSettings"), *Name, Value, *DefaultEngineIni))
	{
		if (const auto CVar = IConsoleManager::Get().FindConsoleVariable(*Name))
		{
			CVar->Set(Value, ECVF_SetByConsole);
		}
	}
}

void FMeshBlendConfigUtils::LoadStringFromConfig(const FString& Name)
{
	const FString DefaultEngineIni = FPaths::Combine(FPaths::ProjectDir(), "Config", "DefaultEngine.ini");
	FString Value;

	if (GConfig->GetString(TEXT("/Script/Engine.RendererSettings"), *Name, Value, *DefaultEngineIni))
	{
		if (const auto CVar = IConsoleManager::Get().FindConsoleVariable(*Name))
		{
			CVar->Set(*Value, ECVF_SetByConsole);
		}
	}
}

void FMeshBlendConfigUtils::SaveFloatToConfig(const FString& Name)
{
	const FString DefaultEngineIni = FPaths::Combine(FPaths::ProjectDir(), "Config", "DefaultEngine.ini");

	if (const auto CVar = IConsoleManager::Get().FindConsoleVariable(*Name))
	{
		GConfig->SetFloat(TEXT("/Script/Engine.RendererSettings"), *Name, CVar->GetFloat(), *DefaultEngineIni);
	}
}

void FMeshBlendConfigUtils::SaveStringToConfig(const FString& Name)
{
	const FString DefaultEngineIni = FPaths::Combine(FPaths::ProjectDir(), "Config", "DefaultEngine.ini");

	if (const auto CVar = IConsoleManager::Get().FindConsoleVariable(*Name))
	{
		GConfig->SetString(TEXT("/Script/Engine.RendererSettings"), *Name, *CVar->GetString(), *DefaultEngineIni);
	}
}

void FMeshBlendConfigUtils::LoadFromConfig()
{
	const FString DefaultEngineIni = FPaths::Combine(FPaths::ProjectDir(), "Config", "DefaultEngine.ini");
	GConfig->EnableFileOperations();
	GConfig->LoadFile(*DefaultEngineIni);

	LoadFloatFromConfig(TEXT("r.MeshBlend.Small.Size"));
	LoadFloatFromConfig(TEXT("r.MeshBlend.Medium.Size"));
	LoadFloatFromConfig(TEXT("r.MeshBlend.Large.Size"));
	LoadFloatFromConfig(TEXT("r.MeshBlend.ExtraLarge.Size"));

	LoadFloatFromConfig(TEXT("r.MeshBlend.Small.MinSize"));
	LoadFloatFromConfig(TEXT("r.MeshBlend.Medium.MinSize"));
	LoadFloatFromConfig(TEXT("r.MeshBlend.Large.MinSize"));
	LoadFloatFromConfig(TEXT("r.MeshBlend.ExtraLarge.MinSize"));

	LoadFloatFromConfig(TEXT("r.MeshBlend.SlopeFactor"));
	LoadFloatFromConfig(TEXT("r.MeshBlend.FrameDither"));

	LoadFloatFromConfig(TEXT("r.MeshBlend.NoiseFactor"));
	LoadFloatFromConfig(TEXT("r.MeshBlend.NoiseFade"));
	LoadFloatFromConfig(TEXT("r.MeshBlend.NoiseOffset"));
	LoadFloatFromConfig(TEXT("r.MeshBlend.NoiseTileSize"));
	LoadStringFromConfig(TEXT("r.MeshBlend.NoiseTexture"));

	GConfig->DisableFileOperations();
}

void FMeshBlendConfigUtils::SaveToConfig()
{
	const FString DefaultEngineIni = FPaths::Combine(FPaths::ProjectDir(), "Config", "DefaultEngine.ini");
	GConfig->EnableFileOperations();
	GConfig->LoadFile(*DefaultEngineIni);

	SaveFloatToConfig(TEXT("r.MeshBlend.Small.Size"));
	SaveFloatToConfig(TEXT("r.MeshBlend.Medium.Size"));
	SaveFloatToConfig(TEXT("r.MeshBlend.Large.Size"));
	SaveFloatToConfig(TEXT("r.MeshBlend.ExtraLarge.Size"));

	SaveFloatToConfig(TEXT("r.MeshBlend.Small.MinSize"));
	SaveFloatToConfig(TEXT("r.MeshBlend.Medium.MinSize"));
	SaveFloatToConfig(TEXT("r.MeshBlend.Large.MinSize"));
	SaveFloatToConfig(TEXT("r.MeshBlend.ExtraLarge.MinSize"));

	SaveFloatToConfig(TEXT("r.MeshBlend.SlopeFactor"));
	SaveFloatToConfig(TEXT("r.MeshBlend.FrameDither"));

	SaveFloatToConfig(TEXT("r.MeshBlend.NoiseFactor"));
	SaveFloatToConfig(TEXT("r.MeshBlend.NoiseFade"));
	SaveFloatToConfig(TEXT("r.MeshBlend.NoiseOffset"));
	SaveFloatToConfig(TEXT("r.MeshBlend.NoiseTileSize"));
	SaveStringToConfig(TEXT("r.MeshBlend.NoiseTexture"));

	GConfig->Flush(false, *DefaultEngineIni);
	GConfig->DisableFileOperations();
}


void FMeshBlendConfigUtils::FixConsoleSettings()
{
	const FString DefaultEngineIni = FPaths::Combine(FPaths::ProjectDir(), "Config", "DefaultEngine.ini");
	GConfig->EnableFileOperations();
	GConfig->LoadFile(*DefaultEngineIni);
	bool bShouldRestartEditor = false;

	const FString MaterialAOName = TEXT("r.Lumen.ScreenProbeGather.MaterialAO");
	if (const auto MaterialAOCVar = IConsoleManager::Get().FindConsoleVariable(*MaterialAOName))
	{
		if (MaterialAOCVar->GetInt() != 0)
		{
			MaterialAOCVar->Set(0, ECVF_SetByConsole);
			GConfig->SetInt(TEXT("/Script/Engine.RendererSettings"), *MaterialAOName, 0, *DefaultEngineIni);
		}
	}

	const FString AllowStaticLightingName = TEXT("r.AllowStaticLighting");
	if (const auto AllowStaticLightingCVar = IConsoleManager::Get().FindConsoleVariable(*AllowStaticLightingName))
	{
		if (AllowStaticLightingCVar->GetBool() != false)
		{
			GConfig->SetBool(TEXT("/Script/Engine.RendererSettings"), *AllowStaticLightingName, false, *DefaultEngineIni);
			bShouldRestartEditor = true;
		}
	}

	GConfig->Flush(false, *DefaultEngineIni);
	GConfig->DisableFileOperations();

	if (bShouldRestartEditor)
	{
		FUnrealEdMisc::Get().RestartEditor(true);
	}
}

bool FMeshBlendConfigUtils::IsLumenMaterialAOCVarCorrect()
{
	static const auto CVarMaterialAO = IConsoleManager::Get().FindConsoleVariable(TEXT("r.Lumen.ScreenProbeGather.MaterialAO"));
	return !CVarMaterialAO || CVarMaterialAO->GetInt() == 0;
}

bool FMeshBlendConfigUtils::IsAllowStaticLightingCVarCorrect()
{
	static const auto CVarAllowStaticLighting = IConsoleManager::Get().FindConsoleVariable(TEXT("r.AllowStaticLighting"));
	return !CVarAllowStaticLighting || CVarAllowStaticLighting->GetInt() == 0;
}

#endif
