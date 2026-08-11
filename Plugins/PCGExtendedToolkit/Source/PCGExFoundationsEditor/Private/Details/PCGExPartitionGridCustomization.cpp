// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Details/PCGExPartitionGridCustomization.h"

#include "DetailLayoutBuilder.h"
#include "DetailWidgetRow.h"
#include "IDetailChildrenBuilder.h"
#include "PropertyHandle.h"
#include "Details/Enums/PCGExInlineEnumCustomization.h"
#include "Elements/Utils/PCGExPartitionIdentifier.h"
#include "Styling/AppStyle.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "PCGExPartitionGridCustomization"

TSharedRef<IPropertyTypeCustomization> FPCGExPartitionGridCustomization::MakeInstance()
{
	return MakeShareable(new FPCGExPartitionGridCustomization());
}

TSharedRef<SWidget> FPCGExPartitionGridCustomization::MakeSuffixWidget(const TSharedPtr<IPropertyHandle>& SuffixHandle)
{
	FSlateFontInfo ItalicFont = IDetailLayoutBuilder::GetDetailFont();
	ItalicFont.TypefaceFontName = TEXT("Italic");

	const TSharedRef<SEditableTextBox> TextBox = SNew(SEditableTextBox)
		.Font(IDetailLayoutBuilder::GetDetailFont())
		.Text_Lambda([SuffixHandle]()
		{
			FName Value = NAME_None;
			return SuffixHandle->GetValue(Value) == FPropertyAccess::Success && !Value.IsNone()
				       ? FText::FromName(Value)
				       : FText::GetEmpty();
		})
		.OnTextCommitted_Lambda([SuffixHandle](const FText& NewText, ETextCommit::Type CommitType)
		{
			if (CommitType != ETextCommit::OnEnter && CommitType != ETextCommit::OnUserMovedFocus) { return; }
			const FString Trimmed = NewText.ToString().TrimStartAndEnd();
			SuffixHandle->SetValue(Trimmed.IsEmpty() ? NAME_None : FName(*Trimmed));
		});

	// Placeholder shows only while the suffix is None AND the box isn't being edited (the live edit
	// text would otherwise sit under it). HitTestInvisible so clicks fall through to the box.
	return SNew(SOverlay)
		+ SOverlay::Slot()
		[
			TextBox
		]
		+ SOverlay::Slot()
		.VAlign(VAlign_Center)
		.Padding(6, 0)
		[
			SNew(STextBlock)
			.Visibility_Lambda([SuffixHandle, TextBox]()
			{
				FName Value = NAME_None;
				const bool bIsNone = SuffixHandle->GetValue(Value) != FPropertyAccess::Success || Value.IsNone();
				const bool bEditing = TextBox->HasKeyboardFocus() || TextBox->HasFocusedDescendants();
				return bIsNone && !bEditing ? EVisibility::HitTestInvisible : EVisibility::Collapsed;
			})
			.Text(LOCTEXT("SuffixSelfPlaceholder", "Self"))
			.Font(ItalicFont)
			.ColorAndOpacity(FSlateColor(FLinearColor(1.f, 1.f, 1.f, 0.35f)))
		];
}

TSharedRef<SWidget> FPCGExPartitionGridCustomization::MakeOffsetWidget(const TSharedPtr<IPropertyHandle>& OffsetHandle)
{
	// FIntVector renders its X/Y/Z as expandable child rows and has no inline value widget, so build
	// one from the component handles (each int child does provide a numeric value widget).
	const TSharedRef<SHorizontalBox> Box = SNew(SHorizontalBox);

	uint32 NumChildren = 0;
	if (OffsetHandle.IsValid() && OffsetHandle->GetNumChildren(NumChildren) == FPropertyAccess::Success)
	{
		for (uint32 i = 0; i < NumChildren; ++i)
		{
			const TSharedPtr<IPropertyHandle> Component = OffsetHandle->GetChildHandle(i);
			if (!Component.IsValid()) { continue; }

			Box->AddSlot()
				.FillWidth(1.f)
				.Padding(i == 0 ? 0.f : 2.f, 0.f, 0.f, 0.f)
				[
					SNew(SBox).MinDesiredWidth(36.f)
					[
						Component->CreatePropertyValueWidget()
					]
				];
		}
	}
	return Box;
}

void FPCGExPartitionGridCustomization::CustomizeHeader(
	TSharedRef<IPropertyHandle> PropertyHandle,
	FDetailWidgetRow& HeaderRow,
	IPropertyTypeCustomizationUtils& CustomizationUtils)
{
	const TSharedPtr<IPropertyHandle> SuffixHandle = PropertyHandle->GetChildHandle(GET_MEMBER_NAME_CHECKED(FPCGExPartitionGrid, Suffix));
	const TSharedPtr<IPropertyHandle> OffsetHandle = PropertyHandle->GetChildHandle(GET_MEMBER_NAME_CHECKED(FPCGExPartitionGrid, Offset));

	HeaderRow
		.NameContent()
		[
			MakeSuffixWidget(SuffixHandle)
		]
		.ValueContent()
		.MinDesiredWidth(150)
		[
			MakeOffsetWidget(OffsetHandle)
		];
}

void FPCGExPartitionGridCustomization::CustomizeChildren(
	TSharedRef<IPropertyHandle> PropertyHandle,
	IDetailChildrenBuilder& ChildBuilder,
	IPropertyTypeCustomizationUtils& CustomizationUtils)
{
	const TSharedPtr<IPropertyHandle> ResolutionHandle = PropertyHandle->GetChildHandle(GET_MEMBER_NAME_CHECKED(FPCGExPartitionGrid, GridSizeResolution));
	const TSharedPtr<IPropertyHandle> Grid2DHandle = PropertyHandle->GetChildHandle(GET_MEMBER_NAME_CHECKED(FPCGExPartitionGrid, Grid2D));
	const TSharedPtr<IPropertyHandle> ExplicitGridHandle = PropertyHandle->GetChildHandle(GET_MEMBER_NAME_CHECKED(FPCGExPartitionGrid, ExplicitGrid));
	const TSharedPtr<IPropertyHandle> GridSizeOffsetHandle = PropertyHandle->GetChildHandle(GET_MEMBER_NAME_CHECKED(FPCGExPartitionGrid, GridSizeOffset));

	ChildBuilder.AddCustomRow(LOCTEXT("GridRowFilter", "Grid Size"))
		.NameContent()
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().Padding(0, 0, 4, 0).VAlign(VAlign_Center)
			[
				PCGExEnumCustomization::CreateRadioGroup(ResolutionHandle, TEXT("EPCGExPartitionResolution"))
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				PCGExEnumCustomization::CreateDropdown(Grid2DHandle, TEXT("EPCGExGrid2DMode"))
			]
		]
		.ValueContent()
		.MinDesiredWidth(220)
		[
			SNew(SHorizontalBox)
			// Explicit grid dropdown -- dimmed (but interactive) while the size comes from the component.
			+ SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center)
			[
				SNew(SBorder)
				.BorderImage(FAppStyle::Get().GetBrush("NoBorder"))
				.Padding(0)
				.VAlign(VAlign_Center)
				.ColorAndOpacity_Lambda([ResolutionHandle]() -> FLinearColor
				{
					uint8 Value = 0;
					const bool bFromComponent = ResolutionHandle->GetValue(Value) == FPropertyAccess::Success
						&& Value == static_cast<uint8>(EPCGExPartitionResolution::FromComponent);
					return FLinearColor(1.f, 1.f, 1.f, bFromComponent ? 0.8f : 1.f);
				})
				[
					PCGExEnumCustomization::CreateDropdown(ExplicitGridHandle, TEXT("EPCGHiGenGrid"))
				]
			]
			+ SHorizontalBox::Slot().AutoWidth().Padding(4, 0).VAlign(VAlign_Center)
			[
				SNew(STextBlock).Text(LOCTEXT("GridSizeOffsetPlus", "+")).Font(IDetailLayoutBuilder::GetDetailFont())
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				SNew(SBox).WidthOverride(52.f)
				[
					GridSizeOffsetHandle->CreatePropertyValueWidget()
				]
			]
		];
}

#undef LOCTEXT_NAMESPACE
