// Copyright (C) Developed by Pask & OlssonDev, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 
#include "ACFAssetAction_AssetAction.h"

#define LOCTEXT_NAMESPACE "UAssetCreatorAction_AssetCreatorAction"

UACFAssetAction_AssetAction::UACFAssetAction_AssetAction()
{
	AssetActionSettings.AssetClass = UACFAssetAction::StaticClass();
	AssetActionSettings.CategoryName = "ACF Asset Creator";
}

#undef LOCTEXT_NAMESPACE
