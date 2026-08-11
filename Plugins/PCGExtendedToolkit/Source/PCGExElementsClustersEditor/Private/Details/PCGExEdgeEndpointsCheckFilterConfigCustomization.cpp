// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Details/PCGExEdgeEndpointsCheckFilterConfigCustomization.h"

#include "DetailWidgetRow.h"
#include "IDetailChildrenBuilder.h"
#include "PropertyHandle.h"
#include "Details/Widgets/SPCGExEdgeEndpointsCheckPreview.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"

TSharedRef<IPropertyTypeCustomization> FPCGExEdgeEndpointsCheckFilterConfigCustomization::MakeInstance()
{
	return MakeShareable(new FPCGExEdgeEndpointsCheckFilterConfigCustomization());
}

void FPCGExEdgeEndpointsCheckFilterConfigCustomization::CustomizeHeader(
	TSharedRef<IPropertyHandle> PropertyHandle,
	FDetailWidgetRow& HeaderRow,
	IPropertyTypeCustomizationUtils& CustomizationUtils)
{
	UseTwoFilterSetsHandle = PropertyHandle->GetChildHandle(TEXT("bUseTwoFilterSets"));
	ModeHandle = PropertyHandle->GetChildHandle(TEXT("Mode"));
	RespectEdgeDirectionHandle = PropertyHandle->GetChildHandle(TEXT("bRespectEdgeDirection"));
	ExpectsHandle = PropertyHandle->GetChildHandle(TEXT("Expects"));
	ExpectsBHandle = PropertyHandle->GetChildHandle(TEXT("ExpectsB"));
	InvertHandle = PropertyHandle->GetChildHandle(TEXT("bInvert"));

	HeaderRow.NameContent()
	[
		PropertyHandle->CreatePropertyNameWidget()
	];
}

void FPCGExEdgeEndpointsCheckFilterConfigCustomization::CustomizeChildren(
	TSharedRef<IPropertyHandle> PropertyHandle,
	IDetailChildrenBuilder& ChildBuilder,
	IPropertyTypeCustomizationUtils& CustomizationUtils)
{
	// The single-set preview and the dual-set note are mutually exclusive on bUseTwoFilterSets.
	// One predicate parameterized by mode keeps the two rows in sync.
	auto RowVisibility = [this](const bool bForTwoFilterSets) -> EVisibility
	{
		bool bTwoFilterSets = false;
		if (UseTwoFilterSetsHandle.IsValid())
		{
			UseTwoFilterSetsHandle->GetValue(bTwoFilterSets);
		}
		return bTwoFilterSets == bForTwoFilterSets ? EVisibility::Visible : EVisibility::Collapsed;
	};

	// 1. Insert the preview widget as the first custom row (single-input mode only).
	ChildBuilder.AddCustomRow(FText::FromString(TEXT("Preview")))
	            .Visibility(TAttribute<EVisibility>::CreateLambda([RowVisibility]()
	            {
		            return RowVisibility(false);
	            }))
	            .WholeRowContent()
	[
		SNew(SBox)
		.HeightOverride(140.0f)
		[
			SAssignNew(PreviewWidget, SPCGExEdgeEndpointsCheckPreview)
			.Mode_Lambda([this]() -> EPCGExEdgeEndpointsCheckMode
			{
				uint8 Value = 0;
				if (ModeHandle.IsValid())
				{
					ModeHandle->GetValue(Value);
				}
				return static_cast<EPCGExEdgeEndpointsCheckMode>(Value);
			})
			.Expects_Lambda([this]() -> EPCGExFilterResult
			{
				uint8 Value = 0;
				if (ExpectsHandle.IsValid())
				{
					ExpectsHandle->GetValue(Value);
				}
				return static_cast<EPCGExFilterResult>(Value);
			})
			.bInvert_Lambda([this]() -> bool
			{
				bool Value = false;
				if (InvertHandle.IsValid())
				{
					InvertHandle->GetValue(Value);
				}
				return Value;
			})
		]
	];

	// 1b. Two-set note (shown instead of the truth table, which doesn't model dual-set logic).
	ChildBuilder.AddCustomRow(FText::FromString(TEXT("Two Filter Sets")))
	            .Visibility(TAttribute<EVisibility>::CreateLambda([RowVisibility]()
	            {
		            return RowVisibility(true);
	            }))
	            .WholeRowContent()
	[
		SNew(SBox)
		.Padding(8.0f)
		[
			SNew(STextBlock)
			.AutoWrapText(true)
			.Text(FText::FromString(TEXT("Two-filter-sets mode: the edge passes when one endpoint matches the 'Vtx Filters' set and the other matches 'Vtx Filters (B)'. Enable 'Respect Edge Direction' to bind the first set to Start and the second to End.")))
		]
	];

	// 2. Add all child properties normally
	uint32 NumChildren = 0;
	PropertyHandle->GetNumChildren(NumChildren);
	for (uint32 i = 0; i < NumChildren; ++i)
	{
		TSharedPtr<IPropertyHandle> Child = PropertyHandle->GetChildHandle(i);
		if (Child.IsValid())
		{
			ChildBuilder.AddProperty(Child.ToSharedRef());
		}
	}

	// 3. Register invalidation delegates
	auto InvalidatePreview = FSimpleDelegate::CreateLambda([WeakPreview = TWeakPtr<SPCGExEdgeEndpointsCheckPreview>(PreviewWidget)]()
	{
		if (TSharedPtr<SPCGExEdgeEndpointsCheckPreview> Pin = WeakPreview.Pin())
		{
			Pin->Invalidate(EInvalidateWidgetReason::Paint);
		}
	});

	auto RegisterInvalidation = [&InvalidatePreview](const TSharedPtr<IPropertyHandle>& Handle)
	{
		if (Handle.IsValid())
		{
			Handle->SetOnPropertyValueChanged(InvalidatePreview);
		}
	};

	RegisterInvalidation(UseTwoFilterSetsHandle);
	RegisterInvalidation(ModeHandle);
	RegisterInvalidation(RespectEdgeDirectionHandle);
	RegisterInvalidation(ExpectsHandle);
	RegisterInvalidation(ExpectsBHandle);
	RegisterInvalidation(InvertHandle);
}
