// Copyright 2024 Tore Lervik. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"


class MESHBLEND_API FMeshBlendConfigUtils
{
public:
#if WITH_EDITOR

	static void LoadFloatFromConfig(const FString& Name);
	static void LoadStringFromConfig(const FString& Name);
	static void SaveFloatToConfig(const FString& Name);
	static void SaveStringToConfig(const FString& Name);

	// Loads all r.MeshBlend.* console variables from DefaultEngine.ini
	static void LoadFromConfig();

	// Saves all r.MeshBlend.* console variables to DefaultEngine.ini
	static void SaveToConfig();

	static void FixConsoleSettings();

	static bool IsLumenMaterialAOCVarCorrect();
	static bool IsAllowStaticLightingCVarCorrect();

#endif
};
