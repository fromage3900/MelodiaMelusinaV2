// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Factories/Factory.h"
#include "QuillscriptInterpreterFactory.generated.h"

/**
 * Implement a factory for Quillscript interpreter assets.
 */
UCLASS()
class QUILLSCRIPTEDITOR_API UQuillscriptInterpreterFactory final : public UFactory
{
	GENERATED_BODY()

public:
	UQuillscriptInterpreterFactory();

	/** UFactory implementation */
	virtual UObject* FactoryCreateNew(UClass* InClass, UObject* InParent, FName InName, EObjectFlags Flags, UObject* Context, FFeedbackContext* Warn) override;
	virtual bool ShouldShowInNewMenu() const override;
};