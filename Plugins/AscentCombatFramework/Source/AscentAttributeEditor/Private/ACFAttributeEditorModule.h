// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

class FACFAttributeGraphPanelPinFactory;

class FACFAttributeEditorModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
	
private:
	TSharedPtr<FACFAttributeGraphPanelPinFactory> PinFactory;
	TSharedPtr<IPropertyTypeIdentifier> EditorIdentifier;
};
