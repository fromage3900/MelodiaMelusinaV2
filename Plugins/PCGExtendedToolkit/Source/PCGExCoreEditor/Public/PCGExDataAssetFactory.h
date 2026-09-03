// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Factories/Factory.h"

#include "PCGExDataAssetFactory.generated.h"

/**
 * Abstract base for UDataAsset factories.
 * Concrete subclasses set SupportedClass in their constructor.
 *
 * Usage in a header that has its own .generated.h:
 *   UCLASS()
 *   class UMyAssetFactory : public UPCGExDataAssetFactoryBase
 *   {
 *       GENERATED_BODY()
 *   public:
 *       UMyAssetFactory() { SupportedClass = UMyDataAsset::StaticClass(); }
 *   };
 */
UCLASS(Abstract)
class PCGEXCOREEDITOR_API UPCGExDataAssetFactoryBase : public UFactory
{
	GENERATED_BODY()

public:
	UPCGExDataAssetFactoryBase()
	{
		bCreateNew = true;
		bEditAfterNew = true;
	}

	virtual UObject* FactoryCreateNew(
		UClass* Class, UObject* InParent, FName Name,
		EObjectFlags Flags, UObject* Context, FFeedbackContext* Warn) override
	{
		return NewObject<UDataAsset>(InParent, SupportedClass, Name, Flags);
	}
};
