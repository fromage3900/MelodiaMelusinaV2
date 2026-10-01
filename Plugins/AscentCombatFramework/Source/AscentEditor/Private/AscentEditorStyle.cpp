// Copyright Epic Games, Inc. All Rights Reserved.

#include "AscentEditorStyle.h"
#include "AscentEditor.h"
#include "Framework/Application/SlateApplication.h"
#include "Styling/SlateStyleRegistry.h"
#include "Slate/SlateGameResources.h"
#include "Interfaces/IPluginManager.h"
#include "Styling/SlateStyleMacros.h"

#define RootToContentDir Style->RootToContentDir

TSharedPtr<FSlateStyleSet> FAscentEditorStyle::StyleInstance = nullptr;


void FAscentEditorStyle::Initialize()
{
	if (!StyleInstance.IsValid())
	{
		StyleInstance = Create();
		FSlateStyleRegistry::RegisterSlateStyle(*StyleInstance);
	}
}

void FAscentEditorStyle::Shutdown()
{
	FSlateStyleRegistry::UnRegisterSlateStyle(*StyleInstance);
	ensure(StyleInstance.IsUnique());
	StyleInstance.Reset();
}

FName FAscentEditorStyle::GetStyleSetName()
{
	return StyleSetName;
}

const FVector2D Icon32x32(32.0f, 32.0f);
const FVector2D Icon20x20(20.0f, 20.0f);

static const FString IconName_ACF   = TEXT("iv");
static const FString IconName_ACFJ  = TEXT("J");

TSharedRef< FSlateStyleSet > FAscentEditorStyle::Create()
{
	const FString ResolvedPluginName = FAscentEditorModule::GetPluginName();
	TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(ResolvedPluginName);
	check(Plugin.IsValid());

	TSharedRef< FSlateStyleSet > Style = MakeShareable(new FSlateStyleSet(StyleSetName));
	Style->SetContentRoot(Plugin->GetBaseDir() / TEXT("Resources"));

	const FString& IconName = Plugin->GetDescriptor().FriendlyName.Contains(TEXT("J"))
		? IconName_ACFJ
		: IconName_ACF;

	Style->Set("AscentEditor.PluginAction", new IMAGE_BRUSH(*IconName, Icon32x32));
	Style->Set("AscentEditor.SmallIcon", new IMAGE_BRUSH(*IconName, Icon20x20));

	return Style;
}

void FAscentEditorStyle::ReloadTextures()
{
	if (FSlateApplication::IsInitialized())
	{
		FSlateApplication::Get().GetRenderer()->ReloadTextureResources();
	}
}

const ISlateStyle& FAscentEditorStyle::Get()
{
	return *StyleInstance;
}
