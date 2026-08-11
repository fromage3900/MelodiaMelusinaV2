// Copyright 2024 Tore Lervik. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

#if WITH_EDITOR
#include "Styling/SlateStyle.h"
#endif

class ISlateStyle;

class FMeshBlendModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

#if WITH_EDITOR
	static TSharedPtr<FSlateStyleSet> StyleSet;
	static TSharedPtr<class ISlateStyle> GetStyleSet();
#endif
};
