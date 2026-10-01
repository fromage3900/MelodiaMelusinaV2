// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFGASCommands.h"



#define LOCTEXT_NAMESPACE "FACFGASCommands"

void FACFGASCommands::RegisterCommands()
{
    UI_COMMAND(OpenAttributeCreator, "Attribute Creator", "Create new Attributed in Editor",
        EUserInterfaceActionType::Button, FInputChord());
}

#undef LOCTEXT_NAMESPACE
