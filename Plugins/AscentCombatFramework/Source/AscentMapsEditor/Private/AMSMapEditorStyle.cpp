// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AMSMapEditorStyle.h"
#include "AscentMapsEditor.h"
#include "Framework/Application/SlateApplication.h"
#include "Styling/SlateStyleRegistry.h"
#include "Slate/SlateGameResources.h"
#include "Interfaces/IPluginManager.h"
#include "Styling/SlateStyleMacros.h"


#define RootToContentDir Style->RootToContentDir

TSharedPtr<FSlateStyleSet> FAMSMapsEditorStyle::StyleInstance = nullptr;

void FAMSMapsEditorStyle::Initialize()
{
	if (!StyleInstance.IsValid())
	{
		StyleInstance = Create();
		FSlateStyleRegistry::RegisterSlateStyle(*StyleInstance);
	}
}

void FAMSMapsEditorStyle::Shutdown()
{
	FSlateStyleRegistry::UnRegisterSlateStyle(*StyleInstance);
	ensure(StyleInstance.IsUnique());
	StyleInstance.Reset();
}

FName FAMSMapsEditorStyle::GetStyleSetName()
{
	static FName StyleSetName(TEXT("AMSMapsEditorStyle"));
	return StyleSetName;
}


const FVector2D Icon32(32.0f, 32.0f);

TSharedRef< FSlateStyleSet > FAMSMapsEditorStyle::Create()
{
	TSharedRef< FSlateStyleSet > Style = MakeShareable(new FSlateStyleSet("AMSMapsEditorStyle"));
	
	// Get the plugin name dynamically using the module name
	FString PluginName = FAscentMapsEditor::GetPluginName();
	
	Style->SetContentRoot(IPluginManager::Get().FindPlugin(PluginName)->GetBaseDir() / TEXT("Resources"));

	Style->Set("AMSMapEditor.PluginAction", new IMAGE_BRUSH(TEXT("map32"), Icon32));
	return Style;
}

void FAMSMapsEditorStyle::ReloadTextures()
{
	if (FSlateApplication::IsInitialized())
	{
		FSlateApplication::Get().GetRenderer()->ReloadTextureResources();
	}
}

const ISlateStyle& FAMSMapsEditorStyle::Get()
{
	return *StyleInstance;
}
