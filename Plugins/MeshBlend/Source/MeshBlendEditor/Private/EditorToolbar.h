// Copyright 2024 Tore Lervik. All Rights Reserved.

#pragma once

#if WITH_EDITOR

#include "CoreMinimal.h"
#include "ToolMenus.h"

class FEditorToolbar
{
public:
	static void Startup(FToolMenuOwner Owner);
	static void Shutdown(FToolMenuOwner Owner);
	static void RegisterMenus();
	static void OpenReadme();
	static void OpenControls();
	static void OpenWidget(const FSoftObjectPath& WidgetPath);
};

#endif
