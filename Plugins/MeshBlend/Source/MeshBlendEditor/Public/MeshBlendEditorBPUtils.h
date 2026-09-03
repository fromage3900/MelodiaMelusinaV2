// Copyright 2024 Tore Lervik. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "EditorUtilityWidget.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MeshBlendEditorBPUtils.generated.h"

UCLASS()
class MESHBLENDEDITOR_API UMeshBlendEditorBPUtils : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "MeshBlend Internal")
	static void SetSlateThrottling(int Value);

	UFUNCTION(BlueprintCallable, Category = "MeshBlend Internal")
	static int GetSlateThrottling();

	UFUNCTION(BlueprintCallable, Category = "MeshBlend Internal")
	static void SetMeshBlendConsoleVariable(const FString Name, const float Value);

	UFUNCTION(BlueprintCallable, Category = "MeshBlend Internal")
	static float GetMeshBlendConsoleVariable(FString Name);

	UFUNCTION(BlueprintCallable, Category = "MeshBlend Internal")
	static void ResizeEditorUtilityWidget(UEditorUtilityWidget* Widget, float X, float Y);

	UFUNCTION(BlueprintCallable, Category = "MeshBlend Internal")
	static bool HasMeshBlendConsoleVariables();

	UFUNCTION(BlueprintCallable, Category = "MeshBlend Internal")
	static void TryAddMeshBlendConsoleVariables();


	static void ToggleEnabled();
	static bool IsEnabled();
	static void ToggleDebugVisualization();
	static bool GetDebugVisualization();
	static void TryResetMeshActivator();
};
