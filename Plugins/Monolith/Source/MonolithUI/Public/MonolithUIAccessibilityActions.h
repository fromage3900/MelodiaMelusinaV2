// MonolithUIAccessibilityActions.h
#pragma once

#include "MonolithToolRegistry.h"

class FMonolithUIAccessibilityActions
{
public:
    static void RegisterActions(FMonolithToolRegistry& Registry);

    static FMonolithActionResult HandleScaffoldAccessibilitySubsystem(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleAuditAccessibility(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleSetColorblindMode(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleSetTextScale(const TSharedPtr<FJsonObject>& Params);
};
