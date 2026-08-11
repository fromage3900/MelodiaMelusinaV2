// Copyright Bruno Caxito. All Rights Reserved.

#include "Core/QuillscriptSettingsFactory.h"

#include "Core/QuillscriptSettings.h"

UQuillscriptSettingsFactory::UQuillscriptSettingsFactory()
{
	this->SupportedClass = UQuillscriptSettings::StaticClass();
	this->bCreateNew = true;
	this->bEditAfterNew = true;
}

UObject* UQuillscriptSettingsFactory::FactoryCreateNew(UClass* InClass, UObject* InParent, FName InName, EObjectFlags Flags, UObject* Context, FFeedbackContext* Warn)
{
	return NewObject<UQuillscriptSettings>(InParent, InClass, InName, Flags);
}

bool UQuillscriptSettingsFactory::ShouldShowInNewMenu() const
{
	return true;
}