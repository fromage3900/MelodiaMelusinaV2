// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Framework/Commands/Commands.h"



class FACFGASCommands : public TCommands<FACFGASCommands>
{
public:

    FACFGASCommands()
        : TCommands<FACFGASCommands>(TEXT("GAS Editor Commands"), NSLOCTEXT("Contexts", "AscentGASEditorCommands", "Ascent GAS Editor Commands"), NAME_None, FAppStyle::GetAppStyleSetName())
    {}
    void RegisterCommands() override;

    TSharedPtr<FUICommandInfo> OpenAttributeCreator;
};


