// MonolithUIActions.h
#pragma once

#include "MonolithToolRegistry.h"

class FMonolithUIActions
{
public:
    static void RegisterActions(FMonolithToolRegistry& Registry);

    static FMonolithActionResult HandleCreateWidgetBlueprint(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleGetWidgetTree(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleAddWidget(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleRemoveWidget(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleSetWidgetProperty(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleCompileWidget(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleListWidgetTypes(const TSharedPtr<FJsonObject>& Params);
};
