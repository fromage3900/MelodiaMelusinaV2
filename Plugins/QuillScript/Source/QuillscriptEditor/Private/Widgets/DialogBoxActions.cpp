// Copyright Bruno Caxito. All Rights Reserved.

#include "Widgets/DialogBoxActions.h"

#include "Widgets/DialogBox.h"

FDialogBoxActions::FDialogBoxActions(const uint32 InAssetCategory)
{
	this->AssetCategory = InAssetCategory;
}

uint32 FDialogBoxActions::GetCategories()
{
	return this->AssetCategory;
}

FText FDialogBoxActions::GetName() const
{
	return FText::FromString("Dialog Box");
}

UClass* FDialogBoxActions::GetSupportedClass() const
{
	return UDialogBox::StaticClass();
}

FColor FDialogBoxActions::GetTypeColor() const
{
	return FColor(33, 150, 243);
}