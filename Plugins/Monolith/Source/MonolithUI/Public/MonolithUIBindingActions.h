// MonolithUIBindingActions.h
#pragma once

#include "MonolithToolRegistry.h"

class FMonolithUIBindingActions
{
public:
    static void RegisterActions(FMonolithToolRegistry& Registry);

    static FMonolithActionResult HandleListWidgetEvents(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleListWidgetProperties(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleSetupListView(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleGetWidgetBindings(const TSharedPtr<FJsonObject>& Params);
};
