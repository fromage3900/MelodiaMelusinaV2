// Copyright Bruno Caxito. All Rights Reserved.

#include "Text/SmartTextBlockDecorator.h"

#include "Text/SmartTextDecorator.h"


TSharedPtr<ITextDecorator> USmartTextBlockDecorator::CreateDecorator(URichTextBlock* InOwner)
{
	return MakeShareable(new FSmartTextDecorator(InOwner, this));
}

float USmartTextBlockDecorator::ConvertDelayToSeconds(FString Delay)
{
	float Unit{ 1000 };

	// Convert the unit to seconds.
	if (Delay.RemoveFromEnd("ms"))
		Unit = 1000;
	else if (Delay.RemoveFromEnd("cs"))
		Unit = 100;
	else if (Delay.RemoveFromEnd("ds"))
		Unit = 10;
	else if (Delay.RemoveFromEnd("s"))
		Unit = 1;
	else if (Delay.RemoveFromEnd("min"))
		Unit = 1 / 60;
	else if (Delay.RemoveFromEnd("h"))
		Unit = 1 / 3600;

	// Convert what left to a float.
	if (Delay.IsNumeric())
		return FCString::Atof(*Delay) / Unit;

	return 0;
}

float USmartTextBlockDecorator::CountDelayTime(FString Text)
{
	float DelayTime{ 0 };

	while (Text.Contains(DelayShortTagOpen))
	{
		FString DelayTag{ Text };
		DelayTag = DelayTag.Mid(DelayTag.Find(DelayShortTagOpen) + DelayShortTagOpen.Len());
		DelayTag = DelayTag.Left(DelayTag.Find(DelayShortTagClose));

		Text = Text.Mid(Text.Find(DelayShortTagClose) + DelayShortTagClose.Len());

		DelayTime += ConvertDelayToSeconds(DelayTag);
	}

	return DelayTime;
}