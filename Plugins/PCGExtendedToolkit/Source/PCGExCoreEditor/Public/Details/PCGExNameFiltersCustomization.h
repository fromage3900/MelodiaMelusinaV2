// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "IPropertyTypeCustomization.h"

class SHorizontalBox;
class SWidget;

/**
 * Shared IPropertyTypeCustomization for FPCGExNameFiltersDetails (and its derivatives
 * that don't bring extra hoisted controls, e.g. FPCGExAttributeGatherDetails).
 *
 * Layout:
 *   Name:   [Property Name]
 *   Value:  [FilterMode radio]   [Ex toggle -> bPreservePCGExData]
 *
 * Children rendered normally in the body, with the hoisted properties skipped.
 * Existing EditConditionHides on Matches / CommaSeparatedNameFilter still controls
 * their visibility based on FilterMode.
 */
class PCGEXCOREEDITOR_API FPCGExNameFiltersDetailsCustomization : public IPropertyTypeCustomization
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
	/** Cache child handles from PropertyHandle. Derived overrides should call Super first. */
	virtual void CacheChildHandles(TSharedRef<IPropertyHandle> PropertyHandle);

	/** Populate the set of child property names that should be omitted from the body. */
	virtual void GetHoistedPropertyNames(TSet<FName>& OutNames) const;

	/** Build the NameContent widget. Default: the property name widget. */
	virtual TSharedRef<SWidget> BuildNameContent(TSharedRef<IPropertyHandle> PropertyHandle);

	/** Append extra trailing toggles inside the ValueContent box, right before the bPreservePCGExData toggle. */
	virtual void AppendHeaderToggles(TSharedRef<IPropertyHandle> PropertyHandle, TSharedRef<SHorizontalBox> Box);

	/** Optional IsEnabled binding applied to header and body rows. */
	virtual TAttribute<bool> GetEnabledAttribute() const;

	/** Helper used by derived classes: builds a small bool-bound toggle button with a text label. */
	static TSharedRef<SWidget> MakeBoolToggleButton(
		const TSharedPtr<IPropertyHandle>& BoolHandle,
		const FText& Label,
		const FText& Tooltip);

	TSharedPtr<IPropertyHandle> FilterModeHandle;
	TSharedPtr<IPropertyHandle> PreservePCGExDataHandle;
};

/**
 * Customization for FPCGExForwardDetails: extends the base layout with
 *   - a leading bEnabled checkbox in front of the name
 *   - a "default" toggle bound to bPreserveAttributesDefaultValue
 * The whole row (header + body) becomes disabled when bEnabled is false.
 */
class PCGEXCOREEDITOR_API FPCGExForwardDetailsCustomization : public FPCGExNameFiltersDetailsCustomization
{
public:
	static TSharedRef<IPropertyTypeCustomization> MakeInstance();

protected:
	virtual void CacheChildHandles(TSharedRef<IPropertyHandle> PropertyHandle) override;
	virtual void GetHoistedPropertyNames(TSet<FName>& OutNames) const override;
	virtual TSharedRef<SWidget> BuildNameContent(TSharedRef<IPropertyHandle> PropertyHandle) override;
	virtual void AppendHeaderToggles(TSharedRef<IPropertyHandle> PropertyHandle, TSharedRef<SHorizontalBox> Box) override;
	virtual TAttribute<bool> GetEnabledAttribute() const override;

	TSharedPtr<IPropertyHandle> EnabledHandle;
	TSharedPtr<IPropertyHandle> PreserveDefaultsHandle;
};
