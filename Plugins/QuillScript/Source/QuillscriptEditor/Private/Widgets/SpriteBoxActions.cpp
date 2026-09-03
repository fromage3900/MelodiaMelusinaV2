// Copyright Bruno Caxito. All Rights Reserved.

#include "Widgets/SpriteBoxActions.h"

#include "Widgets/SpriteBox.h"


FSpriteBoxActions::FSpriteBoxActions(const uint32 InAssetCategory)
{
	this->AssetCategory = InAssetCategory;
}

uint32 FSpriteBoxActions::GetCategories()
{
	return this->AssetCategory;
}

FText FSpriteBoxActions::GetName() const
{
	return FText::FromString("Sprite Box");
}

UClass* FSpriteBoxActions::GetSupportedClass() const
{
	return USpriteBox::StaticClass();
}

FColor FSpriteBoxActions::GetTypeColor() const
{
	return FColor(248, 187, 208);
}