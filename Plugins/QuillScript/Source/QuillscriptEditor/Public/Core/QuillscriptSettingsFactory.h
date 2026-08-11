// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Factories/Factory.h"
#include "QuillscriptSettingsFactory.generated.h"

/**
 * Implement a factory for Quillscript settings assets.
 */
UCLASS()
class QUILLSCRIPTEDITOR_API UQuillscriptSettingsFactory final : public UFactory
{
	GENERATED_BODY()

public:
	UQuillscriptSettingsFactory();

	/** UFactory implementation */
	virtual UObject* FactoryCreateNew(UClass* InClass, UObject* InParent, FName InName, EObjectFlags Flags, UObject* Context, FFeedbackContext* Warn) override;
	virtual bool ShouldShowInNewMenu() const override;
};