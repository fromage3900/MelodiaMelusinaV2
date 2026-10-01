// Copyright (C) Developed by Pask & OlssonDev, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "ACFAssetFactory.h"

#define LOCTEXT_NAMESPACE "UAssetCreator_AssetFactory"

UACFAssetFactory::UACFAssetFactory()
{
	SupportedClass = UACFBaseFactory::StaticClass();
	ParentClass = UACFBaseFactory::StaticClass();
	UseClassPicker = false;
}

#undef LOCTEXT_NAMESPACE
