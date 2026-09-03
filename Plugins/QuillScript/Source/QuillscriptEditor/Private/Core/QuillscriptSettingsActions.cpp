// Copyright Bruno Caxito. All Rights Reserved.

#include "Core/QuillscriptSettingsActions.h"

#include "Core/QuillscriptSettings.h"

FQuillscriptSettingsActions::FQuillscriptSettingsActions(const uint32 InAssetCategory)
{
	this->AssetCategory = InAssetCategory;
}

uint32 FQuillscriptSettingsActions::GetCategories()
{
	return this->AssetCategory;
}

FText FQuillscriptSettingsActions::GetName() const
{
	return FText::FromString("Settings");
}

UClass* FQuillscriptSettingsActions::GetSupportedClass() const
{
	return UQuillscriptSettings::StaticClass();
}

FColor FQuillscriptSettingsActions::GetTypeColor() const
{
	return FColor(255, 112, 67);
}