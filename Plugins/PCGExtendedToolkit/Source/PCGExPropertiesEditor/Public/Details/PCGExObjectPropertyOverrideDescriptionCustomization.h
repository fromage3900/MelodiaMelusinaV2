// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "IPropertyTypeCustomization.h"

class IPropertyHandle;

/**
 * Inline row for the engine struct FPCGObjectPropertyOverrideDescription: [source selector] -> [target].
 * PropertyTarget auto-fills from the source (stripped of '$' / '@domain.') while it still tracks it.
 * Registered globally by FName, so it also affects stock PCG nodes that use this struct.
 */
class FPCGExObjectPropertyOverrideDescriptionCustomization : public IPropertyTypeCustomization
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

private:
	/** Fires when InputSource changes; auto-updates PropertyTarget while it is still tracking the source. */
	void OnInputSourceChanged();

	TSharedPtr<IPropertyHandle> InputSourceHandle;
	TSharedPtr<IPropertyHandle> PropertyTargetHandle;

	/** Derived target value for the last in-sync source - the tracking baseline. */
	FString TrackedDerived;
};
