// MonolithUISlotActions.h
#pragma once

#include "MonolithToolRegistry.h"

class FMonolithUISlotActions
{
public:
    static void RegisterActions(FMonolithToolRegistry& Registry);

    static FMonolithActionResult HandleSetSlotProperty(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleSetAnchorPreset(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleMoveWidget(const TSharedPtr<FJsonObject>& Params);
};
