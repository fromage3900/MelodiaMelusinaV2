// MonolithUIStylingActions.h
#pragma once

#include "MonolithToolRegistry.h"

class FMonolithUIStylingActions
{
public:
    static void RegisterActions(FMonolithToolRegistry& Registry);

    static FMonolithActionResult HandleSetBrush(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleSetFont(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleSetColorScheme(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleBatchStyle(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleSetText(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleSetImage(const TSharedPtr<FJsonObject>& Params);
};
