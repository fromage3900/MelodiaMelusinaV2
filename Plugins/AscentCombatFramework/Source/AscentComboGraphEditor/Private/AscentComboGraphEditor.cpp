// Copyright 1998-2019 Epic Games, Inc. All Rights Reserved.

#include "AscentComboGraphEditor.h"
#include "RerouteNodeDetailsCustomization.h"

#define LOCTEXT_NAMESPACE "FAscentComboGraphModule"

void FAscentComboGraphEditorModule::StartupModule()
{
   
    // This code will execute after your module is loaded into memory; the exact timing is specified in the .uplugin file per-module

    FPropertyEditorModule& PropertyEditorModule = FModuleManager::GetModuleChecked<FPropertyEditorModule>("PropertyEditor");

    PropertyEditorModule.RegisterCustomClassLayout("ACFRerouteNode",
        FOnGetDetailCustomizationInstance::CreateStatic(&FRerouteNodeDetailsCustomization::MakeInstance));
}

void FAscentComboGraphEditorModule::ShutdownModule()
{
    // This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
    // we call this function before unloading the module.
     
    if (FModuleManager::Get().IsModuleLoaded("PropertyEditor")) {
        FPropertyEditorModule& PropertyEditorModule = FModuleManager::GetModuleChecked<FPropertyEditorModule>("PropertyEditor");
        PropertyEditorModule.UnregisterCustomClassLayout("ACFRerouteNode");
    }
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FAscentComboGraphEditorModule, AscentComboGraphEditor)
