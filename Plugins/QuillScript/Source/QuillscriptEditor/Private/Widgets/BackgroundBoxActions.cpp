// Copyright Bruno Caxito. All Rights Reserved.

#include "Widgets/BackgroundBoxActions.h"

#include "Widgets/BackgroundBox.h"

FBackgroundBoxActions::FBackgroundBoxActions(const uint32 InAssetCategory)
{
	this->AssetCategory = InAssetCategory;
}

uint32 FBackgroundBoxActions::GetCategories()
{
	return this->AssetCategory;
}

FText FBackgroundBoxActions::GetName() const
{
	return FText::FromString("Background Box");
}

UClass* FBackgroundBoxActions::GetSupportedClass() const
{
	return UBackgroundBox::StaticClass();
}

FColor FBackgroundBoxActions::GetTypeColor() const
{
	return FColor(149, 117, 205);
}