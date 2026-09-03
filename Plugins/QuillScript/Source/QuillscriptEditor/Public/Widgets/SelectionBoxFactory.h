// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Factories/Factory.h"
#include "SelectionBoxFactory.generated.h"

/**
 * Implement a factory for Selection Box assets.
 */
UCLASS()
class QUILLSCRIPTEDITOR_API USelectionBoxFactory final : public UFactory
{
	GENERATED_BODY()

public:
	bool bUseDefault{ true };

	USelectionBoxFactory();

	/** UFactory implementation */
	virtual UObject* FactoryCreateNew(UClass* InClass, UObject* InParent, FName InName, EObjectFlags Flags, UObject* Context, FFeedbackContext* Warn) override;
	virtual bool ConfigureProperties() override;
	virtual bool ShouldShowInNewMenu() const override;
};