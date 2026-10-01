// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

class FACFAttributeGraphPanelPinFactoryGroup;

/**
 * ACF Graph Editor module.
 *
 * Provides access to the default Graph Panel Pin Factory Group
 * for EasyGas, allowing pin customization in editor graphs.
 */
class ASCENTATTRIBUTEGRAPHEDITOR_API FACFAttributeGraphEditorModule : public IModuleInterface
{
public:
	/**
	 * Returns the default FEasyGasGraphPanelPinFactoryGroup instance.
	 *
	 * This group contains the pin factories registered early in the post-init config phase,
	 * allowing overriding and customizing graph pins in editor graphs.
	 *
	 * @return Shared pointer to the default pin factory group.
	 */
	TSharedPtr<FACFAttributeGraphPanelPinFactoryGroup> GetDefaultGroup() const;

	// IModuleInterface
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
	// End of IModuleInterface

private:
	TSharedPtr<FACFAttributeGraphPanelPinFactoryGroup> DefaultGroup;
};
