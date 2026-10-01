// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFAttributeEditorModule.h"

#include "ACFAttributeCustomization.h"
#include "SACFAttributeGraphPin.h"
#include "AscentAttributeGraphEditor/Public/ACFAttributeGraphEditorModule.h"
#include "AscentAttributeGraphEditor/Public/ACFAttributeGraphPanelPinFactoryGroup.h"

#define LOCTEXT_NAMESPACE "ACFAttributeEditor"

void FACFAttributeEditorModule::StartupModule()
{
	FPropertyEditorModule& PropertyModule = FModuleManager::LoadModuleChecked<FPropertyEditorModule>("PropertyEditor");
	PropertyModule.RegisterCustomPropertyTypeLayout(
		GetFNameSafe(FGameplayAttribute::StaticStruct()),
		FOnGetPropertyTypeCustomizationInstance::CreateStatic(&FACFAttributeCustomization::MakeInstance),
		EditorIdentifier);
	

	if (!PinFactory.IsValid())
	{
		PinFactory = MakeShared<FACFAttributeGraphPanelPinFactory>();
		FACFAttributeGraphEditorModule& GraphEditorModule = FModuleManager::LoadModuleChecked<FACFAttributeGraphEditorModule>("AscentAttributeGraphEditor");
		GraphEditorModule.GetDefaultGroup()->Add(1.f, PinFactory);
	}
}

void FACFAttributeEditorModule::ShutdownModule()
{
	if (EditorIdentifier.IsValid())
	{
		if (FPropertyEditorModule* PropertyModule = FModuleManager::LoadModulePtr<FPropertyEditorModule>("PropertyEditor"))
		{
			PropertyModule->UnregisterCustomPropertyTypeLayout(GetFNameSafe(FGameplayAttribute::StaticStruct()), EditorIdentifier);
		}
		EditorIdentifier.Reset();
	}
		
	if (PinFactory.IsValid())
	{
		if (FACFAttributeGraphEditorModule* GraphEditorModule = FModuleManager::LoadModulePtr<FACFAttributeGraphEditorModule>("AscentAttributeGraphEditor"))
		{
			GraphEditorModule->GetDefaultGroup()->Remove(PinFactory);
		}
		PinFactory.Reset();
	}
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FACFAttributeEditorModule, AscentAttributeEditor);
