// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "IPropertyTypeCustomization.h"

/**
 * Compact single-row layout for FPCGExSelectorClosestMatchAxis.
 *
 * Entire axis lives on the header row so array elements preview inline:
 *   NameContent  : [property name] + Property attribute field
 *   ValueContent : Attribute name field + Weight spinner + Normalize toggle
 *
 * No CustomizeChildren -- there's no shorthand here, so nothing to expand into.
 */
class FPCGExSelectorClosestMatchAxisCustomization : public IPropertyTypeCustomization
{
public:
	static TSharedRef<IPropertyTypeCustomization> MakeInstance();

	virtual void CustomizeHeader(
		TSharedRef<IPropertyHandle> PropertyHandle,
		class FDetailWidgetRow& HeaderRow,
		IPropertyTypeCustomizationUtils& CustomizationUtils) override;

	virtual void CustomizeChildren(
		TSharedRef<IPropertyHandle> PropertyHandle,
		class IDetailChildrenBuilder& ChildBuilder,
		IPropertyTypeCustomizationUtils& CustomizationUtils) override;
};
