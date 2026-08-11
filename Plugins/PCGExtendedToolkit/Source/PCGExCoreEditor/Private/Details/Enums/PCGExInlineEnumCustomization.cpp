// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Details/Enums/PCGExInlineEnumCustomization.h"
#include "DetailLayoutBuilder.h"
#include "DetailWidgetRow.h"
#include "PropertyHandle.h"
#include "Framework/MultiBox/MultiBoxBuilder.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Input/SComboButton.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Layout/SUniformGridPanel.h"
#include "Widgets/Text/STextBlock.h"

namespace PCGExEnumCustomization
{
	/**
	 * Build skip indices from the property's engine-standard ValidEnumValues / InvalidEnumValues
	 * metadata, so per-property gating works through the inline customizations the same way it
	 * does through the default enum combobox.
	 */
	static TSet<int32> GetMetaSkipIndices(const TSharedPtr<IPropertyHandle>& PropertyHandle, const UEnum* Enum)
	{
		TSet<int32> SkipIndices;
		if (!PropertyHandle || !Enum)
		{
			return SkipIndices;
		}

		auto ParseIndices = [Enum](const FString& MetaString, TSet<int32>& OutIndices)
		{
			TArray<FString> Names;
			MetaString.ParseIntoArray(Names, TEXT(","), true);
			for (FString& Name : Names)
			{
				Name.TrimStartAndEndInline();
				const int32 Idx = Enum->GetIndexByNameString(Name);
				if (Idx != INDEX_NONE)
				{
					OutIndices.Add(Idx);
				}
			}
		};

		const FString& InvalidMeta = PropertyHandle->GetMetaData(TEXT("InvalidEnumValues"));
		if (!InvalidMeta.IsEmpty())
		{
			ParseIndices(InvalidMeta, SkipIndices);
		}

		const FString& ValidMeta = PropertyHandle->GetMetaData(TEXT("ValidEnumValues"));
		if (!ValidMeta.IsEmpty())
		{
			TSet<int32> ValidIndices;
			ParseIndices(ValidMeta, ValidIndices);
			if (!ValidIndices.IsEmpty())
			{
				for (int32 i = 0; i < Enum->NumEnums() - 1; ++i)
				{
					if (!ValidIndices.Contains(i))
					{
						SkipIndices.Add(i);
					}
				}
			}
		}

		return SkipIndices;
	}

	TSharedRef<SWidget> CreateRadioGroup(TSharedPtr<IPropertyHandle> PropertyHandle, UEnum* Enum)
	{
		return CreateRadioGroup(PropertyHandle, Enum, GetMetaSkipIndices(PropertyHandle, Enum));
	}

	TSharedRef<SWidget> CreateRadioGroup(const TSharedPtr<IPropertyHandle>& PropertyHandle, const FString& Enum)
	{
		return CreateRadioGroup(PropertyHandle, FindFirstObjectSafe<UEnum>(*Enum), /*SkipIndices=*/{});
	}

	TSharedRef<SWidget> CreateRadioGroup(TSharedPtr<IPropertyHandle> PropertyHandle, UEnum* Enum, const TSet<int32>& SkipIndices)
	{
		TSharedRef<SHorizontalBox> Box = SNew(SHorizontalBox);

		for (int32 i = 0; i < Enum->NumEnums() - 1; ++i)
		{
			if (Enum->HasMetaData(TEXT("Hidden"), i) || SkipIndices.Contains(i))
			{
				continue;
			}
			const FString KeyName = Enum->GetNameStringByIndex(i);

			FString IconName = Enum->GetMetaData(TEXT("ActionIcon"), i);
			if (IconName.IsEmpty())
			{
				Box->AddSlot().AutoWidth().Padding(2, 2)
				[
					SNew(SButton)
					.Text(Enum->GetDisplayNameTextByIndex(i))
					.ToolTipText(Enum->GetToolTipTextByIndex(i))
					.ButtonColorAndOpacity_Lambda(
						[PropertyHandle, KeyName]
						{
							FString CurrentValue;
							PropertyHandle->GetValueAsFormattedString(CurrentValue);
							return CurrentValue == KeyName ? FLinearColor(0.005, 0.005, 0.005, 0.8) : FLinearColor::Transparent;
						})
					.OnClicked_Lambda(
						[PropertyHandle, KeyName]()
						{
							PropertyHandle->SetValueFromFormattedString(KeyName);
							return FReply::Handled();
						})
				];
			}
			else
			{
				IconName = TEXT("PCGEx.ActionIcon.") + IconName;
				Box->AddSlot().AutoWidth().Padding(2, 2)
				[
					SNew(SButton)
					.ToolTipText(Enum->GetToolTipTextByIndex(i))
					.ButtonStyle(FAppStyle::Get(), "PCGEx.ActionIcon")
					.ButtonColorAndOpacity_Lambda(
						[PropertyHandle, KeyName]
						{
							FString CurrentValue;
							PropertyHandle->GetValueAsFormattedString(CurrentValue);
							return CurrentValue == KeyName ? FLinearColor(0.005, 0.005, 0.005, 0.8) : FLinearColor::Transparent;
						})
					.OnClicked_Lambda(
						[PropertyHandle, KeyName]()
						{
							PropertyHandle->SetValueFromFormattedString(KeyName);
							return FReply::Handled();
						})
					[
						SNew(SImage)
						.Image(FAppStyle::Get().GetBrush(*IconName))
						.ColorAndOpacity_Lambda(
							[PropertyHandle, Enum, i]
							{
								FString CurrentValue;
								PropertyHandle->GetValueAsFormattedString(CurrentValue);
								const FString KeyName = Enum->GetNameStringByIndex(i);
								return (CurrentValue == KeyName)
									? FLinearColor::White
									: FLinearColor::Gray;
							})
					]
				];
			}
		}

		return Box;
	}

	TSharedRef<SWidget> CreateRadioGroup(const TSharedPtr<IPropertyHandle>& PropertyHandle, const FString& Enum, const TSet<int32>& SkipIndices)
	{
		return CreateRadioGroup(PropertyHandle, FindFirstObjectSafe<UEnum>(*Enum), SkipIndices);
	}

	TSharedRef<SWidget> CreateRadioGroup(UEnum* Enum, TFunction<int32()> GetValue, TFunction<void(int32)> SetValue)
	{
		TSharedRef<SHorizontalBox> Box = SNew(SHorizontalBox);

		for (int32 i = 0; i < Enum->NumEnums() - 1; ++i)
		{
			if (Enum->HasMetaData(TEXT("Hidden"), i))
			{
				continue;
			}
			const int32 EnumValue = static_cast<int32>(Enum->GetValueByIndex(i));

			FString IconName = Enum->GetMetaData(TEXT("ActionIcon"), i);
			if (IconName.IsEmpty())
			{
				Box->AddSlot().AutoWidth().Padding(2, 2)
				[
					SNew(SButton)
					.Text(Enum->GetDisplayNameTextByIndex(i))
					.ToolTipText(Enum->GetToolTipTextByIndex(i))
					.ButtonColorAndOpacity_Lambda(
						[GetValue, EnumValue]
						{
							return GetValue() == EnumValue ? FLinearColor(0.005, 0.005, 0.005, 0.8) : FLinearColor::Transparent;
						})
					.OnClicked_Lambda(
						[SetValue, EnumValue]()
						{
							SetValue(EnumValue);
							return FReply::Handled();
						})
				];
			}
			else
			{
				IconName = TEXT("PCGEx.ActionIcon.") + IconName;
				Box->AddSlot().AutoWidth().Padding(2, 2)
				[
					SNew(SButton)
					.ToolTipText(Enum->GetToolTipTextByIndex(i))
					.ButtonStyle(FAppStyle::Get(), "PCGEx.ActionIcon")
					.ButtonColorAndOpacity_Lambda(
						[GetValue, EnumValue]
						{
							return GetValue() == EnumValue ? FLinearColor(0.005, 0.005, 0.005, 0.8) : FLinearColor::Transparent;
						})
					.OnClicked_Lambda(
						[SetValue, EnumValue]()
						{
							SetValue(EnumValue);
							return FReply::Handled();
						})
					[
						SNew(SImage)
						.Image(FAppStyle::Get().GetBrush(*IconName))
						.ColorAndOpacity_Lambda(
							[GetValue, EnumValue]
							{
								return GetValue() == EnumValue
									? FLinearColor::White
									: FLinearColor::Gray;
							})
					]
				];
			}
		}

		return Box;
	}

	TSharedRef<SWidget> CreateDropdown(TSharedPtr<IPropertyHandle> PropertyHandle, UEnum* Enum, const TSet<int32>& SkipIndices)
	{
		return SNew(SComboButton)
			// Default ContentPadding -- match the standard property-value enum combobox height.
			// The label below uses the smaller detail font so the visual weight stays consistent
			// with surrounding inline controls.
			.HasDownArrow(true)
			.OnGetMenuContent_Lambda([PropertyHandle, Enum, SkipIndices]() -> TSharedRef<SWidget>
			{
				FMenuBuilder MenuBuilder(/*bCloseSelfOnly=*/true, /*CommandList=*/nullptr);
				for (int32 i = 0; i < Enum->NumEnums() - 1; ++i)
				{
					if (Enum->HasMetaData(TEXT("Hidden"), i) || SkipIndices.Contains(i))
					{
						continue;
					}
					const FString KeyName = Enum->GetNameStringByIndex(i);
					MenuBuilder.AddMenuEntry(
						Enum->GetDisplayNameTextByIndex(i),
						Enum->GetToolTipTextByIndex(i),
						FSlateIcon(),
						FUIAction(
							FExecuteAction::CreateLambda([PropertyHandle, KeyName]()
							{
								PropertyHandle->SetValueFromFormattedString(KeyName);
							}),
							FCanExecuteAction(),
							FIsActionChecked::CreateLambda([PropertyHandle, KeyName]()
							{
								FString Current;
								PropertyHandle->GetValueAsFormattedString(Current);
								return Current == KeyName;
							})
						),
						NAME_None,
						EUserInterfaceActionType::RadioButton);
				}
				return MenuBuilder.MakeWidget();
			})
			.ButtonContent()
			[
				SNew(STextBlock)
				.Font(IDetailLayoutBuilder::GetDetailFont())
				.Text_Lambda([PropertyHandle, Enum]()
				{
					FString Current;
					PropertyHandle->GetValueAsFormattedString(Current);
					const int32 Idx = Enum->GetIndexByNameString(Current);
					return Idx != INDEX_NONE
						? Enum->GetDisplayNameTextByIndex(Idx)
						: FText::FromString(Current);
				})
			];
	}

	TSharedRef<SWidget> CreateDropdown(const TSharedPtr<IPropertyHandle>& PropertyHandle, const FString& Enum, const TSet<int32>& SkipIndices)
	{
		return CreateDropdown(PropertyHandle, FindFirstObjectSafe<UEnum>(*Enum), SkipIndices);
	}

	TSharedRef<SWidget> CreateCheckboxGroup(TSharedPtr<IPropertyHandle> PropertyHandle, UEnum* Enum, const TSet<int32>& SkipIndices)
	{
		TSharedRef<SHorizontalBox> Box = SNew(SHorizontalBox);

		for (int32 i = 0; i < Enum->NumEnums() - 1; ++i)
		{
			if (Enum->HasMetaData(TEXT("Hidden"), i) || SkipIndices.Contains(i))
			{
				continue;
			}

			const FString KeyName = Enum->GetNameStringByIndex(i);
			const uint8 Bit = Enum->GetValueByIndex(i); // or (1LL << i)

			auto IsActive = [PropertyHandle, Bit]() -> bool
			{
				uint8 Mask = 0;
				if (PropertyHandle->GetValue(Mask) == FPropertyAccess::Success)
				{
					return (Mask & Bit) != 0;
				}
				return false;
			};

			auto Toggle = [PropertyHandle, Bit]()
			{
				uint8 Mask = 0;
				if (PropertyHandle->GetValue(Mask) == FPropertyAccess::Success)
				{
					Mask ^= Bit;
					PropertyHandle->SetValue(Mask);
					PropertyHandle->NotifyPostChange(EPropertyChangeType::ValueSet);
				}
				return FReply::Handled();
			};

			FString IconName = Enum->GetMetaData(TEXT("ActionIcon"), i);

			if (IconName.IsEmpty())
			{
				Box->AddSlot().AutoWidth().Padding(2, 2)
				[
					SNew(SButton)
					.Text(Enum->GetDisplayNameTextByIndex(i))
					.ToolTipText(Enum->GetToolTipTextByIndex(i))
					.ButtonColorAndOpacity_Lambda(
						[IsActive]
						{
							return IsActive()
								? FLinearColor(0.005, 0.005, 0.005, 0.8)
								: FLinearColor::Transparent;
						})
					.OnClicked_Lambda(Toggle)
				];
			}
			else
			{
				IconName = TEXT("PCGEx.ActionIcon.") + IconName;

				Box->AddSlot().AutoWidth().Padding(2, 2)
				[
					SNew(SButton)
					.ToolTipText(Enum->GetToolTipTextByIndex(i))
					.ButtonStyle(FAppStyle::Get(), "PCGEx.ActionIcon")
					.ButtonColorAndOpacity_Lambda(
						[IsActive]
						{
							return IsActive()
								? FLinearColor(0.005, 0.005, 0.005, 0.8)
								: FLinearColor::Transparent;
						})
					.OnClicked_Lambda(Toggle)
					[
						SNew(SImage)
						.Image(FAppStyle::Get().GetBrush(*IconName))
						.ColorAndOpacity_Lambda(
							[IsActive]
							{
								return IsActive()
									? FLinearColor::White
									: FLinearColor::Gray;
							})
					]
				];
			}
		}

		return Box;
	}

	TSharedRef<SWidget> CreateCheckboxGroup(const TSharedPtr<IPropertyHandle>& PropertyHandle, const FString& Enum, const TSet<int32>& SkipIndices)
	{
		return CreateCheckboxGroup(PropertyHandle, FindFirstObjectSafe<UEnum>(*Enum), SkipIndices);
	}

	static int32 FindNextVisibleEnumIndex(const UEnum* Enum, int32 FromIndex)
	{
		const int32 NumValues = Enum->NumEnums() - 1;
		if (NumValues <= 0)
		{
			return INDEX_NONE;
		}
		if (FromIndex < 0)
		{
			FromIndex = -1;
		}

		for (int32 Step = 1; Step <= NumValues; ++Step)
		{
			const int32 Next = (FromIndex + Step) % NumValues;
			if (!Enum->HasMetaData(TEXT("Hidden"), Next))
			{
				return Next;
			}
		}
		return INDEX_NONE;
	}

	static bool EnumHasAnyActionIcon(const UEnum* Enum)
	{
		for (int32 i = 0; i < Enum->NumEnums() - 1; ++i)
		{
			if (Enum->HasMetaData(TEXT("Hidden"), i))
			{
				continue;
			}
			if (!Enum->GetMetaData(TEXT("ActionIcon"), i).IsEmpty())
			{
				return true;
			}
		}
		return false;
	}

	// Small "advance" glyph rendered inside cycle buttons so users can tell the button cycles.
	// Plain ASCII '>' is used so the default Slate font (Roboto) can render it without
	// falling back to DroidSansFallback (which spams "Could not find Glyph Index" warnings).
	static TSharedRef<SWidget> MakeCycleIndicator(int32 FontSize)
	{
		return SNew(STextBlock)
			.Text(FText::FromString(TEXT(">")))
			.Font(FCoreStyle::GetDefaultFontStyle("Bold", FontSize))
			.ColorAndOpacity(FSlateColor(FLinearColor(1.0f, 1.0f, 1.0f, 0.4f)));
	}

	TSharedRef<SWidget> CreateCycleButton(TSharedPtr<IPropertyHandle> PropertyHandle, UEnum* Enum)
	{
		auto ToolTip = [PropertyHandle, Enum]()
		{
			FString CurrentValue;
			PropertyHandle->GetValueAsFormattedString(CurrentValue);
			const int32 Idx = Enum->GetIndexByNameString(CurrentValue);
			return Idx != INDEX_NONE ? Enum->GetToolTipTextByIndex(Idx) : FText::GetEmpty();
		};

		auto Cycle = [PropertyHandle, Enum]()
		{
			FString CurrentValue;
			PropertyHandle->GetValueAsFormattedString(CurrentValue);
			const int32 CurrentIdx = Enum->GetIndexByNameString(CurrentValue);
			const int32 NextIdx = FindNextVisibleEnumIndex(Enum, CurrentIdx);
			if (NextIdx != INDEX_NONE)
			{
				PropertyHandle->SetValueFromFormattedString(Enum->GetNameStringByIndex(NextIdx));
			}
			return FReply::Handled();
		};

		if (!EnumHasAnyActionIcon(Enum))
		{
			return SNew(SButton)
				.HAlign(HAlign_Center)
				.VAlign(VAlign_Center)
				.ContentPadding(FMargin(2, 0))
				.ToolTipText_Lambda(ToolTip)
				.OnClicked_Lambda(Cycle)
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot()
					.VAlign(VAlign_Center)
					.AutoWidth()
					[
						SNew(STextBlock)
						.Text_Lambda([PropertyHandle, Enum]()
						{
							FString CurrentValue;
							PropertyHandle->GetValueAsFormattedString(CurrentValue);
							const int32 Idx = Enum->GetIndexByNameString(CurrentValue);
							return Idx != INDEX_NONE ? Enum->GetDisplayNameTextByIndex(Idx) : FText::FromString(TEXT("?"));
						})
					]
					+ SHorizontalBox::Slot()
					.VAlign(VAlign_Center)
					.AutoWidth()
					.Padding(FMargin(4, 0, 0, 0))
					[
						MakeCycleIndicator(7)
					]
				];
		}

		return SNew(SButton)
			.HAlign(HAlign_Center)
			.VAlign(VAlign_Center)
			.ContentPadding(FMargin(2, 0))
			.ButtonStyle(FAppStyle::Get(), "PCGEx.ActionIcon")
			.ToolTipText_Lambda(ToolTip)
			.OnClicked_Lambda(Cycle)
			[
				SNew(SOverlay)
				+ SOverlay::Slot()
				.HAlign(HAlign_Center)
				.VAlign(VAlign_Center)
				[
					SNew(SImage)
					.Image_Lambda([PropertyHandle, Enum]() -> const FSlateBrush*
					{
						FString CurrentValue;
						PropertyHandle->GetValueAsFormattedString(CurrentValue);
						const int32 Idx = Enum->GetIndexByNameString(CurrentValue);
						if (Idx == INDEX_NONE)
						{
							return FAppStyle::Get().GetDefaultBrush();
						}
						FString IconName = Enum->GetMetaData(TEXT("ActionIcon"), Idx);
						if (IconName.IsEmpty())
						{
							return FAppStyle::Get().GetDefaultBrush();
						}
						IconName = TEXT("PCGEx.ActionIcon.") + IconName;
						return FAppStyle::Get().GetBrush(*IconName);
					})
				]
				+ SOverlay::Slot()
				.HAlign(HAlign_Right)
				.VAlign(VAlign_Bottom)
				[
					MakeCycleIndicator(5)
				]
			];
	}

	TSharedRef<SWidget> CreateCycleButton(const TSharedPtr<IPropertyHandle>& PropertyHandle, const FString& Enum)
	{
		return CreateCycleButton(PropertyHandle, FindFirstObjectSafe<UEnum>(*Enum));
	}

	TSharedRef<SWidget> CreateCycleButton(UEnum* Enum, TFunction<int32()> GetValue, TFunction<void(int32)> SetValue)
	{
		auto ToolTip = [GetValue, Enum]()
		{
			const int32 Idx = Enum->GetIndexByValue(GetValue());
			return Idx != INDEX_NONE ? Enum->GetToolTipTextByIndex(Idx) : FText::GetEmpty();
		};

		auto Cycle = [GetValue, SetValue, Enum]()
		{
			const int32 CurrentIdx = Enum->GetIndexByValue(GetValue());
			const int32 NextIdx = FindNextVisibleEnumIndex(Enum, CurrentIdx);
			if (NextIdx != INDEX_NONE)
			{
				SetValue(static_cast<int32>(Enum->GetValueByIndex(NextIdx)));
			}
			return FReply::Handled();
		};

		if (!EnumHasAnyActionIcon(Enum))
		{
			return SNew(SButton)
				.HAlign(HAlign_Center)
				.VAlign(VAlign_Center)
				.ContentPadding(FMargin(2, 0))
				.ToolTipText_Lambda(ToolTip)
				.OnClicked_Lambda(Cycle)
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot()
					.VAlign(VAlign_Center)
					.AutoWidth()
					[
						SNew(STextBlock)
						.Text_Lambda([GetValue, Enum]()
						{
							const int32 Idx = Enum->GetIndexByValue(GetValue());
							return Idx != INDEX_NONE ? Enum->GetDisplayNameTextByIndex(Idx) : FText::FromString(TEXT("?"));
						})
					]
					+ SHorizontalBox::Slot()
					.VAlign(VAlign_Center)
					.AutoWidth()
					.Padding(FMargin(4, 0, 0, 0))
					[
						MakeCycleIndicator(7)
					]
				];
		}

		return SNew(SButton)
			.HAlign(HAlign_Center)
			.VAlign(VAlign_Center)
			.ContentPadding(FMargin(2, 0))
			.ButtonStyle(FAppStyle::Get(), "PCGEx.ActionIcon")
			.ToolTipText_Lambda(ToolTip)
			.OnClicked_Lambda(Cycle)
			[
				SNew(SOverlay)
				+ SOverlay::Slot()
				.HAlign(HAlign_Center)
				.VAlign(VAlign_Center)
				[
					SNew(SImage)
					.Image_Lambda([GetValue, Enum]() -> const FSlateBrush*
					{
						const int32 Idx = Enum->GetIndexByValue(GetValue());
						if (Idx == INDEX_NONE)
						{
							return FAppStyle::Get().GetDefaultBrush();
						}
						FString IconName = Enum->GetMetaData(TEXT("ActionIcon"), Idx);
						if (IconName.IsEmpty())
						{
							return FAppStyle::Get().GetDefaultBrush();
						}
						IconName = TEXT("PCGEx.ActionIcon.") + IconName;
						return FAppStyle::Get().GetBrush(*IconName);
					})
				]
				+ SOverlay::Slot()
				.HAlign(HAlign_Right)
				.VAlign(VAlign_Bottom)
				[
					MakeCycleIndicator(5)
				]
			];
	}

	TSharedRef<SWidget> CreateCheckboxGroup(UEnum* Enum, TFunction<uint8()> GetValue, TFunction<void(uint8)> SetValue, const TSet<int32>& SkipIndices)
	{
		TSharedRef<SHorizontalBox> Box = SNew(SHorizontalBox);

		for (int32 i = 0; i < Enum->NumEnums() - 1; ++i)
		{
			if (Enum->HasMetaData(TEXT("Hidden"), i) || SkipIndices.Contains(i))
			{
				continue;
			}

			const uint8 Bit = static_cast<uint8>(Enum->GetValueByIndex(i));

			auto IsActive = [GetValue, Bit]() -> bool
			{
				return (GetValue() & Bit) != 0;
			};

			auto Toggle = [GetValue, SetValue, Bit]()
			{
				SetValue(GetValue() ^ Bit);
				return FReply::Handled();
			};

			FString IconName = Enum->GetMetaData(TEXT("ActionIcon"), i);

			if (IconName.IsEmpty())
			{
				Box->AddSlot().AutoWidth().Padding(2, 2)
				[
					SNew(SButton)
					.Text(Enum->GetDisplayNameTextByIndex(i))
					.ToolTipText(Enum->GetToolTipTextByIndex(i))
					.ButtonColorAndOpacity_Lambda(
						[IsActive]
						{
							return IsActive()
								? FLinearColor(0.005, 0.005, 0.005, 0.8)
								: FLinearColor::Transparent;
						})
					.OnClicked_Lambda(Toggle)
				];
			}
			else
			{
				IconName = TEXT("PCGEx.ActionIcon.") + IconName;

				Box->AddSlot().AutoWidth().Padding(2, 2)
				[
					SNew(SButton)
					.ToolTipText(Enum->GetToolTipTextByIndex(i))
					.ButtonStyle(FAppStyle::Get(), "PCGEx.ActionIcon")
					.ButtonColorAndOpacity_Lambda(
						[IsActive]
						{
							return IsActive()
								? FLinearColor(0.005, 0.005, 0.005, 0.8)
								: FLinearColor::Transparent;
						})
					.OnClicked_Lambda(Toggle)
					[
						SNew(SImage)
						.Image(FAppStyle::Get().GetBrush(*IconName))
						.ColorAndOpacity_Lambda(
							[IsActive]
							{
								return IsActive()
									? FLinearColor::White
									: FLinearColor::Gray;
							})
					]
				];
			}
		}

		return Box;
	}
}

FPCGExInlineEnumCustomization::FPCGExInlineEnumCustomization(const FString& InEnumName)
	: EnumName(InEnumName)
{
}

void FPCGExInlineEnumCustomization::CustomizeHeader(
	TSharedRef<IPropertyHandle> PropertyHandle,
	FDetailWidgetRow& HeaderRow,
	IPropertyTypeCustomizationUtils& CustomizationUtils)
{
	UEnum* Enum = FindFirstObjectSafe<UEnum>(*EnumName);
	if (!Enum)
	{
		return;
	}

	HeaderRow.NameContent()[PropertyHandle->CreatePropertyNameWidget()]
		.ValueContent()
		.MaxDesiredWidth(400)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot()
			.AutoWidth()
			[
				SNew(SUniformGridPanel)
				+ SUniformGridPanel::Slot(0, 0)
				[
					PCGExEnumCustomization::CreateRadioGroup(PropertyHandle, Enum)
				]
			]
		];
}

void FPCGExInlineEnumCustomization::CustomizeChildren(
	TSharedRef<IPropertyHandle> PropertyHandle,
	IDetailChildrenBuilder& ChildBuilder,
	IPropertyTypeCustomizationUtils& CustomizationUtils)
{
}
