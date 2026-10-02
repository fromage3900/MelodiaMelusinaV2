// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "EdGraphUtilities.h"

/**
 * Grouped Graph Panel Pin Factory for ACF.
 *
 * Allows registering multiple pin factories with priorities and overrides.
 * An instance of this class is registered early during post-init configuration,
 * which allows replacing pin factories at any later loading phase.
 */
class ASCENTATTRIBUTEGRAPHEDITOR_API FACFAttributeGraphPanelPinFactoryGroup : public FGraphPanelPinFactory
{
public:
	/**
	 * Adds a pin factory with a specified priority.
	 *
	 * @param Priority  Priority for the factory; higher values take precedence.
	 * @param Factory   The factory to add.
	 */
	void Add(const float Priority, TSharedPtr<FGraphPanelPinFactory> Factory);

	/**
	 * Removes a previously added pin factory.
	 *
	 * @param Factory  The factory to remove.
	 */
	void Remove(const TSharedPtr<FGraphPanelPinFactory>& Factory);

private:
	
	/// Internal struct storing factory and its priority.
	struct FFactoryInfo
	{
        /// Priority of the factory; higher values are preferred.
		float Priority = 0.f;

		/// The pin factory instance.
		TSharedPtr<FGraphPanelPinFactory> Factory;
	};

	/// Array of registered factories with priorities.
	TArray<FFactoryInfo> Factories;

	/**
	 * Creates a graph pin using the registered factories.
	 *
	 * @param InPin  The graph pin to create.
	 * @return A shared pointer to the created SGraphPin widget.
	 */
	virtual TSharedPtr<SGraphPin> CreatePin(UEdGraphPin* InPin) const override;
};
