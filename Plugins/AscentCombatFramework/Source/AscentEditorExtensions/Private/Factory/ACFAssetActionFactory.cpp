// Copyright (C) Developed by Pask & OlssonDev, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "ACFAssetActionFactory.h"
#include "ACFAssetAction.h"

#define LOCTEXT_NAMESPACE "UACFAssetActionFactory"

UACFAssetActionFactory::UACFAssetActionFactory()
{
	SupportedClass = UACFAssetAction::StaticClass();
	ParentClass = UACFAssetAction::StaticClass();
	UseClassPicker = true;
}

#undef LOCTEXT_NAMESPACE
