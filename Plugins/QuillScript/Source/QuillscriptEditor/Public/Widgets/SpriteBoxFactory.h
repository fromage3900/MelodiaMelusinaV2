// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Factories/Factory.h"
#include "SpriteBoxFactory.generated.h"

/**
 * Implement a factory for Sprite Box assets.
 */
UCLASS()
class QUILLSCRIPTEDITOR_API USpriteBoxFactory final : public UFactory
{
	GENERATED_BODY()

public:
	bool bUseDefault{ true };

	USpriteBoxFactory();

	/** UFactory implementation */
	virtual UObject* FactoryCreateNew(UClass* InClass, UObject* InParent, FName InName, EObjectFlags Flags, UObject* Context, FFeedbackContext* Warn) override;
	virtual bool ConfigureProperties() override;
	virtual bool ShouldShowInNewMenu() const override;
};