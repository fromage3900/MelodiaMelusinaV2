// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFAttributePalette.h"

namespace ACFAttributePalette
{
	FLinearColor GetColor(const FString& InName)
	{
		static const TArray<FLinearColor> Palette = {
			FLinearColor(0.90f, 0.40f, 0.40f),
			FLinearColor(0.40f, 0.80f, 0.40f),
			FLinearColor(0.40f, 0.60f, 1.00f),
			FLinearColor(0.95f, 0.75f, 0.35f),
			FLinearColor(0.70f, 0.50f, 0.95f),
			FLinearColor(0.35f, 0.85f, 0.85f),
			FLinearColor(0.95f, 0.55f, 0.80f),
			FLinearColor(0.85f, 0.85f, 0.40f),
			FLinearColor(1.00f, 0.60f, 0.40f),
			FLinearColor(0.55f, 0.95f, 0.55f) 
		};

		const uint32 Hash = FCrc::StrCrc32(*InName);
		const int32 Index = Hash % Palette.Num();
		return Palette[Index];
	}
}
