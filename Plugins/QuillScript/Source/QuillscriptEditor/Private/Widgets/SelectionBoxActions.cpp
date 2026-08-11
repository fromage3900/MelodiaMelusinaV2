// Copyright Bruno Caxito. All Rights Reserved.

#include "Widgets/SelectionBoxActions.h"

#include "Widgets/SelectionBox.h"

FSelectionBoxActions::FSelectionBoxActions(const uint32 InAssetCategory)
{
	this->AssetCategory = InAssetCategory;
}

uint32 FSelectionBoxActions::GetCategories()
{
	return this->AssetCategory;
}

FText FSelectionBoxActions::GetName() const
{
	return FText::FromString("Selection Box");
}

UClass* FSelectionBoxActions::GetSupportedClass() const
{
	return USelectionBox::StaticClass();
}

FColor FSelectionBoxActions::GetTypeColor() const
{
	return FColor(250, 35, 0);
}