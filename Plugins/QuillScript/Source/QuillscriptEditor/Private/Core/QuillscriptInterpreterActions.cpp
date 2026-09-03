// Copyright Bruno Caxito. All Rights Reserved.

#include "Core/QuillscriptInterpreterActions.h"

#include "Core/QuillscriptInterpreter.h"

FQuillscriptInterpreterActions::FQuillscriptInterpreterActions(const uint32 InAssetCategory)
{
	this->AssetCategory = InAssetCategory;
}

uint32 FQuillscriptInterpreterActions::GetCategories()
{
	return this->AssetCategory;
}

FText FQuillscriptInterpreterActions::GetName() const
{
	return FText::FromString("Interpreter");
}

UClass* FQuillscriptInterpreterActions::GetSupportedClass() const
{
	return AQuillscriptInterpreter::StaticClass();
}

FColor FQuillscriptInterpreterActions::GetTypeColor() const
{
	return FColor(102, 187, 106);
}