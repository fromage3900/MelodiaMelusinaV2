// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Details/PCGExNameFiltersCustomization.h"

#include "DetailLayoutBuilder.h"
#include "DetailWidgetRow.h"
#include "IDetailChildrenBuilder.h"
#include "IDetailPropertyRow.h"
#include "PropertyHandle.h"
#include "Details/Enums/PCGExInlineEnumCustomization.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"

namespace PCGExNameFiltersCustomization
{
	const FName PName_FilterMode = TEXT("FilterMode");
	const FName PName_PreservePCGExData = TEXT("bPreservePCGExData");
	const FName PName_Enabled = TEXT("bEnabled");
	const FName PName_PreserveDefaults = TEXT("bPreserveAttributesDefaultValue");

	struct FBoolHandleBinding
	{
		TWeakPtr<IPropertyHandle> WeakHandle;

		bool Get() const
		{
			TSharedPtr<IPropertyHandle> Handle = WeakHandle.Pin();
			if (!Handle.IsValid()) { return false; }
			bool bValue = false;
			Handle->GetValue(bValue);
			return bValue;
		}

		void Set(bool bNewValue) const
		{
			if (TSharedPtr<IPropertyHandle> Handle = WeakHandle.Pin()) { Handle->SetValue(bNewValue); }
		}
	};
}

#pragma region FPCGExNameFiltersDetailsCustomization

TSharedRef<IPropertyTypeCustomization> FPCGExNameFiltersDetailsCustomization::MakeInstance()
{
	return MakeShareable(new FPCGExNameFiltersDetailsCustomization());
}

void FPCGExNameFiltersDetailsCustomization::CustomizeHeader(
	TSharedRef<IPropertyHandle> PropertyHandle,
	FDetailWidgetRow& HeaderRow,
	IPropertyTypeCustomizationUtils& CustomizationUtils)
{
	CacheChildHandles(PropertyHandle);

	const TAttribute<bool> EnabledAttr = GetEnabledAttribute();

	TSharedRef<SHorizontalBox> ValueBox = SNew(SHorizontalBox);

	if (FilterModeHandle.IsValid())
	{
		ValueBox->AddSlot().Padding(1).AutoWidth()
		[
			PCGExEnumCustomization::CreateRadioGroup(FilterModeHandle, TEXT("EPCGExAttributeFilter"))
		];
	}

	AppendHeaderToggles(PropertyHandle, ValueBox);

	if (PreservePCGExDataHandle.IsValid())
	{
		ValueBox->AddSlot().Padding(1).AutoWidth().VAlign(VAlign_Center)
		[
			MakeBoolToggleButton(
				PreservePCGExDataHandle,
				NSLOCTEXT("PCGEx", "PreservePCGExData_Label", "Ex"),
				NSLOCTEXT("PCGEx", "PreservePCGExData_Tooltip",
					"Exempt PCGEx-internal attributes & tags from filtering. Cluster-related nodes rely on these to work."))
		];
	}

	// EnabledAttr is applied to ValueContent (and the name text in BuildNameContent), but NOT to the
	// bEnabled checkbox itself -- otherwise users would have no way to re-enable a disabled row.
	HeaderRow
		.NameContent()
		[
			BuildNameContent(PropertyHandle)
		]
		.ValueContent()
		.MinDesiredWidth(300)
		[
			SNew(SBox)
			.IsEnabled(EnabledAttr)
			[
				ValueBox
			]
		];
}

void FPCGExNameFiltersDetailsCustomization::CustomizeChildren(
	TSharedRef<IPropertyHandle> PropertyHandle,
	IDetailChildrenBuilder& ChildBuilder,
	IPropertyTypeCustomizationUtils& CustomizationUtils)
{
	TSet<FName> Hoisted;
	GetHoistedPropertyNames(Hoisted);

	const TAttribute<bool> EnabledAttr = GetEnabledAttribute();

	uint32 NumChildren = 0;
	PropertyHandle->GetNumChildren(NumChildren);

	for (uint32 i = 0; i < NumChildren; ++i)
	{
		TSharedPtr<IPropertyHandle> Child = PropertyHandle->GetChildHandle(i);
		if (!Child.IsValid() || !Child->GetProperty())
		{
			continue;
		}

		const FName Name = Child->GetProperty()->GetFName();
		if (Hoisted.Contains(Name))
		{
			continue;
		}

		IDetailPropertyRow& Row = ChildBuilder.AddProperty(Child.ToSharedRef());
		Row.IsEnabled(EnabledAttr);
	}
}

void FPCGExNameFiltersDetailsCustomization::CacheChildHandles(TSharedRef<IPropertyHandle> PropertyHandle)
{
	using namespace PCGExNameFiltersCustomization;
	FilterModeHandle = PropertyHandle->GetChildHandle(PName_FilterMode);
	PreservePCGExDataHandle = PropertyHandle->GetChildHandle(PName_PreservePCGExData);
}

void FPCGExNameFiltersDetailsCustomization::GetHoistedPropertyNames(TSet<FName>& OutNames) const
{
	using namespace PCGExNameFiltersCustomization;
	OutNames.Add(PName_FilterMode);
	OutNames.Add(PName_PreservePCGExData);
}

TSharedRef<SWidget> FPCGExNameFiltersDetailsCustomization::BuildNameContent(TSharedRef<IPropertyHandle> PropertyHandle)
{
	return PropertyHandle->CreatePropertyNameWidget();
}

void FPCGExNameFiltersDetailsCustomization::AppendHeaderToggles(TSharedRef<IPropertyHandle> PropertyHandle, TSharedRef<SHorizontalBox> Box)
{
}

TAttribute<bool> FPCGExNameFiltersDetailsCustomization::GetEnabledAttribute() const
{
	return true;
}

TSharedRef<SWidget> FPCGExNameFiltersDetailsCustomization::MakeBoolToggleButton(
	const TSharedPtr<IPropertyHandle>& BoolHandle,
	const FText& Label,
	const FText& Tooltip)
{
	if (!BoolHandle.IsValid())
	{
		return SNew(SBox);
	}

	const PCGExNameFiltersCustomization::FBoolHandleBinding Bind{BoolHandle};

	return SNew(SButton)
		.ToolTipText(Tooltip)
		.ButtonStyle(FAppStyle::Get(), "PCGEx.ActionIcon")
		.ButtonColorAndOpacity_Lambda(
			[Bind]
			{
				return Bind.Get() ? FLinearColor(0.005, 0.005, 0.005, 0.8) : FLinearColor::Transparent;
			})
		.OnClicked_Lambda(
			[Bind]()
			{
				Bind.Set(!Bind.Get());
				return FReply::Handled();
			})
		[
			SNew(STextBlock)
			.Text(Label)
			.Font(IDetailLayoutBuilder::GetDetailFont())
			.ColorAndOpacity_Lambda(
				[Bind]
				{
					return Bind.Get() ? FSlateColor(FLinearColor::White) : FSlateColor::UseSubduedForeground();
				})
		];
}

#pragma endregion

#pragma region FPCGExForwardDetailsCustomization

TSharedRef<IPropertyTypeCustomization> FPCGExForwardDetailsCustomization::MakeInstance()
{
	return MakeShareable(new FPCGExForwardDetailsCustomization());
}

void FPCGExForwardDetailsCustomization::GetHoistedPropertyNames(TSet<FName>& OutNames) const
{
	using namespace PCGExNameFiltersCustomization;
	FPCGExNameFiltersDetailsCustomization::GetHoistedPropertyNames(OutNames);
	OutNames.Add(PName_Enabled);
	OutNames.Add(PName_PreserveDefaults);
}

void FPCGExForwardDetailsCustomization::CacheChildHandles(TSharedRef<IPropertyHandle> PropertyHandle)
{
	using namespace PCGExNameFiltersCustomization;
	FPCGExNameFiltersDetailsCustomization::CacheChildHandles(PropertyHandle);
	EnabledHandle = PropertyHandle->GetChildHandle(PName_Enabled);
	PreserveDefaultsHandle = PropertyHandle->GetChildHandle(PName_PreserveDefaults);
}

TSharedRef<SWidget> FPCGExForwardDetailsCustomization::BuildNameContent(TSharedRef<IPropertyHandle> PropertyHandle)
{
	TSharedRef<SHorizontalBox> Box = SNew(SHorizontalBox);

	if (EnabledHandle.IsValid())
	{
		const PCGExNameFiltersCustomization::FBoolHandleBinding Bind{EnabledHandle};

		Box->AddSlot().AutoWidth().Padding(0, 0, 4, 0).VAlign(VAlign_Center)
		[
			SNew(SCheckBox)
			.ToolTipText(NSLOCTEXT("PCGEx", "Enabled_Tooltip", "Enable / disable this block."))
			.IsChecked_Lambda(
				[Bind]() { return Bind.Get() ? ECheckBoxState::Checked : ECheckBoxState::Unchecked; })
			.OnCheckStateChanged_Lambda(
				[Bind](ECheckBoxState NewState) { Bind.Set(NewState == ECheckBoxState::Checked); })
		];
	}

	Box->AddSlot().AutoWidth().VAlign(VAlign_Center)
	[
		SNew(SBox)
		.IsEnabled(GetEnabledAttribute())
		[
			PropertyHandle->CreatePropertyNameWidget()
		]
	];

	return Box;
}

void FPCGExForwardDetailsCustomization::AppendHeaderToggles(TSharedRef<IPropertyHandle> PropertyHandle, TSharedRef<SHorizontalBox> Box)
{
	if (PreserveDefaultsHandle.IsValid())
	{
		Box->AddSlot().Padding(1).AutoWidth().VAlign(VAlign_Center)
		[
			MakeBoolToggleButton(
				PreserveDefaultsHandle,
				NSLOCTEXT("PCGEx", "PreserveDefaults_Label", "default"),
				NSLOCTEXT("PCGEx", "PreserveDefaults_Tooltip", "Preserve the attribute's default value on forwarded attributes."))
		];
	}
}

TAttribute<bool> FPCGExForwardDetailsCustomization::GetEnabledAttribute() const
{
	const PCGExNameFiltersCustomization::FBoolHandleBinding Bind{EnabledHandle};
	return TAttribute<bool>::CreateLambda([Bind]() { return Bind.Get(); });
}

#pragma endregion
