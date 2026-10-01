// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFAttributeGraphEditorModule.h"

#include "ACFAttributeGraphPanelPinFactoryGroup.h"

TSharedPtr<FACFAttributeGraphPanelPinFactoryGroup> FACFAttributeGraphEditorModule::GetDefaultGroup() const
{
	return DefaultGroup;
}

void FACFAttributeGraphEditorModule::StartupModule()
{
	DefaultGroup = MakeShared<FACFAttributeGraphPanelPinFactoryGroup>();
	FEdGraphUtilities::RegisterVisualPinFactory(DefaultGroup);
}

void FACFAttributeGraphEditorModule::ShutdownModule()
{
	if (DefaultGroup.IsValid())
	{
		FEdGraphUtilities::UnregisterVisualPinFactory(DefaultGroup);
		DefaultGroup.Reset();
	}
}

IMPLEMENT_MODULE(FACFAttributeGraphEditorModule, AscentAttributeGraphEditor)
