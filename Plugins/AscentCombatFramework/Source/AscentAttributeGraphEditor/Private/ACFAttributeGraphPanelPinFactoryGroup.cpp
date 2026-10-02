// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFAttributeGraphPanelPinFactoryGroup.h"

void FACFAttributeGraphPanelPinFactoryGroup::Add(const float Priority, TSharedPtr<FGraphPanelPinFactory> Factory)
{
	if (!Factory)
		return;
	const int32 Index = Algo::LowerBoundBy(Factories, Priority, [](const FFactoryInfo& Info)
	{
		return Info.Priority;
	});
	Factories.EmplaceAt(Index, FFactoryInfo{Priority, MoveTemp(Factory)});
}

void FACFAttributeGraphPanelPinFactoryGroup::Remove(const TSharedPtr<FGraphPanelPinFactory>& Factory)
{
	const int32 Index = Factories.IndexOfByPredicate([Factory](const FFactoryInfo& Info)
	{
		return Info.Factory == Factory;
	});
	if (Index != INDEX_NONE)
	{
		Factories.RemoveAt(Index);
	}
}

TSharedPtr<SGraphPin> FACFAttributeGraphPanelPinFactoryGroup::CreatePin(UEdGraphPin* InPin) const
{
	for (const auto& [_, Factory] : Factories)
	{
		if (!Factory)
			continue;
		if (TSharedPtr<SGraphPin> VisualPin = Factory->CreatePin(InPin))
		{
			return VisualPin;
		}
	}
	return nullptr;
}
