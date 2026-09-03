// Copyright Bruno Caxito. All Rights Reserved.

#include "Text/SmartTextBlock.h"

#include "Widgets/Text/SRichTextBlock.h"

#include "Utils/Tools.h"

void USmartTextBlock::SynchronizeProperties()
{
	Super::SynchronizeProperties();

	this->SetText(this->GetText());
}

void USmartTextBlock::SetText(const FText& InText)
{
	Super::SetText(InText);

	if (this->GetWorld())
	{
		if (this->MyRichTextBlock.IsValid())
		{
			this->MyRichTextBlock->SetText(
				FText::FromString(
					UTools::ReplaceVariables(
						this,
						InText.ToString(),
						this->VariablesMap,
						this->StringTables
					)
				)
			);
		}
	}
}

void USmartTextBlock::SetVariablesMap(const TMap<FName, FString>& Value)
{
	this->VariablesMap = Value;
	this->SetText(this->GetText());
}

void USmartTextBlock::SetStringTables(const TArray<UStringTable*>& Value)
{
	this->StringTables = Value;
	this->SetText(this->GetText());
}