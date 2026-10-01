// Copyright Epic Games, Inc. All Rights Reserved.

#include "AscentEditorCommands.h"

#define LOCTEXT_NAMESPACE "FAscentEditorModule"

void FAscentEditorCommands::RegisterCommands()
{
	UI_COMMAND(PluginAction, "AscentEditor", "Execute AscentEditor action", EUserInterfaceActionType::Button, FInputChord());
}

#undef LOCTEXT_NAMESPACE
