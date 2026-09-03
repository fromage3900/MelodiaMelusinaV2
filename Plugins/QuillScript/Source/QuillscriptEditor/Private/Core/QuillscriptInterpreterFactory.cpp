// Copyright Bruno Caxito. All Rights Reserved.

#include "Core/QuillscriptInterpreterFactory.h"

#include "Kismet2/KismetEditorUtilities.h"

#include "Core/QuillscriptInterpreter.h"

UQuillscriptInterpreterFactory::UQuillscriptInterpreterFactory()
{
	this->SupportedClass = AQuillscriptInterpreter::StaticClass();
	this->bCreateNew = true;
	this->bEditAfterNew = true;
}

UObject* UQuillscriptInterpreterFactory::FactoryCreateNew(UClass* InClass, UObject* InParent, FName InName, EObjectFlags Flags, UObject* Context, FFeedbackContext* Warn)
{
	return CastChecked<UBlueprint>(
		FKismetEditorUtilities::CreateBlueprint(
			AQuillscriptInterpreter::StaticClass(),
			InParent,
			InName,
			EBlueprintType::BPTYPE_Normal,
			UBlueprint::StaticClass(),
			UBlueprintGeneratedClass::StaticClass()
		)
	);
}

bool UQuillscriptInterpreterFactory::ShouldShowInNewMenu() const
{
	return true;
}