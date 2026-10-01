// Copyright (C) Developed by Pask & OlssonDev, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "ACFAssetAction_AssetFactory.h"

#include "Factory/ACFBaseFactory.h"

#define LOCTEXT_NAMESPACE "UAssetAction_AssetFactory"

UACFAssetAction_AssetFactory::UACFAssetAction_AssetFactory()
{
	AssetActionSettings.AssetClass = UACFBaseFactory::StaticClass();
	AssetActionSettings.CategoryName = "ACF Asset Creator";
}

#undef LOCTEXT_NAMESPACE