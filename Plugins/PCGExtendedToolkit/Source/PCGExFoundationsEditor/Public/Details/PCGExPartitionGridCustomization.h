// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "IPropertyTypeCustomization.h"

class SWidget;

/** Inline editor for FPCGExPartitionGrid: Suffix + cell Offset on the header, the grid-size
 *  resolution / 2D mode / explicit grid / size offset folded into a single child row. */
class FPCGExPartitionGridCustomization : public IPropertyTypeCustomization
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

protected:
	/** FName editor that shows an italic, dimmed "Self" placeholder while the suffix is None. */
	static TSharedRef<SWidget> MakeSuffixWidget(const TSharedPtr<IPropertyHandle>& SuffixHandle);

	/** Inline X/Y/Z editor for the FIntVector cell offset (FIntVector exposes no default inline value widget). */
	static TSharedRef<SWidget> MakeOffsetWidget(const TSharedPtr<IPropertyHandle>& OffsetHandle);
};
