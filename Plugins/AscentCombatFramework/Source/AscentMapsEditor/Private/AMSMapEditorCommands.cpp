// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AMSMapEditorCommands.h"

#define LOCTEXT_NAMESPACE "FAMSMapEditorModule"

void FAMSMapEditorCommands::RegisterCommands()
{
	UI_COMMAND(PluginAction, "AMSMapEditor", "Execute AMSMapEditor action", EUserInterfaceActionType::Button, FInputChord());
}

#undef LOCTEXT_NAMESPACE
