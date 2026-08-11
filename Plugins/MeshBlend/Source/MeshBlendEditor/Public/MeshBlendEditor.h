// Copyright 2024 Tore Lervik. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "MeshBlendProcessor.h"
#include "Modules/ModuleManager.h"
#include "Styling/SlateStyle.h"

class FMeshBlendEditorModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

	static TSharedPtr<FSlateStyleSet> StyleSet;
	static TSharedPtr<class ISlateStyle> GetStyleSet();
	static void TryResetMeshActivator();

private:
	FDelegateHandle OnPreSaveWorldHandle;
	FDelegateHandle OnEndPIEHandle;
	UMeshBlendProcessor* Processor = nullptr;
	void OnPreSaveWorld(UWorld* World, FObjectPreSaveContext ObjectPreSaveContext);
	void OnEndPIE(bool bArg);
	static void CheckShaderPatchStatus();
	static void ShowShaderPatcher();
};
