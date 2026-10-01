// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ANSUIWidgetRegistryDataAsset.h"

TSubclassOf<UCommonActivatableWidget> UANSUIWidgetRegistryDataAsset::FindWidgetClassForTag(FGameplayTag Tag) const
{
	if (const FANSWidgetConfig* Found = WidgetsByTag.Find(Tag))
	{
		return Found->WidgetClass;
	}
	return nullptr;
}

const FANSWidgetConfig* UANSUIWidgetRegistryDataAsset::FindConfigForTag(FGameplayTag Tag) const
{
	return WidgetsByTag.Find(Tag);
}

const FANSWidgetConfig* UANSUIWidgetRegistryDataAsset::FindConfigForClass(TSubclassOf<UCommonActivatableWidget> WidgetClass) const
{
	if (!WidgetClass)
	{
		return nullptr;
	}

	for (const auto& Pair : WidgetsByTag)
	{
		if (Pair.Value.WidgetClass == WidgetClass)
		{
			return &Pair.Value;
		}
	}

	return nullptr;
}
