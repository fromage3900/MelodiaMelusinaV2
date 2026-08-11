// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "IPropertyTypeCustomization.h"

/**
 * Compact one-row layout for FPCGExNumericRange:
 *
 *   Range  [☐ Min  __0.0__]  [☐ Max  __1.0__]
 *
 * The two enable toggles gate their respective value fields. Hides the default
 * expandable sub-children (4 separate rows) which would otherwise crowd the
 * schema definition list.
 */
class PCGEXPROPERTIESEDITOR_API FPCGExNumericRangeCustomization : public IPropertyTypeCustomization
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
