// Copyright (C) Developed by Pask & OlssonDev, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "Factories/BlueprintFactory.h"
#include "ACFBaseFactory.generated.h"

//Responsible for creating the actual asset that the Asset Action has defined.
UCLASS(Blueprintable, NotBlueprintType, /*Abstract,*/ DisplayName = "Asset Factory")
class ASCENTEDITOREXTENSIONS_API UACFBaseFactory : public UBlueprintFactory
{
	GENERATED_BODY()

	public:
	
	UACFBaseFactory();

	//UObject interface implementation
	virtual void PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent) override;
	virtual uint32 GetMenuCategories() const override;
	virtual bool ConfigureProperties() override;
	virtual FString GetDefaultNewAssetName() const override;
	//End of implementation

	//UFactory interface implementation
	virtual UObject* FactoryCreateNew(UClass* InClass, UObject* InParent, FName InName, EObjectFlags Flags, UObject* Context, FFeedbackContext* Warn, FName CallingContext) override;
	virtual FText GetDisplayName() const override;
	//End of implementation

	public:

	//The name this factory should name assets when they're created. If empty, will use default name of the class.
	UPROPERTY(EditDefaultsOnly, Category= "Asset Settings")
	FString DefaultAssetName;

	//If the factory should spawn a class picker window when creating the asset.
	UPROPERTY(EditDefaultsOnly, Category="Class Picker")
	bool UseClassPicker = false;

	private:

	UPROPERTY()
	UClass* OldClass;
	
};
