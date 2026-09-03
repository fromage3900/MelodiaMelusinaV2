// MonolithUITemplateActions.h
#pragma once

#include "MonolithToolRegistry.h"

class FMonolithUITemplateActions
{
public:
    static void RegisterActions(FMonolithToolRegistry& Registry);

    static FMonolithActionResult HandleCreateHudElement(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleCreateMenu(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleCreateSettingsPanel(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleCreateDialog(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleCreateNotificationToast(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleCreateLoadingScreen(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleCreateInventoryGrid(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleCreateSaveSlotList(const TSharedPtr<FJsonObject>& Params);
};
